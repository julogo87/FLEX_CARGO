from dataclasses import dataclass
from typing import Dict, Set, Any

@dataclass
class FlightData:
    operador: str
    numero_vuelo: str
    matricula: str
    fecha_vuelo: str
    hora_vuelo: str
    ruta_vuelo: str
    revision: str
    destino_inicial: str
    fuel_kg: float
    trip_fuel: float
    taxi_fuel: float
    tipo_carga: str
    takeoff_runway: str
    rwy_condition: str
    flaps_conf: str
    temperature: float
    air_condition: str
    anti_ice: str
    qnh: float
    performance_tow: float
    performance_lw: float
    passengers_cockpit: int
    passengers_supernumerary: int

@dataclass
class AircraftData:
    tail: str
    mtoc: float
    mlw: float
    mzfw: float
    oew: float
    arm: float
    moment_aircraft: float
    cg_aircraft: float
    lemac: float
    mac_length: float
    mrw_limit: float
    lateral_imbalance_limit: float

@dataclass
class CalculationState:
    df: Any  # DataFrame
    posiciones_usadas: Set[str]
    rotaciones: Dict[str, bool]
    bow: float
    bow_moment_x: float
    bow_moment_y: float
    moment_x_fuel_tow: float
    moment_y_fuel_tow: float
    moment_x_fuel_lw: float
    moment_y_fuel_lw: float
    passengers_cockpit_total_weight: float
    passengers_cockpit_total_moment_x: float
    passengers_supernumerary_total_weight: float
    passengers_supernumerary_total_moment_x: float
    fuel_distribution: Dict[str, float]
    fuel_mode: str

@dataclass
class FinalResults:
    peso_total: float
    zfw_peso: float
    zfw_momento_x: float
    zfw_momento_y: float
    zfw_mac: float
    tow: float
    tow_momento_x: float
    tow_momento_y: float
    tow_mac: float
    mrow: float
    lw: float
    lw_momento_x: float
    lw_momento_y: float
    lw_mac: float
    lateral_imbalance: float
    underload: float
    pitch_trim: float
    fuel_distribution: Dict[str, float]
    fuel_mode: str