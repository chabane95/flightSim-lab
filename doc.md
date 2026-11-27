# Notizen zur ersten 1D-Version und zum Übergang auf 2D

Diese Notizen halten den Zwischenstand vom 13. März 2026 fest. Den heutigen Einstieg mit GIF, Übungen und Ausbauplan findest du im [Lernskript](LERNSKRIPT.md).

## 0) Ausfuehrliche Gesamtzusammenfassung

Dieses Projekt ist von einem Minimal-Stub zu einem untersuchbaren 1D-Raketenmodell gewachsen.
Der aktuelle Stand ist nicht nur "simulierbar", sondern bereits "analysierbar":

- Das Modell bildet die zentrale 1D-Dynamik konsistent ab:
  - Massenabnahme mit Brennphasenprofil
  - Schub aus Impuls- und Druckanteil
  - Gravitation
  - Drag mit hoehenabhaengiger Dichte
- Die Numerik ist in der aktuellen Parametrisierung stabil:
  - keine negativen Massen
  - keine NaN/Inf-Zustaende
  - sauberes Stop-Kriterium beim Bodenrueckkehrereignis
- Die Visualisierung zeigt sowohl Bewegung als auch Verlauf:
  - animierte Rakete (Position + Trail)
  - synchronisierte Hoehenkurve mit Marker
- Die Testabdeckung geht ueber reine Unit-Tests hinaus:
  - Physik-Bausteine (mdot, Atmosphaere, Schub)
  - Solver-Robustheit
  - Kennzahlen/Plausibilitaet
  - Zeitschritt-Konvergenz
  - Parametersensitivitaet

Damit ist der Projektstatus fachlich sauber zwischen "Lernmodell" und "fruehes Ingenieurmodell" einzuordnen:

- Sehr gut fuer physikalisches Verstaendnis, Parametereinfluss und Numerikverhalten
- Noch nicht ausreichend fuer hochpraezise Flugvorhersagen ohne Datenkalibrierung und 2D/3D-Erweiterung

### 0.1 Aktueller Simulationsworkflow

Der Ablauf pro Zeitschritt in `main.py` ist:

1. Zustand lesen: `t, z, v, m`
2. Ableitungen berechnen:
   - `z_dot = v`
   - `m_dot = mdot(t, m)`
   - `v_dot = vdot(v, m, t, z)`
3. Euler-Update fuer `z, v, m`
4. Massenbegrenzung auf `m_dry`
5. Ground-Impact-Stop pruefen
6. Zeitreihe speichern und fortsetzen

Diese Struktur ist bewusst einfach gehalten (didaktisch), aber bereits robust genug fuer Studien.

### 0.2 Physikalische Bedeutung der wichtigsten Modellteile

- `mdot(t,m)`:
  - Ramp-up -> Plateau -> Ramp-down
  - stoppt bei `m <= m_dry`
  - verhindert unphysikalische Restverbrennung
- `rho_atm(z)` und `p_atm(z)`:
  - exponentielles Atmosphaerenmodell
  - reduziert Drag und Umgebungsdruck mit steigender Hoehe
- `thrust(t,m,z)`:
  - kombiniert Impulsschub und Druckschub
  - setzt Schub auf 0, wenn `mdot == 0`
- `vdot(v,m,t,z)`:
  - aggregiert Schub, Drag, Gewicht in einer Kraftbilanz
  - liefert direkte dynamische Beschleunigung

### 0.3 Numerische Bewertung

- Integrator: explizites Euler-Verfahren
- Starke Seite:
  - transparent, gut nachvollziehbar, schnell fuer Studien
- Grenze:
  - geringere Genauigkeit als RK4 bei groberen `dt`
- Bereits validiert:
  - `dt`-Verfeinerung zeigt stabile Konvergenztendenz in den Hauptkennwerten

### 0.4 Ergebnisbild (aktueller Parametersatz)

Typisches Verhalten im aktuellen Setup:

- Lift-off mit moderater Anfangsdynamik
- deutlicher Aufstieg bis in den Bereich mehrerer hundert Meter
- Brennschluss mit anschliessender ballistischer Phase
- Rueckfall unter Drag-Bremsung bis Bodenkontakt

Die Kenngroessen liegen im plausiblen Bereich fuer den gesetzten Modellrahmen.

### 0.5 Test-Coverage-Matrix

Die folgende Matrix beantwortet explizit die Frage "Ist das diskutierte Testset abgedeckt?":

- Basisphysik:
  - abgedeckt in `tests/test_model.py`
  - Inhalte: `mdot`, `rho_atm`, `p_atm`, `thrust`, Solver-Finitheit
- Plausibilitaet und Analysegroessen:
  - abgedeckt in `tests/test_analysis.py`
  - Inhalte: `z_max`, `v_max`, `t_burnout`, `z_burnout`, `v_burnout`, `t_impact`, `a_max`, `q_max`
- Post-burnout-Verhalten:
  - abgedeckt in `tests/test_analysis.py`
  - Inhalte: `T=0` nach Burnout, Masse konstant nach Burnout, Apogaeumsverhalten
- Numerik/Zeitschrittstudie:
  - abgedeckt in `tests/test_numerics.py`
  - Inhalte: Vergleich `dt`-Stufen, Stabilitaet und Konvergenzrichtung
- Sensitivitaet:
  - abgedeckt in `tests/test_sensitivity.py`
  - Inhalte: Trends fuer `m_dry`, `beta`, `u_e`, `A`, `Cd`
- Visuelle Konsistenz:
  - nicht automatisiert
  - derzeit nur manuelle Pruefung der Animation/Plots

### 0.6 Reproduzierbarkeit

Empfohlener reproduzierbarer Ablauf:

1. Virtuelle Umgebung aktivieren (oder projektlokal nutzen)
2. Testlauf:
   - `./.venv/bin/python -m pytest -q`
3. Direktlauf einzelner Testdateien ist ebenfalls vorbereitet:
   - `python3.11 tests/test_analysis.py`
   - `python3.11 tests/test_numerics.py`
   - `python3.11 tests/test_sensitivity.py`

### 0.7 Technischer Reifegrad

Aktueller Reifegrad:

- "stabiler Forschungs-/Lernprototyp" fuer 1D

Noch offen fuer den naechsten Reifegrad:

- strukturierte Ergebnisexports (CSV fuer Runs + Trajektorien)
- Trennung von Modellkern und Integrator (z. B. RK4-Option)
- automatisierte Reports (z. B. junitxml + Kennzahlenreport)
- spaetere 2D-Erweiterung nach Abschluss der 1D-Validierung

## 1) Kurzbewertung

Gesamtbewertung: **8.1 / 10**

Positiv:

- Klarer 1D-Kern (Masse, Schub, Gravitation, Drag) ist sauber umgesetzt.
- Numerische Stabilitaet verbessert (keine negative Masse, Stop bei Bodenkontakt).
- Realismus deutlich erhoeht durch hoehenabhaengige Luftdichte und erweitertes Schubmodell.
- Visualisierung von statischem Plot auf Animation mit Live-Infos verbessert.

Risiken / offene Punkte:

- `mdot`-Ramp startet bei $t=0$ mit Nullschub, dadurch kann es am Start kurz zu negativem $a$ kommen.
- Aktuell wird nur `z, v, m` gespeichert; `a` und `T` fehlen als direkte Output-Zeitreihen.
- Keine automatischen Tests oder Parameter-Validierung im Runtime-Pfad.
- Fuer 2D fehlen noch automatisierte Regressionstests (`2d_sim` ist aktuell manuell validiert).

## 2) Aktuelles physikalisches Modell (LaTeX)

### 2.1 Massenstrom (mit Ramp-up / Ramp-down)

$$
\dot m(t,m)=
\begin{cases}
0, & m \le m_{\mathrm{dry}} \\
0, & t<0 \ \text{oder}\ t\ge t_b \\
-\beta \frac{t}{t_{\mathrm{rise}}}, & 0 \le t < t_{\mathrm{rise}} \\
-\beta, & t_{\mathrm{rise}} \le t < t_b-t_{\mathrm{fall}} \\
-\beta \frac{t_b-t}{t_{\mathrm{fall}}}, & t_b-t_{\mathrm{fall}} \le t < t_b
\end{cases}
$$

### 2.2 Atmosphaere

$$
\rho(z) = \rho_0 \exp\left(-\frac{\max(z,0)}{H}\right)
$$

$$
p_{\mathrm{atm}}(z) = p_0 \exp\left(-\frac{\max(z,0)}{H}\right)
$$

### 2.3 Schubmodell

$$
T(t,m,z)= -u_e \dot m(t,m) + \left(p_e - p_{\mathrm{atm}}(z)\right)A_e
$$

### 2.4 Bewegungsgleichung

Mit
$$
D = -\frac{1}{2} C_D \rho(z) A\, v|v|
$$
gilt
$$
\dot v = \frac{T + D - mg}{m}, \qquad \dot z = v
$$

Numerik:
$$
x_{k+1}=x_k+\Delta t\,\dot x_k
$$

## 3) Dokumentation aller durchgefuehrten Aenderungen

## 3.1 [README.md](1d_sim/README.md)

- Von 1 Zeile (`# flightSim-lab`) auf vollstaendige Projektdoku erweitert.
- Inhalte ergaenzt:
  - Ziel und Scope des 1D-Modells
  - Zustandsgroessen und Parameter
  - Grundgleichungen
  - Flugphasen
  - Euler-Integration
  - Entwicklungs-Roadmap und Checkliste

## 3.2 [main.py](1d_sim/main.py)

Von Platzhalter auf vollstaendigen Simulationscode erweitert.

Wesentliche Aenderungen:

- Parameterblock fuer realistischere Basiswerte eingefuehrt:
  - `A=0.02`, `rho0=1.225`, `Cd=0.6`, `u_e=250.0`
  - `beta=0.5`, `t_b=8.0`, `dt=0.005`, `max_iter=24000`
  - `m0=10.0`, `m_dry=6.0`, `z0=0.0`, `v0=0.0`
- `mdot(t,m)` von konstantem Profil auf rampenfoermiges Profil erweitert.
- Hoehenabhaengige Dichte `rho_atm(z)` eingefuehrt.
- Atmosphaerendruck `p_atm(z)` eingefuehrt.
- Schubfunktion von reinem Impulsschub auf
  - Impulsschub $(-u_e\dot m)$ plus
  - Druckschub $((p_e-p_{\mathrm{atm}})A_e)$
  erweitert.
- `vdot(...)` auf Signatur `vdot(v,m,t,z)` erweitert (kopplung an Hoehe).
- Massebegrenzung auf `m_dry` statt numerischer Minimalschwelle.
- Stop-Kriterium bei Rueckkehr zum Boden beibehalten:
  - `z <= 0`, `t > 0.5`, `v < 0`.
- Animation aus `main.py` ausgelagert und per Modulaufruf angebunden.

## 3.3 [animation.py](1d_sim/animation.py) (neu)

Neue Datei fuer Visualisierung:

- Funktion `animate_rocket(dt, t, z, v, m)` erstellt.
- Zwei-Panel-Layout:
  - Linkes Panel: Raketenposition + Trail
  - Rechtes Panel: `z(t)`-Kurve mit laufendem Marker
- Live-Overlay fuer `t`, `v`, `m`.
- Frame-Steuerung ueber `frame_step = max(1, int(0.02/dt))`.
- `FuncAnimation(..., blit=True, repeat=False)`.

## 4) Quantitative Plausibilitaet (Sanity Check)

Aus dem aktuellen Modell (gleiche Gleichungen/Parameter) ergibt sich:

- Flugzeit bis Bodenkontakt: $\approx 26.955\ \mathrm{s}$
- Apogee: $\approx 575.02\ \mathrm{m}$ bei $t \approx 14.92\ \mathrm{s}$
- Maximalgeschwindigkeit: $\approx 83.58\ \mathrm{m/s}$ bei $t \approx 7.825\ \mathrm{s}$
- Endmasse / Minimalmasse: $\approx 6.20\ \mathrm{kg}$
- Schubbereich: $0$ bis $\approx 190.69\ \mathrm{N}$

Interpretation:

- Das System ist numerisch stabil und physikalisch plausibel.
- Wegen Ramp-up ist $T(0)=0$, deshalb kann am Start kurz negative Beschleunigung auftreten.
- Mit dem aktuellen Massenstromprofil werden ca. $3.8\ \mathrm{kg}$ Treibstoff verbraucht (nicht volle $4.0\ \mathrm{kg}$).

## 5) Naechste sinnvolle Verbesserungen

- Optionalen Launch-Rail-Abschnitt modellieren (oder nicht-null Startschub).
- `a(t)` und `T(t)` explizit speichern/plotten.
- Parameter in eine Konfigurationsdatei auslagern.
- Unit-Tests fuer `mdot`, `thrust`, `rho_atm`, Stop-Kriterium.

## 6) Wichtige neue Aenderungen (2D-Ausbau, 2026-03-13)

## 6.1 [2d_sim/main.py](2d_sim/main.py)

- Von 1D-artigem Entwurf auf echten 2D-Zustandsvektor umgestellt:
  - `y = (x, z, vx, vz, m)`
  - zentrale rechte Seite `rhs(t, y)`
- Kritischen Solver-Fehler entfernt:
  - kein falscher `vdot(...)`-Pfad mehr
  - Dynamik wird nur noch ueber 2D-Zustandsableitungen gerechnet
- Integrator auf RK4 umgestellt:
  - `rk4_step(...)` mit `k1..k4`
  - Euler-Schritt nicht mehr als aktiver Integrator
- Schubstruktur bereinigt:
  - `thrust_from_mdot(m_dot, z)` eingefuehrt
  - `mdot` wird in `rhs` einmal berechnet und direkt weitergereicht
- Winkelbehandlung korrigiert:
  - `theta` als Grad von der Vertikalen
  - Umrechnung auf `theta_rad = np.deg2rad(theta)`
- Bodenkontakt numerisch sauber gemacht:
  - Ground-Crossing wird per linearer Interpolation auf `z = 0` gesetzt
  - finaler Impact-Zustand wird explizit in den Zeitreihen gespeichert
- Rueckgabe erweitert fuer 2D:
  - `t, x, z, vx, vz, m`
- Unnoetige Konstante `rho` entfernt (es wird `rho_atm(z)` genutzt)

## 6.2 [2d_sim/animation.py](2d_sim/animation.py) (neu)

- Animation aus `main.py` in eigenes Modul ausgelagert (analog 1D-Stil)
- Neue Funktion:
  - `animate_rocket(dt, t, x, z, vx, vz, m)`
- Visualisierung:
  - linkes Panel: 2D-Trajektorie (Rocket + Trail)
  - rechtes Panel: Hoehe ueber Zeit `z(t)` mit laufendem Marker
  - Live-Overlay fuer `t`, `vx`, `vz`, `m`
- Darstellung verbessert:
  - `ax.set_aspect("equal", adjustable="box")` fuer unverzerrte Bahn
- Frame-Logik analog zum 1D-Projekt:
  - `frame_step = max(1, int(0.02 / dt))`
  - `FuncAnimation(..., interval=20, blit=True, repeat=False)`

## 6.3 Aufrufstruktur (wie im 1D-Projekt)

- `main()` in `2d_sim/main.py` importiert das Modul lokal:
  - `import animation`
- Simulation + Animation werden direkt gekoppelt:
  - `t, x, z, vx, vz, m = solver(...)`
  - `_ani = animation.animate_rocket(dt, t, x, z, vx, vz, m)`
