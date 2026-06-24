using UnityEngine;

namespace ReLightX
{
    public class LuminaireController : MonoBehaviour
    {
        public string luminaireId;
        public string poleId;
        public string direction;
        [Range(0f, 1f)] public float currentBrightness = 0.3f;
        [Range(0f, 1f)] public float targetBrightness = 0.3f;
        public float fadeSpeed = 2.4f;
        public Light roadwayLight;
        public Renderer lensRenderer;

        private Material _runtimeMaterial;

        private void Awake()
        {
            if (roadwayLight == null)
            {
                roadwayLight = gameObject.AddComponent<Light>();
                roadwayLight.type = LightType.Spot;
                roadwayLight.range = 32f;
                roadwayLight.spotAngle = 72f;
            }

            if (lensRenderer != null)
            {
                _runtimeMaterial = lensRenderer.material;
            }
        }

        private void Update()
        {
            currentBrightness = Mathf.MoveTowards(currentBrightness, targetBrightness, fadeSpeed * Time.deltaTime);
            ApplyBrightness(currentBrightness);
        }

        public void SetTarget(float brightness)
        {
            targetBrightness = Mathf.Clamp01(brightness);
        }

        public void ForceBrightness(float brightness)
        {
            currentBrightness = Mathf.Clamp01(brightness);
            targetBrightness = currentBrightness;
            ApplyBrightness(currentBrightness);
        }

        private void ApplyBrightness(float brightness)
        {
            if (roadwayLight != null)
            {
                roadwayLight.intensity = Mathf.Lerp(0.2f, 6.5f, brightness);
                roadwayLight.color = Color.Lerp(new Color(1f, 0.78f, 0.48f), Color.white, brightness);
            }

            if (_runtimeMaterial != null)
            {
                Color emissive = Color.Lerp(new Color(0.35f, 0.25f, 0.12f), new Color(1f, 0.92f, 0.72f), brightness);
                _runtimeMaterial.SetColor("_EmissionColor", emissive * Mathf.Lerp(0.4f, 2.8f, brightness));
            }
        }
    }
}
