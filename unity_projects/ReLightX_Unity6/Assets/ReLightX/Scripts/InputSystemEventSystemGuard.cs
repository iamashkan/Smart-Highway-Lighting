using System;
using UnityEngine;
using UnityEngine.EventSystems;

namespace ReLightX
{
    public static class InputSystemEventSystemGuard
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        private static void RepairAfterSceneLoad()
        {
            RepairEventSystems();
        }

        public static void RepairEventSystems()
        {
            EventSystem[] systems = UnityEngine.Object.FindObjectsOfType<EventSystem>();
            EventSystem activeSystem = systems.Length > 0 ? systems[0] : null;
            if (activeSystem == null)
            {
                GameObject eventSystemObject = new GameObject("EventSystem");
                activeSystem = eventSystemObject.AddComponent<EventSystem>();
            }

            for (int i = 1; i < systems.Length; i++)
            {
                UnityEngine.Object.Destroy(systems[i].gameObject);
            }

            Type inputSystemModuleType = FindType("UnityEngine.InputSystem.UI.InputSystemUIInputModule");
            BaseInputModule[] modules = activeSystem.GetComponents<BaseInputModule>();
            bool hasSupportedModule = false;
            foreach (BaseInputModule module in modules)
            {
                bool isInputSystemModule = inputSystemModuleType != null && inputSystemModuleType.IsInstanceOfType(module);
                bool isLegacyModule = inputSystemModuleType == null && module is StandaloneInputModule;
                if (isInputSystemModule || isLegacyModule)
                {
                    hasSupportedModule = true;
                }
                else
                {
                    UnityEngine.Object.Destroy(module);
                }
            }

            if (!hasSupportedModule)
            {
                if (inputSystemModuleType != null)
                {
                    activeSystem.gameObject.AddComponent(inputSystemModuleType);
                }
                else
                {
                    activeSystem.gameObject.AddComponent<StandaloneInputModule>();
                }
            }
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
