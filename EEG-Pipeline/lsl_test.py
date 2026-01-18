from pylsl import resolve_byprop

streams = resolve_byprop("type", "EEG", timeout=5)
print("EEG streams found:", len(streams))
for s in streams:
    print(s.name(), s.channel_count(), s.nominal_srate())
