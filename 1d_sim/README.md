# Rocket1D - Erste Raketen-Flugsimulation (1D)

Diese README beschreibt die erste sinnvolle Minimalversion eines Raketen-Simulators in **einer Dimension (vertikal)**.

Ziel:
**Hoehe, Geschwindigkeit und Masse ueber die Zeit simulieren**, um den dynamischen Kern des Raketenflugs zu verstehen.

## Dokumentation

Fuer eine ausfuehrliche technische Zusammenfassung (Projektstand, Modellgleichungen, Aenderungen, Validierung, Test-Coverage) siehe:

- [doc.md](/Users/aminechabane/Desktop/rocket1D/doc.md)

## 1) Projektumfang (Version 1)

Dieses erste Modell ist absichtlich einfach:

- Nur vertikale Bewegung (`up/down`)
- Keine Rotation, kein Kippen, keine 3D-Bahn
- Keine Seitenwinde
- Fokus auf Grundphysik: Schub, Gewicht, Massenabnahme

Das ist **kein vollstaendiges Flugprogramm**, sondern ein robustes Lern- und Kernmodell.

## 2) Physikalische Groessen

### Zustandsgroessen (zeitabhaengig)

- `t`: Zeit
- `h(t)`: Hoehe
- `v(t)`: Geschwindigkeit
- `m(t)`: Masse

### Abgeleitet

- `a(t)`: Beschleunigung

### Eingabeparameter (zunaechst konstant)

- `m0`: Anfangsmasse
- `m_dry`: Trockenmasse
- `T`: Schub waehrend Brennphase
- `t_b`: Brenndauer
- `g`: Erdbeschleunigung
- `rho`: Luftdichte (fuer Version 2)
- `C_D`: Widerstandsbeiwert (fuer Version 2)
- `A`: Stirnflaeche (fuer Version 2)
- `dt`: Zeitschritt

## 3) Grundgleichungen

### Newton

`F = m * a`

### Kraeftebilanz (vertikal)

`F_ges = T - m*g - D`

### Luftwiderstand (Version 2)

`D = 0.5 * rho * C_D * A * v * |v|`

### Beschleunigung

`a = (T - m*g - D) / m`

## 4) Raketen-spezifisch: Massenabnahme

Waehrend der Brennphase:

- `m_dot = (m0 - m_dry) / t_b`
- `m(t) = m0 - m_dot * t`

Nach Brennschluss:

- `m(t) = m_dry`

Schubmodell:

- fuer `t <= t_b`: `T > 0` (konstant in Version 1)
- fuer `t > t_b`: `T = 0`

## 5) Flugphasen im Modell

1. **Brennphase**  
   Schub aktiv, Masse sinkt, Rakete beschleunigt aufwaerts.
2. **Ballistischer Aufstieg**  
   Kein Schub, Rakete steigt mit Restgeschwindigkeit weiter, bis `v = 0`.
3. **Fallphase**  
   Rakete faellt zurueck, Luftwiderstand bremst (ab Version 2).

## 6) Numerische Integration (Euler)

Rechnung in kleinen Zeitschritten:

1. `m` bestimmen
2. `T` bestimmen
3. `D` berechnen
4. `a` berechnen
5. `v` aktualisieren
6. `h` aktualisieren
7. Werte speichern

Euler-Update:

- `v_new = v_old + a * dt`
- `h_new = h_old + v_new * dt`

## 7) Projektbausteine

- **A Parameterblock**: Alle Konstanten und Startwerte
- **B Simulationskern**: Zeitschleife mit Dynamik
- **C Datenspeicherung**: Arrays fuer `t, h, v, a, m`
- **D Auswertung**: `h_max`, `v_max`, Flugzeit, `v` bei Brennschluss
- **E Visualisierung**: Kurven `h(t), v(t), a(t), m(t)`

## 8) Software-Stack

Fuer den Start ausreichend:

- Python 3
- NumPy
- Matplotlib

Installation:

```bash
pip install numpy matplotlib
```

## 9) Realismus: Was das Modell kann und was nicht

### Kann (physikalischer Kern)

- Schubwirkung
- Gravitation
- Massenabnahme
- (ab Version 2) Luftwiderstand

### Kann noch nicht (Ingenieurdetails)

- Kippbewegung und Rotationen
- 2D/3D Flugbahn
- Windmodell
- variable Aerodynamik
- reale Triebwerkskurven
- Struktur-/Elastizitaetseffekte
- Regelung/GNC

Fazit:

- Zum Lernen: sehr gut
- Fuer erste Abschaetzungen: gut
- Fuer praezise Flugvorhersagen: noch nicht ausreichend

## 10) Empfohlene Entwicklungsreihenfolge

### Version 1 (jetzt)

- Vertikalbewegung
- konstantes `g`
- konstanter Schub waehrend Brennphase
- lineare Massenabnahme
- optional zuerst **ohne** Luftwiderstand

### Version 2

- Luftwiderstand hinzufuegen

### Version 3

- Vollstaendige Diagramme und Kennwerte

### Version 4

- Einfache Animation

Danach:

- hoehenabhaengige Luftdichte
- reale Schubkurve
- 2D/3D Erweiterung
- Lage- und Regelungsdynamik
- Monte-Carlo-Analysen

## 11) Konkrete Definition der Minimalversion

Diese Fragen muessen fuer den Start festgelegt sein:

- Welche Parameterwerte (`m0, m_dry, T, t_b, dt, g`)?
- Wird Luftwiderstand in Version 1 schon aktiviert?
- Wann endet die Simulation (z. B. bei Bodenkontakt `h <= 0` nach Start)?
- Welche Kennwerte werden am Ende immer ausgegeben?

## 12) Start-Checkliste

- [ ] Parameterblock erstellen
- [ ] Euler-Zeitschleife implementieren
- [ ] Masse- und Schubumschaltung korrekt umsetzen
- [ ] Daten speichern (`t, h, v, a, m`)
- [ ] Kennwerte ausgeben (`h_max, v_max, flight_time`)
- [ ] Diagramme erzeugen

---

Kernidee in einem Satz:
**Mit der vertikalen Kraftbilanz plus Massenabnahme und Zeitschrittintegration baust du dein erstes echtes Raketen-Simulationsprojekt.**
