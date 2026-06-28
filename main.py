#!/usr/bin/env python3

import threading
import tempfile
import subprocess
import signal
import os
import sys
import wave
import time

import numpy as np
import sounddevice as sd
from faster_whisper import WhisperModel

WHISPER_MODEL = "small"
SAMPLE_RATE = 16000
CHANNELS = 1
LANGUAGE = "en"


class STTTyper:
    def __init__(self):
        self.recording = False
        self.audio_data = []
        self.stream = None
        self.lock = threading.Lock()
        self.model = WhisperModel(WHISPER_MODEL, device="cpu", compute_type="int8")
        signal.signal(signal.SIGUSR1, self._on_signal)

    def _on_signal(self, signum, frame):
        if not self.recording:
            threading.Thread(target=self.start_recording, daemon=True).start()
        else:
            threading.Thread(target=self.stop_recording, daemon=True).start()

    def _audio_callback(self, indata, frames, time_, status):
        with self.lock:
            self.audio_data.append(indata.copy())

    def start_recording(self):
        self.audio_data = []
        self.stream = sd.InputStream(
            samplerate=SAMPLE_RATE,
            channels=CHANNELS,
            dtype="float32",
            callback=self._audio_callback,
        )
        self.stream.start()
        self.recording = True
        subprocess.Popen(["notify-send", "-t", "2000", "🎙 Recording…"])

    def stop_recording(self):
        self.recording = False
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None
        subprocess.Popen(["notify-send", "-t", "2000", "⏹ Transcribing…"])

        with self.lock:
            chunks = list(self.audio_data)

        if chunks:
            audio = np.concatenate(chunks, axis=0).flatten()
            self._transcribe_and_type(audio)

    def _transcribe_and_type(self, audio: np.ndarray):
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            tmp_path = f.name
            with wave.open(f, "wb") as wf:
                wf.setnchannels(CHANNELS)
                wf.setsampwidth(2)
                wf.setframerate(SAMPLE_RATE)
                pcm = (audio * 32767).astype(np.int16)
                wf.writeframes(pcm.tobytes())

        try:
            segments, _ = self.model.transcribe(
                tmp_path,
                language=LANGUAGE,
                beam_size=5,
                vad_filter=True,
            )
            text = " ".join(seg.text for seg in segments).strip()
        finally:
            os.unlink(tmp_path)

        if text:
            time.sleep(0.1)
            subprocess.run(["ydotool", "type", "--", text])

    def run(self):
        while True:
            signal.pause()


if __name__ == "__main__":
    STTTyper().run()
