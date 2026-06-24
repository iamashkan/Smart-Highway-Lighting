using UnityEngine;

namespace ReLightX
{
    public enum CameraViewMode
    {
        Overview,
        FirstPerson,
        ThirdPerson,
        SideUpWide,
        Cinematic
    }

    [RequireComponent(typeof(Camera))]
    public class DigitalTwinCameraRig : MonoBehaviour
    {
        public CameraViewMode mode = CameraViewMode.Cinematic;
        public VehicleController selectedVehicle;
        public Transform overviewTarget;
        public float followSmoothing = 3.2f;
        public float cinematicSmoothing = 1.5f;
        public float sideUpViewHeightM = 34f;
        public float sideUpViewDistanceM = 58f;
        public float roadLengthM = 1240f;
        public bool keepFollowModeOnReplacement = true;

        private Camera _camera;
        private float _cinematicPhase;

        public string ModeLabel => mode.ToString();

        private void Awake()
        {
            _camera = GetComponent<Camera>();
            _camera.fieldOfView = 48f;
        }

        private void OnEnable()
        {
            VehicleController.VehicleSelected += SelectVehicle;
        }

        private void OnDisable()
        {
            VehicleController.VehicleSelected -= SelectVehicle;
        }

        private void Update()
        {
            if (Input.GetKeyDown(KeyCode.Alpha1) || Input.GetKeyDown(KeyCode.Keypad1))
            {
                SetOverview();
            }
            else if (Input.GetKeyDown(KeyCode.Alpha2) || Input.GetKeyDown(KeyCode.Keypad2))
            {
                SetThirdPerson();
            }
            else if (Input.GetKeyDown(KeyCode.Alpha3) || Input.GetKeyDown(KeyCode.Keypad3))
            {
                SetFirstPerson();
            }
            else if (Input.GetKeyDown(KeyCode.Alpha4) || Input.GetKeyDown(KeyCode.Keypad4))
            {
                SetSideUpWide();
            }
            else if (Input.GetKeyDown(KeyCode.Alpha5) || Input.GetKeyDown(KeyCode.Keypad5))
            {
                SetCinematic();
            }
        }

        private void LateUpdate()
        {
            if (selectedVehicle == null && mode != CameraViewMode.Overview)
            {
                mode = CameraViewMode.Cinematic;
            }

            Vector3 desiredPosition;
            Vector3 lookAt;
            float desiredFov = 48f;
            float smoothing = followSmoothing;

            if (mode == CameraViewMode.FirstPerson && selectedVehicle != null)
            {
                desiredPosition = selectedVehicle.FirstPersonCameraPosition();
                lookAt = selectedVehicle.FirstPersonLookAt();
                desiredFov = 52f;
            }
            else if (mode == CameraViewMode.ThirdPerson && selectedVehicle != null)
            {
                desiredPosition = selectedVehicle.ThirdPersonCameraPosition();
                lookAt = selectedVehicle.ThirdPersonLookAt();
                desiredFov = 48f;
            }
            else if (mode == CameraViewMode.SideUpWide && selectedVehicle != null)
            {
                float side = selectedVehicle.transform.position.z >= 0f ? -1f : 1f;
                desiredPosition = selectedVehicle.transform.position + new Vector3(-selectedVehicle.TravelSign * 8f, sideUpViewHeightM, side * sideUpViewDistanceM);
                lookAt = selectedVehicle.transform.position + new Vector3(selectedVehicle.TravelSign * 6f, 1.2f, 0f);
                desiredFov = 64f;
            }
            else if (mode == CameraViewMode.Overview)
            {
                desiredPosition = new Vector3(roadLengthM * 0.42f, 54f, -76f);
                lookAt = new Vector3(roadLengthM * 0.48f, 0f, 0f);
                desiredFov = 50f;
            }
            else
            {
                _cinematicPhase += Time.deltaTime * 0.020f;
                float x = Mathf.Lerp(80f, roadLengthM - 80f, Mathf.PingPong(_cinematicPhase, 1f));
                desiredPosition = new Vector3(x, 24f, -36f + Mathf.Sin(Time.time * 0.16f) * 8f);
                lookAt = new Vector3(x + 60f, 1.6f, 3f);
                desiredFov = 46f;
                smoothing = cinematicSmoothing;
            }

            transform.position = Vector3.Lerp(transform.position, desiredPosition, 1f - Mathf.Exp(-smoothing * Time.deltaTime));
            Quaternion desiredRotation = Quaternion.LookRotation(lookAt - transform.position, Vector3.up);
            transform.rotation = Quaternion.Slerp(transform.rotation, desiredRotation, 1f - Mathf.Exp(-smoothing * Time.deltaTime));
            _camera.fieldOfView = Mathf.Lerp(_camera.fieldOfView, desiredFov, 1f - Mathf.Exp(-2.4f * Time.deltaTime));
        }

        public void SelectVehicle(VehicleController vehicle)
        {
            if (selectedVehicle != null)
            {
                selectedVehicle.SetSelected(false);
            }

            if (vehicle == null)
            {
                selectedVehicle = null;
                if (mode != CameraViewMode.Overview)
                {
                    mode = CameraViewMode.Cinematic;
                }
                return;
            }

            selectedVehicle = vehicle;
            selectedVehicle.SetSelected(true);
            mode = CameraViewMode.ThirdPerson;
        }

        public void FollowReplacementVehicle(VehicleController vehicle)
        {
            CameraViewMode preservedMode = FollowableMode(mode) ? mode : CameraViewMode.ThirdPerson;
            SelectVehicle(vehicle);
            if (keepFollowModeOnReplacement)
            {
                mode = preservedMode;
            }
        }

        public void FollowReplacementVehicle(VehicleController vehicle, CameraViewMode preferredMode)
        {
            SelectVehicle(vehicle);
            if (keepFollowModeOnReplacement && FollowableMode(preferredMode))
            {
                mode = preferredMode;
            }
        }

        public void SetOverview()
        {
            mode = CameraViewMode.Overview;
        }

        public void SetFirstPerson()
        {
            if (selectedVehicle != null)
            {
                mode = CameraViewMode.FirstPerson;
            }
        }

        public void SetThirdPerson()
        {
            if (selectedVehicle != null)
            {
                mode = CameraViewMode.ThirdPerson;
            }
        }

        public void SetSideUpWide()
        {
            if (selectedVehicle != null)
            {
                mode = CameraViewMode.SideUpWide;
            }
        }

        public void SetCinematic()
        {
            mode = CameraViewMode.Cinematic;
        }

        private bool FollowableMode(CameraViewMode viewMode)
        {
            return viewMode == CameraViewMode.FirstPerson ||
                   viewMode == CameraViewMode.ThirdPerson ||
                   viewMode == CameraViewMode.SideUpWide;
        }
    }
}
