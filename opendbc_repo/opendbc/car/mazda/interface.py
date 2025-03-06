#!/usr/bin/env python3
import os
from opendbc.car import get_safety_config, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.mazda.values import CAR, LKAS_LIMITS
from opendbc.car.interfaces import CarInterfaceBase
from opendbc.can.packer import CANPacker
from opendbc.car import dbc_dict
from openpilot.common.params import Params

# 添加disable_ecu函数导入
def disable_ecu(logcan, sendcan, addr=None, bus=0, subaddr=None):
  """
  禁用指定ECU的功能

  参数:
  - logcan: 日志CAN对象
  - sendcan: 发送CAN对象
  - addr: ECU地址
  - bus: CAN总线号
  - subaddr: 子地址
  """
  print(f"禁用ECU: addr={addr}, bus={bus}, subaddr={subaddr}")
  # 实际禁用ECU的代码在这里实现
  # 这里只是一个占位符，实际实现应该根据具体需求编写

class CarInterface(CarInterfaceBase):

  def __init__(self, CP, CarController, CarState):
    super().__init__(CP, CarController, CarState)
    self.cp_cam = self.CS.get_cam_can_parser(CP)

  @staticmethod
  def _get_params(candidate, fingerprint=None, car_fw=None, disable_radar=False):
    ret = CarInterfaceBase.get_std_params(candidate)
    ret.carName = "mazda"
    ret.radarUnavailable = True
    ret.steerActuatorDelay = 0.1

    # 使用文件读取方式检查参数
    cslc_enabled = False
    try:
      if os.path.exists("/data/params/d/CSLCEnabled"):
        with open("/data/params/d/CSLCEnabled", "r") as f:
          content = f.read().strip()
          cslc_enabled = content == "1"
    except:
      cslc_enabled = False

    # 检查是否为马自达车型
    is_mazda = candidate in (CAR.MAZDA_CX5, CAR.MAZDA_CX5_2022, CAR.MAZDA_CX9, CAR.MAZDA_CX9_2021, CAR.MAZDA_3, CAR.MAZDA_6)

    # 如果是马自达车型且CSLC功能已启用，则设置相关参数
    if is_mazda and cslc_enabled:
      ret.pcmCruise = False
      ret.openpilotLongitudinalControl = True
      ret.stoppingControl = True
      ret.startingState = True
      ret.vEgoStarting = 0.1
      ret.startAccel = 1.0
      ret.stopAccel = -2.0
      ret.vEgoStopping = 0.5
      ret.stoppingDecelRate = 0.2  # m/s^2/s while trying to stop
    else:
      ret.pcmCruise = True
      ret.openpilotLongitudinalControl = False

    # 根据不同车型设置参数
    if candidate == CAR.MAZDA_CX5:
      ret.mass = 3655 * 0.9  # Possibly overestimated
      ret.wheelbase = 2.7
      ret.steerRatio = 15.5
      ret.lateralTuning.pid.kiBP, ret.lateralTuning.pid.kpBP = [[0.], [0.]]
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.19], [0.019]]
      ret.lateralTuning.pid.kf = 0.00006
    elif candidate == CAR.MAZDA_CX5_2022:
      ret.mass = 3655 * 0.9  # Possibly overestimated
      ret.wheelbase = 2.7
      ret.steerRatio = 15.5
      ret.lateralTuning.pid.kiBP, ret.lateralTuning.pid.kpBP = [[0.], [0.]]
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.19], [0.019]]
      ret.lateralTuning.pid.kf = 0.00006
    elif candidate == CAR.MAZDA_CX9:
      ret.mass = 4217 * 0.9  # Possibly overestimated
      ret.wheelbase = 3.1
      ret.steerRatio = 17.6
      ret.lateralTuning.pid.kiBP, ret.lateralTuning.pid.kpBP = [[0.], [0.]]
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.19], [0.019]]
      ret.lateralTuning.pid.kf = 0.00006
    elif candidate == CAR.MAZDA_CX9_2021:
      ret.mass = 4217 * 0.9  # Possibly overestimated
      ret.wheelbase = 3.1
      ret.steerRatio = 17.6
      ret.lateralTuning.pid.kiBP, ret.lateralTuning.pid.kpBP = [[0.], [0.]]
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.19], [0.019]]
      ret.lateralTuning.pid.kf = 0.00006
    elif candidate == CAR.MAZDA_3:
      ret.mass = 2875 * 0.9  # Possibly overestimated
      ret.wheelbase = 2.7
      ret.steerRatio = 14.0
      ret.lateralTuning.pid.kiBP, ret.lateralTuning.pid.kpBP = [[0.], [0.]]
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.19], [0.019]]
      ret.lateralTuning.pid.kf = 0.00006
    elif candidate == CAR.MAZDA_6:
      ret.mass = 3443 * 0.9  # Possibly overestimated
      ret.wheelbase = 2.83
      ret.steerRatio = 15.5
      ret.lateralTuning.pid.kiBP, ret.lateralTuning.pid.kpBP = [[0.], [0.]]
      ret.lateralTuning.pid.kpV, ret.lateralTuning.pid.kiV = [[0.19], [0.019]]
      ret.lateralTuning.pid.kf = 0.00006

    if candidate not in (CAR.MAZDA_CX5_2022, ):
      ret.minSteerSpeed = LKAS_LIMITS.DISABLE_SPEED * 0.8

    return ret

  @staticmethod
  def init(CP, logcan, sendcan):
    if CP.carFingerprint in (CAR.MAZDA_CX5_2022, ):
      disable_ecu(logcan, sendcan, addr=0x243, bus=0, subaddr=None)  # Disable hands-off-monitor

  # returns a car.CarState
  def _update(self, c):
    ret = self.CS.update(self.cp, self.cp_cam)

    ret.cruiseState.enabled = self.CS.main_on or ret.cruiseState.enabled
    ret.canValid = self.cp.can_valid and self.cp_cam.can_valid
    ret.steeringRateLimited = self.CC.steer_rate_limited if self.CC is not None else False

    buttonEvents = []
    be = self.CS.button_event
    if be.pressed and be.type == 'cancel':
      buttonEvents.append(be)

    ret.buttonEvents = buttonEvents

    events = self.create_common_events(ret)
    if not self.CS.lkas_allowed:
      events.add_from(self.CS.events)

    self.CS.events = []
    ret.events = events.to_msg()

    return ret

  def apply(self, c, now_nanos):
    return self.CC.update(c, self.CS, now_nanos)
