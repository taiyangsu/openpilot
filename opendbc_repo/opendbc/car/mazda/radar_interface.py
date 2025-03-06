#!/usr/bin/env python3
from opendbc.car.interfaces import RadarInterfaceBase
from opendbc.car.mazda.values import CAR

class RadarInterface(RadarInterfaceBase):
  """
  马自达车型雷达接口

  注意：马自达车型没有直接访问雷达的能力，完全依赖视觉系统
  对于CX5 2022车型，可以通过视觉系统提供更好的前车跟踪能力
  """
  def __init__(self, CP):
    super().__init__()
    self.CP = CP
    # 检查是否为CX5 2022车型
    self.is_cx5_2022 = CP.carFingerprint == CAR.MAZDA_CX5_2022

  def update(self, can_strings):
    # 由于马自达没有可用的雷达接口，我们返回空的雷达数据
    # 前车跟踪完全依赖视觉系统
    return super().update(can_strings)
