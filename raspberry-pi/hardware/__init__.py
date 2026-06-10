# -*- coding: utf-8 -*-
"""hardware 套件：GPIO 硬體控制 (電子鎖、LED、溫濕度感測器)。"""

import os
import sys

# ------------------------------------------------------------
# 讓本套件內的模組能 `import config`。
# config.py 位於上層的 raspberry-pi/ 目錄，並非 Python 套件，
# 因此將上層目錄加入 sys.path，確保不論從哪裡匯入都能找到它。
# ------------------------------------------------------------
_PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)
