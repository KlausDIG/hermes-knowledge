---
name: dc-power-system-design
version: 1.1.0
description: DC-Netzberechnung bis 220 VDC mit Selektivitätsanalyse (korrigierte IEC 60898 Charakteristiken), Kurzschlussberechnung, USV-Auslegung (1-/3-phasig) für Strahlen- und Maschennetze. Validiert gegen DIN VDE / IEC Standards.
author: KlausDIG
---

# dc-power-system-design

Elektrotechnisches Berechnungstool für DC-Netze bis 220 VDC und USV-Auslegung im Wechsel- und Drehstromnetz.

## Trigger

Nutze diesen Skill, wenn du:
- Ein DC-Versorgungsnetz (bis 220 VDC) auslegen musst
- Selektivität zwischen Schutzgeräten prüfen musst
- Kurzschlussströme in DC- oder AC-Netzen berechnen willst
- Eine USV (ein- oder dreiphasig) dimensionieren musst
- Die Netztopologie (Strahlen- oder Maschennetz) analysieren willst
- Kabelquerschnitte nach Spannungsfall und Strombelastbarkeit berechnen musst

---

## 1. DC-Netzberechnung (bis 220 VDC)

### 1.1 Kabelquerschnitt nach Spannungsfall

Formel nach DIN VDE 0298-4:

```
ΔU = (2 · I · L · cos φ) / (κ · A)
```

| Symbol | Bedeutung | Einheit |
|--------|-----------|---------|
| ΔU | Spannungsfall | V |
| I | Betriebsstrom | A |
| L | Kabellänge | m |
| κ | Leitfähigkeit (Kupfer: 56, Aluminium: 35) | m/(Ω·mm²) |
| A | Leiterquerschnitt | mm² |
| cos φ | Leistungsfaktor (DC: 1,0) | - |

**Mindestquerschnitt:**
```
A_min = (2 · I · L) / (κ · ΔU_zul)
```

Zulässiger Spannungsfall:
- Beleuchtung: 3% (bei 220 VDC = 6,6 V)
- Andere Verbraucher: 5% (bei 220 VDC = 11 V)
- USV-Eingang: max. 2% (bei 220 VDC = 4,4 V)

### 1.2 Strombelastbarkeit

Nach DIN VDE 0298-4, Tabelle 1 (Kupfer, PVC-isoliert):

| Querschnitt [mm²] | Belastbarkeit [A] |
|-------------------|-------------------|
| 1,5 | 19 |
| 2,5 | 26 |
| 4 | 34 |
| 6 | 44 |
| 10 | 61 |
| 16 | 82 |
| 25 | 108 |
| 35 | 135 |
| 50 | 168 |
| 70 | 207 |
| 95 | 250 |
| 120 | 292 |

**Reduktionsfaktoren:**
- Mehradrige Verlegung: 0,8
- Erhöhte Umgebungstemperatur (>30°C): 0,91 (35°C), 0,82 (40°C)

### 1.3 Eigenbedarfsberechnung

**Lastzusammenstellung (Beispiel 48 VDC Telecom):**

```
Verbraucher          Anzahl  Einzelleistung  Gesamtleistung
Router/Gateway       4       25 W            100 W
Switches L2          8       15 W            120 W
Switches L3          2       45 W            90 W
Server (redundant)   2       300 W           600 W
Überwachung          1       50 W            50 W
Reserve (20%)      -       -               192 W
─────────────────────────────────────────────────────
Gesamtleistung P_ges = 1152 W
Gesamtstrom I_ges = P_ges / U_n = 1152 W / 48 V = 24 A
```

**Reserveplanung:**
- Gleichzeitigkeitsfaktor g: 0,7–1,0 (je nach Anwendung)
- Wachstumsreserve: 20–30%

---

## 2. Selektivitätsanalyse

### 2.1 Selektivitätsarten

| Art | Prinzip | Anwendung |
|-----|---------|-----------|
| **Zeitstrom-Selektivität** | t(I)-Charakteristik, upstream träger | LV-Schaltanlagen |
| **Amperemetische Selektivität** | I>>-Instantan, nur downstream löst | Kurzschlussnähe |
| **Energetische Selektivität** | I²t-Differenzierung | Halbleiterschutz |
| **Logische Selektivität** | Kommunikation zwischen Schutzgeräten | Intelligente Schaltanlagen |

### 2.2 Zeitstrom-Selektivität (Back-up-Schutz)

**Bedingung:**
```
t_upstream(I_k) ≥ t_downstream(I_k) + Δt
```

Δt = Toleranz + Auslösezeit + Reserve
- Δt_min = 0,3 s (thermomagnetisch)
- Δt_min = 0,1 s (elektronisch)

**Beispiel Berechnung:**
```
Schutz A (upstream):  B32A, träge Charakteristik
Schutz B (downstream): C16A, träge Charakteristik

Bei I_k = 500 A:
  t_B(500 A) ≈ 0,05 s (aus Herstellerkurve)
  t_A(500 A) ≈ 0,4 s (aus Herstellerkurve)
  Δt = 0,4 - 0,05 = 0,35 s ≥ 0,3 s → SELEKTIV
```

### 2.3 Amperemetische Selektivität

**Bedingung:**
```
I_magnetic_upstream ≥ 1,3 · I_magnetic_downstream
```

**Beispiel:**
```
Upstream:  B63A, magnetisch bei 5·I_n = 315 A
Downstream: B16A, magnetisch bei 5·I_n = 80 A

Verhältnis: 315 / 80 = 3,9 ≥ 1,3 → SELEKTIV (im Magnetikbereich)
```

### 2.4 Energetische Selektivität (I²t)

**Bedingung:**
```
(I²t)_upstream ≥ (I²t)_downstream · k
```

k = Sicherheitsfaktor (1,5–2,0)

---

## 3. Kurzschlussberechnung

### 3.1 Ohmsche Kurzschlussberechnung (DC)

**Thevenin-Ersatzschaltbild:**
```
R_th = R_batt + R_kabel + R_schutz + R_kontakt
U_th = U_batt (Leerlaufspannung)
```

**Kurzschlussstrom:**
```
I_k = U_th / R_th
```

**Beispiel (48 VDC Batterie):**
```
Batterie:  4x 12 V, 100 Ah
  R_batt = 0,005 Ω (Innenwiderstand pro Block)
  U_n = 48 V
Kabel:  10 m, 4 mm² Kupfer
  R_kabel = (2 · 10 m) / (56 · 4 mm²) = 0,089 Ω
Schutz: Sicherung 32 A
  R_schutz ≈ 0 Ω (vernachlässigbar)
Kontakt/Verbindung: 0,01 Ω

R_th = 0,005 + 0,089 + 0 + 0,01 = 0,104 Ω
I_k = 48 V / 0,104 Ω = 461,5 A

I_n = 32 A
I_k / I_n = 461,5 / 32 = 14,4 → sichere Auslösung
```

### 3.2 Kurzschlussleistung (AC, für USV-Auslegung)

**Netzimpedanz:**
```
Z_netz = U_n² / S_k
```

| S_k [MVA] | Z_netz bei 400 V [Ω] |
|-----------|----------------------|
| 250 | 0,64 |
| 500 | 0,32 |
| 1000 | 0,16 |

**Kurzschlussstrom Drehstrom (nahe Generator):**
```
I_k3 = U_n / (√3 · Z_netz)
```

### 3.3 Spannungsfall bei Kurzschluss

**Klemmenspannung beim Motoranlauf:**
```
U_klemme = U_n - (I_anlauf · Z_netz · √3)
```

Anlaufspannung sollte ≥ 85% U_n sein.

---

## 4. USV-Auslegung (Wechsel- und Drehstrom)

### 4.1 Leistungsberechnung

**Grundlast (Beispiel Büro/Serverraum):**

```
Verbraucher          Leistung [W]   cos φ   S [VA]
Server Rack 1        2000          0,95    2105
Server Rack 2        1500          0,95    1579
Netzwerk (Switches)   500          0,90     556
Beleuchtung (LED)     800          1,00     800
Klima (IT)           3000          0,85    3529
───────────────────────────────────────────────
Gesamtwirkleistung P = 7800 W
Gesamtscheinleistung S = 8569 VA
```

**USV-Leistung dimensionieren:**
```
S_USV = S_ges · Reduktionsfaktor · Wachstumsreserve

Reduktionsfaktor g:
  - Büro: 0,7–0,8
  - Serverraum: 0,9–1,0
  - Industrie: 0,6–0,8

Wachstumsreserve: 1,2–1,3

Beispiel:
  S_USV = 8569 VA · 0,9 · 1,25 = 9640 VA
  → gewählt: 10 kVA USV
```

### 4.2 Batteriedimensionierung (Laufzeit)

**Autonomiezeit berechnen:**
```
C_batt = (P_ges · t_autonom) / (U_batt · η_USV · η_batt · K_T · K_Alt)
```

| Symbol | Bedeutung | Typisch |
|--------|-----------|---------|
| P_ges | Wirkleistung | - |
| t_autonom | gewünschte Laufzeit | h |
| U_batt | Batteriespannung | V |
| η_USV | Wirkungsgrad USV | 0,90–0,95 |
| η_batt | Wirkungsgrad Batterie | 0,80–0,90 |
| K_T | Temperaturfaktor (bei 20°C=1,0) | 0,8–1,2 |
| K_Alt | Alterungsfaktor | 0,8 |

**Beispiel (10 kVA USV, 30 Min Autonomie):**
```
P_ges = 7800 W
t_autonom = 0,5 h
U_batt = 192 V (16x 12 V Blöcke)
η_USV = 0,93
η_batt = 0,85
K_T = 1,0 (20°C)
K_Alt = 0,8

C_batt = (7800 · 0,5) / (192 · 0,93 · 0,85 · 1,0 · 0,8)
C_batt = 3900 / 121,2 = 32,2 Ah
→ gewählt: 4x 12 V / 40 Ah (Blöcke in Serie)
```

### 4.3 Ladezeit

**Wiederaufladezeit (nach DIN 41773):**
```
t_lade = (1,2 · C_batt) / I_lade
```
- Ladeschlussspannung: 2,40 V/Zelle (Blei-Säure)
- Ladeschlussspannung: 3,65 V/Zelle (LiFePO4)

**Beispiel:**
```
C_batt = 40 Ah
I_lade_max = 0,1 · C = 4 A

Ladezeit konstantstrom: (1,2 · 40) / 4 = 12 h
Ladezeit IUoU: 8–10 h (empfohlen)
```

---

## 5. Netztopologien

### 5.1 Strahlennetz (Radial)

```
Speisegerät
    │
    ├─── Abzweig 1 ─── Verbraucher A
    │
    ├─── Abzweig 2 ─── Verbraucher B
    │
    └─── Abzweig 3 ─── Verbraucher C
```

**Vorteile:**
- Einfache Berechnung
- Einfache Fehlerortung
- Geringer Kabelbedarf

**Nachteile:**
- Keine Redundanz
- Spannungsfall summiert sich
- Fehler führt zu Totalausfall

**Spannungsfall gesamt:**
```
ΔU_ges = ΔU_Haupt + ΔU_Abzweig
```

### 5.2 Maschennetz (Ring/Mesh)

```
      Speisegerät A
           │
    ┌──────┴──────┐
    │             │
 Verbraucher 1 ───┼─── Verbraucher 2
    │             │
    └──────┬──────┘
           │
      Speisegerät B
```

**Vorteile:**
- Redundanz (n-1)
- Bessere Spannungshaltung
- Höhere Versorgungssicherheit

**Nachteile:**
- Komplexere Berechnung (Knotenpotentialverfahren)
- Höherer Kabelbedarf
- Komplexere Schutzkoordination

**Berechnung nach Knotenpotentialverfahren:**
```
G · U = I

G = Leitwertmatrix
U = Knotenspannungsvektor
I = Stromquellenvektor
```

**Beispiel 2-Speiser-Masche:**
```
Speiser 1: 220 VDC, R_int1 = 0,01 Ω
Speiser 2: 220 VDC, R_int2 = 0,01 Ω
Maschenwiderstand R_masche = 0,05 Ω
Last I_L = 50 A

Stromverteilung:
  I_1 + I_2 = 50 A
  U_1 - I_1·R_int1 = U_2 - I_2·R_int2

  220 - I_1·0,01 = 220 - I_2·0,01
  → I_1 = I_2 = 25 A (symmetrisch)

Klemmenspannung:
  U_klemme = 220 - 25·0,01 - 25·0,05 = 220 - 1,5 = 218,5 V
```

---

## 6. Python-Berechnungstool

Siehe: `scripts/dc_power_calculator.py`

---

## 7. Referenzstandards

| Standard | Thema |
|----------|-------|
| DIN VDE 0298-4 | Strombelastbarkeit von Kabeln |
| DIN VDE 0100-520 | Auswahl und Errichtung von Betriebsmitteln |
| DIN VDE 0102 | Kurzschlussstromberechnung |
| IEC 60909-0 | Kurzschlussströme in Drehstromnetzen |
| DIN 41773 | Gleichstrom-Stromversorgungen |
| IEC 62040 | USV (Uninterruptible Power Systems) |
| DIN VDE 0530-1 | Drehstrommaschinen |

---

## 8. Schnellreferenz

### Kabelquerschnitt DC
```python
# A_min [mm²] = (2 * I[A] * L[m]) / (kappa * deltaU_zul[V])
# kappa Cu = 56, Al = 35
```

### Kurzschlussstrom DC
```python
# I_k = U_n / R_th
# R_th = R_batt + R_kabel + R_innen
```

### USV-Batterie
```python
# C_batt[Ah] = (P[W] * t[h]) / (U[V] * eta_USV * eta_batt * K_T * K_Alt)
# typisch: eta_USV=0.93, eta_batt=0.85, K_Alt=0.8
```

### Selektivität
```python
# Zeitstrom: t_upstream >= t_downstream + 0.3s
# Amperemetrisch: I_mag_upstream >= 1.3 * I_mag_downstream
# Energetisch: I2t_upstream >= I2t_downstream * 1.5
```

---

## 9. Excel-Export der Validierungsergebnisse

Der Skill unterstützt die Generierung eines vollständigen, rechenbaren Excel-Reports mit allen 10 Validierungstests.

### Enthaltene Blätter

| Blatt | Inhalt |
|-------|--------|
| Dashboard | 3 Rechner (Kabel DC, Kurzschluss DC, USV) — gelbe Zellen editierbar |
| Kabelbelastbarkeit | DIN VDE 0298-4 Tabelle mit Reduktionsfaktoren |
| Zeitstrom-Daten | Kennlinien-Rohdaten IEC 60898 |
| Diagramme | 2 eingebettete Charts (Zeitstrom, USV-Laufzeit) |
| Selektivitaet | Prüfrechner Upstream/Downstream (B/C/D) |
| Maschennetz | 2-Speiser-Rechner (symmetrisch) |
| Masche_4Speiser | **4-Speiser mit Knotenpotentialverfahren** — 4×U_i, 4×R_i editierbar |
| Temperatur-Faktoren | Reduktionsfaktoren + kombinierter Rechner |
| USV-Laufzeit-Daten | Diagrammdaten |
| Validierung_v1.1 | Referenzergebnisse 10/10 OK |
| QuickRef-Formeln | 19 Formeln auf einen Blick |

### Script

```bash
python3 scripts/generate_excel_report.py --output dc_power_v2.1.xlsx
```

Siehe: `scripts/generate_excel_report.py`

---

# ENDE
