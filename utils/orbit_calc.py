"""
Orbit calculation module — public API.

Delegates to the active propagator (SGP4 or Numerical).
All other modules should import from here, not from propagators directly.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any

from utils.propagators import PropagatorType, ForceModel, FORCE_MODEL_PRESETS
from utils.propagators.sgp4_prop import SGP4Propagator, get_timescale
from utils.propagators.base import BasePropagator

logger = logging.getLogger(__name__)

# ============================================================
# Propagator registry
# ============================================================

_propagators: Dict[PropagatorType, BasePropagator] = {
    PropagatorType.SGP4: SGP4Propagator(),
}

_active_type: PropagatorType = PropagatorType.SGP4


def _get_numerical():
    """Lazy-load numerical propagator (avoids import cost if unused)."""
    if PropagatorType.NUMERICAL not in _propagators:
        try:
            from utils.propagators.numerical_prop import NumericalPropagator
            _propagators[PropagatorType.NUMERICAL] = NumericalPropagator()
            logger.info("Numerical propagator loaded")
        except ImportError as e:
            logger.warning("Numerical propagator unavailable: %s", e)
            return None
    return _propagators[PropagatorType.NUMERICAL]


def get_active_propagator() -> BasePropagator:
    """Get the currently active propagator."""
    if _active_type == PropagatorType.NUMERICAL:
        num = _get_numerical()
        if num:
            return num
        logger.warning("Numerical propagator unavailable, falling back to SGP4")
    return _propagators[PropagatorType.SGP4]


def set_propagator(prop_type: PropagatorType, force_model: Optional[ForceModel] = None):
    """
    Switch the active propagator.

    Args:
        prop_type: PropagatorType.SGP4 or PropagatorType.NUMERICAL
        force_model: Force model config (only for NUMERICAL)
    """
    global _active_type

    if prop_type == PropagatorType.NUMERICAL:
        if force_model:
            from utils.propagators.numerical_prop import NumericalPropagator
            _propagators[PropagatorType.NUMERICAL] = NumericalPropagator(force_model)
        elif PropagatorType.NUMERICAL not in _propagators:
            _get_numerical()

    _active_type = prop_type
    logger.info("Active propagator: %s", get_active_propagator().name)


def get_propagator_info() -> Dict[str, Any]:
    """Get info about the active propagator."""
    prop = get_active_propagator()
    info = {
        'name': prop.name,
        'description': prop.description,
        'accuracy': prop.accuracy_estimate,
        'type': _active_type.value,
    }
    if _active_type == PropagatorType.NUMERICAL:
        num = _get_numerical()
        if num:
            info['force_model'] = str(num.force_model)
            info['forces'] = num.force_model.enabled_forces()
    return info


def list_propagators() -> List[Dict[str, str]]:
    """List all available propagators."""
    available = [
        {
            'type': PropagatorType.SGP4.value,
            'name': 'SGP4',
            'description': 'Fast analytical (NORAD TLE-based)',
            'accuracy': '~1-10 km over 24h',
        },
    ]
    try:
        from utils.propagators.numerical_prop import NumericalPropagator
        available.append({
            'type': PropagatorType.NUMERICAL.value,
            'name': 'Numerical',
            'description': 'High-fidelity with force models (J2-J6, drag, SRP, 3rd body)',
            'accuracy': '~10-100 m over 24h',
        })
    except ImportError:
        pass
    return available


def list_force_presets() -> Dict[str, ForceModel]:
    """List available force model presets."""
    return FORCE_MODEL_PRESETS.copy()


# ============================================================
# Public API — delegates to active propagator
# ============================================================

def get_satellite_position(satellite_tle: Tuple[str, str], observer) -> Optional[Dict[str, Any]]:
    """Calculate current satellite position using active propagator."""
    return get_active_propagator().get_position(satellite_tle, observer)


def calculate_trajectory(satellite_tle: Tuple[str, str],
                         points: int = 120, interval: int = 30) -> List[Tuple[float, float]]:
    """Calculate satellite trajectory using active propagator."""
    return get_active_propagator().calculate_trajectory(satellite_tle, points, interval)


def calculate_passes(satellite_tle: Tuple[str, str], observer,
                     days: float = 7) -> List[Dict[str, Any]]:
    """Calculate satellite passes using active propagator."""
    return get_active_propagator().calculate_passes(satellite_tle, observer, days)


def get_orbital_elements(satellite_tle: Tuple[str, str]) -> Optional[Dict[str, Any]]:
    """Extract orbital elements from TLE data."""
    return get_active_propagator().get_orbital_elements(satellite_tle)
