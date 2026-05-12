# DC-Power-System-Design Calculator v1.0.0

Elektrotechnisches Berechnungstool für DC-Netze bis 220 VDC und USV-Auslegung (1-/3-phasig).

## Funktionen

| Modus | Beschreibung |
|-------|-------------|
| `cable` | Kabeldimensionierung DC/AC nach Spannungsfall |
| `short-circuit` | Kurzschlussberechnung DC/AC |
| `selectivity` | Selektivitätsanalyse (Zeitstrom/Amperemetrisch/Energetisch) |
| `ups` | USV-Dimensionierung mit Batterieauslegung |
| `mesh` | Maschennetz-Analyse (2-Speiser) |

## Installation

```bash
pip install dc-power-calculator
# oder direkt:
python3 dc_power_calculator.py --help
```

## Beispiele

### Kabel DC
```bash
python3 dc_power_calculator.py cable --voltage 48 --current 25 --length 50
# Querschnitt: 25.0 mm², Spannungsfall: 3.72%
```

### Kabel AC 3-phasig
```bash
python3 dc_power_calculator.py cable --voltage 400 --current 32 --length 100 \
  --ac --phases 3 --cos-phi 0.9
# Querschnitt: 10.0 mm², Spannungsfall: 2.23%
```

### Kurzschluss DC
```bash
python3 dc_power_calculator.py short-circuit --voltage 220 --r-batt 0.01 --r-cable 0.05
# I_k = 3142.9 A, benötigtes Schaltvermögen: 4714.3 A
```

### Selektivität
```bash
python3 dc_power_calculator.py selectivity \
  --upstream-type B --upstream-in 63 \
  --downstream-type C --downstream-in 16 --ik 500
# ✅ Amperemetrisch SELEKTIV (Verhältnis 2.62)
# ❌ Zeitstrom NICHT SELEKTIV (Δt=0.000s)
# ✅ Energetisch SELEKTIV (Verhältnis 68.91)
```

### USV
```bash
python3 dc_power_calculator.py ups --power 7800 --voltage 400 --phases 3 \
  --runtime 0.5 --battery-voltage 192
# Empfohlen: 10000VA / 32.1Ah @ 192VDC, Ladezeit: 12h
```

### Maschennetz
```bash
python3 dc_power_calculator.py mesh --voltage 220 --loads 25 \
  --r-sources 0.01,0.01 --r-lines 0.05
# Lastverteilung: 50/50%, Redundanzfaktor: 2.0
```

## Normenreferenzen

- DIN VDE 0298-4 (Kabelbelastbarkeit)
- DIN VDE 0100-520 (Betriebsmittel)
- DIN VDE 0102 (Kurzschluss)
- IEC 60909-0 (Kurzschlussströme)
- IEC 62040 (USV)

## Lizenz

DIN 5008 konform, KlausDIG Services
