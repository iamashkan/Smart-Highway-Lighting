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
        public int numPoles = 96;
        public float poleSpacingM = 22f;
        public int zoneSizePoles = 9;
        public float ecoBrightness = 0.30f;
        public float heldBrightness = 0.62f;
        public float lightHoldSeconds = 3.2f;
        public float emergencyBrightness = 1.0f;
        public bool generateOnStart = true;
        public Material poleMaterial;
        public Material lensMaterial;
        public Material roadMaterial;
        public Material laneMarkerMaterial;
        public Material guardrailMaterial;
        public Material medianMaterial;
        public Material mountainMaterial;
        public Material forestMaterial;
        public float maxPowerWattsPerLuminaire = 160f;
        public float co2KgPerKwh = 0.404f;
        public float elapsedScenarioSeconds;
        public float actualEnergyKwh;
        public float baselineEnergyKwh;
        public float savedEnergyKwh;
        public float savedEnergyPct;
        public float co2SavedKg;

        private readonly Dictionary<string, PoleManager> _poles = new Dictionary<string, PoleManager>();
        private readonly Dictionary<string, LuminaireController> _luminaires = new Dictionary<string, LuminaireController>();
        private readonly Dictionary<string, float> _frameTargetMap = new Dictionary<string, float>();
        private readonly Dictionary<string, List<string>> _frameVehicleIds = new Dictionary<string, List<string>>();
        private readonly Dictionary<string, float> _frameNearestDistance = new Dictionary<string, float>();
        private readonly Dictionary<string, string> _frameDetectionMode = new Dictionary<string, string>();
        private MQTTClientBridge _mqttBridge;
        private LuminaireController _selectedLuminaire;

        public float RoadLengthM => Mathf.Max(0f, (numPoles - 1) * poleSpacingM);
        public LuminaireController SelectedLuminaire => _selectedLuminaire;
        public IReadOnlyDictionary<string, LuminaireController> Luminaires => _luminaires;

        private void OnEnable()
        {
            LuminaireController.LuminaireSelected += SelectLuminaire;
        }

        private void OnDisable()
        {
            LuminaireController.LuminaireSelected -= SelectLuminaire;
        }

        private void Start()
        {
            if (generateOnStart)
            {
                BuildScene();
            }
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

        private void Update()
        {
            AccumulateEnergy(Time.deltaTime);
        }

        public void BuildScene()
        {
            ClearGeneratedObjects();
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

        public void ApplyAdaptiveLightingFromVehicles(IReadOnlyList<VehicleController> vehicles)
        {
            _frameTargetMap.Clear();
            _frameVehicleIds.Clear();
            _frameNearestDistance.Clear();
            _frameDetectionMode.Clear();

            foreach (LuminaireController luminaire in _luminaires.Values)
            {
                _frameTargetMap[luminaire.luminaireId] = ecoBrightness;
                _frameDetectionMode[luminaire.luminaireId] = "eco watch";
                _frameVehicleIds[luminaire.luminaireId] = new List<string>();
                _frameNearestDistance[luminaire.luminaireId] = 999f;
            }

            if (vehicles != null)
            {
                foreach (VehicleController vehicle in vehicles)
                {
                    if (vehicle == null) continue;
                    if (vehicle.emergencyVehicle)
                    {
                        AddEmergencyLighting(vehicle);
                    }
                    else
                    {
                        AddNormalVehicleWave(vehicle);
                    }
                }
            }

            foreach (LuminaireController luminaire in _luminaires.Values)
            {
                string luminaireId = luminaire.luminaireId;
                luminaire.SetTarget(_frameTargetMap.TryGetValue(luminaireId, out float target) ? target : ecoBrightness);
                luminaire.SetDigitalTwinDetection(
                    _frameVehicleIds.TryGetValue(luminaireId, out List<string> ids) ? ids : null,
                    _frameNearestDistance.TryGetValue(luminaireId, out float nearest) ? nearest : 999f,
                    _frameDetectionMode.TryGetValue(luminaireId, out string mode) ? mode : "eco watch"
                );
            }
        }

        public void TriggerSensorFault()
        {
            SetZoneBrightness("A", 1, 0.70f);
        }

        public void TriggerCommunicationFault()
        {
            SetZoneBrightness("B", 2, 0.70f);
        }

        public void TriggerSafeFallbackVisualization()
        {
            SetAllBrightness(0.70f);
        }

        public void TriggerNormalVehicleA()
        {
            SetZoneBrightness("A", 0, 1.0f);
        }

        public void TriggerNormalVehicleB()
        {
            SetZoneBrightness("B", 0, 1.0f);
        }

        public void TriggerEmergencyVehicleA()
        {
            SetDirectionBrightness("A", 1f);
        }

        public void TriggerEmergencyVehicleB()
        {
            SetDirectionBrightness("B", 1f);
        }

        public int NearestPoleIndex(float positionAlongRoad)
        {
            return Mathf.Clamp(Mathf.RoundToInt(positionAlongRoad / poleSpacingM), 0, numPoles - 1);
        }

        private void ClearGeneratedObjects()
        {
            _poles.Clear();
            _luminaires.Clear();
            _selectedLuminaire = null;
            ResetEnergyCounters();
            for (int i = transform.childCount - 1; i >= 0; i--)
            {
                Transform child = transform.GetChild(i);
                if (Application.isPlaying)
                {
                    Destroy(child.gameObject);
                }
                else
                {
                    DestroyImmediate(child.gameObject);
                }
            }
        }

        private void CreateRoad()
        {
            CreateMountainValley();
            CreateSegmentedRoadSurface();

            CreateLaneMarkers();
            CreateGuardRails();
        }

        private void CreateSegmentedRoadSurface()
        {
            GameObject roadRoot = new GameObject("Road Surface");
            roadRoot.transform.parent = transform;

            CreateSegmentedStrip("Asphalt Segment", roadRoot.transform, 0f, -0.08f, 26.5f, 0.12f, 70f, roadMaterial);
            CreateSegmentedStrip("Left Shoulder Segment", roadRoot.transform, 15.2f, -0.06f, 3.1f, 0.08f, 60f, roadMaterial);
            CreateSegmentedStrip("Right Shoulder Segment", roadRoot.transform, -15.2f, -0.06f, 3.1f, 0.08f, 60f, roadMaterial);
            CreateSegmentedStrip("Median Segment", roadRoot.transform, 0f, 0.20f, 0.54f, 0.45f, 45f, medianMaterial);
        }

        private void CreateSegmentedStrip(string name, Transform parent, float z, float y, float width, float height, float padding, Material material)
        {
            float segmentLength = Mathf.Max(8f, poleSpacingM);
            float startX = -padding;
            float endX = RoadLengthM + padding;
            int segmentCount = Mathf.CeilToInt((endX - startX) / segmentLength);
            for (int i = 0; i < segmentCount; i++)
            {
                float a = startX + i * segmentLength;
                float b = Mathf.Min(a + segmentLength, endX);
                float length = Mathf.Max(0.1f, b - a);
                CreateCube(
                    $"{name} {i + 1:000}",
                    new Vector3(a + length * 0.5f, y, z),
                    new Vector3(length, height, width),
                    material,
                    parent
                );
            }
        }

        private void CreateMountainValley()
        {
            CreateMountainSlope("north green mountain wall", 1);
            CreateMountainSlope("south green mountain wall", -1);
            CreateTreeRows(1);
            CreateTreeRows(-1);
        }

        private void CreateMountainSlope(string name, int side)
        {
            int segments = Mathf.Max(18, numPoles);
            float length = RoadLengthM + 180f;
            float startX = -90f;
            Vector3[] vertices = new Vector3[(segments + 1) * 3];
            Vector2[] uvs = new Vector2[vertices.Length];
            int[] triangles = new int[segments * 12];

            for (int i = 0; i <= segments; i++)
            {
                float t = i / (float)segments;
                float x = startX + t * length;
                float wave = Mathf.Sin(t * Mathf.PI * 4.0f + side * 0.65f) * 0.5f + Mathf.Sin(t * Mathf.PI * 9.0f) * 0.25f;
                float ridgeHeight = 18f + wave * 6f;
                int baseIndex = i * 3;
                vertices[baseIndex] = new Vector3(x, -0.16f, side * 18.8f);
                vertices[baseIndex + 1] = new Vector3(x, 5.8f + wave * 1.8f, side * 48f);
                vertices[baseIndex + 2] = new Vector3(x, ridgeHeight, side * 92f);
                uvs[baseIndex] = new Vector2(t * 12f, 0f);
                uvs[baseIndex + 1] = new Vector2(t * 12f, 0.48f);
                uvs[baseIndex + 2] = new Vector2(t * 12f, 1f);
            }

            int triangleIndex = 0;
            for (int i = 0; i < segments; i++)
            {
                int a = i * 3;
                int b = (i + 1) * 3;
                triangles[triangleIndex++] = a;
                triangles[triangleIndex++] = b;
                triangles[triangleIndex++] = a + 1;
                triangles[triangleIndex++] = b;
                triangles[triangleIndex++] = b + 1;
                triangles[triangleIndex++] = a + 1;
                triangles[triangleIndex++] = a + 1;
                triangles[triangleIndex++] = b + 1;
                triangles[triangleIndex++] = a + 2;
                triangles[triangleIndex++] = b + 1;
                triangles[triangleIndex++] = b + 2;
                triangles[triangleIndex++] = a + 2;
            }

            GameObject slope = new GameObject(name);
            slope.transform.parent = transform;
            MeshFilter filter = slope.AddComponent<MeshFilter>();
            MeshRenderer renderer = slope.AddComponent<MeshRenderer>();
            Mesh mesh = new Mesh
            {
                name = name
            };
            mesh.vertices = vertices;
            mesh.uv = uvs;
            mesh.triangles = triangles;
            mesh.RecalculateNormals();
            filter.sharedMesh = mesh;
            if (mountainMaterial != null)
            {
                renderer.sharedMaterial = mountainMaterial;
                DigitalTwinMaterialUtility.TuneRenderer(renderer);
            }
        }

        private void CreateTreeRows(int side)
        {
            for (float x = -45f; x < RoadLengthM + 70f; x += 28f)
            {
                float offset = Mathf.Sin(x * 0.061f + side * 1.7f) * 5f;
                CreateConifer(new Vector3(x, 0f, side * (29f + Mathf.Abs(offset))), side);
                if (Mathf.Abs(Mathf.Sin(x * 0.037f)) > 0.35f)
                {
                    CreateConifer(new Vector3(x + 9f, 0.3f, side * (40f + Mathf.Abs(offset) * 0.8f)), side);
                }
            }
        }

        private void CreateConifer(Vector3 position, int side)
        {
            GameObject tree = new GameObject("dark roadside conifer");
            tree.transform.parent = transform;
            tree.transform.position = position;
            tree.transform.rotation = Quaternion.Euler(0f, side > 0 ? 8f : -8f, 0f);

            GameObject trunk = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            trunk.name = "trunk";
            trunk.transform.SetParent(tree.transform, false);
            trunk.transform.localPosition = new Vector3(0f, 0.85f, 0f);
            trunk.transform.localScale = new Vector3(0.14f, 0.85f, 0.14f);
            Renderer trunkRenderer = trunk.GetComponent<Renderer>();
            trunkRenderer.sharedMaterial = mountainMaterial;
            DigitalTwinMaterialUtility.TuneRenderer(trunkRenderer);

            for (int i = 0; i < 3; i++)
            {
                GameObject foliage = GameObject.CreatePrimitive(PrimitiveType.Sphere);
                foliage.name = $"foliage tier {i + 1}";
                foliage.transform.SetParent(tree.transform, false);
                foliage.transform.localPosition = new Vector3(0f, 1.45f + i * 0.65f, 0f);
                float scale = 2.2f - i * 0.42f;
                foliage.transform.localScale = new Vector3(scale * 0.72f, 0.82f, scale * 0.72f);
                if (forestMaterial != null)
                {
                    Renderer foliageRenderer = foliage.GetComponent<Renderer>();
                    foliageRenderer.sharedMaterial = forestMaterial;
                    DigitalTwinMaterialUtility.TuneRenderer(foliageRenderer);
                }
            }
        }

        private void CreateLaneMarkers()
        {
            float[] solidZ = { -11.15f, -0.52f, 0.52f, 11.15f };
            foreach (float z in solidZ)
            {
                CreateCube("solid lane boundary", new Vector3(RoadLengthM / 2f, 0.015f, z), new Vector3(RoadLengthM + 80f, 0.035f, 0.08f), laneMarkerMaterial);
            }

            float[] dashedZ = { -7.4f, -3.7f, 3.7f, 7.4f };
            for (float x = 0f; x < RoadLengthM + 20f; x += 22f)
            {
                foreach (float z in dashedZ)
                {
                    CreateCube("dashed lane marker", new Vector3(x, 0.02f, z), new Vector3(9.5f, 0.035f, 0.07f), laneMarkerMaterial);
                }
            }
        }

        private void CreateGuardRails()
        {
            for (float x = -20f; x < RoadLengthM + 40f; x += 8f)
            {
                CreateCube("guardrail post A", new Vector3(x, 0.52f, 16.85f), new Vector3(0.16f, 1.0f, 0.16f), guardrailMaterial);
                CreateCube("guardrail post B", new Vector3(x, 0.52f, -16.85f), new Vector3(0.16f, 1.0f, 0.16f), guardrailMaterial);
            }
            CreateCube("guardrail beam A", new Vector3(RoadLengthM / 2f, 1.02f, 16.85f), new Vector3(RoadLengthM + 110f, 0.18f, 0.20f), guardrailMaterial);
            CreateCube("guardrail beam B", new Vector3(RoadLengthM / 2f, 1.02f, -16.85f), new Vector3(RoadLengthM + 110f, 0.18f, 0.20f), guardrailMaterial);
        }

        private PoleManager CreatePole(string poleId, int index, string zoneId, float x)
        {
            GameObject root = new GameObject(poleId);
            root.transform.parent = transform;
            PoleManager pole = root.AddComponent<PoleManager>();
            pole.Initialize(poleId, index, zoneId, x);

            GameObject mast = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            mast.name = "Mast";
            mast.transform.parent = root.transform;
            mast.transform.localPosition = new Vector3(0f, 4.80f, 0f);
            mast.transform.localScale = new Vector3(0.24f, 4.80f, 0.24f);
            if (poleMaterial != null)
            {
                Renderer mastRenderer = mast.GetComponent<Renderer>();
                mastRenderer.sharedMaterial = poleMaterial;
                DigitalTwinMaterialUtility.TuneRenderer(mastRenderer);
            }

            CreatePoleBase(root.transform);
            CreateArm(root.transform, "A", new Vector3(0f, 9.18f, 4.60f), 9.25f);
            CreateArm(root.transform, "B", new Vector3(0f, 9.18f, -4.60f), 9.25f);
            CreateArmCap(root.transform, "A", new Vector3(0f, 8.48f, 8.95f));
            CreateArmCap(root.transform, "B", new Vector3(0f, 8.48f, -8.95f));
            pole.luminaireA = CreateLuminaire(root.transform, poleId, "A", x, new Vector3(0f, 8.34f, 9.35f));
            pole.luminaireB = CreateLuminaire(root.transform, poleId, "B", x, new Vector3(0f, 8.34f, -9.35f));
            return pole;
        }

        private void CreatePoleBase(Transform parent)
        {
            GameObject basePlate = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            basePlate.name = "Base";
            basePlate.transform.parent = parent;
            basePlate.transform.localPosition = new Vector3(0f, 0.08f, 0f);
            basePlate.transform.localScale = new Vector3(0.62f, 0.08f, 0.62f);
            if (poleMaterial != null)
            {
                Renderer baseRenderer = basePlate.GetComponent<Renderer>();
                baseRenderer.sharedMaterial = poleMaterial;
                DigitalTwinMaterialUtility.TuneRenderer(baseRenderer);
            }
        }

        private void CreateArm(Transform parent, string direction, Vector3 localPosition, float length)
        {
            GameObject arm = GameObject.CreatePrimitive(PrimitiveType.Cube);
            arm.name = $"Arm {direction}";
            arm.transform.parent = parent;
            arm.transform.localPosition = localPosition;
            arm.transform.localScale = new Vector3(0.20f, 0.16f, length);
            if (poleMaterial != null)
            {
                Renderer armRenderer = arm.GetComponent<Renderer>();
                armRenderer.sharedMaterial = poleMaterial;
                DigitalTwinMaterialUtility.TuneRenderer(armRenderer);
            }
        }

        private void CreateArmCap(Transform parent, string direction, Vector3 localPosition)
        {
            GameObject drop = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            drop.name = $"Drop {direction}";
            drop.transform.parent = parent;
            drop.transform.localPosition = localPosition;
            drop.transform.localScale = new Vector3(0.12f, 0.34f, 0.12f);
            if (poleMaterial != null)
            {
                Renderer dropRenderer = drop.GetComponent<Renderer>();
                dropRenderer.sharedMaterial = poleMaterial;
                DigitalTwinMaterialUtility.TuneRenderer(dropRenderer);
            }
        }

        private LuminaireController CreateLuminaire(Transform parent, string poleId, string direction, float roadX, Vector3 localPosition)
        {
            GameObject luminaireObject = new GameObject($"{poleId}-{direction}");
            luminaireObject.name = $"{poleId}-{direction}";
            luminaireObject.transform.parent = parent;
            luminaireObject.transform.localPosition = localPosition;
            luminaireObject.transform.localRotation = Quaternion.identity;
            BoxCollider selector = luminaireObject.AddComponent<BoxCollider>();
            selector.center = new Vector3(0f, -0.12f, 0f);
            selector.size = new Vector3(3.10f, 0.90f, 1.42f);

            GameObject housing = GameObject.CreatePrimitive(PrimitiveType.Cube);
            housing.name = "Luminaire Housing";
            housing.transform.SetParent(luminaireObject.transform, false);
            housing.transform.localPosition = Vector3.zero;
            housing.transform.localRotation = Quaternion.identity;
            housing.transform.localScale = new Vector3(2.72f, 0.36f, 0.96f);
            Renderer housingRenderer = housing.GetComponent<Renderer>();
            if (poleMaterial != null)
            {
                housingRenderer.sharedMaterial = poleMaterial;
            }
            DigitalTwinMaterialUtility.TuneRenderer(housingRenderer);

            LuminaireController controller = luminaireObject.AddComponent<LuminaireController>();
            controller.luminaireId = $"{poleId}-{direction}";
            controller.poleId = poleId;
            controller.direction = direction;
            controller.boardNodeId = $"RLX-{poleId}-{direction}";
            controller.maxPowerWatts = maxPowerWattsPerLuminaire;
            controller.lensRenderer = housingRenderer;
            controller.riseSpeed = 0.65f;
            controller.fallSpeed = 0.08f;
            controller.roadwayLight = CreateRoadwayBeam(luminaireObject.transform, direction, roadX);
            controller.ForceBrightness(ecoBrightness);
            return controller;
        }

        private Light CreateRoadwayBeam(Transform luminaire, string direction, float roadX)
        {
            GameObject beam = new GameObject("Roadway Beam");
            beam.transform.SetParent(luminaire, false);
            beam.transform.localPosition = Vector3.zero;
            beam.transform.localRotation = Quaternion.Euler(direction == "A" ? 97f : 82f, 0f, 0f);

            Light light = beam.AddComponent<Light>();
            light.type = LightType.Spot;
            light.range = 50f;
            light.spotAngle = 80f;
            light.innerSpotAngle = 56f;
            light.shadows = LightShadows.None;
            light.renderMode = LightRenderMode.ForcePixel;
            light.color = new Color(1f, 0.86f, 0.58f);
            return light;
        }

        private void AddNormalVehicleWave(VehicleController vehicle)
        {
            int sign = vehicle.direction == "A" ? 1 : -1;
            int sensorPoleIndex = NearestPoleIndex(vehicle.PositionAlongRoad);
            float speedFactor = Mathf.InverseLerp(8f, 24f, vehicle.speedMps);

            for (int offset = 0; offset <= 5; offset++)
            {
                int poleIndex = sensorPoleIndex + sign * offset;
                if (poleIndex < 0 || poleIndex >= numPoles)
                {
                    continue;
                }

                string luminaireId = $"P{poleIndex + 1:000}-{vehicle.direction}";
                if (_luminaires.ContainsKey(luminaireId))
                {
                    float poleX = poleIndex * poleSpacingM;
                    float distanceM = Mathf.Abs(poleX - vehicle.PositionAlongRoad);
                    float brightness = offset <= 2
                        ? 1f
                        : SpeedBasedPreviewBrightness(offset, speedFactor);
                    string detectionMode = offset == 0
                        ? "vehicle under sensor, full output"
                        : offset <= 2
                            ? "next two poles, full pre-light"
                            : "speed-based forward pre-light";
                    AddLuminaireTarget(luminaireId, brightness, vehicle, distanceM, detectionMode);
                }
            }
        }

        private float SpeedBasedPreviewBrightness(int offset, float speedFactor)
        {
            float offsetFactor = 1f - Mathf.Clamp01((offset - 3f) / 2f);
            float preview = Mathf.Lerp(0.42f, 0.92f, speedFactor);
            float distanceDrop = Mathf.Lerp(0.22f, 0.06f, speedFactor) * (1f - offsetFactor);
            return Mathf.Clamp(preview - distanceDrop, ecoBrightness, 0.96f);
        }

        private void AddEmergencyLighting(VehicleController vehicle)
        {
            AddDirectionTarget(vehicle.direction, emergencyBrightness, vehicle, "emergency full-direction safety mode");
        }

        private int LightsAhead(float speedMps)
        {
            if (speedMps < 12f) return 4;
            if (speedMps < 22f) return 6;
            return 8;
        }

        private GameObject CreateCube(string name, Vector3 position, Vector3 scale, Material material, Transform parent = null)
        {
            GameObject cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.name = name;
            cube.transform.parent = parent != null ? parent : transform;
            cube.transform.position = position;
            cube.transform.localScale = scale;
            if (material != null)
            {
                Renderer renderer = cube.GetComponent<Renderer>();
                renderer.sharedMaterial = material;
                if (material == roadMaterial)
                {
                    DigitalTwinMaterialUtility.TuneRenderer(renderer, 0.90f, 0.10f);
                }
                else
                {
                    DigitalTwinMaterialUtility.TuneRenderer(renderer);
                }
            }
            return cube;
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
                luminaire.healthScore = state.health_score > 0f ? state.health_score : luminaire.healthScore;
                luminaire.driverTemperatureC = state.driver_temperature > 0f ? state.driver_temperature : luminaire.driverTemperatureC;
                if (!string.IsNullOrEmpty(state.fault_status))
                {
                    luminaire.faultStatus = state.fault_status;
                }
                if (!string.IsNullOrEmpty(state.rex_status))
                {
                    luminaire.rexStatus = state.rex_status;
                }
            }
        }

        private void AddLuminaireTarget(string luminaireId, float brightness, VehicleController vehicle, float distanceM, string detectionMode)
        {
            if (!_luminaires.ContainsKey(luminaireId))
            {
                return;
            }

            _frameTargetMap[luminaireId] = Mathf.Max(_frameTargetMap.TryGetValue(luminaireId, out float existing) ? existing : ecoBrightness, Mathf.Clamp01(brightness));
            if (!_frameVehicleIds.TryGetValue(luminaireId, out List<string> ids))
            {
                ids = new List<string>();
                _frameVehicleIds[luminaireId] = ids;
            }
            if (vehicle != null && !ids.Contains(vehicle.vehicleId))
            {
                ids.Add(vehicle.vehicleId);
            }

            _frameNearestDistance[luminaireId] = Mathf.Min(_frameNearestDistance.TryGetValue(luminaireId, out float existingDistance) ? existingDistance : 999f, distanceM);
            _frameDetectionMode[luminaireId] = ids.Count > 1 ? $"{detectionMode}, multi-vehicle tracked ({ids.Count})" : detectionMode;
        }

        private void AddZoneTarget(string direction, int zoneIndex, float brightness, VehicleController vehicle, string detectionMode)
        {
            int start = zoneIndex * zoneSizePoles;
            int end = Mathf.Min(numPoles, start + zoneSizePoles);
            for (int i = start; i < end; i++)
            {
                string luminaireId = $"P{i + 1:000}-{direction}";
                float distance = vehicle == null ? 999f : Mathf.Abs(i * poleSpacingM - vehicle.PositionAlongRoad);
                AddLuminaireTarget(luminaireId, brightness, vehicle, distance, detectionMode);
            }
        }

        private void AddDirectionTarget(string direction, float brightness, VehicleController vehicle, string detectionMode)
        {
            for (int i = 0; i < numPoles; i++)
            {
                string luminaireId = $"P{i + 1:000}-{direction}";
                float distance = vehicle == null ? 999f : Mathf.Abs(i * poleSpacingM - vehicle.PositionAlongRoad);
                AddLuminaireTarget(luminaireId, brightness, vehicle, distance, detectionMode);
            }
        }

        private void SetLuminaireTarget(string luminaireId, float brightness)
        {
            if (_luminaires.TryGetValue(luminaireId, out LuminaireController luminaire))
            {
                luminaire.SetTarget(Mathf.Max(luminaire.targetBrightness, Mathf.Clamp01(brightness)));
            }
        }

        private float HoldSecondsForSpeed(float speedMps)
        {
            float secondsToNextPole = poleSpacingM / Mathf.Max(speedMps, 1f);
            return Mathf.Clamp(secondsToNextPole * 1.15f, 1.1f, lightHoldSeconds);
        }

        private void SetAllBrightness(float brightness)
        {
            foreach (LuminaireController luminaire in _luminaires.Values)
            {
                luminaire.SetTarget(brightness);
            }
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
                SetLuminaireTarget(luminaireId, brightness);
            }
        }

        private void SelectLuminaire(LuminaireController luminaire)
        {
            if (_selectedLuminaire != null)
            {
                _selectedLuminaire.SetSelected(false);
            }

            _selectedLuminaire = luminaire;
            if (_selectedLuminaire != null)
            {
                _selectedLuminaire.SetSelected(true);
            }
        }

        private void ResetEnergyCounters()
        {
            elapsedScenarioSeconds = 0f;
            actualEnergyKwh = 0f;
            baselineEnergyKwh = 0f;
            savedEnergyKwh = 0f;
            savedEnergyPct = 0f;
            co2SavedKg = 0f;
        }

        private void AccumulateEnergy(float dt)
        {
            if (dt <= 0f || _luminaires.Count == 0)
            {
                return;
            }

            elapsedScenarioSeconds += dt;
            float dtHours = dt / 3600f;
            float actualKw = 0f;
            foreach (LuminaireController luminaire in _luminaires.Values)
            {
                actualKw += luminaire.ActualPowerWatts / 1000f;
            }

            float baselineKw = _luminaires.Count * maxPowerWattsPerLuminaire / 1000f;
            actualEnergyKwh += actualKw * dtHours;
            baselineEnergyKwh += baselineKw * dtHours;
            savedEnergyKwh = Mathf.Max(0f, baselineEnergyKwh - actualEnergyKwh);
            savedEnergyPct = baselineEnergyKwh > 0f ? savedEnergyKwh / baselineEnergyKwh * 100f : 0f;
            co2SavedKg = savedEnergyKwh * co2KgPerKwh;
        }
    }
}
