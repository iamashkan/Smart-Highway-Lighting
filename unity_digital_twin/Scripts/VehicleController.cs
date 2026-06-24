using UnityEngine;

namespace ReLightX
{
    public class VehicleController : MonoBehaviour
    {
        public string vehicleId;
        public string vehicleType = "normal_car";
        public string direction = "A";
        public string laneId = "A2";
        public float speedMps = 24f;
        public float roadLengthM = 1240f;
        public bool emergencyVehicle;

        private void Update()
        {
            float sign = direction == "A" ? 1f : -1f;
            transform.position += new Vector3(sign * speedMps * Time.deltaTime, 0f, 0f);
            if (transform.position.x < -160f || transform.position.x > roadLengthM + 160f)
            {
                Destroy(gameObject);
            }
        }

        public void Initialize(string id, string type, string dir, string lane, float startX, float speed, float roadLength)
        {
            vehicleId = id;
            vehicleType = type;
            direction = dir;
            laneId = lane;
            speedMps = speed;
            roadLengthM = roadLength;
            emergencyVehicle = type == "ambulance" || type == "police_car" || type == "fire_truck";

            float laneOffset = LaneOffset(lane);
            transform.position = new Vector3(startX, 0.6f, laneOffset);
            transform.localScale = emergencyVehicle ? new Vector3(4.8f, 1.7f, 2.1f) : new Vector3(4.2f, 1.4f, 1.9f);

            Renderer renderer = GetComponent<Renderer>();
            if (renderer != null)
            {
                renderer.material.color = emergencyVehicle ? new Color(0.95f, 0.12f, 0.08f) : new Color(0.12f, 0.45f, 0.78f);
            }
        }

        private float LaneOffset(string lane)
        {
            switch (lane)
            {
                case "A1": return 2.0f;
                case "A2": return 5.7f;
                case "A3": return 9.4f;
                case "B1": return -2.0f;
                case "B2": return -5.7f;
                case "B3": return -9.4f;
                default: return direction == "A" ? 5.7f : -5.7f;
            }
        }
    }
}
