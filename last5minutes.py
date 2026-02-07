#!/usr/bin/env python
import sys

from moviepy import AudioFileClip

file = sys.argv[1]
output = "last_5_minutes.mp3"

print("Loading file and extracting last 5 minutes...")
audio = AudioFileClip(file)

duration = audio.duration

# Start 5 minutes (300 seconds) before the end
start_time = max(0, duration - 230)

clip = audio.subclipped(start_time, duration)
print(f"Writing {output} ({duration / 60:.1f} min total → last 5 min)...")
clip.write_audiofile(output, bitrate="320k", fps=44100)
print("Done! 🎉")
