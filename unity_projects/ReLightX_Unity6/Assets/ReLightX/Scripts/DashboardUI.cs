using UnityEngine;
using UnityEngine.UI;

namespace ReLightX
{
    public class DashboardUI : MonoBehaviour
    {
        public Text modeText;
        public Text energyText;
        public Text emergencyText;
        public Text faultText;
        public MQTTClientBridge mqttBridge;

        private void Start()
        {
            if (mqttBridge == null)
            {
                mqttBridge = FindObjectOfType<MQTTClientBridge>();
            }
            if (mqttBridge != null)
            {
                mqttBridge.MessageReceived += HandleMessage;
            }
        }

        private void OnDestroy()
        {
            if (mqttBridge != null)
            {
                mqttBridge.MessageReceived -= HandleMessage;
            }
        }

        private void HandleMessage(string topic, string payload)
        {
            if (topic.EndsWith("/system/energy") && energyText != null)
            {
                energyText.text = payload;
            }
            if (topic.EndsWith("/system/emergency") && emergencyText != null)
            {
                emergencyText.text = payload.Contains("true") ? "Emergency active" : "No emergency";
            }
            if (payload.Contains("\"active_mode\"") && modeText != null)
            {
                modeText.text = payload;
            }
            if (payload.Contains("fault") && faultText != null)
            {
                faultText.text = payload;
            }
        }
    }
}
