# FlightSim Lab

Ein interaktives Fluglabor für einen simulierten Raketenflug in der x-z-Ebene. Spiele den Flug ab oder springe zum Scheitelpunkt, um seine Höhe, horizontale Position, Geschwindigkeit und Masse zum selben Zeitpunkt abzulesen.

## 2D-Ansicht öffnen

Lade das Repository herunter, entpacke es und öffne [index.html](index.html) im Browser. Die mitgelieferte Messreihe lässt sich vollständig offline auswerten.

- **Flugbahn** zeigt die zurückgelegte Strecke durchgezogen und den weiteren Verlauf gestrichelt. Mit **1:1** entspricht ein Meter auf beiden Achsen derselben Bildschirmlänge.
- **Abspielen** startet die Wiedergabe. Die Zeitleiste und die Einträge unter **Flugereignisse** halten den Flug an der gewählten Stelle an.
- **Zeitverlauf** zeigt Höhe, Geschwindigkeit über Grund oder Masse. Klicke oder ziehe im Diagramm, um die zugehörige Position in der Flugbahn zu sehen.
- **Tastatur** – Leertaste für Start und Pause, Pfeile links und rechts für Schritte von 0,25 s, mit Umschalt für 1 s. Pos1 und Ende springen zum Anfang oder Ende. Diese Kürzel funktionieren auf der Seite und auf der fokussierten Zeitleiste.

## Flug neu berechnen

Für den Python-Solver benötigst du Python 3 und NumPy. Führe im Repository-Stamm diese Befehle aus.

```sh
python -m pip install numpy
python 2d_sim/main.py
```

Der Solver berechnet den Flug, aktualisiert die Messreihe und öffnet die Browseransicht. Für einen reinen Datenexport genügt `python 2d_sim/main.py --export`. Für die klassische Matplotlib-Animation installiere zusätzlich `matplotlib` und starte `python 2d_sim/main.py --matplotlib`.

## Was die Messwerte zeigen

Das vorhandene Python-Modell integriert die horizontale und vertikale Bewegung mit Runge-Kutta 4. Der Standardlauf verwendet einen Zeitschritt von 5 ms. Die Browseransicht lädt ungefähr alle 50 ms einen Stützpunkt sowie die Messpunkte an Brennschluss, Scheitelpunkt und Bodenkontakt. Zwischen den Stützpunkten interpoliert sie die Anzeige linear.

| Ereignis im mitgelieferten Flug | Flugzeit | Höhe |
| --- | ---: | ---: |
| Scheitelpunkt | 14,73 s | 553,31 m |
| Bodenkontakt | 26,53 s | 0,00 m |

Die Geschwindigkeit beim Bodenkontakt ist der Wert unmittelbar beim Erreichen des Bodens. Das Modell endet dort. Während des Schubaufbaus am Start liegt die berechnete Höhe kurz rund 3 cm unter dem Bodenniveau.

Der [2D-Modellcode](2d_sim/main.py) enthält die Bewegungsgleichungen. Das frühere [1D-Modell](1d_sim/README.md) und seine [technische Beschreibung](doc.md) sind ebenfalls im Repository verfügbar.
