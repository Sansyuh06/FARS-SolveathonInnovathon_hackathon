using UnityEngine;
using TMPro;

namespace FARS.UI
{
    /// <summary>
    /// Handles the LLM command input field, sending data to the Python backend.
    /// </summary>
    public class CommandInput : MonoBehaviour
    {
        public TMP_InputField inputField;

        void Start()
        {
            if (inputField != null)
            {
                inputField.onSubmit.AddListener(OnSubmit);
            }
        }

        private void OnSubmit(string text)
        {
            if (string.IsNullOrWhiteSpace(text)) return;
            if (SimulationBridge.Instance == null || !SimulationBridge.Instance.IsConnected)
            {
                Debug.LogWarning("[CommandInput] Cannot send command: Bridge not connected.");
                return;
            }

            // Create JSON command
            string json = $"{{\"type\":\"command\",\"text\":\"{text}\"}}";
            SimulationBridge.Instance.SendCommand(json);

            // Clear input
            if (inputField != null)
            {
                inputField.text = "";
                inputField.ActivateInputField(); // Keep focus
            }
        }
    }
}
