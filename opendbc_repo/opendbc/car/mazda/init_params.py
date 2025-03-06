#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mazda车型参数初始化脚本

此脚本用于确保Mazda车型所需的参数在系统启动时就被正确初始化，
防止因参数未定义导致的系统崩溃。
"""

import os
import sys
import time

# 添加openpilot路径到系统路径
sys.path.append("/data/openpilot")

from openpilot.common.params import Params

def init_mazda_params():
    """初始化Mazda车型所需的参数"""
    params = Params()

    # 初始化CSLC功能参数
    if not params.get_bool("CSLCEnabled", False):
        print("初始化CSLCEnabled参数...")
        params.put_bool("CSLCEnabled", True)

    # 初始化CSLC速度参数
    if params.get("CSLCSpeed") is None:
        print("初始化CSLCSpeed参数...")
        params.put_float("CSLCSpeed", 0.0)

    # 初始化其他可能需要的参数
    # ...

    print("Mazda参数初始化完成")

if __name__ == "__main__":
    # 等待系统启动完成
    time.sleep(5)

    # 初始化参数
    init_mazda_params()