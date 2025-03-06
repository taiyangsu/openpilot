#!/usr/bin/env python3
import os
from opendbc.car import get_safety_config, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.mazda.values import CAR, LKAS_LIMITS
from opendbc.car.interfaces import CarInterfaceBase
from openpilot.common.params import Params

class CarInterface(CarInterfaceBase):

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, experimental_long, docs) -> structs.CarParams:
    ret.brand = "mazda"
    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.mazda)]
    ret.radarUnavailable = True

    ret.dashcamOnly = candidate not in (CAR.MAZDA_CX5_2022, CAR.MAZDA_CX9_2021)

    # Mazda CX5 2022的特殊优化
    if candidate == CAR.MAZDA_CX5_2022:
      # 降低转向延迟以提高响应性
      ret.steerActuatorDelay = 0.075
      ret.steerLimitTimer = 0.85
    else:
      ret.steerActuatorDelay = 0.1
      ret.steerLimitTimer = 0.8

    CarInterfaceBase.configure_torque_tune(candidate, ret.lateralTuning)

    if candidate not in (CAR.MAZDA_CX5_2022,):
      ret.minSteerSpeed = LKAS_LIMITS.DISABLE_SPEED * CV.KPH_TO_MS

    ret.centerToFront = ret.wheelbase * 0.41

    # 始终启用实验纵向控制功能
    ret.experimentalLongitudinalAvailable = True

    # 使用Params获取CSLC状态
    params = Params()
    cslc_enabled = params.get_bool("CSLCEnabled")

    # 如果未设置CSLCEnabled，则默认启用
    if not params.get_bool("CSLCEnabled", False):
      params.put_bool("CSLCEnabled", True)
      cslc_enabled = True

    # 优化CX5 2022的实验模式参数
    if experimental_long:
      ret.openpilotLongitudinalControl = True

      # CX5 2022的优化纵向控制参数
      if candidate == CAR.MAZDA_CX5_2022:
        # 针对CX5 2022优化的控制参数
        ret.longitudinalTuning.deadzoneBP = [0.]
        ret.longitudinalTuning.deadzoneV = [0.8]  # 减小死区提高响应性
        ret.stoppingDecelRate = 4.0  # 平滑的停车减速率
        ret.longitudinalActuatorDelayLowerBound = 0.8
        ret.longitudinalActuatorDelayUpperBound = 1.5

        # 更平滑的加速控制参数
        ret.longitudinalTuning.kpBP = [0., 5., 30.]
        ret.longitudinalTuning.kpV = [1.2, 1.0, 0.7]
        ret.longitudinalTuning.kiBP = [0., 5., 20., 30.]
        ret.longitudinalTuning.kiV = [0.3, 0.2, 0.15, 0.1]

        # 增加停车/启动性能
        ret.stopAccel = -0.5
        ret.vEgoStarting = 0.2
      else:
        # 其他马自达车型的通用参数
        ret.longitudinalTuning.deadzoneBP = [0.]
        ret.longitudinalTuning.deadzoneV = [0.9]
        ret.stoppingDecelRate = 4.5
        ret.longitudinalActuatorDelayLowerBound = 1.
        ret.longitudinalActuatorDelayUpperBound = 2.

        ret.longitudinalTuning.kpBP = [8.94, 7.2, 28.]
        ret.longitudinalTuning.kpV = [0., 4., 2.]
        ret.longitudinalTuning.kiBP = [0.]
        ret.longitudinalTuning.kiV = [0.1]

    # 如果启用了CSLC但未启用实验模式，也设置纵向控制为True
    if cslc_enabled and not experimental_long:
      ret.openpilotLongitudinalControl = True

      # CX5 2022的CSLC模式优化参数
      if candidate == CAR.MAZDA_CX5_2022:
        ret.longitudinalTuning.deadzoneBP = [0.]
        ret.longitudinalTuning.deadzoneV = [0.8]
        ret.stoppingDecelRate = 4.0
        ret.longitudinalActuatorDelayLowerBound = 0.8
        ret.longitudinalActuatorDelayUpperBound = 1.5

        ret.longitudinalTuning.kpBP = [0., 5., 30.]
        ret.longitudinalTuning.kpV = [1.2, 1.0, 0.7]
        ret.longitudinalTuning.kiBP = [0., 5., 20., 30.]
        ret.longitudinalTuning.kiV = [0.3, 0.2, 0.15, 0.1]

        ret.stopAccel = -0.5
        ret.vEgoStarting = 0.2
      else:
        # 其他马自达车型的参数
        ret.longitudinalTuning.deadzoneBP = [0.]
        ret.longitudinalTuning.deadzoneV = [0.9]
        ret.stoppingDecelRate = 4.5
        ret.longitudinalActuatorDelayLowerBound = 1.
        ret.longitudinalActuatorDelayUpperBound = 2.

        ret.longitudinalTuning.kpBP = [8.94, 7.2, 28.]
        ret.longitudinalTuning.kpV = [0., 4., 2.]
        ret.longitudinalTuning.kiBP = [0.]
        ret.longitudinalTuning.kiV = [0.1]

    return ret
