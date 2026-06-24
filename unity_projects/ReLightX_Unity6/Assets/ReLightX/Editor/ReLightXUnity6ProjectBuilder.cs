using System.IO;
using System;
using ReLightX;
using UnityEditor;
using UnityEditor.Events;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Events;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

namespace ReLightX.EditorTools
{
    [InitializeOnLoad]
    public static class ReLightXUnity6ProjectBuilder
    {
        private const string ScenePath = "Assets/ReLightX/Scenes/ReLightXHighway.unity";
        private const string MaterialFolder = "Assets/ReLightX/Materials";
        private const string SceneVersionMarker = "ReLight-X Digital Twin V27";
        private const string AutoSetupSessionKey = "ReLightXDigitalTwinCheckedV27";

        static ReLightXUnity6ProjectBuilder()
        {
            EditorApplication.delayCall += AutoBuildSceneIfNeeded;
        }

        [MenuItem("ReLight-X/Build Unity 6 Highway Scene")]
        public static void BuildScene()
        {
            EnsureFolders();
            Material road = CreateMaterial("Night wet asphalt.mat", new Color(0.015f, 0.018f, 0.020f), 0.90f, 0.10f);
            Material laneMarker = CreateMaterial("Retroreflective lane paint.mat", new Color(0.88f, 0.92f, 0.86f), 0.35f, 0.28f);
            Material guardrail = CreateMaterial("Brushed guardrail metal.mat", new Color(0.24f, 0.28f, 0.28f), 0.62f, 0.30f);
            Material median = CreateMaterial("Concrete median.mat", new Color(0.12f, 0.13f, 0.12f), 0.05f, 0.70f);
            Material pole = CreateMaterial("Galvanized pole metal.mat", new Color(0.38f, 0.40f, 0.39f), 0.52f, 0.22f);
            Material lens = CreateMaterial("Warm LED emissive lens.mat", new Color(1.0f, 0.86f, 0.50f), 0.0f, 0.10f);
            Material fallbackVehicle = CreateMaterial("Fallback traffic vehicle.mat", new Color(0.12f, 0.32f, 0.52f), DigitalTwinMaterialUtility.VehicleBodyMetallic, DigitalTwinMaterialUtility.VehicleBodySmoothness);
            Material mountain = CreateMaterial("Moonlit green mountain.mat", new Color(0.030f, 0.145f, 0.072f), 0.0f, 0.88f);
            Material forest = CreateMaterial("Dark pine forest.mat", new Color(0.012f, 0.075f, 0.045f), 0.0f, 0.80f);
            Material moonDisc = CreateUnlitMaterial("Small cool moon disc.mat", new Color(0.72f, 0.82f, 0.95f, 1.0f));

            Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

            GameObject root = new GameObject("ReLightXScene");
            HighwaySceneManager manager = root.AddComponent<HighwaySceneManager>();
            root.AddComponent<MQTTClientBridge>();
            manager.numPoles = 96;
            manager.poleSpacingM = 22f;
            manager.zoneSizePoles = 9;
            manager.ecoBrightness = 0.30f;
            manager.heldBrightness = 0.76f;
            manager.lightHoldSeconds = 4.0f;
            manager.generateOnStart = true;
            manager.roadMaterial = road;
            manager.laneMarkerMaterial = laneMarker;
            manager.guardrailMaterial = guardrail;
            manager.medianMaterial = median;
            manager.poleMaterial = pole;
            manager.lensMaterial = lens;
            manager.mountainMaterial = mountain;
            manager.forestMaterial = forest;
            manager.BuildScene();
            GameObject versionMarker = new GameObject(SceneVersionMarker);
            versionMarker.transform.SetParent(root.transform, false);
            versionMarker.hideFlags = HideFlags.HideInHierarchy;

            CreateNightEnvironment();
            CreateLighting(manager.RoadLengthM, moonDisc);
            DigitalTwinCameraRig cameraRig = CreateCamera(manager.RoadLengthM);
            TrafficSimulationManager traffic = CreateTrafficManager(manager, cameraRig, fallbackVehicle);
            CreateDemoCanvas(manager, traffic, cameraRig);
            CreateEventSystemIfMissing();

            EditorSceneManager.MarkSceneDirty(scene);
            EditorSceneManager.SaveScene(scene, ScenePath);
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            AssetDatabase.SaveAssets();
            Selection.activeObject = root;
            Debug.Log($"ReLight-X Unity 6 scene generated at {ScenePath}");
        }

        private static void AutoBuildSceneIfNeeded()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
            {
                return;
            }
            if (SessionState.GetBool(AutoSetupSessionKey, false))
            {
                return;
            }
            SessionState.SetBool(AutoSetupSessionKey, true);
            if (!File.Exists(ScenePath) || ExistingSceneNeedsRebuild())
            {
                BuildScene();
            }
        }

        private static bool ExistingSceneNeedsRebuild()
        {
            string sceneText = File.ReadAllText(ScenePath);
            return sceneText.Contains("Zone Visualizer") ||
                   sceneText.Contains("clean rebuild") ||
                   sceneText.Contains("Clean Rebuild") ||
                   sceneText.Contains("road light pool") ||
                   sceneText.Contains("visible LED source glow") ||
                   sceneText.Contains("Warm LED Diffuser") ||
                   sceneText.Contains("Direction A") ||
                   sceneText.Contains("Direction B") ||
                   sceneText.Contains("Spawn A") ||
                   sceneText.Contains("Spawn B") ||
                   !sceneText.Contains(SceneVersionMarker) ||
                   !sceneText.Contains("Selected Light Card") ||
                   !sceneText.Contains("Car +10") ||
                   !sceneText.Contains("First Top") ||
                   sceneText.Contains("ecoBrightness: 0.42") ||
                   sceneText.Contains("fadeSpeed:");
        }

        private static void EnsureFolders()
        {
            CreateFolderIfMissing("Assets", "ReLightX");
            CreateFolderIfMissing("Assets/ReLightX", "Materials");
            CreateFolderIfMissing("Assets/ReLightX", "Scenes");
            CreateFolderIfMissing("Assets/ReLightX", "Prefabs");
        }

        private static void CreateFolderIfMissing(string parent, string child)
        {
            string path = $"{parent}/{child}";
            if (!AssetDatabase.IsValidFolder(path))
            {
                AssetDatabase.CreateFolder(parent, child);
            }
        }

        private static Material CreateMaterial(string fileName, Color color, float metallic = 0f, float smoothness = 0.35f)
        {
            string path = $"{MaterialFolder}/{fileName}";
            Material existing = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (existing != null)
            {
                existing.color = color;
                ConfigureMaterial(existing, metallic, smoothness);
                return existing;
            }
            Material material = new Material(FindDefaultShader()) { color = color };
            ConfigureMaterial(material, metallic, smoothness);
            AssetDatabase.CreateAsset(material, path);
            return material;
        }

        private static void ConfigureMaterial(Material material, float metallic, float smoothness)
        {
            if (material.HasProperty("_Metallic")) material.SetFloat("_Metallic", metallic);
            if (material.HasProperty("_Smoothness")) material.SetFloat("_Smoothness", smoothness);
            if (material.HasProperty("_Glossiness")) material.SetFloat("_Glossiness", smoothness);
        }

        private static Material CreateUnlitMaterial(string fileName, Color color)
        {
            string path = $"{MaterialFolder}/{fileName}";
            Material existing = AssetDatabase.LoadAssetAtPath<Material>(path);
            Shader shader = Shader.Find("Universal Render Pipeline/Unlit");
            if (shader == null)
            {
                shader = Shader.Find("Unlit/Color");
            }
            if (shader == null)
            {
                shader = FindDefaultShader();
            }
            if (existing != null)
            {
                existing.shader = shader;
                existing.color = color;
                if (existing.HasProperty("_BaseColor")) existing.SetColor("_BaseColor", color);
                ConfigureMaterial(existing, DigitalTwinMaterialUtility.TargetMetallic, DigitalTwinMaterialUtility.TargetSmoothness);
                return existing;
            }
            Material material = new Material(shader) { color = color };
            if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", color);
            ConfigureMaterial(material, DigitalTwinMaterialUtility.TargetMetallic, DigitalTwinMaterialUtility.TargetSmoothness);
            AssetDatabase.CreateAsset(material, path);
            return material;
        }

        private static Shader FindDefaultShader()
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null)
            {
                shader = Shader.Find("Standard");
            }
            return shader;
        }

        private static void CreateNightEnvironment()
        {
            RenderSettings.ambientMode = UnityEngine.Rendering.AmbientMode.Flat;
            RenderSettings.ambientLight = new Color(0.010f, 0.014f, 0.018f);
            RenderSettings.skybox = null;
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.004f, 0.008f, 0.012f);
            RenderSettings.fogDensity = 0.006f;
        }

        private static void CreateLighting(float roadLengthM, Material moonMaterial)
        {
            GameObject moon = new GameObject("Moonlight Directional");
            Light light = moon.AddComponent<Light>();
            light.type = LightType.Directional;
            light.intensity = 0.036f;
            light.color = new Color(0.20f, 0.30f, 0.42f);
            light.shadows = LightShadows.Soft;
            moon.transform.rotation = Quaternion.Euler(28f, -40f, 0f);

            GameObject moonDisc = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            moonDisc.name = "small visible moon";
            moonDisc.transform.position = new Vector3(roadLengthM * 0.58f, 92f, -210f);
            moonDisc.transform.localScale = Vector3.one * 18f;
            if (moonMaterial != null)
            {
                moonDisc.GetComponent<Renderer>().sharedMaterial = moonMaterial;
            }

            GameObject beacon = new GameObject("Emergency Beacon Light");
            Light beaconLight = beacon.AddComponent<Light>();
            beaconLight.type = LightType.Point;
            beaconLight.color = Color.red;
            beaconLight.range = 80f;
            beaconLight.intensity = 0f;
            EmergencyModeVisualizer visualizer = beacon.AddComponent<EmergencyModeVisualizer>();
            visualizer.beaconLight = beaconLight;
            beacon.transform.position = new Vector3(80f, 12f, 0f);
        }

        private static DigitalTwinCameraRig CreateCamera(float roadLengthM)
        {
            GameObject cameraObject = new GameObject("Overview Camera");
            Camera camera = cameraObject.AddComponent<Camera>();
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.002f, 0.004f, 0.007f);
            camera.fieldOfView = 48f;
            cameraObject.transform.position = new Vector3(220f, 42f, -58f);
            cameraObject.transform.rotation = Quaternion.Euler(48f, 34f, 0f);
            camera.nearClipPlane = 0.3f;
            camera.farClipPlane = 2500f;
            cameraObject.tag = "MainCamera";
            DigitalTwinCameraRig rig = cameraObject.AddComponent<DigitalTwinCameraRig>();
            cameraObject.AddComponent<VehicleSelectionInput>();
            rig.roadLengthM = roadLengthM;
            return rig;
        }

        private static TrafficSimulationManager CreateTrafficManager(
            HighwaySceneManager highway,
            DigitalTwinCameraRig cameraRig,
            Material fallbackVehicle)
        {
            GameObject trafficObject = new GameObject("Traffic Simulation Manager");
            TrafficSimulationManager traffic = trafficObject.AddComponent<TrafficSimulationManager>();
            traffic.highway = highway;
            traffic.cameraRig = cameraRig;
            traffic.fallbackVehicleMaterial = fallbackVehicle;
            traffic.maxVehicles = 10;
            traffic.initialVehicleCount = 4;
            traffic.spawnIntervalMin = 6.5f;
            traffic.spawnIntervalMax = 11.0f;
            traffic.minFrontGapM = 50f;
            traffic.emergencyChance = 0.04f;
            traffic.vehicleRemovalMarginM = 28f;
            traffic.autoFollowReplacement = true;
            traffic.normalVehiclePrefabs = LoadVehiclePrefabs(
                "sedan",
                "sedan-sports",
                "suv",
                "suv-luxury",
                "taxi",
                "van",
                "hatchback-sports",
                "truck"
            );
            traffic.policePrefab = LoadVehiclePrefab("police");
            traffic.ambulancePrefab = LoadVehiclePrefab("ambulance");
            traffic.firetruckPrefab = LoadVehiclePrefab("firetruck");
            return traffic;
        }

        private static GameObject[] LoadVehiclePrefabs(params string[] names)
        {
            var prefabs = new System.Collections.Generic.List<GameObject>();
            foreach (string name in names)
            {
                GameObject prefab = LoadVehiclePrefab(name);
                if (prefab != null) prefabs.Add(prefab);
            }
            return prefabs.ToArray();
        }

        private static GameObject LoadVehiclePrefab(string name)
        {
            string path = $"Assets/ReLightX/ImportedAssets/KenneyCarKit/Models/FBX format/{name}.fbx";
            return AssetDatabase.LoadAssetAtPath<GameObject>(path);
        }

        private static void CreateEventSystemIfMissing()
        {
            EventSystem[] existingSystems = UnityEngine.Object.FindObjectsOfType<EventSystem>();
            foreach (EventSystem existing in existingSystems)
            {
                UnityEngine.Object.DestroyImmediate(existing.gameObject);
            }

            GameObject eventSystem = new GameObject("EventSystem");
            eventSystem.AddComponent<EventSystem>();
            Type inputSystemUiModule = FindType("UnityEngine.InputSystem.UI.InputSystemUIInputModule");
            if (inputSystemUiModule != null)
            {
                eventSystem.AddComponent(inputSystemUiModule);
            }
            else
            {
                eventSystem.AddComponent<StandaloneInputModule>();
            }
        }

        private static void CreateDemoCanvas(HighwaySceneManager manager, TrafficSimulationManager traffic, DigitalTwinCameraRig cameraRig)
        {
            GameObject canvasObject = new GameObject("ReLight-X Demo Control Panel");
            Canvas canvas = canvasObject.AddComponent<Canvas>();
            canvas.renderMode = RenderMode.ScreenSpaceOverlay;
            CanvasScaler scaler = canvasObject.AddComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1440, 900);
            canvasObject.AddComponent<GraphicRaycaster>();

            GameObject panel = new GameObject("Control Panel");
            panel.transform.SetParent(canvasObject.transform, false);
            Image panelImage = panel.AddComponent<Image>();
            panelImage.color = new Color(0.025f, 0.040f, 0.060f, 0.88f);
            RectTransform panelRect = panel.GetComponent<RectTransform>();
            panelRect.anchorMin = new Vector2(0f, 1f);
            panelRect.anchorMax = new Vector2(0f, 1f);
            panelRect.pivot = new Vector2(0f, 1f);
            panelRect.anchoredPosition = new Vector2(20f, -20f);
            panelRect.sizeDelta = new Vector2(450f, 868f);

            CreateAccentBar(panel.transform, new Vector2(0f, 0f), new Vector2(450f, 4f), new Color(0.16f, 0.92f, 1f, 0.95f));
            CreateText(panel.transform, "ReLight-X Night Digital Twin", new Vector2(22f, -26f), 22, FontStyle.Bold, new Vector2(370f, 30f), new Color(0.88f, 0.98f, 1f));
            CreateText(panel.transform, "Click a vehicle or use Prev/Next Car to follow active road traffic.", new Vector2(22f, -64f), 13, FontStyle.Normal, new Vector2(400f, 42f), new Color(0.72f, 0.86f, 0.96f));

            GameObject statusCard = CreatePanelCard(panel.transform, "System Status Card", new Vector2(18f, -116f), new Vector2(414f, 126f));
            Text status = CreateText(statusCard.transform, "Mode: --\nTraffic: --\nOn road: --\nClosest gap: --\nAuto spawn: --", new Vector2(14f, -12f), 14, FontStyle.Bold, new Vector2(382f, 104f), new Color(0.86f, 0.98f, 1f));

            GameObject selectedCard = CreatePanelCard(panel.transform, "Selected Vehicle Card", new Vector2(18f, -256f), new Vector2(414f, 126f));
            Text selected = CreateText(selectedCard.transform, "Selected vehicle: none", new Vector2(14f, -12f), 13, FontStyle.Normal, new Vector2(382f, 108f), new Color(0.80f, 0.90f, 0.98f));

            CreateButton(panel.transform, "Prev Car", new Vector2(22f, -394f), traffic.SelectPreviousRoadVehicle, 78f);
            CreateButton(panel.transform, "Next Car", new Vector2(108f, -394f), traffic.SelectNextRoadVehicle, 78f);
            CreateButton(panel.transform, "First Top", new Vector2(194f, -394f), cameraRig.SetFirstPerson, 86f);
            CreateButton(panel.transform, "Third", new Vector2(288f, -394f), cameraRig.SetThirdPerson, 66f);
            CreateButton(panel.transform, "Side", new Vector2(362f, -394f), cameraRig.SetSideUpWide, 68f);

            CreateButton(panel.transform, "Car -10", new Vector2(22f, -436f), traffic.DecreaseVehicleSpeed, 78f);
            CreateButton(panel.transform, "Car +10", new Vector2(108f, -436f), traffic.IncreaseVehicleSpeed, 78f);
            CreateButton(panel.transform, "Reset Car", new Vector2(194f, -436f), traffic.ResetVehicleSpeed, 86f);
            CreateButton(panel.transform, "Overview", new Vector2(288f, -436f), cameraRig.SetOverview, 78f);
            CreateButton(panel.transform, "Cine", new Vector2(374f, -436f), cameraRig.SetCinematic, 56f);

            GameObject roadVehicleCard = CreatePanelCard(panel.transform, "Road Vehicle Selector Card", new Vector2(18f, -482f), new Vector2(414f, 112f));
            Text roadVehicles = CreateText(roadVehicleCard.transform, "Cars on road: none", new Vector2(14f, -12f), 12, FontStyle.Normal, new Vector2(382f, 88f), new Color(0.80f, 0.92f, 1f));

            GameObject processCard = CreatePanelCard(panel.transform, "Process Card", new Vector2(18f, -608f), new Vector2(414f, 74f));
            Text process = CreateText(processCard.transform, "Lighting process: waiting for traffic.", new Vector2(14f, -10f), 12, FontStyle.Normal, new Vector2(382f, 58f), new Color(0.74f, 0.88f, 0.96f));

            DigitalTwinHUD hud = panel.AddComponent<DigitalTwinHUD>();
            hud.highway = manager;
            hud.traffic = traffic;
            hud.cameraRig = cameraRig;
            hud.statusText = status;
            hud.selectedVehicleText = selected;
            hud.roadVehicleListText = roadVehicles;
            hud.processText = process;

            CreateText(panel.transform, "Traffic", new Vector2(22f, -696f), 13, FontStyle.Bold, new Vector2(180f, 22f), new Color(0.42f, 0.90f, 1f));
            CreateButton(panel.transform, "Auto", new Vector2(22f, -724f), traffic.ToggleAutoTraffic, 72f);
            CreateButton(panel.transform, "Car A", new Vector2(102f, -724f), traffic.SpawnNormalA, 72f);
            CreateButton(panel.transform, "Car B", new Vector2(182f, -724f), traffic.SpawnNormalB, 72f);
            CreateButton(panel.transform, "Emerg A", new Vector2(262f, -724f), traffic.SpawnEmergencyA, 78f, new Color(0.35f, 0.06f, 0.10f, 0.96f));
            CreateButton(panel.transform, "Emerg B", new Vector2(348f, -724f), traffic.SpawnEmergencyB, 78f, new Color(0.35f, 0.06f, 0.10f, 0.96f));

            CreateText(panel.transform, "Close-Follow Test", new Vector2(22f, -768f), 13, FontStyle.Bold, new Vector2(180f, 22f), new Color(0.42f, 0.90f, 1f));
            CreateButton(panel.transform, "2 Car A", new Vector2(22f, -796f), traffic.SpawnConvoyA, 86f);
            CreateButton(panel.transform, "2 Car B", new Vector2(116f, -796f), traffic.SpawnConvoyB, 86f);

            GameObject detailsPanel = CreateFloatingPanel(canvasObject.transform, "Digital Twin Details Panel", new Vector2(-20f, -20f), new Vector2(430f, 468f), new Vector2(1f, 1f));
            CreateAccentBar(detailsPanel.transform, new Vector2(0f, 0f), new Vector2(430f, 4f), new Color(0.16f, 0.92f, 1f, 0.95f));
            CreateText(detailsPanel.transform, "Live Digital Twin Data", new Vector2(18f, -24f), 20, FontStyle.Bold, new Vector2(360f, 28f), new Color(0.88f, 0.98f, 1f));
            CreateText(detailsPanel.transform, "Click any pole light to inspect its board/luminaire telemetry.", new Vector2(18f, -58f), 12, FontStyle.Normal, new Vector2(388f, 32f), new Color(0.72f, 0.86f, 0.96f));
            GameObject energyCard = CreatePanelCard(detailsPanel.transform, "Energy Saved Card", new Vector2(14f, -104f), new Vector2(402f, 122f));
            Text energy = CreateText(energyCard.transform, "Energy: waiting for first frame.", new Vector2(14f, -10f), 12, FontStyle.Bold, new Vector2(374f, 104f), new Color(0.86f, 0.98f, 1f));
            GameObject selectedLightCard = CreatePanelCard(detailsPanel.transform, "Selected Light Card", new Vector2(14f, -244f), new Vector2(402f, 206f));
            Text selectedLight = CreateText(selectedLightCard.transform, "Selected light: none", new Vector2(14f, -10f), 11, FontStyle.Normal, new Vector2(374f, 188f), new Color(0.80f, 0.92f, 1f));
            hud.energyText = energy;
            hud.selectedLuminaireText = selectedLight;
        }

        private static Text CreateText(Transform parent, string text, Vector2 position, int size, FontStyle style, Vector2? customSize = null, Color? color = null)
        {
            GameObject textObject = new GameObject(text);
            textObject.transform.SetParent(parent, false);
            Text label = textObject.AddComponent<Text>();
            label.text = text;
            label.font = BuiltInUiFont();
            label.fontSize = size;
            label.fontStyle = style;
            label.color = color ?? Color.white;
            label.alignment = TextAnchor.UpperLeft;
            RectTransform rect = textObject.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(0f, 1f);
            rect.pivot = new Vector2(0f, 1f);
            rect.anchoredPosition = position;
            rect.sizeDelta = customSize ?? new Vector2(290f, 48f);
            return label;
        }

        private static GameObject CreatePanelCard(Transform parent, string name, Vector2 position, Vector2 size)
        {
            GameObject card = new GameObject(name);
            card.transform.SetParent(parent, false);
            Image image = card.AddComponent<Image>();
            image.color = new Color(0.035f, 0.080f, 0.120f, 0.84f);
            RectTransform rect = card.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(0f, 1f);
            rect.pivot = new Vector2(0f, 1f);
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
            CreateAccentBar(card.transform, new Vector2(0f, 0f), new Vector2(4f, size.y), new Color(0.13f, 0.82f, 1f, 0.84f));
            return card;
        }

        private static GameObject CreateFloatingPanel(Transform parent, string name, Vector2 position, Vector2 size, Vector2 anchor)
        {
            GameObject panel = new GameObject(name);
            panel.transform.SetParent(parent, false);
            Image panelImage = panel.AddComponent<Image>();
            panelImage.color = new Color(0.025f, 0.040f, 0.060f, 0.88f);
            RectTransform rect = panel.GetComponent<RectTransform>();
            rect.anchorMin = anchor;
            rect.anchorMax = anchor;
            rect.pivot = anchor;
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
            return panel;
        }

        private static void CreateAccentBar(Transform parent, Vector2 position, Vector2 size, Color color)
        {
            GameObject bar = new GameObject("Accent");
            bar.transform.SetParent(parent, false);
            Image image = bar.AddComponent<Image>();
            image.color = color;
            RectTransform rect = bar.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(0f, 1f);
            rect.pivot = new Vector2(0f, 1f);
            rect.anchoredPosition = position;
            rect.sizeDelta = size;
        }

        private static void CreateButton(Transform parent, string text, Vector2 position, UnityAction action, float width = 138f, Color? background = null)
        {
            GameObject buttonObject = new GameObject(text);
            buttonObject.transform.SetParent(parent, false);
            Image image = buttonObject.AddComponent<Image>();
            image.color = background ?? new Color(0.055f, 0.155f, 0.215f, 0.96f);
            Button button = buttonObject.AddComponent<Button>();
            ColorBlock colors = button.colors;
            colors.highlightedColor = new Color(0.12f, 0.38f, 0.50f, 1f);
            colors.pressedColor = new Color(0.04f, 0.10f, 0.15f, 1f);
            button.colors = colors;
            UnityEventTools.AddPersistentListener(button.onClick, action);

            RectTransform rect = buttonObject.GetComponent<RectTransform>();
            rect.anchorMin = new Vector2(0f, 1f);
            rect.anchorMax = new Vector2(0f, 1f);
            rect.pivot = new Vector2(0f, 1f);
            rect.anchoredPosition = position;
            rect.sizeDelta = new Vector2(width, 34f);

            GameObject textObject = new GameObject("Label");
            textObject.transform.SetParent(buttonObject.transform, false);
            Text label = textObject.AddComponent<Text>();
            label.text = text;
            label.font = BuiltInUiFont();
            label.fontSize = 13;
            label.color = new Color(0.88f, 0.98f, 1f);
            label.alignment = TextAnchor.MiddleCenter;
            RectTransform textRect = textObject.GetComponent<RectTransform>();
            textRect.anchorMin = Vector2.zero;
            textRect.anchorMax = Vector2.one;
            textRect.offsetMin = Vector2.zero;
            textRect.offsetMax = Vector2.zero;
        }

        private static Font BuiltInUiFont()
        {
            Font font = Resources.GetBuiltinResource<Font>("LegacyRuntime.ttf");
            if (font == null)
            {
                Debug.LogWarning("LegacyRuntime.ttf was not found; Unity UI text will use its default runtime font.");
            }
            return font;
        }

        private static Type FindType(string fullName)
        {
            foreach (var assembly in AppDomain.CurrentDomain.GetAssemblies())
            {
                Type type = assembly.GetType(fullName);
                if (type != null)
                {
                    return type;
                }
            }
            return null;
        }
    }
}
