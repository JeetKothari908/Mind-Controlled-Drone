import csv
import os
import signal
import time
from datetime import datetime
from typing import List, Optional, Tuple

from pylsl import StreamInlet, resolve_byprop


# =========================
# CONFIG (edit these)
# =========================
OUTPUT_DIR = r"C:\Users\jeetd\OneDrive\Documents\GitHub\Mind-Controlled-Drone\Data"  # <-- change this
OUTPUT_FILENAME = "recording.csv"      # required by you
STREAM_TYPE = "EEG"                    # muselsl typically streams type='EEG'
RESOLVE_TIMEOUT_S = 15
PULL_CHUNK_MAX_SAMPLES = 256           # pull in chunks for performance
FLUSH_EVERY_N_ROWS = 512               # reduce risk of data loss on crash
# =========================


_stop = False


def _handle_stop(signum, frame):
    global _stop
    _stop = True


def _safe_mkdir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _build_output_path(output_dir: str, filename: str) -> str:
    _safe_mkdir(output_dir)
    return os.path.join(output_dir, filename)


def _infer_channel_names(channel_count: int) -> List[str]:
    """
    Muse 2 EEG is commonly 4 channels: TP9, AF7, AF8, TP10.
    But we keep this generic: if count != 4, name as ch0..chN-1.
    """
    if channel_count == 4:
        return ["TP9", "AF7", "AF8", "TP10"]
    return [f"ch{i}" for i in range(channel_count)]


def connect_eeg_inlet() -> StreamInlet:
    streams = resolve_byprop("type", STREAM_TYPE, timeout=RESOLVE_TIMEOUT_S)
    if not streams:
        raise RuntimeError(
            f"No LSL stream found with type='{STREAM_TYPE}'.\n\n"
            "If using Muse later:\n"
            "  1) start the LSL stream (e.g., `muse stream --eeg`)\n"
            "  2) ensure no other app is connected to Muse\n\n"
            "For now (no Muse): run the included simulator `fake_muse_lsl.py`."
        )
    inlet = StreamInlet(streams[0], max_buflen=10)
    return inlet


def main():
    global _stop
    signal.signal(signal.SIGINT, _handle_stop)
    signal.signal(signal.SIGTERM, _handle_stop)

    output_path = _build_output_path(OUTPUT_DIR, OUTPUT_FILENAME)
    inlet = connect_eeg_inlet()

    info = inlet.info()
    n_channels = info.channel_count()
    srate = info.nominal_srate()
    stream_name = info.name()

    channel_names = _infer_channel_names(n_channels)

    # CSV header: wall_time_iso, wall_time_unix, lsl_timestamp, sample_index, channels...
    header = ["wall_time_iso", "wall_time_unix", "lsl_timestamp", "sample_index"] + channel_names

    rows_written = 0
    sample_index = 0

    print("Connected to LSL stream:")
    print(f"  name: {stream_name}")
    print(f"  type: {info.type()}")
    print(f"  channels: {n_channels}")
    print(f"  nominal_srate: {srate}")
    print(f"Recording to: {output_path}")
    print("Press Ctrl+C to stop.\n")

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(header)

        while not _stop:
            # Pull a chunk for efficiency
            chunk, timestamps = inlet.pull_chunk(
                timeout=1.0, max_samples=PULL_CHUNK_MAX_SAMPLES
            )
            if not timestamps:
                continue

            now_unix = time.time()
            now_iso = datetime.fromtimestamp(now_unix).isoformat()

            for sample, ts in zip(chunk, timestamps):
                # Defensive: ensure correct length
                if len(sample) != n_channels:
                    sample = (sample + [float("nan")] * n_channels)[:n_channels]

                writer.writerow([now_iso, f"{now_unix:.6f}", f"{ts:.6f}", sample_index] + sample)
                rows_written += 1
                sample_index += 1

                if rows_written % FLUSH_EVERY_N_ROWS == 0:
                    f.flush()

        # final flush on exit
        f.flush()

    print(f"\nStopped. Wrote {rows_written} rows to {output_path}")


if __name__ == "__main__":
    main()
