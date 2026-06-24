using System;
using System.Collections.Generic;
using UnityEngine;

namespace ReLightX
{
    [Serializable]
    public class LuminaireState
    {
        public string luminaire_id;
        public string pole_id;
        public string direction;
        public float current_brightness;
        public float target_brightness;
        public float health_score;
        public float driver_temperature;
        public string fault_status;
        public string rex_status;
    }

    public class HighwaySceneManager : MonoBehaviour
    {
        public int numPoles = 32;
        public float poleSpacingM = 40f;
        public int zoneSizePoles = 8;
        public float ecoBrightness = 0.3f;
        public Material poleMaterial;
        public Material lensMaterial;
        public Material roadMaterial;

        private readonly Dictionary<string, PoleManager> _poles = new Dictionary<string, PoleManager>();
        private readonly Dictionary<string, LuminaireController> _luminaires = new Dictionary<string, LuminaireController>();
        private MQTTClientBridge _mqttBridge;

        public float RoadLengthM => Mathf.Max(0f, (numPoles - 1) * poleSpacingM);

        private void Start()
        {
            BuildScene();
            _mqttBridge = GetComponent<MQTTClientBridge>();
            if (_mqttBridge != null)
            {
                _mqttBridge.MessageReceived += HandleMqttMessage;
            }
        }

        private void OnDestroy()
        {
            if (_mqttBridge != null)
            {
                _mqttBridge.MessageReceived -= HandleMqttMessage;
            }
        }

        public void BuildScene()
        {
            CreateRoad();
            for (int i = 0; i < numPoles; i++)
            {
                string poleId = $"P{i + 1:000}";
                string zoneId = $"Z{i / zoneSizePoles:00}";
                PoleManager pole = CreatePole(poleId, i, zoneId, i * poleSpacingM);
                _poles[poleId] = pole;
                _luminaires[pole.luminaireA.luminaireId] = pole.luminaireA;
                _luminaires[pole.luminaireB.luminaireId] = pole.luminaireB;
            }
        }

        private void CreateRoad()
        {
            GameObject road = GameObject.CreatePrimitive(PrimitiveType.Cube);
            road.name = "Six Lane Highway";
            road.transform.position = new Vector3(RoadLengthM / 2f, -0.08f, 0f);
            road.transform.localScale = new Vector3(RoadLengthM + 120f, 0.12f, 25f);
            if (roadMaterial != null)
            {
                road.GetComponent<Renderer>().material = roadMaterial;
            }

            for (int lane = -3; lane <= 3; lane++)
            {
                if (lane == 0) continue;
                GameObject marker = GameObject.CreatePrimitive(PrimitiveType.Cube);
                marker.name = $"Lane marker {lane}";
                marker.transform.position = new Vector3(RoadLengthM / 2f, 0.01f, lane * 3.7f);
                marker.transform.localScale = new Vector3(RoadLengthM + 80f, 0.03f, 0.06f);
                marker.GetComponent<Renderer>().material.color = lane == -1 || lane == 1 ? Color.yellow : Color.white;
            }
        }

        private PoleManager CreatePole(string poleId, int index, string zoneId, float x)
        {
            GameObject root = new GameObject(poleId);
            root.transform.parent = transform;
            PoleManager pole = root.AddComponent<PoleManager>();
            pole.Initialize(poleId, index, zoneId, x);

            GameObject mast = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            mast.name = $"{poleId} mast";
            mast.transform.parent = root.transform;
            mast.transform.localPosition = new Vector3(0f, 4f, 0f);
            mast.transform.localScale = new Vector3(0.18f, 4f, 0.18f);
            if (poleMaterial != null)
            {
                mast.GetComponent<Renderer>().material = poleMaterial;
            }

            pole.luminaireA = CreateLuminaire(root.transform, poleId, "A", new Vector3(0f, 8.2f, 5.2f), new Vector3(62f, 0f, 0f));
            pole.luminaireB = CreateLuminaire(root.transform, poleId, "B", new Vector3(0f, 8.2f, -5.2f), new Vector3(118f, 0f, 180f));
            return pole;
        }

        private LuminaireController CreateLuminaire(Transform parent, string poleId, string direction, Vector3 localPosition, Vector3 euler)
        {
            GameObject luminaireObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
            luminaireObject.name = $"{poleId}-{direction}";
            luminaireObject.transform.parent = parent;
            luminaireObject.transform.localPosition = localPosition;
            luminaireObject.transform.localRotation = Quaternion.Euler(euler);
            luminaireObject.transform.localScale = new Vector3(1.4f, 0.22f, 0.65f);
            if (lensMaterial != null)
            {
                luminaireObject.GetComponent<Renderer>().material = lensMaterial;
            }

            LuminaireController controller = luminaireObject.AddComponent<LuminaireController>();
            controller.luminaireId = $"{poleId}-{direction}";
            controller.poleId = poleId;
            controller.direction = direction;
            controller.lensRenderer = luminaireObject.GetComponent<Renderer>();
            controller.ForceBrightness(ecoBrightness);
            return controller;
        }

        private void HandleMqttMessage(string topic, string payload)
        {
            if (!topic.Contains("/luminaire/") || !topic.EndsWith("/brightness"))
            {
                return;
            }

            LuminaireState state = JsonUtility.FromJson<LuminaireState>(payload);
            if (state == null || string.IsNullOrEmpty(state.luminaire_id))
            {
                return;
            }

            ApplyLuminaireState(state);
        }

        public void ApplyLuminaireState(LuminaireState state)
        {
            if (_luminaires.TryGetValue(state.luminaire_id, out LuminaireController luminaire))
            {
                luminaire.SetTarget(Mathf.Clamp01(state.current_brightness));
            }
        }

        public void TriggerNormalVehicleA()
        {
            SpawnVehicle("UNITY-CAR-A", "normal_car", "A", "A2", -40f, 24f);
        }

        public void TriggerNormalVehicleB()
        {
            SpawnVehicle("UNITY-CAR-B", "normal_car", "B", "B2", RoadLengthM + 40f, 24f);
        }

        public void TriggerEmergencyVehicleA()
        {
            SpawnVehicle("UNITY-AMB-A", "ambulance", "A", "A2", -70f, 31f);
            SetDirectionBrightness("A", 1f);
        }

        public void TriggerEmergencyVehicleB()
        {
            SpawnVehicle("UNITY-POL-B", "police_car", "B", "B2", RoadLengthM + 70f, 30f);
            SetDirectionBrightness("B", 1f);
        }

        public void TriggerSensorFault()
        {
            SetZoneBrightness("A", 1, 0.70f);
        }

        public void TriggerCommunicationFault()
        {
            SetZoneBrightness("B", 2, 0.70f);
        }

        public void TriggerBoardTestMode()
        {
            foreach (LuminaireController luminaire in _luminaires.Values)
            {
                luminaire.SetTarget(0.70f);
            }
        }

        private void SpawnVehicle(string id, string type, string direction, string lane, float x, float speed)
        {
            GameObject vehicleObject = GameObject.CreatePrimitive(PrimitiveType.Cube);
            vehicleObject.name = id;
            VehicleController vehicle = vehicleObject.AddComponent<VehicleController>();
            vehicle.Initialize(id, type, direction, lane, x, speed, RoadLengthM);
        }

        private void SetDirectionBrightness(string direction, float brightness)
        {
            foreach (LuminaireController luminaire in _luminaires.Values)
            {
                if (luminaire.direction == direction)
                {
                    luminaire.SetTarget(brightness);
                }
            }
        }

        private void SetZoneBrightness(string direction, int zoneIndex, float brightness)
        {
            int start = zoneIndex * zoneSizePoles;
            int end = Mathf.Min(numPoles, start + zoneSizePoles);
            for (int i = start; i < end; i++)
            {
                string luminaireId = $"P{i + 1:000}-{direction}";
                if (_luminaires.TryGetValue(luminaireId, out LuminaireController luminaire))
                {
                    luminaire.SetTarget(brightness);
                }
            }
        }
    }
}
