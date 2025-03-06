#!/usr/bin/env python3
import os
import time
from opendbc.car import get_safety_config, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.mazda.values import CAR, LKAS_LIMITS, MazdaFlags
from opendbc.car.interfaces import CarInterfaceBase
from openpilot.common.params import Params
from openpilot.common.realtime import DT_CTRL

class CarInterface(CarInterfaceBase):

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, experimental_long, docs) -> structs.CarParams:
    ret.brand = "mazda"
    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.mazda)]

    # 检查是否为CX5 2022
    is_cx5_2022 = candidate == CAR.MAZDA_CX5_2022

    # 默认雷达不可用，但CX5 2022可能支持雷达
    ret.radarUnavailable = not is_cx5_2022

    # 如果是CX5 2022，检查是否有雷达总线
    if is_cx5_2022 and 1 in fingerprint:
      ret.radarUnavailable = False
      ret.flags |= MazdaFlags.CX5_2022

    ret.dashcamOnly = candidate not in (CAR.MAZDA_CX5_2022, CAR.MAZDA_CX9_2021)

    # Mazda CX5 2022的特殊优化
    if is_cx5_2022:
      # 降低转向延迟以提高响应性
      ret.steerActuatorDelay = 0.075
      ret.steerLimitTimer = 0.85

      # 优化转向参数
      ret.lateralTuning.pid.kpBP = [0., 10., 20., 30.]
      ret.lateralTuning.pid.kpV = [0.15, 0.18, 0.22, 0.25]
      ret.lateralTuning.pid.kiBP = [0., 10., 20., 30.]
      ret.lateralTuning.pid.kiV = [0.02, 0.025, 0.03, 0.035]
      ret.lateralTuning.pid.kf = 0.00006
    else:
      ret.steerActuatorDelay = 0.1
      ret.steerLimitTimer = 0.8
      CarInterfaceBase.configure_torque_tune(candidate, ret.lateralTuning)

    # 只有非CX5 2022车型需要最小转向速度
    if not is_cx5_2022:
      ret.minSteerSpeed = LKAS_LIMITS.DISABLE_SPEED * CV.KPH_TO_MS

    ret.centerToFront = ret.wheelbase * 0.41

    # 始终启用实验纵向控制功能
    ret.experimentalLongitudinalAvailable = True

    # 使用Params获取CSLC状态和实验模式状态
    params = Params()
    cslc_enabled = params.get_bool("CSLCEnabled")
    experimental_mode = params.get_bool("ExperimentalMode")

    # 如果未设置CSLCEnabled，则默认启用
    if not params.get_bool("CSLCEnabled", False):
      params.put_bool("CSLCEnabled", True)
      cslc_enabled = True

    # 如果开启了实验模式，确保CSLC也开启
    if experimental_mode and not cslc_enabled:
      params.put_bool("CSLCEnabled", True)
      cslc_enabled = True

    # 优化CX5 2022的实验模式参数
    if experimental_long or cslc_enabled:
      ret.openpilotLongitudinalControl = True

      # CX5 2022的优化纵向控制参数
      if is_cx5_2022:
        # 针对CX5 2022优化的控制参数
        ret.longitudinalTuning.deadzoneBP = [0.]
        ret.longitudinalTuning.deadzoneV = [0.8]  # 减小死区提高响应性
        ret.stoppingDecelRate = 4.0  # 平滑的停车减速率
        ret.longitudinalActuatorDelayLowerBound = 0.8
        ret.longitudinalActuatorDelayUpperBound = 1.5

        # 更平滑的加速控制参数
        ret.longitudinalTuning.kpBP = [0., 5., 15., 30.]
        ret.longitudinalTuning.kpV = [1.2, 1.0, 0.8, 0.7]
        ret.longitudinalTuning.kiBP = [0., 5., 12., 20., 30.]
        ret.longitudinalTuning.kiV = [0.35, 0.25, 0.2, 0.15, 0.1]

        # 增加停车/启动性能
        ret.stopAccel = -0.5
        ret.vEgoStarting = 0.2

        # 优化跟车距离
        ret.radarTimeStep = 0.0333  # 雷达更新频率

        # 如果开启了实验模式，使用更激进的参数
        if experimental_mode:
          ret.longitudinalTuning.kpBP = [0., 5., 15., 30.]
          ret.longitudinalTuning.kpV = [1.3, 1.1, 0.9, 0.8]
          ret.longitudinalTuning.kiBP = [0., 5., 12., 20., 30.]
          ret.longitudinalTuning.kiV = [0.4, 0.3, 0.25, 0.2, 0.15]

          # 更快的响应
          ret.longitudinalActuatorDelayLowerBound = 0.7
          ret.longitudinalActuatorDelayUpperBound = 1.3
      else:
        # 其他马自达车型的通用参数
        ret.longitudinalTuning.deadzoneBP = [0.]
        ret.longitudinalTuning.deadzoneV = [0.9]
        ret.stoppingDecelRate = 4.5
        ret.longitudinalActuatorDelayLowerBound = 1.
        ret.longitudinalActuatorDelayUpperBound = 2.

        ret.longitudinalTuning.kpBP = [0., 5., 15., 30.]
        ret.longitudinalTuning.kpV = [1.0, 0.8, 0.6, 0.5]
        ret.longitudinalTuning.kiBP = [0., 5., 15., 30.]
        ret.longitudinalTuning.kiV = [0.2, 0.15, 0.1, 0.05]

        # 如果开启了实验模式，使用更激进的参数
        if experimental_mode:
          ret.longitudinalTuning.kpBP = [0., 5., 15., 30.]
          ret.longitudinalTuning.kpV = [1.2, 1.0, 0.8, 0.6]
          ret.longitudinalTuning.kiBP = [0., 5., 15., 30.]
          ret.longitudinalTuning.kiV = [0.25, 0.2, 0.15, 0.1]

    # 记录调试信息
    if is_cx5_2022:
      # 将配置信息写入日志
      log_path = "/data/mazda_cx5_2022_config.log"
      try:
        with open(log_path, "a") as f:
          f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
          f.write(f"Experimental Long: {experimental_long}\n")
          f.write(f"CSLC Enabled: {cslc_enabled}\n")
          f.write(f"Experimental Mode: {experimental_mode}\n")
          f.write(f"Radar Available: {not ret.radarUnavailable}\n")
          f.write(f"Flags: {ret.flags}\n")
          f.write("---\n")
      except:
        pass

    return ret
