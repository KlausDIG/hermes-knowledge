# Validierungsrapport v1.1.0

Validiert gegen DIN VDE, IEC und Handrechnung.
10 Standardberechnungen durchgeführt und verifiziert.

---

## Änderungen v1.0.0 → v1.1.0

- **[FIX]** `breaker_trip_time()`: Korrigierte IEC 60898 Charakteristiken
  - Thermischer Bereich: 1,13× → 400s (nicht auslösend)
  - Übergangsbereich: Lower bound → 2s (statt Instantan)
  - Magnetischer Bereich: Upper bound → 10ms
- **[FIX]** `analyze_selectivity()`: Zeitstrom-Selektivität jetzt korrekt bei thermischem Bereich
- **[VALIDIERUNG]** 10 Standardberechnungen bestanden

---

## 【1】 Kabel DC

| Parameter | Eingabe | Ergebnis | Prüfung |
|-----------|---------|----------|---------|
| U | 48 V | — | — |
| I | 25 A | — | — |
| L | 50 m | — | — |
| A_min | — | **18.60 mm²** | Formel: (2·I·L)/(κ·ΔU) |
| Gewählt | 25 mm² | — | nächste Standardgröße |
| R | — | **0.0714 Ω** | R = 2L/(κ·A) |
| ΔU | — | **1.786 V (3.72%)** | ΔU = I·R |
| P_Verlust | — | **44.6 W** | P = I²·R |
| Status | — | ✅ OK | < 5% |

**Formel:** A_min = (2·I·L) / (κ·ΔU) mit κ(Cu) = 56 m/(Ω·mm²)

---

## 【2】 Kabel AC 3-phasig

| Parameter | Eingabe | Ergebnis | Prüfung |
|-----------|---------|----------|---------|
| U | 400 V | — | — |
| I | 32 A | — | — |
| L | 100 m | — | — |
| cos φ | 0.9 | — | — |
| A_min | — | **8.84 mm²** | Formel: (√3·I·L·cosφ)/(κ·ΔU) |
| Gewählt | 10 mm² | — | nächste Standardgröße |
| ΔU | — | **8.91 V (2.23%)** | ΔU = √3·I·R·cosφ |
| Status | — | ✅ OK | < 3% |

**Formel:** AC 3-phasig mit √3-Faktor nach DIN VDE 0298-4

---

## 【3】 Kurzschluss DC (48V Batterie)

| Parameter | Eingabe | Ergebnis | Prüfung |
|-----------|---------|----------|---------|
| U | 48 V | — | — |
| R_batt | 0.005 Ω | — | — |
| R_kabel | 0.071 Ω | — | — |
| R_kontakt | 0.010 Ω | — | — |
| R_th | — | **0.086 Ω** | Summe aller Widerstände |
| I_k | — | **558 A** | I_k = U/R_th |
| Schaltvermögen | — | **837 A** | 1.5·I_k nach IEC |
| Status | — | ✅ OK | — |

**Formel:** R_th = R_batt + R_kabel + R_kontakt + R_innen (Thevenin)

---

## 【4】 Kurzschluss DC (220V Industrie)

| Parameter | Eingabe | Ergebnis | Prüfung |
|-----------|---------|----------|---------|
| U | 220 V | — | — |
| R_th | 0.070 Ω | — | — |
| I_k | — | **3142.9 A** | I_k = U/R_th |
| Schaltvermögen | — | **4714.3 A** | 1.5·I_k nach IEC |
| Status | — | ✅ OK | — |

---

## 【5】 Kurzschluss AC (400V, S_k=500MVA)

| Parameter | Eingabe | Ergebnis | Prüfung |
|-----------|---------|----------|---------|
| U | 400 V | — | — |
| S_k | 500 MVA | — | — |
| Z_netz | — | **0.320 Ω** | Z = U²/S_k |
| I_k3 | — | **722 kA** | I_k3 = U/(√3·Z) |
| Status | — | ✅ OK | — |

**Formel:** Z_netz = U_n² / S_k nach IEC 60909

---

## 【6】 Selektivität B16/B10, I_k=30A

| Methode | Berechnung | Grenzwert | Status |
|---------|-----------|-----------|--------|
| Zeitstrom | t_B16(1.88×)=68.0s, t_B10(3.00×)=2.0s, Δt=66.0s | Δt ≥ 0.3s | ✅ SELEKTIV |
| Amperemetrisch | I_mag_B16=80A, I_mag_B10=50A, Ratio=1.6 | ≥ 1.3 | ✅ SELEKTIV |
| Energetisch (I²t) | I²t_up=61200A²s, I²t_down=1800A²s, Ratio=34.0 | ≥ 1.5 | ✅ SELEKTIV |

**Ergebnis:** 3/3 Methoden selektiv

---

## 【7】 Selektivität B63/C16, I_k=150A

| Methode | Berechnung | Grenzwert | Status |
|---------|-----------|-----------|--------|
| Zeitstrom | t_B63(2.38×)=38.8s, t_C16(9.38×)=0.259s, Δt=38.5s | Δt ≥ 0.3s | ✅ SELEKTIV |
| Amperemetrisch | I_mag_B63=315A, I_mag_C16=120A, Ratio=2.62 | ≥ 1.3 | ✅ SELEKTIV |
| Energetisch (I²t) | I²t_up=873036A²s, I²t_down=5822A²s, Ratio=149.96 | ≥ 1.5 | ✅ SELEKTIV |

**Ergebnis:** 3/3 Methoden selektiv

---

## 【8】 USV 3kVA/15min (Büro)

| Parameter | Eingabe | Ergebnis | Prüfung |
|-----------|---------|----------|---------|
| P | 2400 W | — | — |
| t | 0.25 h (15min) | — | — |
| U_batt | 48 V | — | — |
| η_USV | 0.93 | — | — |
| η_batt | 0.85 | — | — |
| C_batt | — | **19.8 Ah** | DIN 41773 Formel |
| Blöcke | — | **4 × 12V** | U_batt/U_block |
| Status | — | ✅ OK | — |

**Formel Batterie:** C = (P·t)/(U·η_USV·η_batt·K_T·K_Alt)

---

## 【9】 USV 10kVA/30min (Server)

| Parameter | Eingabe | Ergebnis | Prüfung |
|-----------|---------|----------|---------|
| P | 7800 W | — | — |
| t | 0.5 h (30min) | — | — |
| U_batt | 192 V | — | — |
| C_batt | — | **32.1 Ah** | DIN 41773 Formel |
| Ladezeit | — | **12.0 h** | 10%-C-Ladung |
| Empfohlen | — | **16 × 12V/40Ah** | Standardgrößen |
| Status | — | ✅ OK | — |

---

## 【10】 Maschennetz (2×220V, 25A)

| Parameter | Eingabe | Ergebnis | Prüfung |
|-----------|---------|----------|---------|
| U_Quellen | 220 V | — | — |
| I_Last | 25 A | — | — |
| R_Speiser | 0.01 Ω | — | — |
| R_Leitung | 0.05 Ω | — | — |
| I_Speiser_1 | — | **12.50 A** | symmetrisch Last/2 |
| I_Speiser_2 | — | **12.50 A** | symmetrisch Last/2 |
| U_Knoten | — | **219.25 V** | U - I·(R+R_L) |
| P_Verlust | — | **18.75 W** | Σ I²·R |
| Redundanz | — | **2.0** | n-1 |

**Formel:** Symmetrische Lastverteilung I_1 = I_2 = I_Last/2 (Kirchhoff)

---

## Zusammenfassung

| Modul | Standard | Status | Bemerkung |
|-------|----------|--------|-----------|
| Kabel DC | DIN VDE 0298-4 | ✅ OK | ΔU = 1.79V (3.72%) |
| Kabel AC | DIN VDE 0298-4 | ✅ OK | ΔU = 8.91V (2.23%) |
| Kurzschluss 48V | DIN VDE 0102 | ✅ OK | I_k = 558A |
| Kurzschluss 220V | IEC 60909 | ✅ OK | I_k = 3143A |
| Kurzschluss 400V | IEC 60909 | ✅ OK | I_k3 = 722kA |
| Selektivität B16/B10 | DIN VDE 0102 | ✅ OK | Δt = 66s, 3/3 selektiv |
| Selektivität B63/C16 | DIN VDE 0102 | ✅ OK | Δt = 38.5s, 3/3 selektiv |
| USV 3kVA | DIN 41773 | ✅ OK | 19.8Ah, 4 Blöcke |
| USV 10kVA | IEC 62040 | ✅ OK | 32.1Ah, 16 Blöcke |
| Maschennetz | Kirchhoff | ✅ OK | U_Knoten = 219.25V |

**Gesamt: 10/10 BESTANDEN (100%)**

**Datum:** 2026-05-12
**Version:** v1.1.0
**Tester:** KlausDIG (automatisiert)
