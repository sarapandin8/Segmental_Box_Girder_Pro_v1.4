from __future__ import annotations

"""Unit-safe helpers for AASHTO LRFD formulas used by the app.

The application stores and displays SI units (kN, m, MPa, mm).  AASHTO
LRFD Section 5 equations and commentary are commonly written using kips,
ksi, inches, and feet.  Design-check functions should call this module rather
than embedding ad-hoc conversion factors in page or calculation code.
"""

from dataclasses import dataclass
from math import isfinite, sqrt

KIP_TO_KN = 4.4482216152605
KN_TO_KIP = 1.0 / KIP_TO_KN
KSI_TO_MPA = 6.89475729316836
MPA_TO_KSI = 1.0 / KSI_TO_MPA
PSI_TO_MPA = KSI_TO_MPA / 1000.0
MPA_TO_PSI = 1.0 / PSI_TO_MPA
IN_TO_MM = 25.4
MM_TO_IN = 1.0 / IN_TO_MM
FT_TO_M = 0.3048
M_TO_FT = 1.0 / FT_TO_M
KIP_FT_TO_KN_M = KIP_TO_KN * FT_TO_M
KN_M_TO_KIP_FT = 1.0 / KIP_FT_TO_KN_M


class UnitConversionError(ValueError):
    """Raised when a unit conversion receives a non-finite value."""


def _finite(value: float, label: str) -> float:
    value = float(value)
    if not isfinite(value):
        raise UnitConversionError(f"{label} must be finite; got {value!r}.")
    return value


def mpa_to_ksi(value_mpa: float) -> float:
    return _finite(value_mpa, "MPa value") * MPA_TO_KSI


def ksi_to_mpa(value_ksi: float) -> float:
    return _finite(value_ksi, "ksi value") * KSI_TO_MPA


def mpa_to_psi(value_mpa: float) -> float:
    return _finite(value_mpa, "MPa value") * MPA_TO_PSI


def psi_to_mpa(value_psi: float) -> float:
    return _finite(value_psi, "psi value") * PSI_TO_MPA


def kn_to_kip(value_kn: float) -> float:
    return _finite(value_kn, "kN value") * KN_TO_KIP


def kip_to_kn(value_kip: float) -> float:
    return _finite(value_kip, "kip value") * KIP_TO_KN


def mm_to_in(value_mm: float) -> float:
    return _finite(value_mm, "mm value") * MM_TO_IN


def inch_to_mm(value_in: float) -> float:
    return _finite(value_in, "in value") * IN_TO_MM


def m_to_ft(value_m: float) -> float:
    return _finite(value_m, "m value") * M_TO_FT


def ft_to_m(value_ft: float) -> float:
    return _finite(value_ft, "ft value") * FT_TO_M


def knm_to_kipft(value_knm: float) -> float:
    return _finite(value_knm, "kN·m value") * KN_M_TO_KIP_FT


def kipft_to_knm(value_kipft: float) -> float:
    return _finite(value_kipft, "kip·ft value") * KIP_FT_TO_KN_M


def psi_sqrt_fc_coefficient_to_ksi(coefficient_psi: float) -> float:
    """Convert coefficient N in ``N√f'c`` from psi form to ksi form.

    Use only for equations whose result has stress units and whose concrete
    strength term is under a square root.  This prevents the common error of
    using MPa values directly in AASHTO ksi-based expressions.
    """
    return _finite(coefficient_psi, "psi √fc coefficient") / sqrt(1000.0)


def ksi_sqrt_fc_coefficient_to_psi(coefficient_ksi: float) -> float:
    return _finite(coefficient_ksi, "ksi √fc coefficient") * sqrt(1000.0)


def stress_mpa_from_ksi_sqrt_fc(coefficient_ksi: float, fc_mpa: float) -> float:
    """Return stress in MPa from an AASHTO-style ``C√f'c`` ksi expression.

    ``fc_mpa`` is converted to ksi internally; the computed ksi stress is then
    returned as MPa.
    """
    fc_ksi = mpa_to_ksi(fc_mpa)
    if fc_ksi < 0:
        raise UnitConversionError("Concrete strength for √f'c expression must be non-negative.")
    return ksi_to_mpa(_finite(coefficient_ksi, "ksi √fc coefficient") * sqrt(fc_ksi))


def stress_mpa_from_psi_sqrt_fc(coefficient_psi: float, fc_mpa: float) -> float:
    """Return stress in MPa from a psi-form ``C√f'c`` expression."""
    fc_psi = mpa_to_psi(fc_mpa)
    if fc_psi < 0:
        raise UnitConversionError("Concrete strength for √f'c expression must be non-negative.")
    return psi_to_mpa(_finite(coefficient_psi, "psi √fc coefficient") * sqrt(fc_psi))


@dataclass(frozen=True)
class UnitGuard:
    status: str
    message: str
    recommendation: str = ""


def concrete_strength_guard_mpa(fc_mpa: float) -> UnitGuard:
    """Flag suspicious concrete-strength values before AASHTO formulas run."""
    fc = _finite(fc_mpa, "f'c")
    if fc <= 0:
        return UnitGuard("ERROR", "Concrete strength f′c must be greater than zero.", "Enter f′c in MPa.")
    if fc < 10.0:
        return UnitGuard(
            "WARNING",
            f"f′c = {fc:g} MPa is low for this app context; verify this is not ksi entered into an MPa field.",
            "For example, 8.7 ksi should be entered as approximately 60 MPa.",
        )
    if fc > 105.0:
        return UnitGuard(
            "WARNING",
            f"f′c = {fc:g} MPa is outside the normal app calibration range for AASHTO Section 5 checks.",
            "Confirm project-specific high-strength-concrete provisions and equation applicability.",
        )
    return UnitGuard("PASS", f"f′c = {fc:g} MPa is in the expected SI range.")


def standard_conversion_table() -> list[dict[str, str]]:
    return [
        {"Quantity": "Stress", "SI used by app": "MPa", "AASHTO equation unit": "ksi / psi", "Conversion": "1 ksi = 6.894757 MPa"},
        {"Quantity": "Force", "SI used by app": "kN", "AASHTO equation unit": "kip", "Conversion": "1 kip = 4.448222 kN"},
        {"Quantity": "Length", "SI used by app": "mm / m", "AASHTO equation unit": "in / ft", "Conversion": "1 in = 25.4 mm; 1 ft = 0.3048 m"},
        {"Quantity": "Moment", "SI used by app": "kN·m", "AASHTO equation unit": "kip·ft", "Conversion": "1 kip·ft = 1.355818 kN·m"},
        {"Quantity": "√f′c terms", "SI used by app": "MPa input", "AASHTO equation unit": "ksi expression", "Conversion": "Convert f′c to ksi before evaluating √f′c"},
    ]
