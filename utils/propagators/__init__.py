"""
Propagator module — provides multiple orbit propagation methods.

Propagator types:
    SGP4:       Fast analytical propagator using NORAD TLE data (default)
    NUMERICAL:  High-fidelity numerical propagator with configurable force models
"""

from enum import Enum
from typing import Optional


class PropagatorType(Enum):
    SGP4 = "sgp4"
    NUMERICAL = "numerical"


class ForceModel:
    """Configuration for which perturbation forces to include in numerical propagation."""

    def __init__(
        self,
        j2: bool = True,
        j3: bool = False,
        j4: bool = False,
        j5: bool = False,
        j6: bool = False,
        atmospheric_drag: bool = True,
        solar_radiation_pressure: bool = False,
        third_body_moon: bool = False,
        third_body_sun: bool = False,
        drag_coefficient: float = 2.2,
        area_to_mass_ratio: float = 0.01,  # m²/kg (typical for small sats)
        srp_coefficient: float = 1.8,
    ):
        self.j2 = j2
        self.j3 = j3
        self.j4 = j4
        self.j5 = j5
        self.j6 = j6
        self.atmospheric_drag = atmospheric_drag
        self.solar_radiation_pressure = solar_radiation_pressure
        self.third_body_moon = third_body_moon
        self.third_body_sun = third_body_sun
        self.drag_coefficient = drag_coefficient
        self.area_to_mass_ratio = area_to_mass_ratio
        self.srp_coefficient = srp_coefficient

    def enabled_forces(self) -> list:
        """Return list of enabled force names."""
        forces = []
        for j in ('j2', 'j3', 'j4', 'j5', 'j6'):
            if getattr(self, j):
                forces.append(j.upper())
        if self.atmospheric_drag:
            forces.append("Drag")
        if self.solar_radiation_pressure:
            forces.append("SRP")
        if self.third_body_moon:
            forces.append("Moon")
        if self.third_body_sun:
            forces.append("Sun")
        return forces

    def __repr__(self):
        return f"ForceModel({', '.join(self.enabled_forces())})"


# Preset force model configurations
FORCE_MODEL_PRESETS = {
    'basic': ForceModel(j2=True),
    'standard': ForceModel(j2=True, j3=True, atmospheric_drag=True),
    'high_fidelity': ForceModel(
        j2=True, j3=True, j4=True, j5=True, j6=True,
        atmospheric_drag=True,
        solar_radiation_pressure=True,
        third_body_moon=True,
        third_body_sun=True,
    ),
}
