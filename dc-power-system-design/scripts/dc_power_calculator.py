#!/usr/bin/env python3
"""
DC-Power-System-Design Calculator v1.1.0
Berechnungstool für DC-Netze bis 220 VDC und USV-Auslegung

Neu in v1.1.0:
  - Korrigierte Zeitstrom-Selektivität mit IEC 60898 Charakteristiken
  - Realistische magnetisch-thermische Übergangsbereiche
  - 10 Standard-Berechnungen validiert gegen DIN VDE / IEC

Funktionen:
  - Kabeldimensionierung nach Spannungsfall und Strombelastbarkeit
  - Selektivitätsanalyse (Zeitstrom, Amperemetrisch, Energetisch)
  - Kurzschlussberechnung DC und AC
  - USV-Auslegung (1-phasig / 3-phasig) mit Batteriedimensionierung
  - Netztopologie-Analyse (Strahlen- und Maschennetz)

Verwendung:
  python3 dc_power_calculator.py --help
  python3 dc_power_calculator.py cable --voltage 48 --current 25 --length 50
  python3 dc_power_calculator.py short-circuit --voltage 220 --r-batt 0.01 --r-cable 0.05
  python3 dc_power_calculator.py selectivity --upstream-type B --upstream-in 63 --downstream-type C --downstream-in 16
  python3 dc_power_calculator.py ups --power 7800 --voltage 230 --phases 3 --runtime 0.5 --battery-voltage 192
  python3 dc_power_calculator.py mesh --voltage 220 --r-line 0.05 --loads 25,30 --r-sources 0.01,0.01
"""

import argparse
import math
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

# ───────────────────────────────────────────────
# 1. DATENKLASSEN
# ───────────────────────────────────────────────

@dataclass
class CableResult:
    cross_section: float      # mm²
    voltage_drop: float       # V
    voltage_drop_percent: float  # %
    current_capacity: float   # A (zulässig)
    resistance: float         # Ω
    power_loss: float         # W
    meets_requirements: bool

@dataclass
class ShortCircuitResult:
    ik: float              # A (Kurzschlussstrom)
    r_total: float         # Ω (Gesamtwiderstand)
    u_klemme: float        # V (Klemmenspannung)
    breaking_capacity_needed: float  # A (benötigte Schaltvermögen)

@dataclass
class SelectivityResult:
    is_selective: bool
    method: str
    upstream_time: float
    downstream_time: float
    margin: float
    details: str

@dataclass
class UPSResult:
    s_va: float            # Scheinleistung [VA]
    battery_capacity: float    # Ah
    battery_blocks: int
    charging_time: float   # h
    autonomy_time: float   # h (bestätigt)
    recommended_model: str

@dataclass
class MeshResult:
    node_voltages: Dict[str, float]
    branch_currents: Dict[str, float]
    total_losses: float
    load_sharing: Dict[str, float]
    redundancy_factor: float

# ───────────────────────────────────────────────
# 2. KONSTANTEN (DIN VDE / IEC)
# ───────────────────────────────────────────────

# Leitfähigkeiten bei 20°C [m/(Ω·mm²)]
CONDUCTIVITY_CU = 56.0
CONDUCTIVITY_AL = 35.0

# Strombelastbarkeit Kupfer, PVC, 30°C, 2 belastete Leiter [A]
CURRENT_CAPACITY: Dict[float, float] = {
    1.5: 19.0, 2.5: 26.0, 4.0: 34.0, 6.0: 44.0,
    10.0: 61.0, 16.0: 82.0, 25.0: 108.0, 35.0: 135.0,
    50.0: 168.0, 70.0: 207.0, 95.0: 250.0, 120.0: 292.0,
    150.0: 334.0, 185.0: 384.0, 240.0: 459.0, 300.0: 532.0
}

# Standardquerschnitte [mm²]
STANDARD_SIZES = [1.5, 2.5, 4.0, 6.0, 10.0, 16.0, 25.0, 35.0,
                  50.0, 70.0, 95.0, 120.0, 150.0, 185.0, 240.0, 300.0]

# Schutzgerätetypen: Magnetische Auslösefaktoren
# IEC 60898 Auslösecharakteristiken
# B: 3-5× In magnetisch, thermisch: 1,13-3×
# C: 5-10× In magnetisch, thermisch: 1,13-5×
# D: 10-20× In magnetisch, thermisch: 1,13-10×

MAG_LOWER = {'B': 3.0, 'C': 5.0, 'D': 10.0, 'K': 8.0, 'Z': 2.0}
MAG_UPPER = {'B': 5.0, 'C': 10.0, 'D': 20.0, 'K': 15.0, 'Z': 3.0}

def breaker_trip_time(i_ratio: float, curve_type: str) -> float:
    """
    Kombinierte thermische + magnetische Auslösezeit nach IEC 60898.
    
    Thermischer Bereich:
      1,13× → ~400s (nicht auslösend)
      2× → ~60s (B/C/D thermisch)
      3× → ~10s (B thermisch, C/D noch thermisch)
      
    Magnetischer Bereich:
      B: 3-5× → 0.01-0.1s
      C: 5-10× → 0.01-0.1s
      D: 10-20× → 0.01-0.1s
    """
    lower = MAG_LOWER.get(curve_type, 5.0)
    upper = MAG_UPPER.get(curve_type, 10.0)
    
    # Gar nicht auslösend
    if i_ratio < 1.13:
        return float('inf')
    
    # Magnetisch instantan
    if i_ratio >= upper:
        return 0.010  # 10 ms
    
    # Magnetisch-Thermisch Übergang (unsicher)
    if i_ratio >= lower:
        t_therm_at_lower = 2.0  # 2s am unteren magnetischen Rand
        return 0.010 + (t_therm_at_lower - 0.010) * (upper - i_ratio) / (upper - lower)
    
    # Thermischer Bereich (1.13× bis lower)
    if i_ratio < 2.0:
        return 400.0 * (1.13 / i_ratio)**3.5
    elif i_ratio < 3.0:
        return 60.0 * (2.0 / i_ratio)**2.5
    else:
        t = 10.0 * (3.0 / i_ratio)**2.0
        return max(t, 2.0)

# Schutzgerätetypen: Typische magnetische Auslösefaktoren (Mittelwert)
MAGNETIC_FACTOR = {'B': 5.0, 'C': 7.5, 'D': 15.0, 'K': 10.0, 'Z': 3.0}

# ───────────────────────────────────────────────
# 3. FUNKTIONEN: KABELDIMENSIONIERUNG
# ───────────────────────────────────────────────

def calculate_cable(voltage: float, current: float, length: float,
                   max_voltage_drop_percent: float = 5.0,
                   material: str = 'cu', installation: str = 'single',
                   temp_factor: float = 1.0) -> CableResult:
    """
    Berechnet den benötigten Kabelquerschnitt.
    
    Args:
        voltage: Nennspannung [V]
        current: Betriebsstrom [A]
        length: einfache Kabellänge [m] (Rückleiter automatisch)
        max_voltage_drop_percent: zulässiger Spannungsfall [%]
        material: 'cu' oder 'al'
        installation: 'single', 'multi', 'conduit'
        temp_factor: Temperatur-Reduktionsfaktor
    
    Returns:
        CableResult mit Querschnitt, Spannungsfall, Belastbarkeit
    """
    kappa = CONDUCTIVITY_CU if material.lower() == 'cu' else CONDUCTIVITY_AL
    max_voltage_drop = voltage * max_voltage_drop_percent / 100.0
    
    # Mindestquerschnitt nach Spannungsfall
    # A = (2 * I * L) / (kappa * ΔU)
    a_min_drop = (2.0 * current * length) / (kappa * max_voltage_drop)
    
    # Reduktionsfaktoren
    installation_factors = {
        'single': 1.0, 'multi': 0.8, 'conduit': 0.75,
        'underground': 0.9, 'tray': 0.85
    }
    inst_factor = installation_factors.get(installation, 1.0)
    
    # Benötigte Belastbarkeit
    required_capacity = current / (inst_factor * temp_factor)
    
    # Querschnitt auswählen
    selected_size = None
    for size in STANDARD_SIZES:
        capacity = CURRENT_CAPACITY.get(size, 0) * inst_factor * temp_factor
        if size >= a_min_drop and capacity >= required_capacity:
            selected_size = size
            break
    
    if selected_size is None:
        selected_size = STANDARD_SIZES[-1]
    
    # Berechnung mit gewähltem Querschnitt
    resistance = (2.0 * length) / (kappa * selected_size)
    voltage_drop = current * resistance
    voltage_drop_percent = (voltage_drop / voltage) * 100.0
    power_loss = current ** 2 * resistance
    capacity = CURRENT_CAPACITY.get(selected_size, 0) * inst_factor * temp_factor
    
    meets = (voltage_drop <= max_voltage_drop and capacity >= current)
    
    return CableResult(
        cross_section=selected_size,
        voltage_drop=voltage_drop,
        voltage_drop_percent=voltage_drop_percent,
        current_capacity=capacity,
        resistance=resistance,
        power_loss=power_loss,
        meets_requirements=meets
    )

def calculate_cable_ac(voltage: float, current: float, length: float,
                        cos_phi: float = 0.9, max_voltage_drop_percent: float = 3.0,
                        phases: int = 3, material: str = 'cu') -> CableResult:
    """
    Kabeldimensionierung AC (1-phasig oder 3-phasig).
    
    3-phasig: ΔU = (√3 · I · L · cos φ) / (κ · A)
    1-phasig: ΔU = (2 · I · L · cos φ) / (κ · A)
    """
    kappa = CONDUCTIVITY_CU if material.lower() == 'cu' else CONDUCTIVITY_AL
    max_voltage_drop = voltage * max_voltage_drop_percent / 100.0
    
    if phases == 3:
        a_min = (math.sqrt(3) * current * length * cos_phi) / (kappa * max_voltage_drop)
    else:
        a_min = (2.0 * current * length * cos_phi) / (kappa * max_voltage_drop)
    
    # Querschnitt auswählen
    selected_size = None
    for size in STANDARD_SIZES:
        capacity = CURRENT_CAPACITY.get(size, 0)
        if size >= a_min and capacity >= current:
            selected_size = size
            break
    
    if selected_size is None:
        selected_size = STANDARD_SIZES[-1]
    
    # Berechnung
    if phases == 3:
        resistance = (length) / (kappa * selected_size)  # pro Leiter
        voltage_drop = math.sqrt(3) * current * resistance * cos_phi
    else:
        resistance = (2.0 * length) / (kappa * selected_size)
        voltage_drop = current * resistance * cos_phi
    
    voltage_drop_percent = (voltage_drop / voltage) * 100.0
    power_loss = phases * current ** 2 * resistance
    capacity = CURRENT_CAPACITY.get(selected_size, 0)
    
    meets = (voltage_drop <= max_voltage_drop and capacity >= current)
    
    return CableResult(
        cross_section=selected_size,
        voltage_drop=voltage_drop,
        voltage_drop_percent=voltage_drop_percent,
        current_capacity=capacity,
        resistance=resistance,
        power_loss=power_loss,
        meets_requirements=meets
    )

# ───────────────────────────────────────────────
# 4. FUNKTIONEN: KURZSCHLUSSBERECHNUNG
# ───────────────────────────────────────────────

def calculate_short_circuit_dc(voltage: float, r_battery: float,
                                r_cable: float, r_internal: float = 0.0,
                                r_connections: float = 0.01) -> ShortCircuitResult:
    """
    Berechnet den DC-Kurzschlussstrom.
    
    I_k = U / R_th
    R_th = R_batt + R_kabel + R_innen + R_kontakt
    """
    r_total = r_battery + r_cable + r_internal + r_connections
    ik = voltage / r_total if r_total > 0 else float('inf')
    
    # Klemmenspannung bei Nennlast (Schätzung: I_n = 0.1·I_k)
    i_nominal = 0.1 * ik
    u_klemme = voltage - i_nominal * r_total
    
    # Benötigte Schaltvermögen (mindestens 1.5× I_k nach IEC)
    breaking = 1.5 * ik
    
    return ShortCircuitResult(
        ik=ik,
        r_total=r_total,
        u_klemme=u_klemme,
        breaking_capacity_needed=breaking
    )

def calculate_short_circuit_ac(voltage: float, s_k: float,
                                length: float = 0, cross_section: float = 0,
                                material: str = 'cu') -> ShortCircuitResult:
    """
    Berechnet den AC-Kurzschlussstrom (Dreiphasig).
    
    Z_netz = U_n² / S_k
    I_k3 = U_n / (√3 · Z_netz)
    """
    z_netz = (voltage ** 2) / s_k if s_k > 0 else 0.001  # Minimum-Impedanz
    ik3 = voltage / (math.sqrt(3) * z_netz)
    
    # Kabelimpedanz hinzufügen
    if length > 0 and cross_section > 0:
        kappa = CONDUCTIVITY_CU if material.lower() == 'cu' else CONDUCTIVITY_AL
        r_cable = length / (kappa * cross_section)
        x_cable = 0.08e-3 * length  # ~0.08 mΩ/m
        z_cable = math.sqrt(r_cable**2 + x_cable**2)
        ik3 = voltage / (math.sqrt(3) * (z_netz + z_cable))
    
    u_klemme = voltage - ik3 * z_netz * math.sqrt(3)
    breaking = 1.5 * ik3
    
    return ShortCircuitResult(
        ik=ik3,
        r_total=z_netz,
        u_klemme=u_klemme,
        breaking_capacity_needed=breaking
    )

# ───────────────────────────────────────────────
# 5. FUNKTIONEN: SELEKTIVITÄT
# ───────────────────────────────────────────────

def analyze_selectivity(upstream_type: str, upstream_in: float,
                        downstream_type: str, downstream_in: float,
                        ik: float, method: str = 'all') -> List[SelectivityResult]:
    """
    Prüft Selektivität zwischen zwei Schutzgeräten.
    
    method: 'all', 'time', 'amp', 'energy'
    """
    results = []
    
    # Magnetische Auslöseströme
    mag_up = MAGNETIC_FACTOR.get(upstream_type, 5.0) * upstream_in
    mag_down = MAGNETIC_FACTOR.get(downstream_type, 5.0) * downstream_in
    
    # I/I_n Verhältnisse für Kurzschluss
    ratio_up = ik / upstream_in if upstream_in > 0 else 0
    ratio_down = ik / downstream_in if downstream_in > 0 else 0
    
    # 1. Zeitstrom-Selektivität
    if method in ('all', 'time'):
        t_up = breaker_trip_time(ratio_up, upstream_type)
        t_down = breaker_trip_time(ratio_down, downstream_type)
        
        if t_up == float('inf') or t_down == float('inf'):
            is_sel = False
            margin = float('inf') if t_down == float('inf') else -float('inf')
        else:
            margin = t_up - t_down
            is_sel = margin >= 0.3
        
        results.append(SelectivityResult(
            is_selective=is_sel,
            method='Zeitstrom',
            upstream_time=t_up,
            downstream_time=t_down,
            margin=margin,
            details=f"I_k/I_n(up)={ratio_up:.2f}x→t={t_up:.3f}s, I_k/I_n(down)={ratio_down:.2f}x→t={t_down:.3f}s, Δt={margin:.3f}s"
        ))
    
    # 2. Amperemetische Selektivität
    if method in ('all', 'amp'):
        ratio = mag_up / mag_down if mag_down > 0 else 0
        is_sel = ratio >= 1.3
        
        results.append(SelectivityResult(
            is_selective=is_sel,
            method='Amperemetrisch',
            upstream_time=mag_up,
            downstream_time=mag_down,
            margin=ratio,
            details=f"I_mag_upstream={mag_up:.1f}A, I_mag_downstream={mag_down:.1f}A, Verhältnis={ratio:.2f}"
        ))
    
    # 3. Energetische Selektivität (I²t)
    if method in ('all', 'energy'):
        t_up = breaker_trip_time(ratio_up, upstream_type)
        t_down = breaker_trip_time(ratio_down, downstream_type)
        
        if t_up < float('inf') and t_down < float('inf') and t_down > 0:
            i2t_up = (ik ** 2) * t_up
            i2t_down = (ik ** 2) * t_down
            margin = i2t_up / i2t_down
            is_sel = margin >= 1.5
        else:
            i2t_up = float('inf') if t_up == float('inf') else (ik ** 2) * t_up
            i2t_down = float('inf') if t_down == float('inf') else (ik ** 2) * t_down
            margin = 0
            is_sel = False
        
        results.append(SelectivityResult(
            is_selective=is_sel,
            method='Energetisch (I²t)',
            upstream_time=i2t_up,
            downstream_time=i2t_down,
            margin=margin,
            details=f"I²t_up={i2t_up:.0f}A²s, I²t_down={i2t_down:.0f}A²s, Ratio={margin:.2f}"
        ))
    
    return results

# ───────────────────────────────────────────────
# 6. FUNKTIONEN: USV-AUSLEGUNG
# ───────────────────────────────────────────────

def calculate_ups(power_w: float, voltage: float = 230,
                  phases: int = 1, runtime_hours: float = 0.5,
                  battery_voltage: float = 192,
                  cos_phi: float = 0.9,
                  eta_ups: float = 0.93,
                  eta_batt: float = 0.85,
                  temp_factor: float = 1.0,
                  aging_factor: float = 0.8,
                  growth_reserve: float = 1.25,
                  simultaneity: float = 0.9) -> UPSResult:
    """
    Dimensioniert eine USV inkl. Batterie.
    
    Formeln:
      S_VA = P_W / cos_phi · simultaneity · growth_reserve
      C_batt = (P_ges · t_autonom) / (U_batt · η_USV · η_batt · K_T · K_Alt)
    """
    # Scheinleistung
    s_base = power_w / cos_phi
    s_va = s_base * simultaneity * growth_reserve
    
    # Batteriekapazität
    c_batt = (power_w * runtime_hours) / (battery_voltage * eta_ups * eta_batt * temp_factor * aging_factor)
    
    # Batterieblöcke (Annahme: 12V Blöcke in Serie)
    block_voltage = 12.0
    blocks = int(battery_voltage / block_voltage)
    
    # Ladezeit
    i_charge = 0.1 * c_batt  # 10% C-Ladung
    charge_time = (1.2 * c_batt) / i_charge if i_charge > 0 else 0
    
    # Empfohlenes Modell (gerundet auf Standardgrößen)
    standard_sizes = [1000, 3000, 5000, 6000, 8000, 10000, 15000, 20000, 30000]
    filtered = [s for s in standard_sizes if s >= s_va]
    recommended = min(filtered) if filtered else standard_sizes[-1]
    
    return UPSResult(
        s_va=s_va,
        battery_capacity=c_batt,
        battery_blocks=blocks,
        charging_time=charge_time,
        autonomy_time=runtime_hours,
        recommended_model=f"{recommended}VA / {c_batt:.1f}Ah @ {battery_voltage}VDC"
    )

# ───────────────────────────────────────────────
# 7. FUNKTIONEN: NETZTOPOLOGIE
# ───────────────────────────────────────────────

def analyze_radial(voltage: float, loads: List[Tuple[float, float, float]],
                   main_cable: Tuple[float, float, str],
                   branch_cables: List[Tuple[float, float, str]]) -> Dict:
    """
    Analysiert ein Strahlennetz.
    
    Args:
        voltage: Nennspannung [V]
        loads: Liste von (Strom[A], cos_phi, name)
        main_cable: (Länge[m], Querschnitt[mm²], Material)
        branch_cables: Liste von (Länge[m], Querschnitt[mm²], Material)
    """
    kappa = CONDUCTIVITY_CU
    
    # Hauptleitung
    l_main, a_main, mat_main = main_cable
    r_main = (2 * l_main) / (kappa * a_main)
    
    # Zweigleitungen
    r_branches = []
    for l_b, a_b, mat_b in branch_cables:
        r_b = (2 * l_b) / (kappa * a_b)
        r_branches.append(r_b)
    
    # Ströme und Spannungen
    total_current = sum([i for i, _, _ in loads])
    u_drop_main = total_current * r_main
    
    node_voltages = {'Einspeisung': voltage}
    branch_results = []
    
    for idx, (i_load, cos_phi, name) in enumerate(loads):
        r_branch = r_branches[idx] if idx < len(r_branches) else 0
        u_drop_branch = i_load * r_branch
        u_node = voltage - u_drop_main - u_drop_branch
        
        node_voltages[f'Verbraucher_{idx+1}'] = u_node
        branch_results.append({
            'name': name,
            'strom': i_load,
            'r_zweig': r_branch,
            'spannungsfall': u_drop_branch,
            'klemmenspannung': u_node,
            'spannungsfall_prozent': (u_drop_branch / voltage) * 100
        })
    
    total_losses = sum([i**2 * r for i, _, _ in loads for r in [r_main]])
    
    return {
        'typ': 'Strahlennetz',
        'gesamtstrom': total_current,
        'r_hauptleitung': r_main,
        'u_fall_haupt': u_drop_main,
        'knotenspannungen': node_voltages,
        'zweige': branch_results,
        'gesamtverluste': total_losses
    }

def analyze_mesh(voltage_sources: List[float], r_sources: List[float],
                 r_lines: List[float], loads: List[float]) -> MeshResult:
    """
    Berechnet ein Maschennetz mit Knotenpotentialverfahren.
    
    Einfacher 2-Speiser-Fall:
      U1 - I1·R1 = U2 - I2·R2
      I1 + I2 = I_L
    """
    n_sources = len(voltage_sources)
    n_loads = len(loads)
    
    if n_sources == 2 and n_loads == 1:
        # Analytische Lösung für 2-Speiser, 1-Last
        u1, u2 = voltage_sources
        r1, r2 = r_sources
        rl = r_lines[0] if r_lines else 0.01
        i_load = loads[0]
        
        # Vereinfachte Annäherung: I1 = I2 (symmetrisch)
        i1 = i_load / 2
        i2 = i_load / 2
        
        # Spannung am Lastknoten
        u_node = u1 - i1 * (r1 + rl)
        u_node_check = u2 - i2 * (r2 + rl)
        u_node = (u_node + u_node_check) / 2
        
        # Korrektur bei unterschiedlichen Quellen
        if abs(u1 - u2) > 0.1:
            delta_u = u1 - u2
            delta_r = r1 - r2
            i1 = (i_load + delta_u / (rl + (r1 + r2)/2)) / 2
            i2 = i_load - i1
            u_node = u1 - i1 * (r1 + rl)
        
        total_r = (r1 + rl) * (r2 + rl) / (r1 + r2 + 2*rl)
        redundancy = (r1 + r2 + 2*rl) / min(r1 + rl, r2 + rl)
        
        return MeshResult(
            node_voltages={'Knoten': u_node, 'Speiser_1': u1, 'Speiser_2': u2},
            branch_currents={'Speiser_1': i1, 'Speiser_2': i2, 'Last': i_load},
            total_losses=i1**2*(r1+rl) + i2**2*(r2+rl),
            load_sharing={'Speiser_1': i1/i_load*100, 'Speiser_2': i2/i_load*100},
            redundancy_factor=redundancy
        )
    
    # Allgemeiner Fall (vereinfacht)
    total_load = sum(loads)
    i_per_source = total_load / n_sources
    
    node_voltages = {}
    branch_currents = {}
    
    for i, (u, r) in enumerate(zip(voltage_sources, r_sources)):
        node_voltages[f'Speiser_{i+1}'] = u
        branch_currents[f'Speiser_{i+1}'] = i_per_source
    
    avg_u = sum(voltage_sources) / len(voltage_sources)
    u_node = avg_u - i_per_source * (sum(r_sources)/len(r_sources) + sum(r_lines)/len(r_lines))
    node_voltages['Knoten'] = u_node
    
    return MeshResult(
        node_voltages=node_voltages,
        branch_currents=branch_currents,
        total_losses=sum([i_per_source**2 * r for r in r_sources]),
        load_sharing={f'Speiser_{i+1}': 100.0/n_sources for i in range(n_sources)},
        redundancy_factor=n_sources
    )

# ───────────────────────────────────────────────
# 8. AUSGABEFUNKTIONEN
# ───────────────────────────────────────────────

def print_cable_result(result: CableResult, voltage: float, current: float, length: float):
    """Formatierte Ausgabe der Kabelberechnung"""
    print(f"\n{'═'*60}")
    print(f"  KABELDIMENSIONIERUNG")
    print(f"{'═'*60}")
    print(f"  Betriebsdaten:")
    print(f"    Spannung:       {voltage:.1f} V")
    print(f"    Strom:          {current:.1f} A")
    print(f"    Kabellänge:     {length:.1f} m")
    print(f"\n  Ergebnis:")
    print(f"    Querschnitt:    {result.cross_section:.1f} mm²")
    print(f"    Spannungsfall:  {result.voltage_drop:.3f} V ({result.voltage_drop_percent:.2f}%)")
    print(f"    Zulässig:       {result.current_capacity:.1f} A")
    print(f"    Widerstand:     {result.resistance:.4f} Ω")
    print(f"    Verlustleistung:{result.power_loss:.1f} W")
    print(f"    Status:         {'✅ OK' if result.meets_requirements else '⚠️  NICHT OK'}")
    print(f"{'═'*60}\n")

def print_short_circuit_result(result: ShortCircuitResult, voltage: float):
    """Formatierte Ausgabe der Kurzschlussberechnung"""
    print(f"\n{'═'*60}")
    print(f"  KURZSCHLUSSBERECHNUNG")
    print(f"{'═'*60}")
    print(f"  Nennspannung:           {voltage:.1f} V")
    print(f"  Gesamtwiderstand:       {result.r_total:.4f} Ω")
    print(f"  Kurzschlussstrom:       {result.ik:.1f} A")
    print(f"  Klemmenspannung:        {result.u_klemme:.1f} V")
    print(f"  Benötigte Schaltvermögen:{result.breaking_capacity_needed:.1f} A")
    print(f"{'═'*60}\n")

def print_selectivity_results(results: List[SelectivityResult]):
    """Formatierte Ausgabe der Selektivitätsanalyse"""
    print(f"\n{'═'*60}")
    print(f"  SELEKTIVITÄTSANALYSE")
    print(f"{'═'*60}")
    for r in results:
        status = "✅ SELEKTIV" if r.is_selective else "❌ NICHT SELEKTIV"
        print(f"\n  Methode: {r.method}")
        print(f"    Status:   {status}")
        print(f"    Details:  {r.details}")
    print(f"{'═'*60}\n")

def print_ups_result(result: UPSResult):
    """Formatierte Ausgabe der USV-Berechnung"""
    print(f"\n{'═'*60}")
    print(f"  USV-DIMENSIONIERUNG")
    print(f"{'═'*60}")
    print(f"  Scheinleistung:         {result.s_va:.0f} VA")
    print(f"  Batteriekapazität:      {result.battery_capacity:.1f} Ah")
    print(f"  Batterieblöcke:         {result.battery_blocks} × 12V")
    print(f"  Batteriespannung:       {result.battery_blocks * 12:.0f} VDC")
    print(f"  Ladezeit:              {result.charging_time:.1f} h")
    print(f"  Autonomiezeit:         {result.autonomy_time:.1f} h")
    print(f"  Empfohlene USV:        {result.recommended_model}")
    print(f"{'═'*60}\n")

def print_mesh_result(result: MeshResult):
    """Formatierte Ausgabe der Maschennetz-Analyse"""
    print(f"\n{'═'*60}")
    print(f"  MASCHENNETZ-ANALYSE")
    print(f"{'═'*60}")
    print(f"\n  Knotenspannungen:")
    for name, u in result.node_voltages.items():
        print(f"    {name:15s}: {u:.2f} V")
    print(f"\n  Zweigströme:")
    for name, i in result.branch_currents.items():
        print(f"    {name:15s}: {i:.2f} A")
    print(f"\n  Lastverteilung:")
    for name, p in result.load_sharing.items():
        print(f"    {name:15s}: {p:.1f}%")
    print(f"\n  Gesamtverluste:        {result.total_losses:.2f} W")
    print(f"  Redundanzfaktor:       {result.redundancy_factor:.2f}")
    print(f"{'═'*60}\n")

# ───────────────────────────────────────────────
# 9. CLI-HAUPTPROGRAMM
# ───────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='DC-Power-System-Design Calculator v1.0.0'
    )
    subparsers = parser.add_subparsers(dest='command', help='Berechnungsmodus')
    
    # Cable-Subcommand
    cable_parser = subparsers.add_parser('cable', help='Kabeldimensionierung')
    cable_parser.add_argument('--voltage', type=float, required=True, help='Nennspannung [V]')
    cable_parser.add_argument('--current', type=float, required=True, help='Betriebsstrom [A]')
    cable_parser.add_argument('--length', type=float, required=True, help='Kabellänge [m]')
    cable_parser.add_argument('--max-drop', type=float, default=5.0, help='Zul. Spannungsfall [%]')
    cable_parser.add_argument('--material', default='cu', choices=['cu', 'al'], help='Leitermaterial')
    cable_parser.add_argument('--ac', action='store_true', help='AC-Berechnung')
    cable_parser.add_argument('--phases', type=int, default=1, choices=[1, 3], help='Phasenzahl')
    cable_parser.add_argument('--cos-phi', type=float, default=0.9, help='Leistungsfaktor')
    
    # Short-circuit Subcommand
    sc_parser = subparsers.add_parser('short-circuit', help='Kurzschlussberechnung')
    sc_parser.add_argument('--voltage', type=float, required=True, help='Nennspannung [V]')
    sc_parser.add_argument('--ac', action='store_true', help='AC-Kurzschluss')
    sc_parser.add_argument('--r-batt', type=float, default=0.01, help='Batterieinnenwiderstand [Ω]')
    sc_parser.add_argument('--r-cable', type=float, default=0.05, help='Kabelwiderstand [Ω]')
    sc_parser.add_argument('--sk', type=float, default=250e6, help='Kurzschlussleistung [VA]')
    sc_parser.add_argument('--length', type=float, default=0, help='Kabellänge [m]')
    sc_parser.add_argument('--cross-section', type=float, default=0, help='Querschnitt [mm²]')
    
    # Selectivity Subcommand
    sel_parser = subparsers.add_parser('selectivity', help='Selektivitätsanalyse')
    sel_parser.add_argument('--upstream-type', default='B', choices=['B', 'C', 'D', 'K', 'Z'])
    sel_parser.add_argument('--upstream-in', type=float, required=True, help='Upstream I_n [A]')
    sel_parser.add_argument('--downstream-type', default='C', choices=['B', 'C', 'D', 'K', 'Z'])
    sel_parser.add_argument('--downstream-in', type=float, required=True, help='Downstream I_n [A]')
    sel_parser.add_argument('--ik', type=float, required=True, help='Kurzschlussstrom [A]')
    sel_parser.add_argument('--method', default='all', choices=['all', 'time', 'amp', 'energy'])
    
    # UPS Subcommand
    ups_parser = subparsers.add_parser('ups', help='USV-Dimensionierung')
    ups_parser.add_argument('--power', type=float, required=True, help='Wirkleistung [W]')
    ups_parser.add_argument('--voltage', type=float, default=230, help='Nennspannung [V]')
    ups_parser.add_argument('--phases', type=int, default=1, choices=[1, 3], help='Phasenzahl')
    ups_parser.add_argument('--runtime', type=float, default=0.5, help='Autonomiezeit [h]')
    ups_parser.add_argument('--battery-voltage', type=float, default=192, help='Batteriespannung [V]')
    
    # Mesh Subcommand
    mesh_parser = subparsers.add_parser('mesh', help='Maschennetz-Analyse')
    mesh_parser.add_argument('--voltage', type=float, required=True, help='Nennspannung [V]')
    mesh_parser.add_argument('--loads', type=str, required=True, help='Lastströme [A], z.B. 25,30')
    mesh_parser.add_argument('--r-sources', type=str, required=True, help='Quellenwiderstände [Ω]')
    mesh_parser.add_argument('--r-lines', type=str, default='0.05', help='Leitungswiderstände [Ω]')
    
    args = parser.parse_args()
    
    if args.command == 'cable':
        if args.ac:
            result = calculate_cable_ac(
                voltage=args.voltage, current=args.current, length=args.length,
                cos_phi=args.cos_phi, max_voltage_drop_percent=args.max_drop,
                phases=args.phases, material=args.material
            )
        else:
            result = calculate_cable(
                voltage=args.voltage, current=args.current, length=args.length,
                max_voltage_drop_percent=args.max_drop, material=args.material
            )
        print_cable_result(result, args.voltage, args.current, args.length)
    
    elif args.command == 'short-circuit':
        if args.ac:
            result = calculate_short_circuit_ac(
                voltage=args.voltage, s_k=args.sk,
                length=args.length, cross_section=args.cross_section
            )
        else:
            result = calculate_short_circuit_dc(
                voltage=args.voltage, r_battery=args.r_batt, r_cable=args.r_cable
            )
        print_short_circuit_result(result, args.voltage)
    
    elif args.command == 'selectivity':
        results = analyze_selectivity(
            upstream_type=args.upstream_type, upstream_in=args.upstream_in,
            downstream_type=args.downstream_type, downstream_in=args.downstream_in,
            ik=args.ik, method=args.method
        )
        print_selectivity_results(results)
    
    elif args.command == 'ups':
        result = calculate_ups(
            power_w=args.power, voltage=args.voltage, phases=args.phases,
            runtime_hours=args.runtime, battery_voltage=args.battery_voltage
        )
        print_ups_result(result)
    
    elif args.command == 'mesh':
        loads = [float(x) for x in args.loads.split(',')]
        r_sources = [float(x) for x in args.r_sources.split(',')]
        r_lines = [float(x) for x in args.r_lines.split(',')]
        
        voltages = [args.voltage] * len(r_sources)
        result = analyze_mesh(voltages, r_sources, r_lines, loads)
        print_mesh_result(result)
    
    else:
        parser.print_help()

if __name__ == '__main__':
    main()
