"""
Hydraulic Calculation Module for Industrial Centrifugal Pumps.
Contains functions for NPSH, Total Dynamic Head (TDH), and friction loss.
"""

import math


def calculate_npsh_available(suction_pressure_bar: float, vapor_pressure_bar: float, liquid_density_kg_m3: float, suction_velocity_m_s: float) -> float:
    """
    Calculates Net Positive Suction Head Available (NPSHa) in meters of liquid.
    
    Formula: NPSHa = (P_suction - P_vapor) / (rho * g) + (V^2 / 2g)
    """
    g = 9.81
    pressure_head = ((suction_pressure_bar - vapor_pressure_bar) * 100000.0) / (liquid_density_kg_m3 * g)
    velocity_head = (suction_velocity_m_s ** 2) / (2.0 * g)
    return pressure_head + velocity_head


def calculate_total_dynamic_head(static_discharge_head_m: float, static_suction_head_m: float, total_friction_loss_m: float) -> float:
    """
    Calculates Total Dynamic Head (TDH) required for pump selection.
    
    Formula: TDH = Static Discharge Lift - Static Suction Lift + Total Pipe Friction Losses
    """
    return static_discharge_head_m - static_suction_head_m + total_friction_loss_m


def calculate_pipe_friction_loss(darcy_friction_factor: float, pipe_length_m: float, pipe_diameter_m: float, flow_velocity_m_s: float) -> float:
    """
    Calculates Darcy-Weisbach pipe friction head loss in meters.
    
    Formula: h_f = f * (L / D) * (V^2 / 2g)
    """
    g = 9.81
    return darcy_friction_factor * (pipe_length_m / pipe_diameter_m) * ((flow_velocity_m_s ** 2) / (2.0 * g))
