using UnityEngine;

namespace ReLightX
{
    public class EmergencyModeVisualizer : MonoBehaviour
    {
        public Light beaconLight;
        public float pulseSpeed = 5f;
        public bool emergencyActive;

        private void Update()
        {
            if (beaconLight == null) return;
            beaconLight.enabled = emergencyActive;
            if (emergencyActive)
            {
                beaconLight.intensity = 2f + Mathf.Abs(Mathf.Sin(Time.time * pulseSpeed)) * 7f;
            }
        }

        public void SetEmergency(bool active)
        {
            emergencyActive = active;
        }
    }
}
