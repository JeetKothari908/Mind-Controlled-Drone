import time
import numpy as np
from pylsl import StreamInlet, resolve_byprop

ELECTRODES = ["TP9", "AF7", "AF8", "TP10"]
PRINT_INTERVAL_S = 0.5   # ~2 prints per second

print("Looking for EEG stream...")
streams = resolve_byprop("type", "EEG", timeout=10)
if not streams:
    raise RuntimeError("No EEG stream found. Is BlueMuse streaming?")

inlet = StreamInlet(streams[0])
info = inlet.info()

n_ch = info.channel_count()
print("Connected to:", info.name())
print("Channels:", n_ch)
print("Sample rate:", info.nominal_srate())
print("\nStreaming EEG summary (Ctrl+C to stop):\n")

buffer = []
last_print = time.time()

try:
    while True:
        sample, ts = inlet.pull_sample(timeout=1.0)
        if sample is None:
            continue

        # Ensure at least 4 channels
        vals = (sample + [np.nan] * 4)[:4]
        buffer.append(vals)

        now = time.time()
        if now - last_print >= PRINT_INTERVAL_S:
            data = np.array(buffer)
            buffer.clear()
            last_print = now

            means = np.nanmean(data, axis=0)
            stds = np.nanstd(data, axis=0)

            line = f"{ts:.3f} | "
            for name, m, s in zip(ELECTRODES, means, stds):
                line += f"{name}={m:7.1f}±{s:5.1f}  "
            print(line)

except KeyboardInterrupt:
    print("\nStopped.")
