import os
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np


def save_flight_gif(t, x, z, destination):
    """Write a looping, equal-scale animation of a sampled x-z trajectory."""
    from PIL import Image, ImageDraw, ImageFont

    t, x, z = (np.asarray(values, dtype=float) for values in (t, x, z))
    if t.ndim != 1 or len(t) < 2 or x.shape != t.shape or z.shape != t.shape:
        raise ValueError("t, x und z müssen gleich lange eindimensionale Reihen mit mindestens zwei Werten sein.")
    if not all(np.isfinite(values).all() for values in (t, x, z)) or not np.all(np.diff(t) > 0):
        raise ValueError("Alle Werte müssen endlich sein und die Zeit muss streng ansteigen.")

    width, height = 580, 528
    supersample = 2
    ink, secondary, grid = '#252824', '#52564f', '#dadcd6'
    current = '#b23f2b'
    paper = Image.new('RGB', (width * supersample, height * supersample), 'white')
    drawing = ImageDraw.Draw(paper)

    # Prefer fonts with German glyphs, and retain a usable figure on minimal installs.
    fonts = {}
    for face in ('DejaVuSans.ttf', 'LiberationSans-Regular.ttf',
                 Path(os.environ.get('WINDIR', 'C:/Windows')) / 'Fonts' / 'arial.ttf'):
        try:
            fonts = {size: ImageFont.truetype(face, size * supersample) for size in (15, 17, 21)}
            break
        except OSError:
            continue
    use_ascii = not fonts
    if use_ascii:
        fonts = {size: ImageFont.load_default(size=size * supersample) for size in (15, 17, 21)}

    def pixels(point):
        return tuple(round(value * supersample) for value in point)

    def line(draw, coords, color, weight=1):
        draw.line([pixels(p) for p in coords], fill=color, width=round(weight * supersample))

    def label(draw, point, string, size, color=ink, anchor='lm'):
        if use_ascii:
            string = string.replace('ö', 'oe')
        draw.text(pixels(point), string, font=fonts[size], fill=color, anchor=anchor)

    def dot(draw, p, radius, fill, outline):
        cx, cy = p
        draw.ellipse((*pixels((cx - radius, cy - radius)), *pixels((cx + radius, cy + radius))),
                     fill=fill, outline=outline, width=round(1.2 * supersample))

    def decimal(value, digits):
        value = round(float(value), digits) or 0.0
        return f'{value:.{digits}f}'.replace('.', ',')

    x_low, x_high = min(0.0, x.min()), max(0.0, x.max())
    z_low, z_high = min(0.0, z.min()), max(0.0, z.max())
    span = max(x_high - x_low, z_high - z_low, 1.0)
    magnitude = 10 ** np.floor(np.log10(span / 5))
    step = min((1, 2, 2.5, 5, 10), key=lambda factor: abs(np.log(factor * magnitude / (span / 5)))) * magnitude
    # Avoid an entire extra interval for sub-pixel excursions below an axis.
    x_low = x_low if x_low > -span / 100 else np.floor(x_low / step) * step
    z_low = z_low if z_low > -span / 100 else np.floor(z_low / step) * step
    x_high = max(np.ceil(x_high / step) * step, x_low + step)
    z_high = max(np.ceil(z_high / step) * step, z_low + step)
    left, right, top, bottom = 63, width - 30, 94, height - 68
    scale = min((right - left) / (x_high - x_low), (bottom - top) / (z_high - z_low))
    plot_width, plot_height = (x_high - x_low) * scale, (z_high - z_low) * scale
    left += (right - left - plot_width) / 2
    top += (bottom - top - plot_height) / 2
    right, bottom = left + plot_width, top + plot_height

    def project(horizontal, altitude):
        return left + (horizontal - x_low) * scale, bottom - (altitude - z_low) * scale

    def ticks(low, high):
        return np.arange(np.ceil(low / step), np.floor(high / step) + 1) * step

    def tick_label(value):
        return f'{float(value) or 0.0:g}'.replace('.', ',')

    label(drawing, (31, 29), 'Flugzeit', 17, secondary)
    label(drawing, (width / 2 + 7, 29), 'Höhe', 17, secondary)
    line(drawing, [(30, 55), (width - 30, 55)], grid)
    label(drawing, (left, top - 17), 'Höhe z (m)', 17)
    label(drawing, ((left + right) / 2, bottom + 46), 'Horizontale Position x (m)', 17, anchor='mm')
    for value in ticks(x_low, x_high):
        px, _ = project(value, 0)
        line(drawing, [(px, top), (px, bottom)], grid, 0.6)
        line(drawing, [(px, bottom), (px, bottom + 5)], ink)
        label(drawing, (px, bottom + 17), tick_label(value), 15, secondary, 'mm')
    for value in ticks(z_low, z_high):
        _, py = project(0, value)
        line(drawing, [(left, py), (right, py)], grid, 0.6)
        line(drawing, [(left - 5, py), (left, py)], ink)
        label(drawing, (left - 9, py), tick_label(value), 15, secondary, 'rm')
    line(drawing, [(left, top), (left, bottom), (right, bottom)], ink)

    # All frames share a palette. This keeps static text stable and GIF deltas small.
    colors = [(a, a, a) for a in np.linspace(0, 244, 62).round().astype(int)] + [(255, 255, 255)]
    colors += [tuple(round(255 + amount * (end - 255)) for end in (178, 63, 43))
               for amount in np.linspace(0.08, 1, 30)]
    palette = Image.new('P', (1, 1))
    palette.putpalette([component for color in colors for component in color])

    frames = []
    projected = [project(horizontal, altitude) for horizontal, altitude in zip(x, z)]
    previous = projected[0]
    first_unseen = 1
    for now in np.linspace(t[0], t[-1], 126):
        next_index = np.searchsorted(t, now, side='right')
        altitude = np.interp(now, t, z)
        point = project(np.interp(now, t, x), altitude)
        # Preserve all measured points crossed between two displayed frames.
        line(drawing, [previous, *projected[first_unseen:next_index], point], ink, 2.3)
        first_unseen, previous = next_index, point
        frame = paper.copy()
        frame_draw = ImageDraw.Draw(frame)
        dot(frame_draw, projected[0], 3.8, 'white', ink)
        dot(frame_draw, point, 5.6, current, 'white')
        label(frame_draw, (110, 29), decimal(now, 2) + ' s', 21)
        label(frame_draw, (width / 2 + 70, 29), decimal(altitude, 1) + ' m', 21)
        reduced = frame.resize((width, height), Image.Resampling.LANCZOS)
        frames.append(reduced.quantize(palette=palette, dither=Image.Dither.NONE))

    destination = Path(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with NamedTemporaryFile(dir=destination.parent, prefix='.flight-', suffix='.gif', delete=False) as temp:
        temporary = Path(temp.name)
    try:
        frames[0].save(temporary, format='GIF', save_all=True, append_images=frames[1:],
                       duration=[360] + [60] * (len(frames) - 2) + [1250],
                       loop=0, disposal=1, optimize=False)
        temporary.replace(destination)
    finally:
        temporary.unlink(missing_ok=True)
    return destination


def animate_rocket(dt, t, x, z, vx, vz, m):
    import matplotlib.pyplot as plt
    from matplotlib.animation import FuncAnimation

    fig, (ax, ax_curve) = plt.subplots(1, 2, figsize=(10, 6))
    ax.axhline(0.0, color="black", linewidth=1.0)

    x_min = min(float(np.min(x)), 0.0) - 0.2
    x_max = max(float(np.max(x)), 0.0) + 0.2
    z_min = min(float(np.min(z)), 0.0) - 0.2
    z_max = max(float(np.max(z)), 0.0) + 0.2

    if x_max - x_min < 0.5:
        x_min = x_min - 0.5
        x_max = x_max + 0.5

    if z_max - z_min < 0.5:
        z_min = z_min - 0.5
        z_max = z_max + 0.5

    ax.set_xlim(x_min, x_max)
    ax.set_ylim(z_min, z_max)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel("x")
    ax.set_ylabel("z")
    ax.set_title("Rocket 2D")
    ax.grid(True, alpha=0.3)

    rocket, = ax.plot([x[0]], [z[0]], marker="o", markersize=10, color="red")
    trail, = ax.plot([], [], color="red", linewidth=1.0, alpha=0.6)
    info = ax.text(
        0.05,
        0.95,
        "",
        transform=ax.transAxes,
        va="top",
        fontsize=10,
        family="monospace",
    )

    ax_curve.plot(t, z, color="steelblue", linewidth=1.2, label="z(t)")
    marker, = ax_curve.plot([t[0]], [z[0]], marker="o", color="orange", markersize=6)
    ax_curve.set_xlabel("t")
    ax_curve.set_ylabel("z")
    ax_curve.set_title("Height vs Time")
    ax_curve.grid(True)
    ax_curve.legend()

    frame_step = max(1, int(0.02 / dt))
    frame_indices = np.arange(0, len(t), frame_step)

    def update(frame_i):
        i = int(frame_indices[frame_i])
        rocket.set_data([x[i]], [z[i]])
        trail.set_data(x[: i + 1], z[: i + 1])
        marker.set_data([t[i]], [z[i]])
        info.set_text(
            f"t={t[i]:5.2f} s\nvx={vx[i]:6.2f}\nvz={vz[i]:6.2f}\nm={m[i]:6.3f}"
        )
        return rocket, trail, info, marker

    ani = FuncAnimation(
        fig,
        update,
        frames=len(frame_indices),
        interval=20,
        blit=True,
        repeat=False,
    )
    plt.show()
    return ani
