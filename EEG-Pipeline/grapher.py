import time
from collections import deque

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pylsl import StreamInlet, resolve_byprop


# ===== Config =====
WINDOW_SEC = 10.0          # show last 10 seconds
UPDATE_MS = 50             # redraw every 50 ms (~20 FPS)
ELECTRODES = ["TP9", "AF7", "AF8", "TP10"]
STREAM_TYPE = "EEG"
# ==================


def connect_inlet():
    print("Looking for LSL EEG stream...")
    streams = resolve_byprop("type", STREAM_TYPE, timeout=10)
    if not streams:
        raise RuntimeError(
            "No LSL EEG stream found.\n"
            "Make sure BlueMuse is streaming (Start Streaming) and try again."
        )
    inlet = StreamInlet(streams[0], max_buflen=30)
    info = inlet.info()
    print("Connected to:", info.name())
    print("Channels:", info.channel_count())
    print("Nominal srate:", info.nominal_srate())
    return inlet, info


def main():
    inlet, info = connect_inlet()
    n_ch = info.channel_count()
    if n_ch < 4:
        raise RuntimeError(f"Expected at least 4 EEG channels, got {n_ch}.")

    # We will store timestamps + 4 channels for last WINDOW_SEC
    t_buf = deque()
    y_bufs = [deque() for _ in range(4)]

    fig, axes = plt.subplots(4, 1, sharex=True, figsize=(10, 8))
    lines = []

    for i, ax in enumerate(axes):
        ax.set_title(ELECTRODES[i])
        ax.set_ylabel("uV (raw)")
        line, = ax.plot([], [])
        lines.append(line)
        ax.grid(True)

    axes[-1].set_xlabel("Time (last 10 seconds)")

    # Initialize x-limits
    now = time.time()
    for ax in axes:
        ax.set_xlim(now - WINDOW_SEC, now)

    def prune_old(current_time: float):
        """Drop samples older than WINDOW_SEC from buffers."""
        cutoff = current_time - WINDOW_SEC
        while t_buf and t_buf[0] < cutoff:
            t_buf.popleft()
            for b in y_bufs:
                b.popleft()

    def update(_frame):
        # Pull as much data as is available quickly (chunked)
        chunk, ts = inlet.pull_chunk(timeout=0.0, max_samples=512)
        if ts:
            for sample, tstamp in zip(chunk, ts):
                # Keep only first 4 channels for Muse 2 EEG
                vals = sample[:4]
                t_buf.append(float(tstamp))
                for i in range(4):
                    y_bufs[i].append(float(vals[i]))

        if not t_buf:
            return lines

        current_time = t_buf[-1]
        prune_old(current_time)

        # Update plots
        t_arr = np.array(t_buf, dtype=float)

        for i in range(4):
            y_arr = np.array(y_bufs[i], dtype=float)

            lines[i].set_data(t_arr, y_arr)

            # Moving x-axis window
            axes[i].set_xlim(current_time - WINDOW_SEC, current_time)

            # Moving y-axis (auto-scale to recent data with margin)
            if len(y_arr) > 10:
                y_min = float(np.nanmin(y_arr))
                y_max = float(np.nanmax(y_arr))
                if np.isfinite(y_min) and np.isfinite(y_max):
                    span = y_max - y_min
                    if span < 1e-6:
                        span = 1.0
                    pad = 0.15 * span
                    axes[i].set_ylim(y_min - pad, y_max + pad)

        return lines

    ani = FuncAnimation(fig, update, interval=UPDATE_MS, blit=False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
