using System;
using System.Collections;
using System.Collections.Generic;
using System.Net.WebSockets;
using System.Text;
using System.Threading;
using System.Threading.Tasks;
using UnityEngine;

/// <summary>
/// SimulationBridge.cs
/// Connects Unity to the Python FARS simulation backend via WebSocket.
/// Receives agent state JSON every frame and drives robot/human GameObjects.
/// Place on an empty GameObject in your scene called "SimulationBridge".
/// </summary>
[DefaultExecutionOrder(-100)]
public class SimulationBridge : MonoBehaviour
{
    [Header("Connection")]
    [Tooltip("Python backend WebSocket address")]
    public string serverUrl = "ws://localhost:8765";
    public float reconnectInterval = 3f;

    [Header("Status")]
    [SerializeField] private bool _connected = false;
    [SerializeField] private int _framesReceived = 0;

    // Singleton
    public static SimulationBridge Instance { get; private set; }

    // Latest state received from Python
    public SimulationState LatestState { get; private set; }

    // Events
    public event Action<SimulationState> OnStateUpdated;
    public event Action<string>           OnConnected;
    public event Action<string>           OnDisconnected;

    private ClientWebSocket _ws;
    private CancellationTokenSource _cts;
    private readonly Queue<string> _messageQueue = new Queue<string>();
    private readonly object _lock = new object();

    void Awake()
    {
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
        DontDestroyOnLoad(gameObject);
    }

    void Start()
    {
        StartCoroutine(ConnectLoop());
    }

    void Update()
    {
        // Process messages on main thread
        lock (_lock)
        {
            while (_messageQueue.Count > 0)
            {
                string msg = _messageQueue.Dequeue();
                try
                {
                    LatestState = JsonUtility.FromJson<SimulationState>(msg);
                    _framesReceived++;
                    OnStateUpdated?.Invoke(LatestState);
                }
                catch (Exception e)
                {
                    Debug.LogWarning($"[SimBridge] JSON parse error: {e.Message}");
                }
            }
        }
    }

    IEnumerator ConnectLoop()
    {
        while (true)
        {
            yield return StartCoroutine(ConnectAndReceive());
            _connected = false;
            OnDisconnected?.Invoke(serverUrl);
            Debug.Log($"[SimBridge] Disconnected. Retrying in {reconnectInterval}s...");
            yield return new WaitForSeconds(reconnectInterval);
        }
    }

    IEnumerator ConnectAndReceive()
    {
        _cts = new CancellationTokenSource();
        _ws  = new ClientWebSocket();

        Debug.Log($"[SimBridge] Connecting to {serverUrl}...");

        var connectTask = _ws.ConnectAsync(new Uri(serverUrl), _cts.Token);
        yield return new WaitUntil(() => connectTask.IsCompleted);

        if (connectTask.IsFaulted || _ws.State != WebSocketState.Open)
        {
            Debug.LogWarning($"[SimBridge] Connection failed.");
            yield break;
        }

        _connected = true;
        Debug.Log("[SimBridge] Connected!");
        OnConnected?.Invoke(serverUrl);

        // Receive loop (background thread)
        var buffer = new byte[1024 * 64];
        var receiveTask = ReceiveAsync(buffer);

        yield return new WaitUntil(() => receiveTask.IsCompleted);
    }

    async Task ReceiveAsync(byte[] buffer)
    {
        try
        {
            var sb = new StringBuilder();
            while (_ws.State == WebSocketState.Open)
            {
                sb.Clear();
                WebSocketReceiveResult result;
                do
                {
                    result = await _ws.ReceiveAsync(
                        new ArraySegment<byte>(buffer), _cts.Token);

                    if (result.MessageType == WebSocketMessageType.Close)
                    {
                        await _ws.CloseAsync(WebSocketCloseStatus.NormalClosure, "", CancellationToken.None);
                        return;
                    }
                    sb.Append(Encoding.UTF8.GetString(buffer, 0, result.Count));
                }
                while (!result.EndOfMessage);

                lock (_lock)
                {
                    _messageQueue.Enqueue(sb.ToString());
                }
            }
        }
        catch (OperationCanceledException) { }
        catch (Exception e)
        {
            Debug.LogWarning($"[SimBridge] Receive error: {e.Message}");
        }
    }

    public async void SendCommand(string command)
    {
        if (_ws == null || _ws.State != WebSocketState.Open) return;
        try
        {
            var bytes = Encoding.UTF8.GetBytes(command);
            await _ws.SendAsync(new ArraySegment<byte>(bytes),
                                WebSocketMessageType.Text, true, _cts.Token);
        }
        catch (Exception e)
        {
            Debug.LogWarning($"[SimBridge] Send error: {e.Message}");
        }
    }

    public bool IsConnected => _connected;

    void OnDestroy()
    {
        _cts?.Cancel();
        _ws?.Dispose();
    }
}


// ─── Data Structures matching Python JSON ─────────────────────────────────────

[Serializable]
public class SimulationState
{
    public RobotData[]  robots;
    public HumanData[]  humans;
    public TaskData[]   tasks;
    public MetricsData  metrics;
    public string[]     alerts;
    public float        sim_time;
}

[Serializable]
public class RobotData
{
    public int    id;
    public string state;
    public float  battery;
    public float  world_x;
    public float  world_z;
    public string current_node;
    public int    tasks_completed;
    public float  reward_signal;
    public string[] thoughts;
}

[Serializable]
public class HumanData
{
    public int    id;
    public string agent_type;
    public float  world_x;
    public float  world_z;
    public string current_node;
    public bool   needs_help;
}

[Serializable]
public class TaskData
{
    public int    id;
    public string task_type;
    public string location_node;
    public int    priority;
    public string status;
}

[Serializable]
public class MetricsData
{
    public int   pending;
    public int   active;
    public int   completed;
    public float avg_response_time;
}
