# -*- coding: utf-8 -*-
"""Unit tests for thermal ampacity and temperature-corrected resistance."""

import pytest
from pc_classes.thermal_ampacity import (
    AmpacityEnvironment,
    ThermalRatingResult,
    calculate_conductor_ampacity,
)


def test_calculate_conductor_ampacity_acsr():
    """Verify IEEE 738 calculation for standard ACSR conductor."""
    res = calculate_conductor_ampacity(
        gmr_ft=0.0048,
        dcohm_per_kft=0.201,
        acohm_per_kft=0.271,
        conductor_type='ACSR',
        temp_amb_c=25.0,
        temp_rise_c=50.0,
    )
    assert isinstance(res, ThermalRatingResult)
    assert res.ampacity_amps > 100.0
    assert res.r_ac_ohms_per_mile > 0.0
    assert res.r_dc_ohms_per_mile > 0.0
    assert res.convected_loss_w_per_ft > 0.0
    assert res.radiated_loss_w_per_ft > 0.0
    assert res.solar_gain_w_per_ft > 0.0


def test_temperature_rise_increases_resistance():
    """Verify conductor resistance increases with operating temperature."""
    cold = calculate_conductor_ampacity(
        gmr_ft=0.0059,
        dcohm_per_kft=0.159,
        acohm_per_kft=0.218,
        conductor_type='ACSR',
        temp_amb_c=25.0,
        temp_rise_c=20.0,
    )
    hot = calculate_conductor_ampacity(
        gmr_ft=0.0059,
        dcohm_per_kft=0.159,
        acohm_per_kft=0.218,
        conductor_type='ACSR',
        temp_amb_c=25.0,
        temp_rise_c=75.0,
    )
    assert hot.r_ac_ohms_per_mile > cold.r_ac_ohms_per_mile
    assert hot.r_dc_ohms_per_mile > cold.r_dc_ohms_per_mile


def test_wind_increases_ampacity():
    """Verify wind cooling increases allowable ampacity."""
    env_calm = AmpacityEnvironment(wind_speed=0.0)
    env_windy = AmpacityEnvironment(wind_speed=5.0)

    calm = calculate_conductor_ampacity(
        gmr_ft=0.0059,
        dcohm_per_kft=0.159,
        acohm_per_kft=0.218,
        conductor_type='ACSR',
        env=env_calm,
    )
    windy = calculate_conductor_ampacity(
        gmr_ft=0.0059,
        dcohm_per_kft=0.159,
        acohm_per_kft=0.218,
        conductor_type='ACSR',
        env=env_windy,
    )
    assert windy.ampacity_amps > calm.ampacity_amps
    assert windy.convected_loss_w_per_ft > calm.convected_loss_w_per_ft


def test_copper_conduction_model():
    """Verify Copper conduction model behaves as expected."""
    res = calculate_conductor_ampacity(
        gmr_ft=0.005,
        dcohm_per_kft=0.1,
        acohm_per_kft=0.13,
        conductor_type='Copper',
        temp_amb_c=25.0,
        temp_rise_c=50.0,
    )
    assert res.ampacity_amps > 0.0
    assert res.r_ac_ohms_per_mile > 0.0
