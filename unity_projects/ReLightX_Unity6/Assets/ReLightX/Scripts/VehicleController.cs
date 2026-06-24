using System;
using UnityEngine;

namespace ReLightX
{
    [RequireComponent(typeof(BoxCollider))]
    public class VehicleController : MonoBehaviour
    {
        public static event Action<VehicleController> VehicleSelected;

        public string vehicleId;
        public string vehicleType = "normal_car";
        public string direction = "A";
        public string laneId = "A2";
        public float speedMps = 24f;
        public float desiredSpeedMps = 24f;
        public float baseCruiseSpeedMps = 24f;
        public float manualSpeedOffsetKph;
        public float roadLengthM = 1240f;
        public bool emergencyVehicle;
        public bool selected;
        public float measuredFrontGapM = 999f;

        public Light leftHeadlight;
        public Light rightHeadlight;
        public Light emergencyBeacon;

        private float _destroyMarginM = 180f;

        public float PositionAlongRoad => transform.position.x;
        public int TravelSign => direction == "A" ? 1 : -1;
        public float SpeedKph => speedMps * 3.6f;
        public float DesiredSpeedKph => desiredSpeedMps * 3.6f;

        private void Awake()
        {
            BoxCollider collider = GetComponent<BoxCollider>();
            collider.size = new Vector3(5.6f, 2.2f, 2.5f);
            collider.center = new Vector3(0f, 1.0f, 0f);
        }

        private void Update()
        {
            speedMps = Mathf.MoveTowards(speedMps, desiredSpeedMps, 8f * Time.deltaTime);
            transform.position += new Vector3(TravelSign * speedMps * Time.deltaTime, 0f, 0f);
            UpdateLights();

            if (transform.position.x < -_destroyMarginM || transform.position.x > roadLengthM + _destroyMarginM)
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
            desiredSpeedMps = speed;
            baseCruiseSpeedMps = speed;
            manualSpeedOffsetKph = 0f;
            roadLengthM = roadLength;
            emergencyVehicle = type == "ambulance" || type == "police_car" || type == "fire_truck";

            float laneOffset = LaneOffset(lane);
            transform.position = new Vector3(startX, 0.05f, laneOffset);
            transform.rotation = Quaternion.Euler(0f, direction == "A" ? 90f : -90f, 0f);

            BuildFallbackBodyIfNeeded();
            CreateVehicleLights();
        }

        public void Select()
        {
            VehicleSelected?.Invoke(this);
        }

        public void SetSelected(bool active)
        {
            selected = active;
        }

        public Vector3 FirstPersonCameraPosition()
        {
            return transform.position + new Vector3(-TravelSign * 0.35f, 2.35f, 0f);
        }

        public Vector3 FirstPersonLookAt()
        {
            return transform.position + new Vector3(TravelSign * 44f, 1.85f, 0f);
        }

        public Vector3 ThirdPersonCameraPosition()
        {
            return transform.position + new Vector3(-TravelSign * 11f, 5.2f, 0f);
        }

        public Vector3 ThirdPersonLookAt()
        {
            return transform.position + new Vector3(TravelSign * 12f, 1.4f, 0f);
        }

        public static float LaneOffset(string lane)
        {
            switch (lane)
            {
                case "A1": return 2.1f;
                case "A2": return 5.8f;
                case "A3": return 9.5f;
                case "B1": return -2.1f;
                case "B2": return -5.8f;
                case "B3": return -9.5f;
                default: return lane.StartsWith("A") ? 5.8f : -5.8f;
            }
        }

        private void BuildFallbackBodyIfNeeded()
        {
            if (transform.childCount > 0)
            {
                return;
            }

            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Cube);
            body.name = "procedural vehicle body";
            body.transform.SetParent(transform, false);
            body.transform.localPosition = new Vector3(0f, 0.85f, 0f);
            body.transform.localScale = emergencyVehicle ? new Vector3(4.8f, 1.7f, 2.1f) : new Vector3(4.3f, 1.35f, 1.9f);

            Renderer renderer = body.GetComponent<Renderer>();
            renderer.material.color = VehicleColor();
            DigitalTwinMaterialUtility.TuneVehicleBodyRenderer(renderer);

            GameObject cabin = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cabin.name = "procedural cabin";
            cabin.transform.SetParent(transform, false);
            cabin.transform.localPosition = new Vector3(-0.35f, 1.75f, 0f);
            cabin.transform.localScale = new Vector3(1.8f, 0.75f, 1.55f);
            Renderer cabinRenderer = cabin.GetComponent<Renderer>();
            cabinRenderer.material.color = new Color(0.09f, 0.13f, 0.16f);
            DigitalTwinMaterialUtility.TuneVehicleBodyRenderer(cabinRenderer);
        }

        private Color VehicleColor()
        {
            if (vehicleType == "police_car") return new Color(0.05f, 0.09f, 0.16f);
            if (vehicleType == "ambulance") return new Color(0.94f, 0.96f, 0.92f);
            if (vehicleType == "fire_truck") return new Color(0.85f, 0.05f, 0.02f);
            int hash = Mathf.Abs(vehicleId.GetHashCode());
            Color[] colors =
            {
                new Color(0.08f, 0.32f, 0.58f),
                new Color(0.55f, 0.58f, 0.62f),
                new Color(0.12f, 0.12f, 0.13f),
                new Color(0.72f, 0.16f, 0.08f),
                new Color(0.90f, 0.78f, 0.22f)
            };
            return colors[hash % colors.Length];
        }

        private void CreateVehicleLights()
        {
            leftHeadlight = CreateHeadlight("left headlight", new Vector3(1.95f, 0.85f, -0.62f));
            rightHeadlight = CreateHeadlight("right headlight", new Vector3(1.95f, 0.85f, 0.62f));
            if (emergencyVehicle)
            {
                GameObject beaconObject = new GameObject("emergency beacon");
                beaconObject.transform.SetParent(transform, false);
                beaconObject.transform.localPosition = new Vector3(0f, 2.35f, 0f);
                emergencyBeacon = beaconObject.AddComponent<Light>();
                emergencyBeacon.type = LightType.Point;
                emergencyBeacon.range = 18f;
                emergencyBeacon.color = vehicleType == "police_car" ? new Color(0.15f, 0.35f, 1f) : Color.red;
            }
        }

        private Light CreateHeadlight(string name, Vector3 localPosition)
        {
            GameObject lightObject = new GameObject(name);
            lightObject.transform.SetParent(transform, false);
            lightObject.transform.localPosition = localPosition;
            lightObject.transform.localRotation = Quaternion.identity;
            Light light = lightObject.AddComponent<Light>();
            light.type = LightType.Spot;
            light.range = 42f;
            light.spotAngle = 32f;
            light.intensity = 3.2f;
            light.color = new Color(1f, 0.90f, 0.72f);
            return light;
        }

        private void UpdateLights()
        {
            if (emergencyBeacon != null)
            {
                emergencyBeacon.intensity = 1.2f + Mathf.Abs(Mathf.Sin(Time.time * 8f)) * 7f;
            }
        }

    }
}
