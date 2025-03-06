#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Mazda CSLC功能测试脚本
此脚本用于测试Mazda车型的Cruise Speed Limit Control功能的核心逻辑
"""

import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# 添加当前目录到路径，以便导入模块
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from opendbc.car.mazda.mazdacan import create_mazda_acc_spam_command
from opendbc.car.mazda.values import Buttons
from opendbc.car.common.conversions import Conversions as CV

# 定义最大巡航速度常量（km/h），与carcontroller.py中保持一致
V_CRUISE_MAX = 160