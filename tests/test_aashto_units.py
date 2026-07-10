from __future__ import annotations

import math

import pytest

from core.aashto_units import (
    concrete_strength_guard_mpa,
    inch_to_mm,
    kip_to_kn,
    kipft_to_knm,
    ksi_to_mpa,
    kn_to_kip,
    knm_to_kipft,
    m_to_ft,
    mm_to_in,
    mpa_to_ksi,
    psi_sqrt_fc_coefficient_to_ksi,
    stress_mpa_from_ksi_sqrt_fc,
)


def test_basic_aashto_unit_conversions_are_reversible() -> None:
    assert ksi_to_mpa(1.0) == pytest.approx(6.89475729316836)
    assert mpa_to_ksi(6.89475729316836) == pytest.approx(1.0)
    assert kip_to_kn(1.0) == pytest.approx(4.4482216152605)
    assert kn_to_kip(4.4482216152605) == pytest.approx(1.0)
    assert inch_to_mm(1.0) == pytest.approx(25.4)
    assert mm_to_in(25.4) == pytest.approx(1.0)
    assert m_to_ft(0.3048) == pytest.approx(1.0)
    assert kipft_to_knm(1.0) == pytest.approx(1.3558179483314004)
    assert knm_to_kipft(1.3558179483314004) == pytest.approx(1.0)


def test_sqrt_fc_coefficient_conversion_guard_matches_aashto_ksi_commentary() -> None:
    assert psi_sqrt_fc_coefficient_to_ksi(1.0) == pytest.approx(1.0 / math.sqrt(1000.0))
    assert psi_sqrt_fc_coefficient_to_ksi(6.0) == pytest.approx(0.1897366596, rel=1e-6)


def test_ksi_sqrt_fc_expression_accepts_si_input_and_returns_si_output() -> None:
    # For f'c = 60 MPa = 8.702 ksi, 0.19*sqrt(f'c_ksi) ksi ≈ 0.560 ksi ≈ 3.86 MPa.
    stress = stress_mpa_from_ksi_sqrt_fc(0.19, 60.0)
    assert stress == pytest.approx(3.86, rel=0.01)


def test_concrete_strength_guard_flags_likely_unit_mistakes() -> None:
    assert concrete_strength_guard_mpa(60.0).status == "PASS"
    assert concrete_strength_guard_mpa(8.7).status == "WARNING"
    assert concrete_strength_guard_mpa(120.0).status == "WARNING"
