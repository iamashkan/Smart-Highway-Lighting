import unittest

from backend.config import SimulationConfig
from backend.scenario_runner import SimulationRuntime


class BackendBehaviorTests(unittest.TestCase):
    def make_config(self) -> SimulationConfig:
        return SimulationConfig(num_poles=24, zone_size_poles=6, fade_rate_per_second=1.0)

    def run_steps(self, scenario: str, steps: int = 8) -> dict:
        runtime = SimulationRuntime(scenario_name=scenario, config=self.make_config())
        try:
            state = {}
            for _ in range(steps):
                state = runtime.step()
            return state
        finally:
            runtime.close()

    def test_normal_direction_a_only_raises_direction_a(self):
        state = self.run_steps("normal_car_direction_a", steps=12)
        a_max = max(l["current_brightness"] for l in state["luminaires"] if l["direction"] == "A")
        b_max = max(l["current_brightness"] for l in state["luminaires"] if l["direction"] == "B")
        self.assertGreater(a_max, 0.7)
        self.assertAlmostEqual(b_max, 0.3, places=3)

    def test_normal_direction_b_only_raises_direction_b(self):
        state = self.run_steps("normal_car_direction_b", steps=12)
        a_max = max(l["current_brightness"] for l in state["luminaires"] if l["direction"] == "A")
        b_max = max(l["current_brightness"] for l in state["luminaires"] if l["direction"] == "B")
        self.assertAlmostEqual(a_max, 0.3, places=3)
        self.assertGreater(b_max, 0.7)

    def test_emergency_activates_multiple_directional_zones(self):
        state = self.run_steps("emergency_ambulance_direction_a", steps=4)
        emergency_zones = [z for z in state["zones"] if z["mode"] == "emergency"]
        self.assertGreaterEqual(len(emergency_zones), 2)
        self.assertTrue(all(z["direction"] == "A" for z in emergency_zones))
        high_a = [l for l in state["luminaires"] if l["direction"] == "A" and l["target_brightness"] == 1.0]
        self.assertGreaterEqual(len(high_a), 6)

    def test_fault_writes_passport_and_safe_fallback(self):
        state = self.run_steps("degraded_luminaire", steps=5)
        luminaire = next(l for l in state["luminaires"] if l["luminaire_id"] == "P010-A")
        passport = next(p for p in state["passports"] if p["luminaire_id"] == "P010-A")
        self.assertEqual(luminaire["fault_status"], "driver_degraded")
        self.assertLess(luminaire["health_score"], 60)
        self.assertIn(passport["rex_decision"], {"Repair", "Remanufacture"})
        self.assertGreaterEqual(luminaire["target_brightness"], 0.7)


if __name__ == "__main__":
    unittest.main()
