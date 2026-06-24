using System.Linq;
using UnityEngine;
using UnityEngine.UI;

namespace ReLightX
{
    public class DigitalTwinHUD : MonoBehaviour
    {
        public HighwaySceneManager highway;
        public TrafficSimulationManager traffic;
        public DigitalTwinCameraRig cameraRig;
        public Text statusText;
        public Text selectedVehicleText;
        public Text selectedLuminaireText;
        public Text roadVehicleListText;
        public Text processText;
        public Text energyText;

        private void Start()
        {
            if (highway == null) highway = FindObjectOfType<HighwaySceneManager>();
            if (traffic == null) traffic = FindObjectOfType<TrafficSimulationManager>();
            if (cameraRig == null) cameraRig = FindObjectOfType<DigitalTwinCameraRig>();
        }

        private void Update()
        {
            if (traffic != null && statusText != null)
            {
                string selectedOffset = traffic.SelectedVehicle == null
                    ? "--"
                    : $"{traffic.SelectedVehicleSpeedOffsetKph:+0;-0;0} km/h";
                statusText.text =
                    $"Mode: {(traffic.emergencyActive ? "EMERGENCY" : "ADAPTIVE ECO")}\n" +
                    $"Traffic: {traffic.activeVehicleCount} vehicles\n" +
                    $"On road: {traffic.roadVehicleCount} vehicles\n" +
                    $"Closest gap: {(traffic.closestGapM > 200f ? "--" : traffic.closestGapM.ToString("0.0") + " m")}\n" +
                    $"Auto spawn: {(traffic.autoTraffic ? "on" : "paused")}\n" +
                    $"Selected speed offset: {selectedOffset}";
            }

            if (cameraRig != null && selectedVehicleText != null)
            {
                VehicleController vehicle = cameraRig.selectedVehicle;
                selectedVehicleText.text = vehicle == null
                    ? "Selected vehicle: none\nClick any car or use Prev/Next Car.\nThen use First Top, Third, Side, Car -10, Car +10, or Reset Car."
                    : $"Selected: {vehicle.vehicleId}\n" +
                      $"Type: {vehicle.vehicleType} | Lane: {vehicle.laneId}\n" +
                      $"Speed: {vehicle.speedMps:0.0} m/s ({vehicle.SpeedKph:0} km/h)\n" +
                      $"Target: {vehicle.desiredSpeedMps:0.0} m/s ({vehicle.DesiredSpeedKph:0} km/h)\n" +
                      $"Offset: {vehicle.manualSpeedOffsetKph:+0;-0;0} km/h | View: {cameraRig.ModeLabel}";
            }

            if (traffic != null && processText != null)
            {
                processText.text =
                    $"Last event: {traffic.lastEvent}\n" +
                    "Digital twin loop: traffic/sensor state -> multi-vehicle pole detection -> adaptive lights -> energy/health telemetry";
            }

            if (highway != null && energyText != null)
            {
                energyText.text =
                    $"Scenario time: {highway.elapsedScenarioSeconds:0}s\n" +
                    $"Baseline energy: {highway.baselineEnergyKwh:0.0000} kWh\n" +
                    $"Adaptive energy: {highway.actualEnergyKwh:0.0000} kWh\n" +
                    $"Saved: {highway.savedEnergyKwh:0.0000} kWh ({highway.savedEnergyPct:0.0}%)\n" +
                    $"CO2 avoided: {highway.co2SavedKg:0.000} kg";
            }

            if (highway != null && selectedLuminaireText != null)
            {
                LuminaireController luminaire = highway.SelectedLuminaire;
                if (luminaire == null)
                {
                    selectedLuminaireText.text = "Selected light: none\nClick any pole light to inspect live digital-twin data.";
                }
                else
                {
                    string vehicleIds = luminaire.DetectedVehicleIds.Count == 0 ? "none" : string.Join(", ", luminaire.DetectedVehicleIds);
                    selectedLuminaireText.text =
                        $"Selected light: {luminaire.luminaireId}\n" +
                        $"Board node: {luminaire.boardNodeId}\n" +
                        $"Pole/direction: {luminaire.poleId} / {luminaire.direction}\n" +
                        $"Brightness: {luminaire.currentBrightness * 100f:0.0}% -> {luminaire.targetBrightness * 100f:0.0}%\n" +
                        $"0-10V output: {luminaire.OutputVoltage:0.00} V | Power: {luminaire.ActualPowerWatts:0.0} W\n" +
                        $"Temp/current: {luminaire.driverTemperatureC:0.0} C / {luminaire.currentMa:0} mA\n" +
                        $"Detected cars: {luminaire.activeVehicleCount} | nearest: {(luminaire.nearestVehicleDistanceM > 200f ? "--" : luminaire.nearestVehicleDistanceM.ToString("0.0") + " m")}\n" +
                        $"Vehicle IDs: {vehicleIds}\n" +
                        $"Process: {luminaire.lastDetectionMode}\n" +
                        $"Health: {luminaire.healthScore:0.0}% | Fault: {luminaire.faultStatus} | Re-X: {luminaire.rexStatus}";
                }
            }

            if (traffic != null && roadVehicleListText != null)
            {
                VehicleController[] roadVehicles = traffic.Vehicles
                    .Where(traffic.IsInsideRoad)
                    .OrderBy(vehicle => vehicle.PositionAlongRoad)
                    .Take(6)
                    .ToArray();

                if (roadVehicles.Length == 0)
                {
                    roadVehicleListText.text = "Cars on road: none\nUse Car A/B or Emerg A/B to spawn one.";
                }
                else
                {
                    roadVehicleListText.text = "Cars on road:\n" + string.Join(
                        "\n",
                        roadVehicles.Select(vehicle =>
                            $"{(vehicle.selected ? "> " : "  ")}{vehicle.vehicleId}  {vehicle.laneId}  {vehicle.speedMps:0.0} m/s{SpeedOffsetLabel(vehicle)}")
                    );
                }
            }
        }

        private static string SpeedOffsetLabel(VehicleController vehicle)
        {
            return Mathf.Abs(vehicle.manualSpeedOffsetKph) < 0.1f
                ? ""
                : $"  {vehicle.manualSpeedOffsetKph:+0;-0;0} km/h";
        }
    }
}
