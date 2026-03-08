# Rocket1D - Projektbewertung und Aenderungsdokumentation

Stand: Working Tree vom 2026-03-08 (lokal, nicht committed)

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
- `rho = 1.225` ist noch als Konstante vorhanden, wird aber nicht mehr direkt genutzt.

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

## 3.1 [README.md](/Users/aminechabane/Desktop/rocket1D/README.md)

- Von 1 Zeile (`# flightSim-lab`) auf vollstaendige Projektdoku erweitert.
- Inhalte ergaenzt:
  - Ziel und Scope des 1D-Modells
  - Zustandsgroessen und Parameter
  - Grundgleichungen
  - Flugphasen
  - Euler-Integration
  - Entwicklungs-Roadmap und Checkliste

## 3.2 [main.py](/Users/aminechabane/Desktop/rocket1D/main.py)

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

## 3.3 [animation.py](/Users/aminechabane/Desktop/rocket1D/animation.py) (neu)

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
