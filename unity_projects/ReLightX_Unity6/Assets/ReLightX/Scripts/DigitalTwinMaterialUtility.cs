using UnityEngine;

namespace ReLightX
{
    public static class DigitalTwinMaterialUtility
    {
        public const float TargetMetallic = 0.65f;
        public const float TargetSmoothness = 0.10f;
        public const float VehicleBodyMetallic = 1.0f;
        public const float VehicleBodySmoothness = 1.0f;

        public static void TuneHierarchy(GameObject root)
        {
            if (root == null)
            {
                return;
            }

            Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);
            foreach (Renderer renderer in renderers)
            {
                TuneRenderer(renderer);
            }
        }

        public static void TuneRenderer(Renderer renderer)
        {
            TuneRenderer(renderer, TargetMetallic, TargetSmoothness);
        }

        public static void TuneVehicleBodyHierarchy(GameObject root)
        {
            if (root == null)
            {
                return;
            }

            Renderer[] renderers = root.GetComponentsInChildren<Renderer>(true);
            foreach (Renderer renderer in renderers)
            {
                TuneVehicleBodyRenderer(renderer);
            }
        }

        public static void TuneVehicleBodyRenderer(Renderer renderer)
        {
            TuneRenderer(renderer, VehicleBodyMetallic, VehicleBodySmoothness);
        }

        public static void TuneRenderer(Renderer renderer, float metallic, float smoothness)
        {
            if (renderer == null)
            {
                return;
            }

            Material[] materials = renderer.materials;
            for (int i = 0; i < materials.Length; i++)
            {
                TuneMaterial(materials[i], metallic, smoothness);
            }
            renderer.materials = materials;
        }

        public static void TuneMaterial(Material material)
        {
            TuneMaterial(material, TargetMetallic, TargetSmoothness);
        }

        public static void TuneMaterial(Material material, float metallic, float smoothness)
        {
            if (material == null)
            {
                return;
            }

            if (material.HasProperty("_Metallic"))
            {
                material.SetFloat("_Metallic", metallic);
            }
            if (material.HasProperty("_Smoothness"))
            {
                material.SetFloat("_Smoothness", smoothness);
            }
            if (material.HasProperty("_Glossiness"))
            {
                material.SetFloat("_Glossiness", smoothness);
            }
        }
    }
}
