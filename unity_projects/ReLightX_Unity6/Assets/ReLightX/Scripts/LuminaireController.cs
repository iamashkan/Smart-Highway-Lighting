using UnityEngine;
using System.Collections.Generic;

namespace ReLightX
{
    public class LuminaireController : MonoBehaviour
    {
        public static event System.Action<LuminaireController> LuminaireSelected;

        public string luminaireId;
        public string poleId;
        public string direction;
        public string boardNodeId;
        [Range(0f, 1f)] public float currentBrightness = 0.3f;
        [Range(0f, 1f)] public float targetBrightness = 0.3f;
        public float riseSpeed = 0.65f;
        public float fallSpeed = 0.08f;
        public float maxPowerWatts = 160f;
        public float healthScore = 100f;
        public float driverTemperatureC = 34f;
        public float currentMa = 0f;
        public string faultStatus = "ok";
        public string rexStatus = "Reuse";
        public int activeVehicleCount;
        public float nearestVehicleDistanceM = 999f;
        public string lastDetectionMode = "eco watch";
        public Light roadwayLight;
        public Renderer lensRenderer;
        public bool selected;

        private Material _runtimeMaterial;
        private GameObject _selectionMarker;
        private readonly List<string> _detectedVehicleIds = new List<string>();

        public float OutputVoltage => currentBrightness * 10f;
        public float ActualPowerWatts => maxPowerWatts * currentBrightness;
        public IReadOnlyList<string> DetectedVehicleIds => _detectedVehicleIds;

        private void Awake()
        {
            EnsureRuntimeMaterial();
            CreateSelectionMarker();
        }

        private void Update()
        {
            float speed = targetBrightness > currentBrightness ? riseSpeed : fallSpeed;
            currentBrightness = Mathf.MoveTowards(currentBrightness, targetBrightness, speed * Time.deltaTime);
            ApplyBrightness(currentBrightness);
        }

        public void SetTarget(float brightness)
        {
            targetBrightness = Mathf.Clamp01(brightness);
        }

        public void SetDigitalTwinDetection(IReadOnlyList<string> vehicleIds, float nearestDistanceM, string detectionMode)
        {
            _detectedVehicleIds.Clear();
            if (vehicleIds != null)
            {
                _detectedVehicleIds.AddRange(vehicleIds);
            }
            activeVehicleCount = _detectedVehicleIds.Count;
            nearestVehicleDistanceM = nearestDistanceM;
            lastDetectionMode = string.IsNullOrEmpty(detectionMode) ? "eco watch" : detectionMode;
        }

        public void Select()
        {
            LuminaireSelected?.Invoke(this);
        }

        public void SetSelected(bool active)
        {
            selected = active;
            if (_selectionMarker != null)
            {
                _selectionMarker.SetActive(active);
            }
        }

        public void ForceBrightness(float brightness)
        {
            currentBrightness = Mathf.Clamp01(brightness);
            targetBrightness = currentBrightness;
            ApplyBrightness(currentBrightness);
        }

        private void ApplyBrightness(float brightness)
        {
            EnsureRoadwayLight();
            EnsureRuntimeMaterial();

            driverTemperatureC = 28f + brightness * 31f + activeVehicleCount * 1.2f;
            currentMa = 95f + brightness * 870f;

            if (roadwayLight != null)
            {
                roadwayLight.range = 50f;
                roadwayLight.spotAngle = 80f;
                roadwayLight.innerSpotAngle = 56f;
                float intensityLevel = Mathf.InverseLerp(0.30f, 1.0f, brightness);
                roadwayLight.intensity = Mathf.Lerp(2f, 40f, intensityLevel);
                roadwayLight.color = Color.Lerp(new Color(1f, 0.62f, 0.32f), new Color(1f, 0.92f, 0.68f), brightness);
            }

            if (_runtimeMaterial != null)
            {
                Color emissive = Color.Lerp(new Color(0.35f, 0.25f, 0.12f), new Color(1f, 0.92f, 0.72f), brightness);
                _runtimeMaterial.EnableKeyword("_EMISSION");
                _runtimeMaterial.SetColor("_EmissionColor", emissive * Mathf.Lerp(1.4f, 8.0f, brightness));
            }
        }

        private void EnsureRoadwayLight()
        {
            if (roadwayLight != null)
            {
                return;
            }

            roadwayLight = gameObject.AddComponent<Light>();
            roadwayLight.type = LightType.Spot;
            roadwayLight.range = 50f;
            roadwayLight.spotAngle = 80f;
            roadwayLight.innerSpotAngle = 56f;
            roadwayLight.shadows = LightShadows.Soft;
        }

        private void EnsureRuntimeMaterial()
        {
            if (lensRenderer == null)
            {
                lensRenderer = GetComponent<Renderer>();
            }
            if (_runtimeMaterial == null && lensRenderer != null)
            {
                _runtimeMaterial = lensRenderer.material;
                DigitalTwinMaterialUtility.TuneMaterial(_runtimeMaterial);
            }
        }

        private void CreateSelectionMarker()
        {
            _selectionMarker = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            _selectionMarker.name = "selected luminaire digital twin marker";
            _selectionMarker.transform.SetParent(transform, false);
            _selectionMarker.transform.localPosition = new Vector3(0f, -0.42f, 0f);
            _selectionMarker.transform.localScale = new Vector3(0.42f, 0.10f, 0.42f);
            Renderer renderer = _selectionMarker.GetComponent<Renderer>();
            renderer.material.color = new Color(0.06f, 0.88f, 1.0f, 0.82f);
            DigitalTwinMaterialUtility.TuneRenderer(renderer);
            _selectionMarker.SetActive(false);
        }
    }
}
