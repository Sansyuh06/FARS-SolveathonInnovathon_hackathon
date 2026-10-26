using System.Collections;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using UnityEngine;
using UnityEngine.UI;
using UnityEngine.Networking;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem;

// ======================================================================
// FARS HOSPITAL DIGITAL TWIN — UNIFIED ENHANCED SIMULATION
// ======================================================================

public class FarsSimulation : MonoBehaviour
{

    private static Shader _cachedDefaultShader = null;
    public static Shader SafeGetShader(string preferredName = "Universal Render Pipeline/Lit")
    {
        if (_cachedDefaultShader != null) return _cachedDefaultShader;
        var temp = GameObject.CreatePrimitive(PrimitiveType.Cube);
        if (temp != null && temp.GetComponent<Renderer>() != null && temp.GetComponent<Renderer>().sharedMaterial != null)
        {
            _cachedDefaultShader = temp.GetComponent<Renderer>().sharedMaterial.shader;
        }
        GameObject.Destroy(temp);
        return _cachedDefaultShader;
    }

    private List<RobotAgent> robots = new();
    private List<HumanAgent> humans = new();
    private TaskManager taskMgr;
    private DashboardUI dashboard;
    private CameraController cam;
    
    private int patientsAssisted = 0;
    private bool typingMode = false;
    private int selectedRobot = -1;

    void Start()
    {
        HospitalGraph.EnsureBuilt();
        
        cam = gameObject.AddComponent<CameraController>();
        Camera.main.backgroundColor = new Color32(12, 14, 20, 255);
        Camera.main.clearFlags = CameraClearFlags.SolidColor;
        
        var worldGO = new GameObject("HospitalWorld");
        worldGO.AddComponent<HospitalWorldGenerator>();
        
        var tmGO = new GameObject("TaskManager");
        taskMgr = tmGO.AddComponent<TaskManager>();
        
        for (int i = 0; i < 5; i++)
        {
            var go = new GameObject($"Robot_{i + 1}");
            var r = go.AddComponent<RobotAgent>();
            r.Init(i);
            robots.Add(r);
        }
        
        var rooms = HospitalGraph.GetAllRoomNodes();
        for (int i = 0; i < 15; i++)
        {
            var go = new GameObject($"Patient_{i + 1}");
            var h = go.AddComponent<HumanAgent>();
            h.Init("patient", rooms[i % rooms.Count]);
            humans.Add(h);
        }
        foreach (string role in new[] { "doctor", "nurse", "visitor" })
        {
            for (int i = 0; i < 6; i++)
            {
                var go = new GameObject($"{role}_{i + 1}");
                var h = go.AddComponent<HumanAgent>();
                h.Init(role);
                humans.Add(h);
            }
        }
        
        var canvasGO = new GameObject("HUD_Canvas");
        var canvas = canvasGO.AddComponent<Canvas>();
        canvas.renderMode = RenderMode.ScreenSpaceOverlay;
        canvasGO.AddComponent<CanvasScaler>().uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
        canvasGO.AddComponent<GraphicRaycaster>();
        
        dashboard = canvasGO.AddComponent<DashboardUI>();
        dashboard.Init(this, robots);
        
        cam.ResetOverview();
        
        StartCoroutine(BootSequence(canvasGO.transform));
    }

    IEnumerator BootSequence(Transform parent)
    {
        var bootGO = new GameObject("BootScreen");
        bootGO.transform.SetParent(parent, false);
        var img = bootGO.AddComponent<Image>();
        img.color = Color.black;
        var rt = bootGO.GetComponent<RectTransform>();
        rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one;
        rt.sizeDelta = Vector2.zero;
        
        var txtGO = new GameObject("BootText");
        txtGO.transform.SetParent(bootGO.transform, false);
        var txt = txtGO.AddComponent<Text>();
        txt.font = Font.CreateDynamicFontFromOSFont("Consolas", 24);
        txt.color = Color.green;
        txt.alignment = TextAnchor.MiddleCenter;
        var trt = txtGO.GetComponent<RectTransform>();
        trt.anchorMin = Vector2.zero; trt.anchorMax = Vector2.one;
        trt.sizeDelta = Vector2.zero;

        string[] steps = {
            "FARS DIGITAL TWIN",
            "NAVIGATION SYSTEM OK",
            "ROBOT FLEET ONLINE",
            "TASK MANAGER READY",
            "LLM INTERFACE CONNECTED"
        };

        StringBuilder sb = new();
        foreach (var step in steps)
        {
            sb.AppendLine(step);
            txt.text = sb.ToString();
            yield return new WaitForSeconds(0.3f);
        }
        yield return new WaitForSeconds(0.5f);
        
        float alpha = 1;
        while (alpha > 0)
        {
            alpha -= Time.deltaTime * 2;
            img.color = new Color(0, 0, 0, alpha);
            txt.color = new Color(0, 1, 0, alpha);
            yield return null;
        }
        Destroy(bootGO);
    }

    void Update()
    {
        float dt = Time.deltaTime;
        if (dt <= 0) return;

        HandleKeyboardInputs();

        taskMgr.AutoGenerateFromHumans(humans, dt);
        taskMgr.AssignTasks(robots);

        var completed = taskMgr.CheckCompleted(robots);
        foreach (var t in completed)
        {
            patientsAssisted++;
            foreach (var h in humans)
            {
                if (h.CurrentNode == t.LocationNode && h.NeedsHelp)
                {
                    h.FulfillHelp();
                    break;
                }
            }
            HospitalWorldGenerator.HighlightRoom(t.LocationNode);
        }

        if (dashboard != null)
        {
            int active = robots.Count(r => r.State != "idle" && r.State != "charging");
            var m = taskMgr.GetMetrics();
            dashboard.UpdateHUD(active, robots.Count, patientsAssisted, m.completed, m.avgResponse);
            dashboard.UpdateQueue(taskMgr.GetQueueDisplay());
            dashboard.UpdateRobots(robots.Select(r => r.GetInfo()).ToList());
            dashboard.UpdateAlerts(taskMgr.GetRecentAlerts());
        }
    }

    void HandleKeyboardInputs()
    {
        if (Keyboard.current.tabKey.wasPressedThisFrame)
        {
            typingMode = !typingMode;
            dashboard.SetTypingMode(typingMode);
        }

        if (typingMode) return;

        if (Keyboard.current.digit1Key.wasPressedThisFrame) { if (robots.Count > 0) SelectRobot(0); }
        if (Keyboard.current.digit2Key.wasPressedThisFrame) { if (robots.Count > 1) SelectRobot(1); }
        if (Keyboard.current.digit3Key.wasPressedThisFrame) { if (robots.Count > 2) SelectRobot(2); }
        if (Keyboard.current.digit4Key.wasPressedThisFrame) { if (robots.Count > 3) SelectRobot(3); }
        if (Keyboard.current.digit5Key.wasPressedThisFrame) { if (robots.Count > 4) SelectRobot(4); }

        if (Keyboard.current.escapeKey.wasPressedThisFrame)
        {
            selectedRobot = -1;
            dashboard.ShowFeedback("Selection cleared.");
        }

        if (Keyboard.current.homeKey.wasPressedThisFrame)
        {
            cam.ResetOverview();
            dashboard.ShowFeedback("Camera reset to overview.");
        }

        if (Mouse.current.leftButton.wasPressedThisFrame)
        {
            Ray ray = Camera.main.ScreenPointToRay(Mouse.current.position.ReadValue());
            if (Physics.Raycast(ray, out RaycastHit hit, 250f))
            {
                var r = hit.collider.GetComponentInParent<RobotAgent>();
                if (r != null)
                {
                    SelectRobot(robots.IndexOf(r));
                }
            }
        }
        
        if (Mouse.current.rightButton.wasPressedThisFrame)
        {
            Ray ray = Camera.main.ScreenPointToRay(Mouse.current.position.ReadValue());
            if (Physics.Raycast(ray, out RaycastHit hit, 250f))
            {
                if (hit.collider.name.StartsWith("Floor_"))
                {
                    string room = hit.collider.name.Substring(6);
                    SubmitCommand($"security check {room}");
                }
            }
        }
    }
    
    public void SelectRobot(int index)
    {
        selectedRobot = index;
        cam.GoToNode(robots[index].CurrentNode);
        dashboard.ShowFeedback($"SELECTED: R{selectedRobot+1}");
    }

    public void SubmitCommand(string text)
    {
        StartCoroutine(LLMRequest(text));
    }

    IEnumerator LLMRequest(string text)
    {
        dashboard.ShowFeedback("[AI] Processing command...");
        string jsonPayload = $"{{\"model\":\"llama3\",\"prompt\":\"You are the AI brain of a hospital digital twin. Parse the user command into JSON.\\nFORMAT: {{\\\"task_type\\\":\\\"assist_patient\\\"|\\\"deliver_medicine\\\"|\\\"guide_patient\\\"|\\\"security_check\\\",\\\"location_node\\\":\\\"<node>\\\",\\\"priority\\\":<1-4>,\\\"description\\\":\\\"<summary>\\\"}}\\nLOCATIONS: Room1-Room20, ICU1-ICU4, Pharmacy, EmergencyRoom, Reception, WaitingHall, MainHall, ChargingDock, StaffOffice, Entrance\\nRULES: \\\"go to room 5\\\"->Room5 (no space). \\\"go to X\\\"->security_check.\\nCOMMAND: \\\"{text}\\\"\\nReply ONLY valid JSON.\",\"stream\":false,\"format\":\"json\"}}";
        
        using UnityWebRequest req = new UnityWebRequest("http://localhost:11434/api/generate", "POST");
        byte[] bodyRaw = Encoding.UTF8.GetBytes(jsonPayload);
        req.uploadHandler = new UploadHandlerRaw(bodyRaw);
        req.downloadHandler = new DownloadHandlerBuffer();
        req.SetRequestHeader("Content-Type", "application/json");
        
        yield return req.SendWebRequest();
        
        if (req.result == UnityWebRequest.Result.Success)
        {
            try
            {
                string resp = req.downloadHandler.text;
                int respStart = resp.IndexOf("\"response\":\"") + 12;
                int respEnd = resp.IndexOf("\"", respStart);
                string innerJsonStr = resp.Substring(respStart, respEnd - respStart);
                innerJsonStr = innerJsonStr.Replace("\\\"", "\"").Replace("\\n", "");
                
                var data = ParseLLMJSON(innerJsonStr, text);
                taskMgr.CreateTask(data.type, data.loc, data.pri, data.desc);
                dashboard.ShowFeedback($"[AI] Task created: {data.type} at {data.loc}");
                HospitalWorldGenerator.HighlightRoom(data.loc);
                yield break;
            }
            catch
            {
                // Fallthrough to fallback
            }
        }
        
        // Fallback
        var fb = FallbackParse(text);
        taskMgr.CreateTask(fb.type, fb.loc, fb.pri, fb.desc);
        dashboard.ShowFeedback($"[FALLBACK] Task created: {fb.type} at {fb.loc}");
        HospitalWorldGenerator.HighlightRoom(fb.loc);
    }
    
    (string type, string loc, int pri, string desc) ParseLLMJSON(string json, string text)
    {
        string t = "security_check";
        string l = "MainHall";
        int p = 2;
        
        if (json.Contains("assist_patient")) t = "assist_patient";
        else if (json.Contains("deliver_medicine")) t = "deliver_medicine";
        else if (json.Contains("guide_patient")) t = "guide_patient";
        
        foreach (var node in HospitalGraph.GetAllNodes().Keys)
        {
            if (json.Contains(node)) { l = node; break; }
        }
        
        if (json.Contains("\"priority\":1")) p = 1;
        if (json.Contains("\"priority\":3")) p = 3;
        if (json.Contains("\"priority\":4")) p = 4;
        
        return (t, l, p, text);
    }

    (string type, string loc, int pri, string desc) FallbackParse(string text)
    {
        string tl = text.ToLower();
        string tn = tl.Replace(" ", "");
        string type = "security_check";
        int pri = 2;
        string loc = "MainHall";
        
        if (tl.Contains("medicine") || tl.Contains("deliver") || tl.Contains("pill")) { type = "deliver_medicine"; pri = 3; }
        else if (tl.Contains("guide") || tl.Contains("escort") || tl.Contains("show")) { type = "guide_patient"; pri = 1; }
        else if (tl.Contains("emergency") || tl.Contains("urgent") || tl.Contains("help")) { type = "assist_patient"; pri = 4; }
        
        foreach (var node in HospitalGraph.GetAllNodes().Keys)
        {
            if (tn.Contains(node.ToLower())) { loc = node; break; }
        }
        
        return (type, loc, pri, text);
    }
}

// ======================================================================
// HOSPITAL NAVIGATION GRAPH
// ======================================================================
public static class HospitalGraph
{
    private static Dictionary<string, Vector3> _nodes;
    private static Dictionary<string, List<string>> _edges;
    private static bool _built = false;

    public static void EnsureBuilt() { if (!_built) Build(); }
    public static Dictionary<string, Vector3> GetAllNodes() => _nodes;
    public static Vector3 GetNodePosition(string name) => _nodes.TryGetValue(name, out var p) ? p : Vector3.zero;
    public static List<string> GetAllRoomNodes() => _nodes.Keys.Where(n => n.StartsWith("Room")).ToList();
    public static List<string> GetNeighbors(string node) => _edges.TryGetValue(node, out var nb) ? nb : new List<string>();

    public static List<string> FindPath(string from, string to)
    {
        EnsureBuilt();
        if (from == to) return new List<string> { from };
        if (!_nodes.ContainsKey(from) || !_nodes.ContainsKey(to)) return new List<string> { from };

        var queue = new Queue<List<string>>();
        queue.Enqueue(new List<string> { from });
        var visited = new HashSet<string> { from };

        while (queue.Count > 0)
        {
            var path = queue.Dequeue();
            string curr = path[path.Count - 1];
            if (curr == to) return path;

            foreach (var nb in GetNeighbors(curr))
            {
                if (!visited.Contains(nb))
                {
                    visited.Add(nb);
                    var newPath = new List<string>(path) { nb };
                    queue.Enqueue(newPath);
                }
            }
        }
        return new List<string> { from };
    }

    private static void Build()
    {
        _nodes = new Dictionary<string, Vector3>();
        _edges = new Dictionary<string, List<string>>();

        N("Entrance", 0, -35); N("Reception", 0, -28); N("WaitingHall", -15, -20);
        N("MainHall", 0, 0); N("HallNorth", 0, 10); N("Pharmacy", 20, -20);
        N("EmergencyRoom", -20, -10); N("StaffOffice", 20, 10); N("ChargingDock", 0, 35);
        N("WestCorr1", -20, 0); N("WestCorr2", -20, 10); N("WestCorr3", -20, 20);
        N("EastCorr1", 20, 0); N("EastCorr2", 20, 20); N("RoomCorr1", -10, 20); N("RoomCorr2", 10, 20);
        N("Room1", -30, -5); N("Room2", -30, 5); N("Room3", -30, 15); N("Room4", -30, 25);
        N("Room5", -10, 25); N("Room6", 10, 25); N("Room7", 30, -5); N("Room8", 30, 5);
        N("Room9", 30, 15); N("Room10", 30, 25); N("Room11", -35, -15); N("Room12", -35, -5);
        N("Room13", 35, -15); N("Room14", 35, -5); N("Room15", -10, 30); N("Room16", 10, 30);
        N("Room17", -35, 10); N("Room18", -35, 20); N("Room19", 35, 10); N("Room20", 35, 20);
        N("ICU_Corr", 0, -10); N("ICU1", -10, -15); N("ICU2", 10, -15); N("ICU3", -10, -5); N("ICU4", 10, -5);

        E("Entrance", "Reception");
        E("Reception", "MainHall"); E("Reception", "WaitingHall"); E("Reception", "Pharmacy");
        E("WaitingHall", "EmergencyRoom"); E("WaitingHall", "MainHall");
        E("MainHall", "HallNorth"); E("MainHall", "WestCorr1"); E("MainHall", "EastCorr1"); E("MainHall", "ICU_Corr");
        E("HallNorth", "RoomCorr1"); E("HallNorth", "RoomCorr2"); E("HallNorth", "StaffOffice"); E("HallNorth", "ChargingDock");
        E("WestCorr1", "WestCorr2"); E("WestCorr1", "Room1"); E("WestCorr1", "Room2"); E("WestCorr1", "EmergencyRoom");
        E("WestCorr2", "WestCorr3"); E("WestCorr2", "Room3"); E("WestCorr3", "Room4"); E("WestCorr3", "RoomCorr1");
        E("EastCorr1", "EastCorr2"); E("EastCorr1", "Room7"); E("EastCorr1", "Room8"); E("EastCorr1", "Pharmacy"); E("EastCorr1", "StaffOffice");
        E("EastCorr2", "Room9"); E("EastCorr2", "Room10"); E("EastCorr2", "RoomCorr2");
        E("RoomCorr1", "Room5"); E("RoomCorr1", "Room15"); E("RoomCorr2", "Room6"); E("RoomCorr2", "Room16");
        E("EmergencyRoom", "Room11"); E("EmergencyRoom", "Room12"); E("Pharmacy", "Room13"); E("Pharmacy", "Room14");
        E("WestCorr2", "Room17"); E("WestCorr3", "Room18"); E("EastCorr1", "Room19"); E("EastCorr2", "Room20");
        E("ICU_Corr", "ICU1"); E("ICU_Corr", "ICU2"); E("ICU_Corr", "ICU3"); E("ICU_Corr", "ICU4");

        _built = true;
    }

    private static void N(string name, float x, float z) => _nodes[name] = new Vector3(x, 0, z);
    private static void E(string a, string b)
    {
        if (!_edges.ContainsKey(a)) _edges[a] = new List<string>();
        if (!_edges.ContainsKey(b)) _edges[b] = new List<string>();
        if (!_edges[a].Contains(b)) _edges[a].Add(b);
        if (!_edges[b].Contains(a)) _edges[b].Add(a);
    }
}

// ======================================================================
// 3D WORLD PROCEDURAL GENERATOR
// ======================================================================
public class HospitalWorldGenerator : MonoBehaviour
{
    private static readonly Color32 WallCol = new(20, 24, 32, 255);
    private static readonly Color32 CorridorCol = new(18, 20, 26, 255);
    private static readonly Color32 EdgeCol = new(10, 12, 16, 255);

    void Start()
    {
        GenerateFloor();
        GenerateZones();
        GenerateCorridors();
    }

    void GenerateFloor()
    {
        var floor = GameObject.CreatePrimitive(PrimitiveType.Cube);
        floor.name = "FloorBase";
        floor.transform.position = new Vector3(0, -0.05f, 0);
        floor.transform.localScale = new Vector3(250, 0.1f, 250);
        floor.GetComponent<Renderer>().material = CreateMaterial(new Color32(8, 10, 14, 255));

        for (int i = -70; i <= 70; i += 5)
        {
            MakeBar($"GridX_{i}", new Vector3(i, 0.01f, 0), new Vector3(0.04f, 0.015f, 140f), EdgeCol);
            MakeBar($"GridZ_{i}", new Vector3(0, 0.01f, i), new Vector3(140f, 0.015f, 0.04f), EdgeCol);
        }
    }

    void GenerateZones()
    {
        var nodes = HospitalGraph.GetAllNodes();
        foreach (var kv in nodes)
        {
            string name = kv.Key;
            Vector3 pos = kv.Value;
            if (name.StartsWith("RoomCorr") || name.StartsWith("WestCorr") || name.StartsWith("EastCorr") || name == "HallNorth" || name == "ICU_Corr")
                continue;

            Vector2 size = GetSize(name);
            Color32 zc = GetZoneColor(name);
            Color32 led = GetLEDColor(name);

            var floorTile = MakeBar($"Floor_{name}", pos + Vector3.up * 0.02f, new Vector3(size.x, 0.08f, size.y), zc);
            floorTile.AddComponent<BoxCollider>().size = Vector3.one;

            float hw = size.x / 2f, hh = size.y / 2f;
            MakeLED($"LED_{name}_N", pos + new Vector3(0, 0.07f, -hh), new Vector3(size.x, 0.03f, 0.06f), led);
            MakeLED($"LED_{name}_S", pos + new Vector3(0, 0.07f, hh), new Vector3(size.x, 0.03f, 0.06f), led);
            MakeLED($"LED_{name}_W", pos + new Vector3(-hw, 0.07f, 0), new Vector3(0.06f, 0.03f, size.y), led);
            MakeLED($"LED_{name}_E", pos + new Vector3(hw, 0.07f, 0), new Vector3(0.06f, 0.03f, size.y), led);

            float wh = 2.5f;
            MakeBar($"Wall_{name}_N", pos + new Vector3(0, wh/2, -hh), new Vector3(size.x + 0.2f, wh, 0.2f), WallCol);
            MakeBar($"Wall_{name}_W", pos + new Vector3(-hw, wh/2, 0), new Vector3(0.2f, wh, size.y + 0.2f), WallCol);
            MakeBar($"Wall_{name}_E", pos + new Vector3(hw, wh/2, 0), new Vector3(0.2f, wh, size.y + 0.2f), WallCol);

            float doorW = 1.8f;
            float remW = (size.x - doorW) / 2f;
            if (remW > 0.2f)
            {
                MakeBar($"WallF_{name}_L", pos + new Vector3(-hw + remW/2, wh/2, hh), new Vector3(remW, wh, 0.2f), WallCol);
                MakeBar($"WallF_{name}_R", pos + new Vector3(hw - remW/2, wh/2, hh), new Vector3(remW, wh, 0.2f), WallCol);
                MakeBar($"WallF_{name}_T", pos + new Vector3(0, wh - 0.25f, hh), new Vector3(doorW, 0.5f, 0.2f), WallCol);
            }

            CreateBillboardText(name, pos + Vector3.up * (wh + 1.2f), led);
        }
    }

    void GenerateCorridors()
    {
        var nodes = HospitalGraph.GetAllNodes();
        HashSet<string> visited = new();
        foreach (var kv in nodes)
        {
            string a = kv.Key;
            foreach (var b in HospitalGraph.GetNeighbors(a))
            {
                string id = string.Compare(a, b) < 0 ? $"{a}-{b}" : $"{b}-{a}";
                if (visited.Contains(id)) continue;
                visited.Add(id);

                Vector3 pa = nodes[a], pb = nodes[b];
                Vector3 mid = (pa + pb) / 2f;
                float length = Vector3.Distance(pa, pb);
                Vector3 dir = (pb - pa).normalized;
                float angle = Mathf.Atan2(dir.x, dir.z) * Mathf.Rad2Deg;

                var path = MakeBar($"Path_{id}", mid + Vector3.up * 0.005f, new Vector3(1.6f, 0.05f, length), CorridorCol);
                path.transform.rotation = Quaternion.Euler(0, angle, 0);

                var techLine = MakeBar($"Line_{id}", mid + Vector3.up * 0.015f, new Vector3(0.12f, 0.06f, length), new Color32(200, 160, 40, 180));
                techLine.transform.rotation = Quaternion.Euler(0, angle, 0);
            }
        }
    }

    GameObject MakeBar(string name, Vector3 pos, Vector3 scale, Color col)
    {
        var go = GameObject.CreatePrimitive(PrimitiveType.Cube);
        go.name = name;
        go.transform.position = pos;
        go.transform.localScale = scale;
        go.GetComponent<Renderer>().material = CreateMaterial(col);
        if (!name.StartsWith("Floor_") && !name.StartsWith("FloorBase"))
            Destroy(go.GetComponent<Collider>());
        return go;
    }
    
    GameObject MakeLED(string name, Vector3 pos, Vector3 scale, Color col)
    {
        var go = MakeBar(name, pos, scale, col);
        var m = go.GetComponent<Renderer>().material;
        m.EnableKeyword("_EMISSION");
        m.SetColor("_EmissionColor", col * 1.5f);
        var p = go.AddComponent<PulsingLED>();
        p.baseColor = col;
        return go;
    }

    Material CreateMaterial(Color c)
    {
        var m = new Material(FarsSimulation.SafeGetShader("Universal Render Pipeline/Lit"));
        m.color = c;
        if (c.a < 1f)
        {
            m.SetFloat("_Mode", 3);
            m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
            m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
            m.SetInt("_ZWrite", 0);
            m.EnableKeyword("_ALPHABLEND_ON");
            m.renderQueue = 3000;
        }
        return m;
    }

    void CreateBillboardText(string node, Vector3 pos, Color led)
    {
        var go = new GameObject($"Label_{node}");
        go.transform.position = pos;
        var tm = go.AddComponent<TextMesh>();
        tm.text = node.ToUpper();
        tm.fontSize = 28;
        tm.characterSize = 0.12f;
        tm.anchor = TextAnchor.MiddleCenter;
        tm.alignment = TextAlignment.Center;
        tm.color = led;
        
        var bg = GameObject.CreatePrimitive(PrimitiveType.Quad);
        bg.transform.SetParent(go.transform, false);
        bg.transform.localPosition = new Vector3(0, 0, 0.1f);
        bg.transform.localScale = new Vector3(tm.text.Length * 0.25f, 0.6f, 1);
        var m = bg.GetComponent<Renderer>().material = CreateMaterial(new Color(0, 0, 0, 0.7f));
        Destroy(bg.GetComponent<Collider>());
        
        go.AddComponent<BillboardText>();
    }

    public static void HighlightRoom(string nodeName)
    {
        Vector3 pos = HospitalGraph.GetNodePosition(nodeName);
        var ring = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        ring.transform.position = pos + Vector3.up * 0.15f;
        ring.transform.localScale = new Vector3(8, 0.05f, 8);
        var m = new Material(FarsSimulation.SafeGetShader("Universal Render Pipeline/Lit"));
        m.color = new Color32(0, 200, 255, 128);
        m.SetFloat("_Mode", 3);
        m.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        m.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        m.SetInt("_ZWrite", 0);
        m.EnableKeyword("_ALPHABLEND_ON");
        m.EnableKeyword("_EMISSION");
        m.SetColor("_EmissionColor", new Color32(0, 200, 255, 128));
        ring.GetComponent<Renderer>().material = m;
        Destroy(ring.GetComponent<Collider>());
        ring.AddComponent<ExpandingRing>();
    }

    Vector2 GetSize(string name)
    {
        if (name == "MainHall") return new Vector2(12, 10);
        if (name == "ChargingDock") return new Vector2(8, 6);
        if (name == "Entrance") return new Vector2(8, 4);
        if (name.StartsWith("Room")) return new Vector2(5, 4);
        if (name.StartsWith("ICU")) return new Vector2(6, 5);
        return new Vector2(8, 8);
    }

    Color32 GetZoneColor(string name)
    {
        if (name.StartsWith("Room")) return new Color32(20, 28, 42, 255);
        if (name.StartsWith("ICU")) return new Color32(45, 15, 20, 255);
        if (name == "Pharmacy") return new Color32(15, 38, 25, 255);
        if (name == "EmergencyRoom") return new Color32(50, 28, 12, 255);
        if (name == "WaitingHall") return new Color32(35, 18, 48, 255);
        if (name == "StaffOffice") return new Color32(15, 28, 48, 255);
        if (name == "Reception") return new Color32(24, 28, 38, 255);
        if (name == "ChargingDock") return new Color32(50, 45, 12, 255);
        return new Color32(12, 14, 18, 255);
    }

    Color32 GetLEDColor(string name)
    {
        if (name.StartsWith("Room")) return new Color32(0, 180, 255, 255);
        if (name.StartsWith("ICU")) return new Color32(255, 30, 60, 255);
        if (name == "Pharmacy") return new Color32(20, 220, 90, 255);
        if (name == "EmergencyRoom") return new Color32(255, 180, 30, 255);
        if (name == "WaitingHall") return new Color32(150, 60, 255, 255);
        return new Color32(0, 180, 255, 255);
    }
}

public class BillboardText : MonoBehaviour
{
    void LateUpdate()
    {
        if (Camera.main != null)
            transform.rotation = Quaternion.LookRotation(transform.position - Camera.main.transform.position);
    }
}

public class PulsingLED : MonoBehaviour
{
    public Color baseColor;
    private Material mat;
    private float offset;
    
    void Start()
    {
        mat = GetComponent<Renderer>().material;
        offset = transform.position.x + transform.position.z;
    }
    
    void Update()
    {
        float p = (Mathf.Sin(Time.time * 2f + offset) + 1f) * 0.5f;
        mat.SetColor("_EmissionColor", baseColor * Mathf.Lerp(0.4f, 1.5f, p));
    }
}

public class ExpandingRing : MonoBehaviour
{
    private float life = 0;
    private Material mat;
    void Start() { mat = GetComponent<Renderer>().material; }
    void Update()
    {
        life += Time.deltaTime;
        float t = life / 1.5f;
        transform.localScale = Vector3.Lerp(new Vector3(7, 0.05f, 7), new Vector3(14, 0.05f, 14), t);
        var c = mat.color;
        mat.color = new Color(c.r, c.g, c.b, 1f - t);
        if (life > 1.5f) Destroy(gameObject);
    }
}

// ======================================================================
// ROBOT AGENT FSM & VISUALS
// ======================================================================
public class RobotAgent : MonoBehaviour
{
    public int RobotId;
    public string State = "idle";
    public float Battery = 100f;
    public string CurrentNode = "ChargingDock";
    
    private TaskData currentTask;
    private List<TaskData> history = new();
    private List<string> path = new();
    private int pathIdx;
    private float taskTimer;
    private float animTime;
    
    private Color32 themeColor;
    private Transform modelPivot;
    private LineRenderer line;
    private TextMesh label, status;
    private GameObject groundGlow, antennaLight;
    private Material glowMat, antMat;

    private static readonly Color32[] PALETTE = {
        new Color32(0,200,255,255), new Color32(255,100,100,255),
        new Color32(100,255,100,255), new Color32(255,200,50,255),
        new Color32(200,100,255,255)
    };

    public void Init(int id)
    {
        RobotId = id;
        themeColor = PALETTE[id % PALETTE.Length];
        
        Vector3 dockPos = HospitalGraph.GetNodePosition("ChargingDock");
        transform.position = dockPos + new Vector3((id - 2) * 2.0f, 0.6f, 0);

        BuildRobotMesh();
    }

    void BuildRobotMesh()
    {
        modelPivot = new GameObject("Visuals").transform;
        modelPivot.SetParent(transform, false);

        var body = GameObject.CreatePrimitive(PrimitiveType.Cube);
        body.transform.SetParent(modelPivot, false);
        body.transform.localScale = new Vector3(1.2f, 1.4f, 1.2f);
        var bm = body.GetComponent<Renderer>().material;
        bm.color = themeColor;
        bm.EnableKeyword("_EMISSION");
        bm.SetColor("_EmissionColor", (Color)themeColor * 0.2f);
        Destroy(body.GetComponent<Collider>());

        var chest = GameObject.CreatePrimitive(PrimitiveType.Cube);
        chest.transform.SetParent(modelPivot, false);
        chest.transform.localPosition = new Vector3(0, 0.1f, 0.61f);
        chest.transform.localScale = new Vector3(0.8f, 0.6f, 0.1f);
        chest.GetComponent<Renderer>().material.color = new Color32(20, 24, 30, 255);
        Destroy(chest.GetComponent<Collider>());

        var head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        head.transform.SetParent(modelPivot, false);
        head.transform.localPosition = new Vector3(0, 0.9f, 0);
        head.transform.localScale = new Vector3(1.0f, 0.6f, 1.0f);
        head.GetComponent<Renderer>().material.color = new Color32(120, 130, 145, 255);
        Destroy(head.GetComponent<Collider>());

        var eye = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        eye.transform.SetParent(modelPivot, false);
        eye.transform.localPosition = new Vector3(0, 0.95f, 0.45f);
        eye.transform.localScale = Vector3.one * 0.25f;
        var em = eye.GetComponent<Renderer>().material;
        em.color = themeColor;
        em.EnableKeyword("_EMISSION");
        em.SetColor("_EmissionColor", (Color)themeColor * 2f);
        Destroy(eye.GetComponent<Collider>());

        var ant = GameObject.CreatePrimitive(PrimitiveType.Cube);
        ant.transform.SetParent(modelPivot, false);
        ant.transform.localPosition = new Vector3(0, 1.35f, 0);
        ant.transform.localScale = new Vector3(0.06f, 0.5f, 0.06f);
        ant.GetComponent<Renderer>().material.color = Color.gray;
        Destroy(ant.GetComponent<Collider>());
        
        antennaLight = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        antennaLight.transform.SetParent(modelPivot, false);
        antennaLight.transform.localPosition = new Vector3(0, 1.6f, 0);
        antennaLight.transform.localScale = Vector3.one * 0.15f;
        antMat = antennaLight.GetComponent<Renderer>().material;
        antMat.color = themeColor;
        antMat.EnableKeyword("_EMISSION");
        Destroy(antennaLight.GetComponent<Collider>());

        for (int s = -1; s <= 1; s += 2)
        {
            var tread = GameObject.CreatePrimitive(PrimitiveType.Cube);
            tread.transform.SetParent(modelPivot, false);
            tread.transform.localPosition = new Vector3(s * 0.5f, -0.6f, 0);
            tread.transform.localScale = new Vector3(0.4f, 0.4f, 0.8f);
            tread.GetComponent<Renderer>().material.color = new Color32(20, 24, 30, 255);
            Destroy(tread.GetComponent<Collider>());
        }
        
        groundGlow = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        groundGlow.transform.SetParent(transform, false);
        groundGlow.transform.localPosition = new Vector3(0, -0.55f, 0);
        groundGlow.transform.localScale = new Vector3(2.5f, 0.01f, 2.5f);
        glowMat = new Material(FarsSimulation.SafeGetShader("Universal Render Pipeline/Lit"));
        glowMat.color = new Color(themeColor.r/255f, themeColor.g/255f, themeColor.b/255f, 0.2f);
        glowMat.SetFloat("_Mode", 3);
        glowMat.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        glowMat.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        glowMat.SetInt("_ZWrite", 0);
        glowMat.EnableKeyword("_ALPHABLEND_ON");
        glowMat.EnableKeyword("_EMISSION");
        groundGlow.GetComponent<Renderer>().material = glowMat;
        Destroy(groundGlow.GetComponent<Collider>());

        var lgo = new GameObject("Label");
        lgo.transform.SetParent(transform, false);
        lgo.transform.localPosition = new Vector3(0, 2.5f, 0);
        label = lgo.AddComponent<TextMesh>();
        label.text = $"R{RobotId + 1}";
        label.fontSize = 32;
        label.characterSize = 0.1f;
        label.anchor = TextAnchor.MiddleCenter;
        label.color = Color.white;
        lgo.AddComponent<BillboardText>();

        var lineGO = new GameObject("PathLine");
        lineGO.transform.SetParent(transform, false);
        line = lineGO.AddComponent<LineRenderer>();
        line.startWidth = 0.3f; line.endWidth = 0.1f;
        line.material = new Material(FarsSimulation.SafeGetShader("Sprites/Default"));
        line.startColor = new Color(themeColor.r / 255f, themeColor.g / 255f, themeColor.b / 255f, 0.6f);
        line.endColor = new Color(themeColor.r / 255f, themeColor.g / 255f, themeColor.b / 255f, 0.0f);
        line.positionCount = 0;
        line.textureMode = LineTextureMode.Tile;

        var col = gameObject.AddComponent<BoxCollider>();
        col.size = new Vector3(1.4f, 2.5f, 1.4f);
        col.center = new Vector3(0, 0.6f, 0);
    }

    void Update()
    {
        float dt = Time.deltaTime;
        animTime += dt;

        float pulse = (Mathf.Sin(animTime * 4f + RobotId) + 1f) * 0.5f;
        antMat.SetColor("_EmissionColor", (Color)themeColor * Mathf.Lerp(0.5f, 2f, pulse));
        glowMat.color = new Color(themeColor.r/255f, themeColor.g/255f, themeColor.b/255f, Mathf.Lerp(0.1f, 0.3f, pulse));
        
        if (State != "idle" && State != "charging")
            groundGlow.transform.localScale = Vector3.one * Mathf.Lerp(2.2f, 2.8f, pulse) + Vector3.up * 0.01f;
        else
            groundGlow.transform.localScale = new Vector3(2.5f, 0.01f, 2.5f);

        if (modelPivot != null && State != "idle" && State != "charging")
        {
            modelPivot.localPosition = new Vector3(0, Mathf.Sin(animTime * 12f) * 0.05f, 0);
        }

        if (State == "charging")
        {
            Battery = Mathf.Min(100f, Battery + 10f * dt);
            if (Battery >= 100f) State = "idle";
            return;
        }

        if (State == "navigating" || State == "returning")
        {
            MoveAlongPath(dt);
            DrawPathAnim(dt);
        }
        else if (State == "executing")
        {
            taskTimer -= dt;
            if (taskTimer <= 0) CompleteTask();
        }
    }

    void MoveAlongPath(float dt)
    {
        if (pathIdx >= path.Count) { Arrive(); return; }

        Vector3 targetPos = HospitalGraph.GetNodePosition(path[pathIdx]) + Vector3.up * 0.6f;
        Vector3 dir = targetPos - transform.position;
        float dist = dir.magnitude;

        if (dist < 0.25f)
        {
            transform.position = targetPos;
            CurrentNode = path[pathIdx];
            pathIdx++;
        }
        else
        {
            float step = Mathf.Min(8.0f * dt, dist);
            transform.position += (dir / dist) * step;
            Quaternion rot = Quaternion.LookRotation(new Vector3(dir.x, 0, dir.z));
            transform.rotation = Quaternion.Slerp(transform.rotation, rot, dt * 10f);
        }

        Battery = Mathf.Max(0f, Battery - 0.05f * dt);
        if (Battery <= 0f) AbortToDock();
    }
    
    void DrawPathAnim(float dt)
    {
        if (line.positionCount > 0)
        {
            line.SetPosition(0, transform.position - Vector3.up * 0.4f);
            line.material.mainTextureOffset = new Vector2(-animTime * 2f, 0);
        }
    }

    void Arrive()
    {
        ClearLine();
        if (State == "returning")
        {
            State = "charging";
            return;
        }

        if (currentTask != null)
        {
            State = "executing";
            taskTimer = 3.0f;
        }
        else
        {
            State = "idle";
        }
    }

    void CompleteTask()
    {
        if (currentTask != null)
        {
            currentTask.Status = "completed";
            currentTask.CompletedTime = Time.time;
            history.Add(currentTask);
            SpawnStarburst();
            currentTask = null;
        }
        
        path.Clear();
        if (Battery < 15f) AbortToDock();
        else State = "idle";
    }

    void SpawnStarburst()
    {
        for(int i = 0; i < 12; i++)
        {
            var p = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            p.transform.position = transform.position;
            p.transform.localScale = Vector3.one * 0.3f;
            var m = p.GetComponent<Renderer>().material = new Material(FarsSimulation.SafeGetShader("Universal Render Pipeline/Lit"));
            m.color = themeColor;
            m.EnableKeyword("_EMISSION");
            m.SetColor("_EmissionColor", (Color)themeColor * 2f);
            Destroy(p.GetComponent<Collider>());
            p.AddComponent<ParticleMover>().vel = Random.onUnitSphere * 4f + Vector3.up * 2f;
        }
    }

    void AbortToDock()
    {
        if (currentTask != null) { currentTask.Status = "pending"; currentTask = null; }
        State = "returning";
        path = HospitalGraph.FindPath(CurrentNode, "ChargingDock");
        pathIdx = 0;
        DrawPath();
    }

    public void AssignTask(TaskData task)
    {
        currentTask = task;
        State = "navigating";
        path = HospitalGraph.FindPath(CurrentNode, task.LocationNode);
        pathIdx = 0;
        DrawPath();
    }

    public bool IsAvailable() => State == "idle" && Battery > 15f;

    void DrawPath()
    {
        if (line == null) return;
        line.positionCount = path.Count - pathIdx + 1;
        line.SetPosition(0, transform.position - Vector3.up * 0.4f);
        for (int i = pathIdx; i < path.Count; i++)
            line.SetPosition(i - pathIdx + 1, HospitalGraph.GetNodePosition(path[i]) + Vector3.up * 0.15f);
    }

    void ClearLine() { if (line != null) line.positionCount = 0; }

    public Dictionary<string, string> GetInfo()
    {
        return new Dictionary<string, string>
        {
            ["id"] = $"R{RobotId + 1}",
            ["state"] = State,
            ["battery"] = Battery.ToString("F0"),
            ["location"] = CurrentNode,
            ["current_task"] = currentTask?.TaskType ?? "None",
            ["tasks_completed"] = history.Count.ToString(),
            ["thoughts"] = State == "charging" ? "> Commencing inductive load..." : "> Path logic nominal."
        };
    }
}

public class ParticleMover : MonoBehaviour
{
    public Vector3 vel;
    void Update()
    {
        transform.position += vel * Time.deltaTime;
        transform.localScale *= (1f - Time.deltaTime * 2f);
        if (transform.localScale.x < 0.05f) Destroy(gameObject);
    }
}

// ======================================================================
// HUMAN AGENT (WANDERING & REQUESTING HELP)
// ======================================================================
public class HumanAgent : MonoBehaviour
{
    public string Role;
    public string CurrentNode;
    public bool NeedsHelp;
    public string HelpType;

    private List<string> path = new();
    private int pathIdx;
    private float idleTimer;
    private float helpRequestTimer;
    private float animTime;
    
    private GameObject alertGlow;
    private Color32 roleColor;
    private Transform modelPivot;

    public void Init(string role, string homeRoom = null)
    {
        Role = role;
        CurrentNode = !string.IsNullOrEmpty(homeRoom) ? homeRoom : "Reception";

        Vector3 pos = HospitalGraph.GetNodePosition(CurrentNode);
        transform.position = pos + new Vector3(Random.Range(-1.5f, 1.5f), 0.5f, Random.Range(-1.5f, 1.5f));

        roleColor = role switch
        {
            "patient" => new Color32(230, 180, 40, 255),
            "doctor" => new Color32(40, 200, 120, 255),
            "nurse" => new Color32(60, 160, 255, 255),
            _ => new Color32(180, 100, 240, 255)
        };

        idleTimer = Random.Range(3f, 9f);
        helpRequestTimer = role == "patient" ? Random.Range(20f, 60f) : 999999f;

        BuildVisuals();
    }

    void BuildVisuals()
    {
        modelPivot = new GameObject("Visuals").transform;
        modelPivot.SetParent(transform, false);

        var torso = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        torso.transform.SetParent(modelPivot, false);
        torso.transform.localScale = new Vector3(0.5f, 0.6f, 0.5f);
        var tm = torso.GetComponent<Renderer>().material = new Material(FarsSimulation.SafeGetShader("Universal Render Pipeline/Lit"));
        tm.color = roleColor;
        Destroy(torso.GetComponent<Collider>());

        var head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        head.transform.SetParent(modelPivot, false);
        head.transform.localPosition = new Vector3(0, 0.8f, 0);
        head.transform.localScale = Vector3.one * 0.4f;
        head.GetComponent<Renderer>().material.color = new Color32(220, 185, 150, 255);
        Destroy(head.GetComponent<Collider>());
        
        var shadow = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
        shadow.transform.SetParent(transform, false);
        shadow.transform.localPosition = new Vector3(0, -0.48f, 0);
        shadow.transform.localScale = new Vector3(0.8f, 0.01f, 0.8f);
        var sm = shadow.GetComponent<Renderer>().material = new Material(FarsSimulation.SafeGetShader("Universal Render Pipeline/Lit"));
        sm.color = new Color(0,0,0, 0.3f);
        sm.SetFloat("_Mode", 3);
        sm.SetInt("_SrcBlend", (int)UnityEngine.Rendering.BlendMode.SrcAlpha);
        sm.SetInt("_DstBlend", (int)UnityEngine.Rendering.BlendMode.OneMinusSrcAlpha);
        sm.SetInt("_ZWrite", 0);
        sm.EnableKeyword("_ALPHABLEND_ON");
        Destroy(shadow.GetComponent<Collider>());

        alertGlow = GameObject.CreatePrimitive(PrimitiveType.Sphere);
        alertGlow.transform.SetParent(transform, false);
        alertGlow.transform.localPosition = new Vector3(0, 1.4f, 0);
        alertGlow.transform.localScale = Vector3.one * 0.3f;
        var am = alertGlow.GetComponent<Renderer>().material;
        am.color = Color.red;
        am.EnableKeyword("_EMISSION");
        am.SetColor("_EmissionColor", Color.red * 2f);
        alertGlow.SetActive(false);
        Destroy(alertGlow.GetComponent<Collider>());
    }

    void Update()
    {
        float dt = Time.deltaTime;
        animTime += dt;

        if (path.Count > 0)
        {
            modelPivot.localPosition = new Vector3(0, Mathf.Sin(animTime * 12f) * 0.06f, 0);
            MoveAlongPath(dt);
        }
        else
        {
            modelPivot.localPosition = Vector3.zero;
            idleTimer -= dt;
            if (idleTimer <= 0) Wander();
        }

        if (Role == "patient")
        {
            helpRequestTimer -= dt;
            if (helpRequestTimer <= 0 && !NeedsHelp) TriggerHelpRequest();
        }

        if (NeedsHelp && alertGlow != null)
        {
            float p = (Mathf.Sin(animTime * 6f) + 1f) * 0.5f;
            alertGlow.transform.localScale = Vector3.one * Mathf.Lerp(0.2f, 0.35f, p);
        }
    }

    void Wander()
    {
        var nodes = HospitalGraph.GetAllNodes().Keys.ToList();
        string target = nodes[Random.Range(0, nodes.Count)];
        
        if (Role == "patient" && Random.value < 0.6f) return; 

        if (target.StartsWith("RoomCorr") || target.StartsWith("WestCorr") || target.StartsWith("EastCorr")) return;

        path = HospitalGraph.FindPath(CurrentNode, target);
        pathIdx = 0;
        idleTimer = Random.Range(6f, 15f);
    }

    void MoveAlongPath(float dt)
    {
        if (pathIdx >= path.Count) { path.Clear(); return; }

        Vector3 target = HospitalGraph.GetNodePosition(path[pathIdx]) + new Vector3(Random.Range(-0.5f, 0.5f), 0.5f, Random.Range(-0.5f, 0.5f));
        Vector3 dir = target - transform.position;
        float dist = dir.magnitude;

        if (dist < 0.4f)
        {
            CurrentNode = path[pathIdx];
            pathIdx++;
        }
        else
        {
            float step = Mathf.Min(3.0f * dt, dist);
            transform.position += (dir / dist) * step;
            Quaternion rot = Quaternion.LookRotation(new Vector3(dir.x, 0, dir.z));
            transform.rotation = Quaternion.Slerp(transform.rotation, rot, dt * 8f);
        }
    }

    void TriggerHelpRequest()
    {
        NeedsHelp = true;
        HelpType = Random.value > 0.5f ? "assist_patient" : "deliver_medicine";
        alertGlow.SetActive(true);
    }

    public void FulfillHelp()
    {
        NeedsHelp = false;
        HelpType = null;
        alertGlow.SetActive(false);
        helpRequestTimer = Random.Range(30f, 90f);
    }
}

// ======================================================================
// TASK DATA & MANAGER
// ======================================================================
public class TaskData
{
    public string TaskType;
    public string LocationNode;
    public int Priority;
    public string Status = "pending";
    public int AssignedRobot = -1;
    public float CreatedTime;
    public float CompletedTime;
    public string Desc;

    public TaskData(string type, string loc, int pri, string d)
    {
        TaskType = type; LocationNode = loc; Priority = pri; Desc = d;
        CreatedTime = Time.time;
    }
}

public class TaskManager : MonoBehaviour
{
    private List<TaskData> queue = new();
    private List<TaskData> active = new();
    private List<TaskData> resolved = new();
    private List<string> logs = new() { "System scheduler live." };
    private float timer = 0f;

    public void CreateTask(string type, string loc, int pri, string desc)
    {
        var task = new TaskData(type, loc, pri, desc);
        queue.Add(task);
        queue = queue.OrderByDescending(t => t.Priority).ToList();
        AddLog($"Queued: {type} -> {loc}");
    }

    public void AssignTasks(List<RobotAgent> robots)
    {
        var avail = robots.Where(r => r.IsAvailable()).ToList();
        while (queue.Count > 0 && avail.Count > 0)
        {
            var task = queue[0];
            RobotAgent best = null;
            float bestDist = 9999f;
            foreach (var r in avail)
            {
                float d = Vector3.Distance(r.transform.position, HospitalGraph.GetNodePosition(task.LocationNode));
                if (d < bestDist) { bestDist = d; best = r; }
            }

            if (best != null)
            {
                queue.RemoveAt(0);
                task.Status = "active";
                task.AssignedRobot = best.RobotId;
                best.AssignTask(task);
                active.Add(task);
                avail.Remove(best);
            }
            else break;
        }
    }

    public List<TaskData> CheckCompleted(List<RobotAgent> robots)
    {
        var done = new List<TaskData>();
        for (int i = active.Count - 1; i >= 0; i--)
        {
            if (active[i].Status == "completed")
            {
                done.Add(active[i]);
                resolved.Add(active[i]);
                AddLog($"Complete: {active[i].LocationNode}");
                active.RemoveAt(i);
            }
        }
        return done;
    }

    public void AutoGenerateFromHumans(List<HumanAgent> humans, float dt)
    {
        timer += dt;
        if (timer < 2.5f) return;
        timer = 0;

        foreach (var h in humans)
        {
            if (h.NeedsHelp && !string.IsNullOrEmpty(h.HelpType))
            {
                bool q = queue.Any(x => x.LocationNode == h.CurrentNode && x.TaskType == h.HelpType);
                bool a = active.Any(x => x.LocationNode == h.CurrentNode && x.TaskType == h.HelpType);
                if (!q && !a)
                {
                    CreateTask(h.HelpType, h.CurrentNode, h.HelpType == "assist_patient" ? 3 : 2, "Auto request");
                }
            }
        }
    }

    public void AddLog(string msg)
    {
        logs.Insert(0, $"> {msg}");
        if (logs.Count > 15) logs.RemoveAt(logs.Count - 1);
    }

    public List<string> GetQueueDisplay() => queue.Take(5).Select(t => $"[P{t.Priority}] {t.TaskType}\n   -> {t.LocationNode}").ToList();
    public List<string> GetRecentAlerts() => logs;
    public (int completed, float avgResponse) GetMetrics()
    {
        float avg = 0f;
        if (resolved.Count > 0) avg = resolved.Average(t => t.CompletedTime - t.CreatedTime);
        return (resolved.Count, avg);
    }
}

// ======================================================================
// CAMERA ISOMETRIC SMOOTH CONTROLLER
// ======================================================================
public class CameraController : MonoBehaviour
{
    private float dist = 70f, targetDist = 70f;
    private float angleX = 45f, targetAX = 45f;
    private float angleY = -45f, targetAY = -45f;
    private Vector3 focal = new(0, 0, 0), targetFocal = new(0, 0, 0);

    void Start()
    {
        Camera.main.orthographic = true;
        Camera.main.orthographicSize = 40f;
        transform.position = new Vector3(0, 50, -50);
    }

    void LateUpdate()
    {
        float dt = Time.deltaTime;
        focal = Vector3.Lerp(focal, targetFocal, dt * 5.0f);
        
        Camera.main.orthographicSize = Mathf.Lerp(Camera.main.orthographicSize, targetDist, dt * 5.0f);

        if (Mouse.current != null && Mouse.current.middleButton.isPressed)
        {
            Vector2 delta = Mouse.current.delta.ReadValue() * 0.1f;
            float mx = delta.x;
            float my = delta.y;

            if (Keyboard.current != null && Keyboard.current.leftShiftKey.isPressed)
            {
                targetAY += mx * 180f * dt;
            }
            else
            {
                float sp = 0.4f * targetDist;
                float rad = Mathf.Deg2Rad * targetAY;
                targetFocal -= (new Vector3(Mathf.Sin(rad), 0, Mathf.Cos(rad)) * my + new Vector3(Mathf.Cos(rad), 0, -Mathf.Sin(rad)) * mx) * sp * dt * 10f;
            }
        }

        if (Mouse.current != null)
        {
            float scroll = Mouse.current.scroll.ReadValue().y / 120f;
            if (scroll != 0)
            {
                targetDist -= scroll * 15f;
                targetDist = Mathf.Clamp(targetDist, 15f, 80f);
            }
        }

        float rx = Mathf.Deg2Rad * angleX;
        float ry = Mathf.Deg2Rad * angleY;
        Vector3 offset = new(
            100f * Mathf.Sin(ry) * Mathf.Cos(rx),
            100f * Mathf.Sin(rx),
            -100f * Mathf.Cos(ry) * Mathf.Cos(rx)
        );
        transform.position = focal + offset;
        transform.LookAt(focal);
    }

    public void GoToNode(string name)
    {
        targetFocal = HospitalGraph.GetNodePosition(name);
        targetDist = Mathf.Min(targetDist, 30f);
    }

    public void ResetOverview()
    {
        targetFocal = new Vector3(0, 0, 0);
        targetDist = 45f; targetAX = 45f; targetAY = -45f;
    }
}

// ======================================================================
// PROGRAMMATIC BENTO BOX DASHBOARD HUD UI + MINIMAP
// ======================================================================
public class DashboardUI : MonoBehaviour
{
    private Text topBarText;
    private Text queueText, alertText, metricsText, cmdText;
    private InputField inputField;
    private List<RobotUIRefs> cards = new();
    private bool isTyping;
    private FarsSimulation sim;
    
    private RectTransform miniMapBlipsContainer;
    private List<RobotAgent> trackedRobots;
    private List<RectTransform> blips = new();

    struct RobotUIRefs { public Text state, bat, loc; public Image bar; }

    public void Init(FarsSimulation simRef, List<RobotAgent> rbts)
    {
        sim = simRef;
        trackedRobots = rbts;
        BuildInterface();
    }

    void BuildInterface()
    {
        var left = MakeRect("LeftPanel", new Vector2(0, 0.5f), new Vector2(300, 1080), new Color32(12, 16, 22, 245));
        left.anchorMin = new Vector2(0, 0); left.anchorMax = new Vector2(0, 1);
        left.pivot = new Vector2(0, 0.5f);
        
        MakeRect("EdgeLine", new Vector2(300, 0.5f), new Vector2(2, 1080), new Color32(35, 45, 60, 255), left.transform);

        float y = -20f;
        MakeText("Title", "FARS DIGITAL TWIN", new Vector2(15, y), 18, new Color32(0, 200, 255, 255), left.transform); y -= 25f;
        MakeText("LiveInfo", "● LIVE | AI: PHI-3 MINI", new Vector2(15, y), 11, new Color32(100, 255, 120, 255), left.transform); y -= 35f;
        
        MakeRect("Div1", new Vector2(150, y), new Vector2(270, 1), new Color32(35, 45, 60, 255), left.transform); y -= 15f;

        MakeText("FleetHeader", ">> ROBOT FLEET MONITOR", new Vector2(15, y), 12, new Color32(0, 180, 255, 255), left.transform); y -= 25f;

        Color32[] pal = { new Color32(0,200,255,255), new Color32(255,100,100,255), new Color32(100,255,100,255), new Color32(255,200,50,255), new Color32(200,100,255,255) };
        for (int i = 0; i < 5; i++)
        {
            var cBg = MakeRect($"Card_{i}", new Vector2(150, y), new Vector2(270, 48), new Color32(20, 24, 32, 255), left.transform);
            
            var btn = cBg.gameObject.AddComponent<Button>();
            int idx = i;
            btn.onClick.AddListener(() => sim.SelectRobot(idx));

            MakeRect("CLine", new Vector2(2, 24), new Vector2(4, 40), pal[i], cBg.transform);
            MakeText("ID", $"R{i+1}", new Vector2(12, -4), 12, pal[i], cBg.transform);
            var rState = MakeText("State", "IDLE", new Vector2(45, -4), 11, Color.white, cBg.transform);
            
            MakeRect("BatBG", new Vector2(105, -8), new Vector2(70, 6), new Color32(10, 12, 18, 255), cBg.transform);
            var bFill = MakeRect("BatFill", new Vector2(105, -8), new Vector2(70, 6), new Color32(20, 220, 90, 255), cBg.transform).GetComponent<Image>();
            var bTxt = MakeText("BatTxt", "100%", new Vector2(180, -7), 9, new Color32(100, 110, 125, 255), cBg.transform);

            var rLoc = MakeText("Loc", "@ ChargingDock", new Vector2(12, -26), 9, new Color32(150, 160, 175, 255), cBg.transform);

            cards.Add(new RobotUIRefs { state = rState, bar = bFill, bat = bTxt, loc = rLoc });
            y -= 54f;
        }

        MakeRect("Div2", new Vector2(150, y), new Vector2(270, 1), new Color32(35, 45, 60, 255), left.transform); y -= 15f;

        MakeText("QueueHeader", ">> LIVE TASK QUEUE", new Vector2(15, y), 12, new Color32(255, 180, 30, 255), left.transform); y -= 20f;
        queueText = MakeText("QueueList", "", new Vector2(20, y), 11, Color.white, left.transform); 
        queueText.GetComponent<RectTransform>().sizeDelta = new Vector2(260, 120);
        y -= 125f;

        MakeRect("Div3", new Vector2(150, y), new Vector2(270, 1), new Color32(35, 45, 60, 255), left.transform); y -= 15f;

        MakeText("AlertsHeader", ">> SYSTEM LOGS", new Vector2(15, y), 12, Color.cyan, left.transform); y -= 20f;
        alertText = MakeText("AlertsBody", "", new Vector2(20, y), 10, new Color32(150, 160, 175, 255), left.transform);
        alertText.GetComponent<RectTransform>().sizeDelta = new Vector2(260, 150);
        y -= 155f;
        
        MakeRect("Div4", new Vector2(150, y), new Vector2(270, 1), new Color32(35, 45, 60, 255), left.transform); y -= 15f;

        // Minimap
        MakeText("MapHeader", ">> MINIMAP", new Vector2(15, y), 12, Color.gray, left.transform); y -= 20f;
        var mapBg = MakeRect("MiniMap", new Vector2(150, y), new Vector2(260, 160), new Color32(8, 10, 14, 255), left.transform);
        mapBg.anchorMin = new Vector2(0, 1); mapBg.anchorMax = new Vector2(0, 1);
        mapBg.pivot = new Vector2(0.5f, 1);
        MakeRect("MOutline", new Vector2(130, -80), new Vector2(262, 162), new Color32(35, 45, 60, 255), mapBg.transform).transform.SetAsFirstSibling();
        
        miniMapBlipsContainer = mapBg;
        for (int i = 0; i < 5; i++)
        {
            var blip = MakeRect($"Blip_{i}", new Vector2(0.5f, 0.5f), new Vector2(6, 6), pal[i], mapBg.transform);
            blips.Add(blip);
        }

        var top = MakeRect("TopBar", new Vector2(0.5f, 1), new Vector2(1920, 48), new Color32(12, 16, 22, 230));
        top.anchorMin = new Vector2(0, 1); top.anchorMax = new Vector2(1, 1); top.pivot = new Vector2(0.5f, 1);
        top.anchoredPosition = Vector2.zero;
        MakeRect("TopBorder", new Vector2(0.5f, 0), new Vector2(1920, 2), new Color32(35, 45, 60, 255), top.transform).GetComponent<RectTransform>().anchoredPosition = new Vector2(0, 0);

        MakeText("TopTitle", "FARS CENTRAL OPERATIONS CENTER", new Vector2(320, -14), 14, Color.white, top.transform);
        topBarText = MakeText("TopStats", "Active Robots: 0/5  |  Resolved: 0  |  FPS: 60", new Vector2(850, -14), 12, new Color32(150, 160, 175, 255), top.transform);
        metricsText = MakeText("MetTxt", "EFF: 100% | LAT: 0s | UTIL: 0%", new Vector2(1450, -14), 12, new Color32(20, 220, 90, 255), top.transform);

        var bot = MakeRect("BottomBar", new Vector2(0.5f, 0), new Vector2(1920, 52), new Color32(12, 16, 22, 240));
        bot.anchorMin = new Vector2(0, 0); bot.anchorMax = new Vector2(1, 0); bot.pivot = new Vector2(0.5f, 0);
        bot.anchoredPosition = Vector2.zero;
        MakeRect("BotBorder", new Vector2(0.5f, 1), new Vector2(1920, 2), new Color32(0, 180, 255, 180), bot.transform).GetComponent<RectTransform>().anchoredPosition = new Vector2(0, 0);

        MakeText("ConsoleTag", "[SYSTEM_INPUT] >", new Vector2(320, -16), 14, new Color32(0, 200, 255, 255), bot.transform);
        
        var ifGo = new GameObject("InputField");
        ifGo.transform.SetParent(bot.transform, false);
        var irt = ifGo.AddComponent<RectTransform>();
        irt.anchorMin = new Vector2(0, 1); irt.anchorMax = new Vector2(0, 1); irt.pivot = new Vector2(0, 1);
        irt.anchoredPosition = new Vector2(480, -10);
        irt.sizeDelta = new Vector2(600, 32);
        
        var itbg = ifGo.AddComponent<Image>();
        itbg.color = new Color32(20, 24, 32, 255);
        
        inputField = ifGo.AddComponent<InputField>();
        var itxtGo = new GameObject("Text");
        itxtGo.transform.SetParent(ifGo.transform, false);
        var itxt = itxtGo.AddComponent<Text>();
        itxt.font = Font.CreateDynamicFontFromOSFont("Consolas", 14);
        itxt.color = Color.white;
        var itr = itxtGo.GetComponent<RectTransform>();
        itr.anchorMin = Vector2.zero; itr.anchorMax = Vector2.one; itr.offsetMin = new Vector2(10, 0);
        
        inputField.textComponent = itxt;
        inputField.onEndEdit.AddListener(OnCommandSubmit);
        
        cmdText = MakeText("ConsoleTxt", "Press TAB to enter command terminal...", new Vector2(1100, -16), 12, new Color32(150, 160, 175, 255), bot.transform);
    }
    
    void Update()
    {
        if (trackedRobots == null) return;
        for(int i = 0; i < trackedRobots.Count; i++)
        {
            Vector3 wpos = trackedRobots[i].transform.position;
            float mx = (wpos.x / 40f) * 120f;
            float my = (wpos.z / 40f) * 75f;
            blips[i].anchoredPosition = new Vector2(mx, my);
        }
    }

    void OnCommandSubmit(string text)
    {
        if (string.IsNullOrEmpty(text)) return;
        sim.SubmitCommand(text);
        inputField.text = "";
        EventSystem.current.SetSelectedGameObject(null);
        sim.gameObject.SendMessage("HandleKeyboardInputs"); 
    }

    public void UpdateHUD(int active, int total, int assisted, int completed, float avgResp)
    {
        int fps = Mathf.RoundToInt(1f / Mathf.Max(0.001f, Time.deltaTime));
        if (topBarText != null)
            topBarText.text = $"Active Robots: {active}/{total}  |  Tasks Resolved: {completed}  |  FPS: {fps}";
        if (metricsText != null)
        {
            int eff = completed + active > 0 ? (int)(completed * 100f / (completed + active)) : 100;
            metricsText.text = $"EFF: {eff}% | LAT: {avgResp:F1}s | UTIL: {(int)((active * 100f) / total)}%";
        }
    }

    public void UpdateQueue(List<string> items)
    {
        if (queueText != null)
            queueText.text = items.Count > 0 ? string.Join("\n\n", items) : "(No active tasks queued)";
    }

    public void UpdateRobots(List<Dictionary<string, string>> infos)
    {
        for (int i = 0; i < Mathf.Min(5, infos.Count); i++)
        {
            var info = infos[i];
            var card = cards[i];
            if (card.state != null)
            {
                card.state.text = info["state"].ToUpper();
                card.state.color = info["state"] == "executing" ? (Color)new Color32(20, 220, 90, 255) : (info["state"] == "navigating" ? (Color)new Color32(0, 200, 255, 255) : Color.white);
            }
            float bat = float.Parse(info["battery"]);
            if (card.bar != null)
            {
                card.bar.rectTransform.sizeDelta = new Vector2(70f * bat / 100f, 6f);
                card.bar.color = bat > 40f ? (Color)new Color32(20, 220, 90, 255) : (bat > 18f ? (Color)new Color32(255, 200, 50, 255) : Color.red);
            }
            if (card.bat != null) card.bat.text = $"{bat:F0}%";
            if (card.loc != null) card.loc.text = $"@ {info["location"]}";
        }
    }

    public void UpdateAlerts(List<string> alerts)
    {
        if (alertText != null) alertText.text = string.Join("\n", alerts);
    }

    public void SetTypingMode(bool typing)
    {
        isTyping = typing;
        if (cmdText != null)
        {
            cmdText.text = typing ? "Type prompt in console..." : "Press TAB to enter command terminal...";
            cmdText.color = typing ? Color.white : (Color)new Color32(150, 160, 175, 255);
        }
        if (typing)
        {
            inputField.ActivateInputField();
            inputField.Select();
        }
    }

    public void ShowFeedback(string msg)
    {
        if (cmdText != null) cmdText.text = msg;
        CancelInvoke(nameof(ResetConsole));
        Invoke(nameof(ResetConsole), 4f);
    }

    void ResetConsole()
    {
        SetTypingMode(isTyping);
    }

    RectTransform MakeRect(string name, Vector2 pivot, Vector2 size, Color32 col, Transform parent = null)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent != null ? parent : transform, false);
        var img = go.AddComponent<Image>();
        img.color = col;
        var rt = go.GetComponent<RectTransform>();
        rt.sizeDelta = size;
        rt.pivot = pivot;
        return rt;
    }

    Text MakeText(string name, string text, Vector2 pos, int size, Color32 col, Transform parent)
    {
        var go = new GameObject(name);
        go.transform.SetParent(parent, false);
        var t = go.AddComponent<Text>();
        t.text = text;
        t.fontSize = size;
        t.font = Font.CreateDynamicFontFromOSFont("Consolas", size);
        t.color = col;
        t.horizontalOverflow = HorizontalWrapMode.Overflow;
        t.verticalOverflow = VerticalWrapMode.Overflow;
        var rt = go.GetComponent<RectTransform>();
        rt.anchorMin = new Vector2(0, 1); rt.anchorMax = new Vector2(0, 1);
        rt.pivot = new Vector2(0, 1);
        rt.anchoredPosition = pos;
        rt.sizeDelta = new Vector2(270, 150);
        return t;
    }
}
