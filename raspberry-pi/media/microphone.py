# -*- coding: utf-8 -*-
"""
麥克風錄音模組 (microphone.py)
============================================================
提供 `Microphone` 類別，使用 sounddevice 錄製指定秒數的音訊，
並以標準 `wave` 模組存成 .wav 檔。

(sounddevice 負責擷取 PCM 資料，wave 負責寫檔，無需額外的編碼套件。)
"""

import wave
import config

# 只有在實機模式才匯入 sounddevice / numpy。
if not config.MOCK_MODE:
    import sounddevice as sd
    import numpy as np


class Microphone:
    """麥克風錄音類別。"""

    def __init__(self,
                 sample_rate: int = config.AUDIO_SAMPLE_RATE,
                 channels: int = config.AUDIO_CHANNELS):
        """
        :param sample_rate: 取樣率 (Hz)
        :param channels:    聲道數 (1 = 單聲道)
        """
        self.sample_rate = sample_rate
        self.channels = channels

    def record(self, save_path: str,
               duration: int = config.AUDIO_DURATION_SECONDS) -> str:
        """
        錄製指定秒數的音訊並存成 .wav。

        :param save_path: 音檔儲存路徑 (例如 recordings/note_xxx.wav)
        :param duration:  錄音秒數 (預設取自 config，4 秒)
        :return: 實際存檔路徑；失敗則回傳 None
        """
        # ---- 模擬模式：不真的錄音，只印出訊息 ----
        if config.MOCK_MODE:
            print(f"[Mock] 錄音 {duration} 秒成功 → {save_path}")
            return save_path

        # ---- 實機模式：用 sounddevice 錄音 ----
        try:
            # 以 int16 格式錄製，方便直接寫入 wav (每樣本 2 bytes)
            frames = sd.rec(
                int(duration * self.sample_rate),
                samplerate=self.sample_rate,
                channels=self.channels,
                dtype="int16",
            )
            sd.wait()  # 等待錄音完成 (此呼叫為阻塞，由上層以執行緒包裝為非阻塞)

            # 用標準 wave 模組寫出 .wav 檔
            with wave.open(save_path, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)            # int16 = 2 bytes
                wf.setframerate(self.sample_rate)
                wf.writeframes(frames.tobytes())

            print(f"錄音 {duration} 秒成功 → {save_path}")
            return save_path

        except Exception as err:
            print(f"錄音失敗: {err}")
            return None
