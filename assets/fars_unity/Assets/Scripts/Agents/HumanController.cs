using System.Collections.Generic;
using UnityEngine;

namespace FARS.Agents
{
    /// <summary>
    /// Spawns and updates Human agents based on WebSocket data.
    /// </summary>
    public class HumanController : MonoBehaviour
    {
        [Header("Prefabs")]
        public GameObject defaultHumanPrefab;
        public GameObject doctorPrefab;
        public GameObject nursePrefab;
        public GameObject patientPrefab;
        public GameObject visitorPrefab;
        
        [Header("Settings")]
        public float positionLerpSpeed = 10f;
        
        private Dictionary<int, HumanInstance> _humans = new Dictionary<int, HumanInstance>();

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
            if (state.humans == null) return;

            foreach (var hData in state.humans)
            {
                if (!_humans.TryGetValue(hData.id, out var instance))
                {
                    // Spawn new human with correct prefab
                    GameObject prefab = defaultHumanPrefab;
                    if (hData.agent_type == "doctor" && doctorPrefab != null) prefab = doctorPrefab;
                    else if (hData.agent_type == "nurse" && nursePrefab != null) prefab = nursePrefab;
                    else if (hData.agent_type == "patient" && patientPrefab != null) prefab = patientPrefab;
                    else if (hData.agent_type == "visitor" && visitorPrefab != null) prefab = visitorPrefab;

                    if (prefab == null)
                    {
                        prefab = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                        prefab.transform.localScale = new Vector3(0.5f, 0.5f, 0.5f);
                    }

                    GameObject go = Instantiate(prefab, transform);
                    go.name = $"Human_{hData.id}_{hData.agent_type}";
                    instance = go.AddComponent<HumanInstance>();
                    instance.Initialize(hData.id);
                    _humans[hData.id] = instance;
                    
                    // Set initial position
                    instance.transform.position = new Vector3(hData.world_x, 0, hData.world_z);
                }
                
                // Update data
                instance.UpdateData(hData, positionLerpSpeed);
            }
        }
    }

    /// <summary>
    /// Attached to each individual Human GameObject.
    /// </summary>
    public class HumanInstance : MonoBehaviour
    {
        public int HumanId { get; private set; }
        
        private Vector3 _targetPosition;
        private HumanData _latestData;
        public GameObject helpIndicator; // Optional visual for "needs_help"

        public void Initialize(int id)
        {
            HumanId = id;
            _targetPosition = transform.position;
        }

        public void UpdateData(HumanData data, float lerpSpeed)
        {
            _latestData = data;
            
            _targetPosition = new Vector3(data.world_x, transform.position.y, data.world_z);
            
            // Move smoothly
            transform.position = Vector3.Lerp(transform.position, _targetPosition, Time.deltaTime * lerpSpeed);
            
            // Rotate towards movement
            Vector3 dir = _targetPosition - transform.position;
            dir.y = 0;
            if (dir.sqrMagnitude > 0.001f)
            {
                transform.rotation = Quaternion.Slerp(transform.rotation, Quaternion.LookRotation(dir), Time.deltaTime * lerpSpeed);
            }

            // Visual for needs help
            if (helpIndicator != null)
            {
                helpIndicator.SetActive(data.needs_help);
            }
        }
    }
}
