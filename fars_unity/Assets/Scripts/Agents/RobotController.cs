using System.Collections.Generic;
using UnityEngine;
using TMPro; // Assuming TextMeshPro for labels

namespace FARS.Agents
{
    /// <summary>
    /// Spawns and updates Robot agents based on WebSocket data.
    /// </summary>
    public class RobotController : MonoBehaviour
    {
        [Header("Prefabs")]
        public GameObject robotPrefab;
        
        [Header("Settings")]
        public float positionLerpSpeed = 10f;
        
        private Dictionary<int, RobotInstance> _robots = new Dictionary<int, RobotInstance>();

        void Start()
        {
            if (SimulationBridge.Instance != null)
            {
                SimulationBridge.Instance.OnStateUpdated += HandleStateUpdated;
            }
        }

        void OnDestroy()
        {
            if (SimulationBridge.Instance != null)
            {
                SimulationBridge.Instance.OnStateUpdated -= HandleStateUpdated;
            }
        }

        private void HandleStateUpdated(SimulationState state)
        {
            if (state.robots == null) return;

            foreach (var rData in state.robots)
            {
                if (!_robots.TryGetValue(rData.id, out var instance))
                {
                    // Spawn new robot
                    GameObject go = Instantiate(robotPrefab, transform);
                    go.name = $"Robot_{rData.id}";
                    instance = go.AddComponent<RobotInstance>();
                    instance.Initialize(rData.id);
                    _robots[rData.id] = instance;
                    
                    // Set initial position
                    instance.transform.position = new Vector3(rData.world_x, 0, rData.world_z);
                }
                
                // Update data
                instance.UpdateData(rData, positionLerpSpeed);
            }
        }
    }

    /// <summary>
    /// Attached to each individual Robot GameObject.
    /// </summary>
    public class RobotInstance : MonoBehaviour
    {
        public int RobotId { get; private set; }
        
        private Vector3 _targetPosition;
        private RobotData _latestData;

        // Visual components you might have on your prefab
        // public TextMeshProUGUI idLabel;
        // public TextMeshProUGUI stateLabel;

        public void Initialize(int id)
        {
            RobotId = id;
            _targetPosition = transform.position;
        }

        public void UpdateData(RobotData data, float lerpSpeed)
        {
            _latestData = data;
            
            // X and Z are standard unity world coordinates. 
            // In python, Z might map to Z or Y depending on the 2D plane, but standard is XZ.
            _targetPosition = new Vector3(data.world_x, transform.position.y, data.world_z);
            
            // Move smoothly
            transform.position = Vector3.Lerp(transform.position, _targetPosition, Time.deltaTime * lerpSpeed);
            
            // Simple rotation facing direction of movement
            Vector3 dir = _targetPosition - transform.position;
            dir.y = 0;
            if (dir.sqrMagnitude > 0.001f)
            {
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(dir), Time.deltaTime * lerpSpeed);
            }

            // Update UI/Visuals if mapped
            // if (stateLabel != null) stateLabel.text = data.state;
            // if (idLabel != null) idLabel.text = $"R{data.id}";
        }
    }
}
