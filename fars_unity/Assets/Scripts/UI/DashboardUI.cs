using UnityEngine;
using TMPro;
using System.Text;

namespace FARS.UI
{
    /// <summary>
    /// Displays metrics and alerts from the SimulationState.
    /// </summary>
    public class DashboardUI : MonoBehaviour
    {
        [Header("UI References")]
        public TextMeshProUGUI statsText;
        public TextMeshProUGUI alertsText;
        public TextMeshProUGUI activeTasksText;

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
            if (state == null) return;

            // 1. Stats Text
            if (statsText != null && state.metrics != null)
            {
                float totalReward = 0;
                int activeRobots = 0;
                if (state.robots != null)
                {
                    foreach (var r in state.robots)
                    {
                        totalReward += r.reward_signal;
                        if (r.state != "idle" && r.state != "charging") activeRobots++;
                    }
                }

                statsText.text = $"TIME: {(int)state.sim_time}s\n" +
                                 $"ACTIVE ROBOTS: {activeRobots}\n" +
                                 $"TASKS DONE: {state.metrics.completed}\n" +
                                 $"REWARD SIGNAL: {totalReward:F1}";
            }

            // 2. Alerts Text
            if (alertsText != null && state.alerts != null)
            {
                StringBuilder sb = new StringBuilder();
                sb.AppendLine("--- SYSTEM ALERTS ---");
                // Show last 5 alerts
                int start = Mathf.Max(0, state.alerts.Length - 5);
                for (int i = start; i < state.alerts.Length; i++)
                {
                    sb.AppendLine(state.alerts[i]);
                }
                alertsText.text = sb.ToString();
            }

            // 3. Active Tasks
            if (activeTasksText != null && state.tasks != null)
            {
                StringBuilder sb = new StringBuilder();
                sb.AppendLine("--- TASK QUEUE ---");
                int count = 0;
                foreach (var t in state.tasks)
                {
                    sb.AppendLine($"[P{t.priority}] {t.task_type} @ {t.location_node} ({t.status})");
                    count++;
                    if (count > 6)
                    {
                        sb.AppendLine($"... and {state.tasks.Length - 6} more");
                        break;
                    }
                }
                activeTasksText.text = sb.ToString();
            }
        }
    }
}
