from __future__ import annotations

from dataclasses import dataclass

from .highway_layout import HighwayLayout
from .models import Luminaire, RexDecision


@dataclass
class RexEngine:
    design_life_hours: float = 100_000.0

    def estimate_remaining_useful_life(self, luminaire: Luminaire) -> float:
        health_factor = max(0.0, luminaire.health_score / 100.0)
        thermal_factor = 1.0
        if luminaire.average_driver_temperature > 65:
            thermal_factor = 0.72
        elif luminaire.average_driver_temperature > 55:
            thermal_factor = 0.86
        fault_factor = max(0.25, 1.0 - luminaire.fault_count * 0.12)
        consumed = min(self.design_life_hours, luminaire.operating_hours)
        remaining = (self.design_life_hours - consumed) * health_factor * thermal_factor * fault_factor
        return round(max(0.0, remaining), 1)

    def classify(self, luminaire: Luminaire) -> RexDecision:
        if luminaire.health_score >= 82 and luminaire.fault_count == 0:
            return "Reuse"
        if luminaire.health_score >= 62 and luminaire.fault_count <= 2:
            return "Repair"
        if luminaire.health_score >= 35:
            return "Remanufacture"
        return "Recycle"

    def update_layout(self, layout: HighwayLayout) -> None:
        for luminaire in layout.luminaires.values():
            luminaire.rex_status = self.classify(luminaire)
