# Einen Flug lesen, einen Rechenschritt verstehen

Schau dir die [Fluganimation](media/flugbahn.gif) einmal ganz an. Beim zweiten Durchlauf achte auf den höchsten Punkt. Wandert die Markierung dort noch nach rechts? An dieser kleinen Beobachtung lässt sich schon verstehen, was die zweite Dimension im Modell ausmacht.

## 1. Vom Bild zu den Zahlen

Im Bild ist `x` die horizontale Position und `z` die Höhe. Beide Achsen sind in Metern beschriftet. Die Spur verbindet Positionen, an denen die Rakete zuvor war. Das GIF spielt knapp 27 Sekunden simulierte Flugzeit in rund neun Sekunden ab. Für die Übungen mit Python brauchst du die Pakete aus der [Startanleitung](README.md#selbst-ausprobieren).

Die Zeit kommt in zwei verschiedenen Rollen vor. Im Flugbild bedeutet eine Bewegung nach rechts, dass `x` zunimmt. Wenn du dagegen die Höhe über der **Zeit** zeichnest, bedeutet rechts einfach „später“. Die Steigung dieser zweiten Kurve gibt die vertikale Geschwindigkeit `vz` an. In der ersten Kurve hängt die Steigung zusätzlich davon ab, wie schnell sich der Körper seitwärts bewegt.

**Skizziere die Höhe über der Zeit** mit drei Punkten aus dem Standardlauf.

| Zeit in s | Höhe in m | Masse in kg |
| ---: | ---: | ---: |
| 8,0 | 307,9 | 6,20 |
| 14,7 (nahe dem höchsten Punkt) | 553,3 | 6,20 |
| 16,0 | 545,4 | 6,20 |

Was fällt dir an den letzten beiden Spalten auf? Nach 8 s bleibt die Masse gleich. Die Höhe nimmt zunächst weiter zu, weil die vertikale Geschwindigkeit zu diesem Zeitpunkt noch positiv ist. Später ist `vz` negativ und die Höhe nimmt ab. Die Masse allein verrät also wenig über die Flugrichtung.

## 2. Was im Code passiert

Ein guter Einstieg sind die zwei Zeilen `dxdt = vx` und `dzdt = vz` in der Funktion `rhs`. Sie bedeuten, dass Geschwindigkeit die Änderung der Position pro Sekunde ist. Rechne einen Schritt auf Papier. Ein Spielzeugauto ist an der Marke 2 m und fährt mit konstanten 3 m/s weiter. Wo ist es 0,1 s später? [2D-Code](2d_sim/main.py)

Vergleiche deine Rechnung mit der Funktion `euler_step`. Führe diese Befehle im Terminal aus und starte dabei im Projektordner.

```sh
cd 1d_sim
python -c "from main import euler_step; print(euler_step(2, 3, 0.1))"
cd ..
```

Die Ausgabe `2.3` entspricht 2 m + 3 m/s × 0,1 s. Für diesen Schritt benutzt Euler die Änderungsrate am Anfang. Der 1D-Solver führt dieselbe Rechnung getrennt für Höhe, vertikale Geschwindigkeit und Masse aus. [1D-Code](1d_sim/main.py)

Im 2D-Modell stehen fünf Zahlen in einer festen Reihenfolge für den Zustand `(x, z, vx, vz, m)`. Die Funktion `rhs(t, y)` berechnet, wie schnell sich diese fünf Werte gerade ändern. `rk4_step` fragt `rhs` viermal ab, am Anfang, zweimal mit unterschiedlichen Schätzungen für die Mitte und einmal am Ende des Schritts. Die beiden mittleren Schätzungen erhalten doppeltes Gewicht. Daraus entsteht der nächste Zustand. Das Verfahren heißt Runge–Kutta vierter Ordnung, kurz RK4. [2D-Code](2d_sim/main.py)

Der `solver` wiederholt das mit einem Zeitschritt von 0,005 s. Eine simulierte Sekunde enthält also 200 Rechenschritte. Das GIF zeigt eine Auswahl der Zustände. Für einen genauen Zahlenvergleich kannst du direkt die vom Solver gelieferten Reihen lesen.

## 3. Den höchsten Punkt selbst finden

Wechsle im Terminal mit `cd 2d_sim` in den Modellordner und starte dort `python`. Diese Zeilen berechnen den Standardlauf und suchen den Eintrag mit der größten gespeicherten Höhe.

```python
import numpy as np
import main as sim

t, x, z, vx, vz, m = sim.solver(
    sim.x0, sim.z0, sim.vx0, sim.vz0, sim.m0, sim.dt, sim.max_iter
)
i = np.argmax(z)
print(f"Zeit {t[i]:.1f} s, Höhe {z[i]:.1f} m")
print(f"Horizontal {vx[i]:.2f} m/s, vertikal {vz[i]:.2f} m/s")
```

**Lies erst die erste Ausgabe.** Welche der beiden Geschwindigkeiten müsste jetzt ungefähr null sein? Im Standardlauf liegt der höchste gespeicherte Punkt bei rund 14,7 s und 553,3 m. Die zweite Ausgabe zeigt horizontal etwa 23,46 m/s und vertikal etwa −0,01 m/s. Der Körper bewegt sich also am höchsten Punkt weiter nach rechts. Der tatsächliche Vorzeichenwechsel von `vz` im kontinuierlichen Modell kann zwischen zwei gespeicherten Zeitpunkten liegen.

**Wie schnell ist der Körper insgesamt?** In Python ergibt `np.hypot(vx[i], vz[i])` rund 23,46 m/s über Grund. Die Richtung geht beim Bilden dieses Betrags verloren. Wer Aufstieg und Abstieg unterscheiden will, braucht das Vorzeichen von `vz`.

## Ausbauplan

1. **Einheiten einmal von Hand prüfen.** Schreibe neben `x, z` die Einheit m, neben `vx, vz` die Einheit m/s und neben `m` die Einheit kg. Das Produkt `dzdt * dt` hat die Einheit m, weil m/s mal s wieder m ergibt. Auf diese Weise entdeckt man etwa einen versehentlich in Millisekunden eingesetzten Zeitschritt.
2. **Fehler mit einem Test abfangen.** Der vorhandene 1D-Test `test_solver_outputs_are_finite_and_time_monotonic` kontrolliert unter anderem die Reihenfolge der Zeitwerte. Prüfe im nächsten 2D-Test, ob alle sechs Ergebnisreihen gleich lang sind und jeder Zeitpunkt größer ist als der vorherige. So fällt ein vergessener Eintrag am Ende sofort auf. [Vorhandene 1D-Tests](1d_sim/tests/test_model.py)
3. **Das Rechenverfahren an etwas Bekanntem prüfen.** Stell dir einen leeren Messbecher vor. In Minute 0 fließen 0 Liter pro Minute hinein, in Minute 1 sind es 2 und in Minute 2 sind es 4. Die Zuflussrate steigt dazwischen geradlinig. Nach zwei Minuten müssen genau 4 Liter im Becher sein. Die Fläche unter der Zuflusskurve ist ein Dreieck mit Grundseite 2 und Höhe 4. Euler mit zwei Schritten von je einer Minute zählt nur 0 + 2 = 2 Liter. Mit vier halben Minuten erhältst du 0,5 × (0 + 1 + 2 + 3) = 3 Liter. Für diesen einfachen Verlauf ergibt die RK4-Gewichtung schon mit großen Schritten die exakten 4 Liter. Hier kennst du die Lösung unabhängig vom Programm.
4. **Ergebnis und Unsicherheit zusammen angeben.** „Rund 553 m im Standardlauf“ ist eine Aussage über diese Modellrechnung. Ein Messwert bräuchte zusätzlich eine Beobachtung mit einem Instrument und Angaben zu dessen Genauigkeit. Halte bei einem Zahlenvergleich fest, was sich durch einen anderen Zeitschritt ändert und welche Modellannahmen dabei gleich bleiben. Das Projekt enthält dafür bereits einen Vergleich verschiedener Zeitschritte im 1D-Modell. [Zeitschritttests](1d_sim/tests/test_numerics.py)
5. **Bei jedem Commit automatisch testen.** Der Solver lässt sich schon heute direkt aufrufen. Prüfe die Zahlen getrennt vom GIF-Export und lass beide Prüfungen bei jedem Commit laufen, etwa mit GitHub Actions. Probiere auf einem Testbranch einen absichtlichen Fehler aus. Die passende Prüfung muss fehlschlagen und nach der Korrektur wieder bestehen.
6. **Eine Version zur unabhängigen Prüfung freigeben.** Halte Python- und Paketversionen, Startbefehl und den Zweck des Modells fest. Als erste Freigabe genügt der dokumentierte 2D-Standardlauf mit seinen Annahmen und Grenzen. Bitte eine zweite Person, ihn in einer frischen Umgebung auszuführen, das GIF zu öffnen und die Zahlen aus Abschnitt 3 zu prüfen. Wenn das gelingt, markiere genau diesen geprüften Commit mit einem Git-Tag und verlinke die Anleitung in der Versionsbeschreibung. So lässt sich später derselbe Stand wiederfinden.
