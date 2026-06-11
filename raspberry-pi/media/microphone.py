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
        # 串流錄音用狀態(start/stop 變動長度錄音,配合 HMI「說完按錄好了」)
        self._stream = None
        self._frames = []

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

    # ------------------------------------------------------------
    #  變動長度錄音(配合 HMI:開始說話 → 按「錄好了」才停)
    # ------------------------------------------------------------
    def start(self):
        """開始串流錄音(不限長度)，之後用 stop() 結束並存檔。"""
        if config.MOCK_MODE:
            print("[Mock] 開始錄音…")
            return
        self._frames = []

        def _callback(indata, frames, time_info, status):
            # 持續把麥克風進來的音框收集起來
            self._frames.append(indata.copy())

        self._stream = sd.InputStream(
            samplerate=self.sample_rate, channels=self.channels,
            dtype="int16", callback=_callback)
        self._stream.start()

    def stop(self, save_path: str) -> str:
        """結束串流錄音並存成 .wav，回傳存檔路徑。"""
        if config.MOCK_MODE:
            print(f"[Mock] 結束錄音 → {save_path}")
            return save_path
        if self._stream is None:
            print("尚未開始錄音(請先呼叫 start())")
            return None

        self._stream.stop()
        self._stream.close()
        self._stream = None

        if self._frames:
            data = np.concatenate(self._frames, axis=0)
        else:
            data = np.zeros((0, self.channels), dtype="int16")

        with wave.open(save_path, "wb") as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)            # int16 = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(data.tobytes())

        secs = len(data) / self.sample_rate if len(data) else 0
        print(f"錄音結束({secs:.1f} 秒)→ {save_path}")
        return save_path

    def discard(self):
        """取消串流錄音並丟棄已收集的音框。"""
        if config.MOCK_MODE:
            print("[Mock] 取消錄音")
            return
        if self._stream is not None:
            self._stream.stop()
            self._stream.close()
            self._stream = None
        self._frames = []
