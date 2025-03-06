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

    # 读取参数文件内容，而不只是检查文件是否存在
    cslc_enabled = False
    try:
        if os.path.exists("/data/params/d/CSLCEnabled"):
            with open("/data/params/d/CSLCEnabled", "rb") as f:
                value = f.read()
                # 如果值为1（二进制01），则启用CSLC
                cslc_enabled = (value == b'\x01')
    except Exception as e:
        print(f"读取CSLCEnabled参数时出错: {e}")
        cslc_enabled = False

    # 如果CSLC功能已启用（参数值为1），配置相关参数
    if cslc_enabled:
        # 配置CSLC的纵向控制参数
        ret.openpilotLongitudinalControl = True
        ret.longitudinalTuning.deadzoneBP = [0.]
        ret.longitudinalTuning.deadzoneV = [0.9]  # 允许2mph的速度误差
        ret.stoppingDecelRate = 4.5  # 10 mph/s的减速率
        ret.longitudinalActuatorDelayLowerBound = 1.
        ret.longitudinalActuatorDelayUpperBound = 2.

        ret.longitudinalTuning.kpBP = [8.94, 7.2, 28.]  # 8.94 m/s == 20 mph
        ret.longitudinalTuning.kpV = [0., 4., 2.]  # 低速时设为0，因为无法在该速度以下驾驶
        ret.longitudinalTuning.kiBP = [0.]
        ret.longitudinalTuning.kiV = [0.1]

    return ret
