from __future__ import annotations

import json
from pathlib import Path

from .highway_layout import HighwayLayout
from .models import DigitalPassport, Luminaire
from .rex_engine import RexEngine


def generate_passport(luminaire: Luminaire, rex_engine: RexEngine) -> DigitalPassport:
    return DigitalPassport(
        passport_id=luminaire.digital_passport_id,
        luminaire_id=luminaire.luminaire_id,
        manufacturer_placeholder="Roadway LED OEM placeholder",
        model_placeholder="Zhaga-D4i / NEMA 7-pin compatible highway luminaire class",
        installation_date="2026-01-15",
        driver_type="Dimmable LED driver, simulated 0-10V/PWM lab interface",
        dimming_protocol=luminaire.dimming_protocol,
        material_composition_placeholder={
            "housing": "aluminium alloy",
            "lens": "polycarbonate or tempered glass",
            "electronics": "LED driver, control board, surge protection",
            "notes": "Simulated data for research prototype; verify with OEM passport data for deployment.",
        },
        maintenance_history=list(luminaire.maintenance_history),
        operating_hours=round(luminaire.operating_hours, 2),
        energy_history={"adaptive_kwh": round(luminaire.energy_history_kwh, 5)},
        fault_history=list(luminaire.fault_history),
        health_score=round(luminaire.health_score, 2),
        remaining_useful_life_estimate=rex_engine.estimate_remaining_useful_life(luminaire),
        rex_decision=rex_engine.classify(luminaire),
    )


def generate_passports(layout: HighwayLayout, rex_engine: RexEngine) -> list[DigitalPassport]:
    return [generate_passport(luminaire, rex_engine) for luminaire in layout.luminaires.values()]


def write_passports(layout: HighwayLayout, rex_engine: RexEngine, path: str | Path) -> None:
    passports = [passport.to_dict() for passport in generate_passports(layout, rex_engine)]
    Path(path).write_text(json.dumps(passports, indent=2), encoding="utf-8")
