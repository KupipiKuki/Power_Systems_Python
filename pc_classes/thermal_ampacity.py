# -*- coding: utf-8 -*-
"""Thermal ampacity and conductor resistance calculation per IEEE 738.

Extracts the heat balance and temperature-dependent resistance models
from legacy powercad into a standalone, pure calculation module.
"""

from dataclasses import dataclass
import numpy as np
import pandas as pd


# Conduction model:
# 1 = Copper (annealed copper temperature coefficient 0.00381 at 20 C)
# 2 = ACCC (linear interpolation between 25 C and 75 C)
# 3 = Standard Aluminum/ACSR/AAAC (temperature coefficient 0.00403 at 20 C)
_CONDUCTION_TYPES = {'Copper': 1, 'ACCC': 2}


@dataclass
class AmpacityEnvironment:
    """Environmental parameters for IEEE 738-style thermal ratings."""
    wind_speed: float = 2.0         # Wind speed in ft/s
    sun_intensity: float = 96.0     # Solar heat flux in W/ft^2
    sun_altitude: float = 90.0      # Solar altitude angle (degrees)
    sun_azimuth: float = 0.0        # Solar azimuth angle (degrees)
    conductor_azimuth: float = 0.0  # Conductor azimuth angle (degrees)
    altitude: float = 1000.0        # Conductor elevation above sea level (feet)


@dataclass(frozen=True)
class ThermalRatingResult:
    """Results of conductor thermal ampacity evaluation."""
    ampacity_amps: float            # Maximum steady-state current capacity (Amperes)
    r_ac_ohms_per_mile: float       # AC resistance at conductor operating temperature (ohms/mile)
    r_dc_ohms_per_mile: float       # DC resistance at conductor operating temperature (ohms/mile)
    convected_loss_w_per_ft: float  # Convective heat loss (W/ft)
    radiated_loss_w_per_ft: float   # Radiated heat loss (W/ft)
    solar_gain_w_per_ft: float      # Solar heat gain (W/ft)


def calculate_conductor_ampacity(
    gmr_ft: float,
    dcohm_per_kft: float,
    acohm_per_kft: float,
    conductor_type: str | int = 'ACSR',
    temp_amb_c: float = 25.0,
    temp_rise_c: float = 50.0,
    env: AmpacityEnvironment | None = None,
    diameter_in: float | None = None,
) -> ThermalRatingResult:
    """Calculate conductor steady-state ampacity and temperature-corrected resistance.

    Parameters
    ----------
    gmr_ft : float
        Conductor geometric mean radius in feet.
    dcohm_per_kft : float
        DC resistance in ohms per 1000 ft (at standard 20 C or 25 C table base).
    acohm_per_kft : float
        AC resistance in ohms per 1000 ft (at standard 75 C table base).
    conductor_type : str or int
        'Copper' (1), 'ACCC' (2), or default aluminum alloy/ACSR/AAAC (3).
    temp_amb_c : float
        Ambient temperature in degrees Celsius (default 25 C).
    temp_rise_c : float
        Conductor temperature rise above ambient in degrees Celsius (default 50 C).
    env : AmpacityEnvironment, optional
        Atmospheric and solar conditions. If None, default environment is used.
    diameter_in : float, optional
        Conductor outside diameter in inches. If omitted, approximated from GMR.

    Returns
    -------
    ThermalRatingResult
    """
    if env is None:
        env = AmpacityEnvironment()

    if isinstance(conductor_type, int):
        conduction = conductor_type
    else:
        conduction = _CONDUCTION_TYPES.get(conductor_type, 3)

    resdc = float(dcohm_per_kft) / 1000.0  # ohms/ft
    resac = float(acohm_per_kft) / 1000.0  # ohms/ft

    # Conductor dimensions
    if diameter_in is not None and diameter_in > 0:
        radius = float(diameter_in) / 2.0  # inches
    else:
        radius = float(gmr_ft) * 12.0      # inches (legacy approximation)

    surfaceareaft = 2.0 * np.pi * float(gmr_ft)
    surfaceareain = 2.0 * np.pi * radius * 12.0
    tempcond = temp_rise_c + temp_amb_c
    tf = (tempcond + temp_amb_c) / 2.0

    # Atmospheric properties at film temperature tf
    pf = (0.080695 - (0.000002901 * env.altitude)
          + (0.000000000037 * env.altitude ** 2)) / (1.0 + 0.00367 * tf)
    uf = (0.0415 + 0.00012034 * tf - 0.00000011442 * tf ** 2
          + 0.00000000019416 * tf ** 3)
    kf = 0.007388 + 0.0000227889 * tf - 0.00000000134328 * tf ** 2

    # Radiated heat loss (W/ft)
    wr = 0.138 * radius * 2.0 * 0.5 * (
        ((273.0 + tempcond) / 100.0) ** 4 - ((273.0 + temp_amb_c) / 100.0) ** 4
    )

    # Convected heat loss (W/ft)
    if env.wind_speed <= 0:
        wc = 0.283 * np.sqrt(pf) * (radius * 2.0) ** 0.75 * (temp_rise_c) ** 1.25
    else:
        wc1 = (1.01 + 0.371 * ((pf * env.wind_speed * 3600.0 * radius * 2.0)
                               / uf) ** 0.52) * kf * temp_rise_c
        wc2 = 0.1695 * ((pf * env.wind_speed * 3600.0 * radius * 2.0)
                        / uf) ** 0.6 * kf * temp_rise_c
        wc = max(wc1, wc2)

    # Solar heat gain (W/ft)
    angle = env.sun_altitude * np.pi / 180.0
    ws = 0.5 * env.sun_intensity * np.sin(
        np.arccos(np.cos(angle)
                  * np.cos((env.sun_azimuth * np.pi / 180.0)
                           - (env.conductor_azimuth * np.pi / 180.0)))
    ) * surfaceareaft
    wsbase = 0.5 * 100.0 * np.sin(90.0 * np.pi / 180.0) * surfaceareaft

    # Total heat losses (W/in^2-ft)
    powerloss = (wc + wr) / surfaceareain

    # Conductor temperature-corrected resistance
    if conduction == 2:
        # ACCC linear interpolation
        resac = resdc + ((resac - resdc) / (75.0 - 25.0)) * (tempcond - 25.0)
        resdc_at_temp = resdc
    elif conduction == 1:
        # Copper temperature correction (alpha = 0.00381 at 20 C)
        resdctemp = resdc * (1.0 + 0.00381 * (75.0 - 20.0))
        resacdc = resac / resdctemp
        resdc_at_temp = resdc * (1.0 + 0.00381 * (tempcond - 20.0))
        resac = resdc_at_temp * resacdc
    else:
        # Standard aluminum / ACSR (alpha = 0.00403 at 20 C)
        resdctemp = resdc * (1.0 + 0.00403 * (75.0 - 20.0))
        resacdc = resac / resdctemp
        resdc_at_temp = resdc * (1.0 + 0.00403 * (tempcond - 20.0))
        resac = resdc_at_temp * resacdc

    ohmval_ac = resac * 5280.0
    ohmval_dc = resdc_at_temp * 5280.0

    # Current capacity before and after solar/wind derating
    currentbase = np.sqrt((37.7 * radius * 2.0 * powerloss) / resac)
    if ws == 0:
        current = currentbase
    else:
        if env.wind_speed > 0:
            current = currentbase * (0.99 - ((0.05 * radius * 2.0)
                                             * (ws / wsbase)))
        else:
            current = currentbase * (0.99 - (0.07 * (angle / (np.pi / 2.0)))
                                     - ((0.05 * radius * 2.0)
                                        * (ws / wsbase)))

    return ThermalRatingResult(
        ampacity_amps=float(current),
        r_ac_ohms_per_mile=float(ohmval_ac),
        r_dc_ohms_per_mile=float(ohmval_dc),
        convected_loss_w_per_ft=float(wc),
        radiated_loss_w_per_ft=float(wr),
        solar_gain_w_per_ft=float(ws),
    )
