using System.Collections.Generic;
using System.Linq;
using UnityEngine;

namespace ReLightX
{
    public class TrafficSimulationManager : MonoBehaviour
    {
        public HighwaySceneManager highway;
        public DigitalTwinCameraRig cameraRig;
        public GameObject[] normalVehiclePrefabs;
        public GameObject policePrefab;
        public GameObject ambulancePrefab;
        public GameObject firetruckPrefab;
        public Material fallbackVehicleMaterial;

        public bool autoTraffic = true;
        public int maxVehicles = 10;
        public int initialVehicleCount = 4;
        public float spawnIntervalMin = 6.5f;
        public float spawnIntervalMax = 11.0f;
        public float minFrontGapM = 50f;
        public float emergencyChance = 0.04f;
        public float vehicleRemovalMarginM = 28f;
        public bool autoFollowReplacement = true;
        public float minVehicleSpeedMps = 4f;
        public float maxVehicleSpeedMps = 34f;

        public int activeVehicleCount;
        public int roadVehicleCount;
        public float closestGapM = 999f;
        public bool emergencyActive;
        public string lastEvent = "traffic simulation ready";

        private readonly List<VehicleController> _vehicles = new List<VehicleController>();
        private float _nextSpawnTime;
        private int _vehicleSerial;
        private bool _followReplacementRequested;
        private CameraViewMode _replacementViewMode = CameraViewMode.ThirdPerson;

        public IReadOnlyList<VehicleController> Vehicles => _vehicles;
        public VehicleController SelectedVehicle => cameraRig != null ? cameraRig.selectedVehicle : null;
        public float SelectedVehicleSpeedOffsetKph => SelectedVehicle != null ? SelectedVehicle.manualSpeedOffsetKph : 0f;

        private void Start()
        {
            if (highway == null) highway = FindObjectOfType<HighwaySceneManager>();
            if (cameraRig == null) cameraRig = FindObjectOfType<DigitalTwinCameraRig>();
            ScheduleNextSpawn(spawnIntervalMin);
            int startCount = Mathf.Clamp(initialVehicleCount, 0, maxVehicles);
            for (int i = 0; i < startCount; i++)
            {
                SpawnRandomVehicle(true);
            }
        }

        private void Update()
        {
            CleanupDestroyedVehicles();
            RemoveVehiclesOutsideRoad();
            MaintainFollowCameraSelection();
            if (autoTraffic && Time.time >= _nextSpawnTime && _vehicles.Count < maxVehicles)
            {
                SpawnRandomVehicle(false);
                ScheduleNextSpawn();
            }

            ApplyGapControl();
            activeVehicleCount = _vehicles.Count;
            roadVehicleCount = _vehicles.Count(IsInsideRoad);
            emergencyActive = _vehicles.Any(vehicle => vehicle != null && vehicle.emergencyVehicle);
            highway?.ApplyAdaptiveLightingFromVehicles(_vehicles);
        }

        public void ToggleAutoTraffic()
        {
            autoTraffic = !autoTraffic;
            lastEvent = autoTraffic ? "auto traffic enabled" : "auto traffic paused";
        }

        public void SpawnNormalA()
        {
            SpawnManualVehicle("normal_car", "A");
        }

        public void SpawnNormalB()
        {
            SpawnManualVehicle("normal_car", "B");
        }

        public void SpawnEmergencyA()
        {
            string type = Random.value < 0.5f ? "ambulance" : "police_car";
            SpawnManualVehicle(type, "A");
        }

        public void SpawnEmergencyB()
        {
            string type = Random.value < 0.5f ? "fire_truck" : "police_car";
            SpawnManualVehicle(type, "B");
        }

        public void SelectNextRoadVehicle()
        {
            SelectRoadVehicle(1);
        }

        public void SelectPreviousRoadVehicle()
        {
            SelectRoadVehicle(-1);
        }

        public void IncreaseVehicleSpeed()
        {
            AdjustSelectedVehicleSpeedKph(10f);
        }

        public void DecreaseVehicleSpeed()
        {
            AdjustSelectedVehicleSpeedKph(-10f);
        }

        public void ResetVehicleSpeed()
        {
            VehicleController selected = SelectedVehicle;
            if (selected == null || !IsInsideRoad(selected))
            {
                lastEvent = "select one road car before resetting speed";
                return;
            }

            selected.manualSpeedOffsetKph = 0f;
            selected.desiredSpeedMps = Mathf.Clamp(selected.baseCruiseSpeedMps, minVehicleSpeedMps, maxVehicleSpeedMps);
            lastEvent = $"{selected.vehicleId} speed offset reset";
        }

        public void SpawnConvoyA()
        {
            SpawnConvoy("A");
        }

        public void SpawnConvoyB()
        {
            SpawnConvoy("B");
        }

        private void SpawnRandomVehicle(bool insideRoad)
        {
            string direction = Random.value < 0.5f ? "A" : "B";
            bool emergency = Random.value < emergencyChance;
            string type = emergency ? RandomEmergencyType() : "normal_car";
            float start = direction == "A" ? -80f : highway.RoadLengthM + 80f;
            if (insideRoad)
            {
                start = Random.Range(40f, highway.RoadLengthM - 40f);
            }
            SpawnVehicle(type, direction, RandomLane(direction), start, emergency ? Random.Range(14f, 22f) : Random.Range(8f, 15f), insideRoad);
        }

        private void SpawnManualVehicle(string type, string direction)
        {
            if (highway == null)
            {
                lastEvent = "manual spawn failed: highway not ready";
                return;
            }

            string lane = RandomLane(direction);
            float startX = FindManualSpawnPosition(direction, lane);
            float speed = type == "normal_car" ? Random.Range(8f, 15f) : Random.Range(14f, 22f);
            VehicleController spawned = SpawnVehicle(type, direction, lane, startX, speed, false, true);
            if (spawned != null)
            {
                lastEvent = $"manual spawn {spawned.vehicleId} direction {direction}";
            }
        }

        private VehicleController SpawnVehicle(string type, string direction, string lane, float startX, float speed, bool spreadInitial, bool selectAfterSpawn = false)
        {
            _vehicleSerial++;
            string id = $"{type.ToUpperInvariant()}-{_vehicleSerial:000}";
            GameObject root = new GameObject(id);
            GameObject prefab = PrefabForType(type);
            if (prefab != null)
            {
                GameObject visual = Instantiate(prefab, root.transform);
                visual.name = $"{type} visual";
                visual.transform.localPosition = Vector3.zero;
                visual.transform.localRotation = Quaternion.identity;
                visual.transform.localScale = Vector3.one * ModelScale(type);
                DigitalTwinMaterialUtility.TuneVehicleBodyHierarchy(visual);
            }
            else
            {
                GameObject fallback = GameObject.CreatePrimitive(PrimitiveType.Cube);
                fallback.name = $"{type} fallback visual";
                fallback.transform.SetParent(root.transform, false);
                fallback.transform.localScale = type == "fire_truck" ? new Vector3(6.5f, 2.5f, 2.2f) : new Vector3(4.4f, 1.5f, 1.9f);
                Renderer renderer = fallback.GetComponent<Renderer>();
                if (fallbackVehicleMaterial != null) renderer.sharedMaterial = fallbackVehicleMaterial;
                DigitalTwinMaterialUtility.TuneVehicleBodyRenderer(renderer);
            }

            VehicleController vehicle = root.AddComponent<VehicleController>();
            vehicle.Initialize(id, type, direction, lane, startX, speed, highway.RoadLengthM);
            _vehicles.Add(vehicle);
            lastEvent = $"spawned {type} {direction} lane {lane}";

            if (selectAfterSpawn && cameraRig != null)
            {
                cameraRig.FollowReplacementVehicle(vehicle, cameraRig.mode);
            }

            return vehicle;
        }

        private void ApplyGapControl()
        {
            closestGapM = 999f;
            foreach (string lane in new[] { "A1", "A2", "A3", "B1", "B2", "B3" })
            {
                List<VehicleController> laneVehicles = _vehicles
                    .Where(vehicle => vehicle != null && vehicle.laneId == lane)
                    .OrderBy(vehicle => vehicle.direction == "A" ? vehicle.PositionAlongRoad : -vehicle.PositionAlongRoad)
                    .ToList();

                for (int i = 0; i < laneVehicles.Count; i++)
                {
                    VehicleController current = laneVehicles[i];
                    float baseDesired = current.emergencyVehicle ? 20f : Mathf.Clamp(current.baseCruiseSpeedMps, 8f, 15f);
                    baseDesired += current.manualSpeedOffsetKph / 3.6f;
                    current.measuredFrontGapM = 999f;
                    if (i < laneVehicles.Count - 1)
                    {
                        VehicleController front = laneVehicles[i + 1];
                        float gap = Mathf.Abs(front.PositionAlongRoad - current.PositionAlongRoad);
                        current.measuredFrontGapM = gap;
                        closestGapM = Mathf.Min(closestGapM, gap);
                        if (gap < minFrontGapM)
                        {
                            baseDesired = Mathf.Max(minVehicleSpeedMps, front.speedMps - 3f);
                        }
                        else if (gap < minFrontGapM * 1.6f)
                        {
                            baseDesired = Mathf.Min(baseDesired, front.speedMps);
                        }
                    }
                    current.desiredSpeedMps = Mathf.Clamp(baseDesired, minVehicleSpeedMps, maxVehicleSpeedMps);
                }
            }
        }

        private void AdjustSelectedVehicleSpeedKph(float deltaKph)
        {
            VehicleController selected = SelectedVehicle;
            if (selected == null || !IsInsideRoad(selected))
            {
                lastEvent = "select one road car before changing speed";
                return;
            }

            selected.manualSpeedOffsetKph = Mathf.Clamp(selected.manualSpeedOffsetKph + deltaKph, -30f, 60f);
            selected.desiredSpeedMps = Mathf.Clamp(
                selected.baseCruiseSpeedMps + selected.manualSpeedOffsetKph / 3.6f,
                minVehicleSpeedMps,
                maxVehicleSpeedMps
            );
            lastEvent = $"{selected.vehicleId} speed offset {selected.manualSpeedOffsetKph:+0;-0;0} km/h";
        }

        private void SpawnConvoy(string direction)
        {
            if (highway == null)
            {
                lastEvent = "convoy spawn failed: highway not ready";
                return;
            }

            string lane = RandomLane(direction);
            float leadX = FindManualSpawnPosition(direction, lane);
            float spacing = Mathf.Max(highway.poleSpacingM * 2f, 18f);
            float trailX = Mathf.Clamp(leadX - (direction == "A" ? spacing : -spacing), 45f, highway.RoadLengthM - 45f);
            float speed = Random.Range(9f, 13f);
            VehicleController lead = SpawnVehicle("normal_car", direction, lane, leadX, speed, false, true);
            VehicleController trail = SpawnVehicle("normal_car", direction, lane, trailX, speed * 0.98f, false, false);
            if (lead != null && trail != null)
            {
                lastEvent = $"spawned two-car convoy {direction}, gap {Mathf.Abs(lead.PositionAlongRoad - trail.PositionAlongRoad):0.0} m";
            }
        }

        private void CleanupDestroyedVehicles()
        {
            _vehicles.RemoveAll(vehicle => vehicle == null);
        }

        private void RemoveVehiclesOutsideRoad()
        {
            if (highway == null)
            {
                return;
            }

            for (int i = _vehicles.Count - 1; i >= 0; i--)
            {
                VehicleController vehicle = _vehicles[i];
                if (vehicle == null)
                {
                    _vehicles.RemoveAt(i);
                    continue;
                }

                bool outsideRoad = vehicle.PositionAlongRoad < -vehicleRemovalMarginM ||
                                   vehicle.PositionAlongRoad > highway.RoadLengthM + vehicleRemovalMarginM;
                if (!outsideRoad)
                {
                    continue;
                }

                bool wasSelected = cameraRig != null && cameraRig.selectedVehicle == vehicle;
                bool wasFollowMode = wasSelected &&
                                     (cameraRig.mode == CameraViewMode.FirstPerson ||
                                      cameraRig.mode == CameraViewMode.ThirdPerson ||
                                      cameraRig.mode == CameraViewMode.SideUpWide);
                _vehicles.RemoveAt(i);
                Destroy(vehicle.gameObject);
                if (wasSelected && cameraRig != null)
                {
                    _followReplacementRequested = wasFollowMode;
                    _replacementViewMode = cameraRig.mode;
                    cameraRig.SelectVehicle(null);
                    lastEvent = "followed vehicle left road; selecting another active car";
                }
            }
        }

        private void MaintainFollowCameraSelection()
        {
            if (!autoFollowReplacement || cameraRig == null)
            {
                return;
            }

            bool needsReplacement = _followReplacementRequested ||
                                    (cameraRig.selectedVehicle != null && !IsInsideRoad(cameraRig.selectedVehicle));
            if (!needsReplacement)
            {
                return;
            }

            List<VehicleController> candidates = _vehicles
                .Where(IsInsideRoad)
                .ToList();
            if (candidates.Count == 0)
            {
                return;
            }

            VehicleController replacement = candidates[Random.Range(0, candidates.Count)];
            cameraRig.FollowReplacementVehicle(replacement, _replacementViewMode);
            _followReplacementRequested = false;
            lastEvent = $"camera jumped to {replacement.vehicleId}";
        }

        public bool IsInsideRoad(VehicleController vehicle)
        {
            if (vehicle == null || highway == null)
            {
                return false;
            }
            return vehicle.PositionAlongRoad >= 0f && vehicle.PositionAlongRoad <= highway.RoadLengthM;
        }

        private void SelectRoadVehicle(int step)
        {
            if (cameraRig == null)
            {
                lastEvent = "vehicle select failed: camera not ready";
                return;
            }

            List<VehicleController> candidates = _vehicles
                .Where(IsInsideRoad)
                .OrderBy(vehicle => vehicle.PositionAlongRoad)
                .ToList();
            if (candidates.Count == 0)
            {
                lastEvent = "no cars currently inside the road";
                return;
            }

            int currentIndex = cameraRig.selectedVehicle == null ? -1 : candidates.IndexOf(cameraRig.selectedVehicle);
            int nextIndex;
            if (currentIndex < 0)
            {
                nextIndex = step >= 0 ? 0 : candidates.Count - 1;
            }
            else
            {
                nextIndex = (currentIndex + step + candidates.Count) % candidates.Count;
            }

            VehicleController selected = candidates[nextIndex];
            cameraRig.FollowReplacementVehicle(selected, cameraRig.mode);
            lastEvent = $"selected {selected.vehicleId}";
        }

        private float FindManualSpawnPosition(string direction, string lane)
        {
            float baseX = direction == "A" ? 90f : highway.RoadLengthM - 90f;
            if (cameraRig != null && IsInsideRoad(cameraRig.selectedVehicle))
            {
                float behindSelected = cameraRig.selectedVehicle.PositionAlongRoad - cameraRig.selectedVehicle.TravelSign * 65f;
                baseX = Mathf.Clamp(behindSelected, 50f, highway.RoadLengthM - 50f);
            }

            float searchStep = direction == "A" ? -28f : 28f;
            for (int i = 0; i < 10; i++)
            {
                float candidateX = Mathf.Clamp(baseX + searchStep * i, 45f, highway.RoadLengthM - 45f);
                bool clear = _vehicles
                    .Where(vehicle => vehicle != null && vehicle.laneId == lane && IsInsideRoad(vehicle))
                    .All(vehicle => Mathf.Abs(vehicle.PositionAlongRoad - candidateX) >= minFrontGapM * 0.75f);
                if (clear)
                {
                    return candidateX;
                }
            }

            return baseX;
        }

        private void ScheduleNextSpawn(float fixedDelay = -1f)
        {
            _nextSpawnTime = Time.time + (fixedDelay > 0f ? fixedDelay : Random.Range(spawnIntervalMin, spawnIntervalMax));
        }

        private string RandomLane(string direction)
        {
            int lane = Random.Range(1, 4);
            return $"{direction}{lane}";
        }

        private string RandomEmergencyType()
        {
            float roll = Random.value;
            if (roll < 0.40f) return "police_car";
            if (roll < 0.72f) return "ambulance";
            return "fire_truck";
        }

        private GameObject PrefabForType(string type)
        {
            if (type == "police_car") return policePrefab;
            if (type == "ambulance") return ambulancePrefab;
            if (type == "fire_truck") return firetruckPrefab;
            if (normalVehiclePrefabs != null && normalVehiclePrefabs.Length > 0)
            {
                return normalVehiclePrefabs[Random.Range(0, normalVehiclePrefabs.Length)];
            }
            return null;
        }

        private float ModelScale(string type)
        {
            if (type == "fire_truck") return 1.05f;
            if (type == "ambulance") return 1.0f;
            return 0.95f;
        }
    }
}
