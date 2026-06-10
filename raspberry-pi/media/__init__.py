# -*- coding: utf-8 -*-
"""media 套件：多媒體擷取 (人臉相機、食物相機、麥克風)。"""

import os
import sys

# 將上層 raspberry-pi/ 目錄加入 sys.path，使本套件模組能 `import config`。
_PARENT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _PARENT_DIR not in sys.path:
    sys.path.insert(0, _PARENT_DIR)
