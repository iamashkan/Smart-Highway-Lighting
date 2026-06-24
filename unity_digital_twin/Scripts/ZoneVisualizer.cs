using System.Collections.Generic;
using UnityEngine;

namespace ReLightX
{
    public class ZoneVisualizer : MonoBehaviour
    {
        public int zoneCount = 4;
        public int zoneSizePoles = 8;
        public float poleSpacingM = 40f;
        public Material ecoMaterial;
        public Material normalMaterial;
        public Material emergencyMaterial;
        public Material faultMaterial;

        private readonly Dictionary<string, Renderer> _zones = new Dictionary<string, Renderer>();

        private void Start()
        {
            BuildZones();
        }

        public void BuildZones()
        {
            for (int zone = 0; zone < zoneCount; zone++)
            {
                CreateZone("A", zone, 7.4f);
                CreateZone("B", zone, -7.4f);
            }
        }

        private void CreateZone(string direction, int zone, float z)
        {
            GameObject obj = GameObject.CreatePrimitive(PrimitiveType.Cube);
            obj.name = $"{direction}-Z{zone:00}";
            obj.transform.parent = transform;
            float length = zoneSizePoles * poleSpacingM;
            obj.transform.position = new Vector3(zone * length + length / 2f - poleSpacingM / 2f, 0.02f, z);
            obj.transform.localScale = new Vector3(length, 0.04f, 6.8f);
            Renderer renderer = obj.GetComponent<Renderer>();
            renderer.material = ecoMaterial;
            _zones[obj.name] = renderer;
        }

        public void SetZoneMode(string zoneId, string mode)
        {
            if (!_zones.TryGetValue(zoneId, out Renderer renderer)) return;
            if (mode == "emergency" && emergencyMaterial != null) renderer.material = emergencyMaterial;
            else if (mode == "normal_vehicle" && normalMaterial != null) renderer.material = normalMaterial;
            else if (mode == "fault" && faultMaterial != null) renderer.material = faultMaterial;
            else if (ecoMaterial != null) renderer.material = ecoMaterial;
        }
    }
}
