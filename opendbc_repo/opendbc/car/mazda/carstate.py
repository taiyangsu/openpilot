from opendbc.can.can_define import CANDefine
from opendbc.can.parser import CANParser
from opendbc.car import Bus, create_button_events, structs
from opendbc.car.common.conversions import Conversions as CV
from opendbc.car.interfaces import CarStateBase
from opendbc.car.mazda.values import DBC, LKAS_LIMITS, MazdaFlags, Buttons, CAR
from openpilot.common.params import Params
from dataclasses import dataclass
import numpy as np
from cereal import car

ButtonType = structs.CarState.ButtonEvent.Type
BUTTONS_DICT = {Buttons.SET_PLUS: ButtonType.accelCruise, Buttons.SET_MINUS: ButtonType.decelCruise,
                Buttons.RESUME: ButtonType.resumeCruise, Buttons.CANCEL: ButtonType.cancel}

# Speed threshold for LKAS enabling (km/h)
LKAS_ENABLE_SPEED = 52
LKAS_DISABLE_SPEED = 44

@dataclass
class MazdaButtonEvents:
  cancel: bool = False
  set_p: bool = False
  set_m: bool = False
  resume: bool = False
  gra_acc_p: bool = False
  gra_acc_m: bool = False
  distance: bool = False
  lkas_btn: bool = False

class CarState(CarStateBase):
  def __init__(self, CP):
    super().__init__(CP)

    can_define = CANDefine(DBC[CP.carFingerprint][Bus.pt])
    self.shifter_values = can_define.dv["GEAR"]["GEAR"]

    self.crz_btns_counter = 0
    self.acc_active_last = False
    self.low_speed_alert = False
    self.lkas_allowed_speed = False
    self.lkas_disabled = False

    # 存储前一个巡航按钮状态和当前巡航按钮状态
    self.prev_cruise_buttons = Buttons.NONE
    self.cruise_buttons = Buttons.NONE

    # 跟车距离按钮状态
    self.prev_distance_button = 0
    self.distance_button = 0
    self.pcmCruiseGap = 0 # 巡航跟车距离设置

    # 帧计数器，用于控制更新频率
    self.frame = 0

    # CX5 2022特殊处理
    self.is_cx5_2022 = CP.carFingerprint == CAR.MAZDA_CX5_2022

    # 为CX5 2022使用优化的限制参数
    if self.is_cx5_2022:
      self.steer_threshold = LKAS_LIMITS.CX5_2022_STEER_THRESHOLD
      self.enable_speed = LKAS_LIMITS.CX5_2022_ENABLE_SPEED
      self.disable_speed = LKAS_LIMITS.CX5_2022_DISABLE_SPEED
    else:
      self.steer_threshold = LKAS_LIMITS.STEER_THRESHOLD
      self.enable_speed = LKAS_LIMITS.ENABLE_SPEED
      self.disable_speed = LKAS_LIMITS.DISABLE_SPEED

    # LKAS状态跟踪
    self.lkas_previously_enabled = False
    self.lkas_enabled = False

    # 雷达数据跟踪
    self.lead_distance = 0.0
    self.lead_speed = 0.0
    self.lead_present = False
    self.lead_status_counter = 0

    # 添加巡航状态缓存，用于CSLC功能
    self.cruiseStateActive = False

    # Initialize params for settings
    self.params = Params()
    try:
      self.experimental_mode = self.params.get_bool("ExperimentalMode")
    except:
      self.experimental_mode = False

    try:
      self.speed_from_pcm = self.params.get_int("SpeedFromPCM")
    except:
      self.speed_from_pcm = 1

    try:
      self.is_metric = self.params.get_bool("IsMetric")
    except:
      self.is_metric = True

  def update(self, can_parsers) -> structs.CarState:
    cp = can_parsers[Bus.pt]
    cp_cam = can_parsers[Bus.cam]

    # 处理雷达数据（如果有）
    cp_radar = can_parsers.get(Bus.radar)

    # 更新帧计数器
    self.frame += 1

    # 每50帧更新一次参数设置
    if self.frame % 50 == 0:
      try:
        self.experimental_mode = self.params.get_bool("ExperimentalMode")
      except:
        self.experimental_mode = False

      try:
        self.speed_from_pcm = self.params.get_int("SpeedFromPCM")
      except:
        self.speed_from_pcm = 1

      try:
        self.is_metric = self.params.get_bool("IsMetric")
      except:
        self.is_metric = True

    ret = structs.CarState()

    # 更新距离按钮状态
    self.prev_distance_button = self.distance_button
    self.distance_button = cp.vl["CRZ_BTNS"]["DISTANCE_LESS"]

    # 读取巡航按钮状态
    self.prev_cruise_buttons = self.cruise_buttons

    # 优化按钮读取逻辑，特别处理CX5 2022
    if self.is_cx5_2022 and self.experimental_mode:
      # 检查CX5 2022特有的按钮信号
      try:
        if cp.vl["CX5_2022_BTNS"]["CX5_2022_RES_BTN"] == 1:
          self.cruise_buttons = Buttons.RESUME
        elif bool(cp.vl["CRZ_BTNS"]["SET_P"]):
          self.cruise_buttons = Buttons.SET_PLUS
        elif bool(cp.vl["CRZ_BTNS"]["SET_M"]):
          self.cruise_buttons = Buttons.SET_MINUS
        elif bool(cp.vl["CRZ_BTNS"]["RES"]):
          self.cruise_buttons = Buttons.RESUME
        else:
          self.cruise_buttons = Buttons.NONE
      except:
        # 如果CX5_2022_BTNS不存在，使用标准按钮逻辑
        if bool(cp.vl["CRZ_BTNS"]["SET_P"]):
          self.cruise_buttons = Buttons.SET_PLUS
        elif bool(cp.vl["CRZ_BTNS"]["SET_M"]):
          self.cruise_buttons = Buttons.SET_MINUS
        elif bool(cp.vl["CRZ_BTNS"]["RES"]):
          self.cruise_buttons = Buttons.RESUME
        else:
          self.cruise_buttons = Buttons.NONE
    else:
      # 标准按钮逻辑
      if bool(cp.vl["CRZ_BTNS"]["SET_P"]):
        self.cruise_buttons = Buttons.SET_PLUS
      elif bool(cp.vl["CRZ_BTNS"]["SET_M"]):
        self.cruise_buttons = Buttons.SET_MINUS
      elif bool(cp.vl["CRZ_BTNS"]["RES"]):
        self.cruise_buttons = Buttons.RESUME
      else:
        self.cruise_buttons = Buttons.NONE

    # 车轮速度
    ret.wheelSpeeds = self.get_wheel_speeds(
      cp.vl["WHEEL_SPEEDS"]["FL"],
      cp.vl["WHEEL_SPEEDS"]["FR"],
      cp.vl["WHEEL_SPEEDS"]["RL"],
      cp.vl["WHEEL_SPEEDS"]["RR"],
    )
    ret.vEgoRaw = (ret.wheelSpeeds.fl + ret.wheelSpeeds.fr + ret.wheelSpeeds.rl + ret.wheelSpeeds.rr) / 4.
    ret.vEgo, ret.aEgo = self.update_speed_kf(ret.vEgoRaw)

    # 匹配panda速度读取
    speed_kph = cp.vl["ENGINE_DATA"]["SPEED"]
    ret.standstill = speed_kph <= .1

    # 档位信息
    can_gear = int(cp.vl["GEAR"]["GEAR"])
    ret.gearShifter = self.parse_gear_shifter(self.shifter_values.get(can_gear, None))
    ret.gearStep = cp.vl["GEAR"]["GEAR_BOX"]
    ret.engineRpm = cp.vl["ENGINE_DATA"]["RPM"] # 马自达RPM

    # 将CAN总线上的DISTANCE_SETTING值转换为与车辆显示一致的值
    can_distance_setting = cp.vl["CRZ_CTRL"]["DISTANCE_SETTING"]
    # 假设最大值为4，使用5减去CAN值来获取正确的显示值
    ret.pcmCruiseGap = 5 - can_distance_setting if 1 <= can_distance_setting <= 4 else can_distance_setting

    # 灯光和盲点监测
    ret.genericToggle = bool(cp.vl["BLINK_INFO"]["HIGH_BEAMS"])
    ret.leftBlindspot = cp.vl["BSM"]["LEFT_BS_STATUS"] != 0
    ret.rightBlindspot = cp.vl["BSM"]["RIGHT_BS_STATUS"] != 0
    ret.leftBlinker, ret.rightBlinker = self.update_blinker_from_lamp(40, cp.vl["BLINK_INFO"]["LEFT_BLINK"] == 1,
                                                                      cp.vl["BLINK_INFO"]["RIGHT_BLINK"] == 1)

    # 转向信息
    ret.steeringAngleDeg = cp.vl["STEER"]["STEER_ANGLE"]
    ret.steeringTorque = cp.vl["STEER_TORQUE"]["STEER_TORQUE_SENSOR"]
    # 使用对应车型的转向阈值
    ret.steeringPressed = abs(ret.steeringTorque) > self.steer_threshold

    ret.steeringTorqueEps = cp.vl["STEER_TORQUE"]["STEER_TORQUE_MOTOR"]
    ret.steeringRateDeg = cp.vl["STEER_RATE"]["STEER_ANGLE_RATE"]

    # 刹车信息
    ret.brakePressed = cp.vl["PEDALS"]["BRAKE_ON"] == 1
    ret.brake = cp.vl["BRAKE"]["BRAKE_PRESSURE"]

    # 安全带和车门状态
    ret.seatbeltUnlatched = cp.vl["SEATBELT"]["DRIVER_SEATBELT"] == 0
    ret.doorOpen = any([cp.vl["DOORS"]["FL"], cp.vl["DOORS"]["FR"],
                        cp.vl["DOORS"]["BL"], cp.vl["DOORS"]["BR"]])

    # 油门信息
    ret.gas = cp.vl["ENGINE_DATA"]["PEDAL_GAS"]
    ret.gasPressed = ret.gas > 0

    # LKAS状态
    lkas_blocked = cp.vl["STEER_RATE"]["LKAS_BLOCK"] == 1

    if self.CP.minSteerSpeed > 0:
      # 使用车型特定的速度限制
      if speed_kph > self.enable_speed and not lkas_blocked:
        self.lkas_allowed_speed = True
      elif speed_kph < self.disable_speed:
        self.lkas_allowed_speed = False
    else:
      self.lkas_allowed_speed = True

    # 巡航控制状态
    ret.cruiseState.available = cp.vl["CRZ_CTRL"]["CRZ_AVAILABLE"] == 1
    ret.cruiseState.enabled = cp.vl["CRZ_CTRL"]["CRZ_ACTIVE"] == 1
    self.cruiseStateActive = ret.cruiseState.enabled  # 存储巡航状态
    ret.cruiseState.standstill = cp.vl["PEDALS"]["STANDSTILL"] == 1
    ret.cruiseState.speed = cp.vl["CRZ_EVENTS"]["CRZ_SPEED"] * CV.KPH_TO_MS

    # 处理雷达数据（如果有）
    if cp_radar is not None and self.is_cx5_2022:
      # 检查前车
      lead_valid = False
      for track_id in range(1, 7):  # 处理所有6个雷达跟踪
        track_msg = f"RADAR_TRACK_36{track_id}"
        if track_msg in cp_radar.vl:
          status = cp_radar.vl[track_msg].get("STATUS", 0)
          if status >= 3:  # 状态3+表示可靠检测
            distance = cp_radar.vl[track_msg].get("DIST_OBJ", 0)
            rel_speed = cp_radar.vl[track_msg].get("RELV_OBJ", 0)
            if distance > 0 and distance < 150:  # 有效检测范围
              lead_valid = True
              if distance < self.lead_distance or self.lead_distance == 0:
                self.lead_distance = float(distance)
                self.lead_speed = float(rel_speed)

      # 更新前车检测
      if lead_valid:
        self.lead_present = True
        self.lead_status_counter = 20  # 保持检测20帧
      elif self.lead_status_counter > 0:
        self.lead_status_counter -= 1
      else:
        self.lead_present = False
        self.lead_distance = 0.0
        self.lead_speed = 0.0

      # 更新ret.leadOne字段
      ret.leadOne.dRel = float(self.lead_distance)
      ret.leadOne.vRel = float(self.lead_speed)
      ret.leadOne.status = self.lead_present

    # 检查LKAS设置
    ret.invalidLkasSetting = cp_cam.vl["CAM_LANEINFO"]["LANE_LINES"] == 0

    # 低速提醒
    if ret.cruiseState.enabled:
      if not self.lkas_allowed_speed and self.acc_active_last:
        self.low_speed_alert = True
      else:
        self.low_speed_alert = False
    ret.lowSpeedAlert = self.low_speed_alert

    # 检查转向故障
    ret.steerFaultTemporary = self.lkas_allowed_speed and lkas_blocked

    self.acc_active_last = ret.cruiseState.enabled
    self.crz_btns_counter = cp.vl["CRZ_BTNS"]["CTR"]

    # 相机信号
    self.lkas_disabled = cp_cam.vl["CAM_LANEINFO"]["LANE_LINES"] == 0
    self.cam_lkas = cp_cam.vl["CAM_LKAS"]
    self.cam_laneinfo = cp_cam.vl["CAM_LANEINFO"]
    ret.steerFaultPermanent = cp_cam.vl["CAM_LKAS"]["ERR_BIT_1"] == 1

    # 更新LKAS状态
    self.lkas_previously_enabled = self.lkas_enabled
    self.lkas_enabled = not self.lkas_disabled

    # 按钮事件
    ret.buttonEvents = [
      *create_button_events(self.cruise_buttons, self.prev_cruise_buttons, BUTTONS_DICT),
      *create_button_events(self.distance_button, self.prev_distance_button, {1: ButtonType.gapAdjustCruise}),
      *create_button_events(self.lkas_enabled, self.lkas_previously_enabled, {1: ButtonType.lfaButton}),
    ]
    return ret

  @staticmethod
  def get_can_parsers(CP):
    pt_messages = [
      # sig_address, frequency
      ("BLINK_INFO", 10),
      ("STEER", 67),
      ("STEER_RATE", 83),
      ("STEER_TORQUE", 83),
      ("WHEEL_SPEEDS", 100),
    ]

    if CP.flags & MazdaFlags.GEN1:
      pt_messages += [
        ("ENGINE_DATA", 100),
        ("CRZ_CTRL", 50),
        ("CRZ_EVENTS", 50),
        ("CRZ_BTNS", 10),
        ("PEDALS", 50),
        ("BRAKE", 50),
        ("SEATBELT", 10),
        ("DOORS", 10),
        ("GEAR", 20),
        ("BSM", 10),
      ]

    # 添加CX5 2022特有的消息
    if CP.carFingerprint == CAR.MAZDA_CX5_2022:
      pt_messages += [
        ("CX5_2022_BTNS", 10),
      ]

    cam_messages = []
    if CP.flags & MazdaFlags.GEN1:
      cam_messages += [
        # sig_address, frequency
        ("CAM_LANEINFO", 2),
        ("CAM_LKAS", 16),
      ]

    # 创建基本解析器
    parsers = {
      Bus.pt: CANParser(DBC[CP.carFingerprint][Bus.pt], pt_messages, 0),
      Bus.cam: CANParser(DBC[CP.carFingerprint][Bus.pt], cam_messages, 2),
    }

    # 添加雷达解析器（如果是CX5 2022）
    if CP.carFingerprint == CAR.MAZDA_CX5_2022 and CP.flags & MazdaFlags.CX5_2022:
      radar_messages = []

      # 添加所有雷达跟踪信号
      for i in range(1, 7):  # 6个雷达跟踪
        track_msg = f"RADAR_TRACK_36{i}"
        radar_messages.append((track_msg, 20))

      # 添加巡航控制信息
      radar_messages += [
        ("CRZ_INFO", 50),
      ]

      parsers[Bus.radar] = CANParser("mazda_radar", radar_messages, 1)

    return parsers
