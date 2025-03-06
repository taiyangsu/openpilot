#!/usr/bin/env python3
import os
from opendbc.car import get_safety_config, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.mazda.values import CAR, LKAS_LIMITS
from opendbc.car.interfaces import CarInterfaceBase
# 确保没有导入Params类
# from openpilot.common.params import Params

class CarInterface(CarInterfaceBase):

  @staticmethod
  def _get_params(ret: structs.CarParams, candidate, fingerprint, car_fw, experimental_long, docs) -> structs.CarParams:
    ret.brand = "mazda"
    ret.safetyConfigs = [get_safety_config(structs.CarParams.SafetyModel.mazda)]
    ret.radarUnavailable = True

    ret.dashcamOnly = candidate not in (CAR.MAZDA_CX5_2022, CAR.MAZDA_CX9_2021)

    ret.steerActuatorDelay = 0.1
    ret.steerLimitTimer = 0.8

    CarInterfaceBase.configure_torque_tune(candidate, ret.lateralTuning)

    if candidate not in (CAR.MAZDA_CX5_2022,):
      ret.minSteerSpeed = LKAS_LIMITS.DISABLE_SPEED * CV.KPH_TO_MS

    ret.centerToFront = ret.wheelbase * 0.41

    # 设置马自达车型支持实验纵向控制功能
    ret.experimentalLongitudinalAvailable = True

    # 判断是否开启了实验模式
    if experimental_long:
        # 如果开启了实验模式，则设置openpilot控制纵向功能
        ret.openpilotLongitudinalControl = True

        # 配置纵向控制参数
        ret.longitudinalTuning.deadzoneBP = [0.]
        ret.longitudinalTuning.deadzoneV = [0.9]  # 允许2mph的速度误差
        ret.stoppingDecelRate = 4.5  # 10 mph/s的减速率
        ret.longitudinalActuatorDelayLowerBound = 1.
        ret.longitudinalActuatorDelayUpperBound = 2.

        ret.longitudinalTuning.kpBP = [8.94, 7.2, 28.]  # 8.94 m/s == 20 mph
        ret.longitudinalTuning.kpV = [0., 4., 2.]  # 低速时设为0，因为无法在该速度以下驾驶
        ret.longitudinalTuning.kiBP = [0.]
        ret.longitudinalTuning.kiV = [0.1]

    # 尝试读取CSLC参数，如果已启用CSLC，也设置纵向控制为True
    try:
        cslc_enabled = False
        if os.path.exists("/data/params/d/CSLCEnabled"):
            with open("/data/params/d/CSLCEnabled", "rb") as f:
                value = f.read()
                cslc_enabled = (value == b'\x01')

        if cslc_enabled:
            ret.openpilotLongitudinalControl = True

            # 如果CSLC已启用但实验模式参数尚未配置纵向控制参数
            if not experimental_long:
                ret.longitudinalTuning.deadzoneBP = [0.]
                ret.longitudinalTuning.deadzoneV = [0.9]
                ret.stoppingDecelRate = 4.5
                ret.longitudinalActuatorDelayLowerBound = 1.
                ret.longitudinalActuatorDelayUpperBound = 2.

                ret.longitudinalTuning.kpBP = [8.94, 7.2, 28.]
                ret.longitudinalTuning.kpV = [0., 4., 2.]
                ret.longitudinalTuning.kiBP = [0.]
                ret.longitudinalTuning.kiV = [0.1]
    except Exception as e:
        print(f"读取CSLCEnabled参数时出错: {e}")

    return ret
