import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np

def animate_rocket(dt, t, z, v, m):
    fig, (ax, ax_curve) = plt.subplots(1, 2, figsize=(10, 6))
    ax.axhline(0.0, color="black", linewidth=1.0)
    ax.set_xlim(-1.0, 1.0)

    z_min = min(float(np.min(z)), 0.0) - 0.2
    z_max = max(float(np.max(z)), 0.0) + 0.2
    ax.set_ylim(z_min, z_max)
    ax.set_xticks([])
    ax.set_ylabel("z")
    ax.set_title("Rocket")

    rocket, = ax.plot([0.0], [z[0]], marker="o", markersize=10, color="red")
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
        rocket.set_data([0.0], [z[i]])
        trail.set_data(np.zeros(i + 1), z[: i + 1])
        marker.set_data([t[i]], [z[i]])
        info.set_text(f"t={t[i]:5.2f} s\nv={v[i]:6.2f}\nm={m[i]:6.3f}")
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