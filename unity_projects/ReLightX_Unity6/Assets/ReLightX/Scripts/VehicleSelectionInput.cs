using UnityEngine;
using UnityEngine.EventSystems;

namespace ReLightX
{
    [RequireComponent(typeof(Camera))]
    public class VehicleSelectionInput : MonoBehaviour
    {
        private Camera _camera;

        private void Awake()
        {
            _camera = GetComponent<Camera>();
        }

        private void Update()
        {
            if (Input.GetMouseButtonDown(0))
            {
                TrySelectAt(Input.mousePosition);
            }

            if (Input.touchCount > 0)
            {
                Touch touch = Input.GetTouch(0);
                if (touch.phase == TouchPhase.Began)
                {
                    TrySelectAt(touch.position);
                }
            }
        }

        private void TrySelectAt(Vector2 screenPosition)
        {
            if (EventSystem.current != null && EventSystem.current.IsPointerOverGameObject())
            {
                return;
            }

            Ray ray = _camera.ScreenPointToRay(screenPosition);
            if (Physics.Raycast(ray, out RaycastHit hit, 1500f))
            {
                LuminaireController luminaire = hit.collider.GetComponentInParent<LuminaireController>();
                if (luminaire != null)
                {
                    luminaire.Select();
                    return;
                }

                VehicleController vehicle = hit.collider.GetComponentInParent<VehicleController>();
                if (vehicle != null)
                {
                    vehicle.Select();
                }
            }
        }
    }
}
