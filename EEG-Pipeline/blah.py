import time
import csv
from collections import deque

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from pylsl import StreamInlet, resolve_byprop


# ================= CONFIG =================
WINDOW_SEC = 10.0
UPDATE_MS = 50
ELECTRODES = ["TP9", "AF7", "AF8", "TP10"]
CSV_FILENAME = "recording.csv"
STREAM_TYPE = "EEG"
# =========================================


def connect_inlet():
    print("Looking for LSL EEG stream...")
    streams = resolve_byprop("type", STREAM_TYPE, timeout=10)
    if not streams:
        raise RuntimeError(
            "No LSL EEG stream found. Make sure BlueMuse is streaming."
        )
    inlet = StreamInlet(streams[0], max_buflen=30)
    info = inlet.info()
    print("Connected to:", info.name())
    print("Channels:", info.channel_count())
    print("Sample rate:", info.nominal_srate())
    return inlet, info


def main():
    inlet, info = connect_inlet()
    if info.channel_count() < 4:
        raise RuntimeError("Expected at least 4 EEG channels.")

    # Buffers for plotting
    t_buf = deque()
    y_bufs = [deque() for _ in range(4)]

    # Open CSV file
    csv_file = open(CSV_FILENAME, "w", newline="", encoding="utf-8")
    csv_writer = csv.writer(csv_file)
    csv_writer.writerow(["lsl_timestamp"] + ELECTRODES)

    # Set up plots
    fig, axes = plt.subplots(4, 1, sharex=True, figsize=(10, 8))
    lines = []

    for i, ax in enumerate(axes):
        ax.set_title(ELECTRODES[i])
        ax.set_ylabel("uV (raw)")
        line, = ax.plot([], [])
        lines.append(line)
        ax.grid(True)

    axes[-1].set_xlabel("Time (last 10 seconds)")

    def prune_old(current_time):
        cutoff = current_time - WINDOW_SEC
        while t_buf and t_buf[0] < cutoff:
            t_buf.popleft()
            for b in y_bufs:
                b.popleft()

    def update(_frame):
        # Pull EEG samples
        chunk, timestamps = inlet.pull_chunk(timeout=0.0, max_samples=512)

        if timestamps:
            for sample, ts in zip(chunk, timestamps):
                vals = sample[:4]

                # Save to CSV
                csv_writer.writerow([ts] + vals)

                # Save to plot buffers
                t_buf.append(float(ts))
                for i in range(4):
                    y_bufs[i].append(float(vals[i]))

        if not t_buf:
            return lines

        current_time = t_buf[-1]
        prune_old(current_time)
        t_arr = np.array(t_buf)

        # Update plots
        for i in range(4):
            y_arr = np.array(y_bufs[i])
            lines[i].set_data(t_arr, y_arr)

            axes[i].set_xlim(current_time - WINDOW_SEC, current_time)

            if len(y_arr) > 10:
                y_min = float(np.nanmin(y_arr))
                y_max = float(np.nanmax(y_arr))
                span = max(y_max - y_min, 1.0)
                pad = 0.15 * span
                axes[i].set_ylim(y_min - pad, y_max + pad)

        return lines

    def on_close(event):
        print("Closing CSV file...")
        csv_file.close()

    fig.canvas.mpl_connect("close_event", on_close)

    ani = FuncAnimation(fig, update, interval=UPDATE_MS, blit=False)
    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    main()
