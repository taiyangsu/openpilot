#!/usr/bin/env python3
import math
import os
from enum import IntEnum
from collections.abc import Callable

from cereal import log, car
import cereal.messaging as messaging
from openpilot.common.conversions import Conversions as CV
from openpilot.common.params import Params
from openpilot.common.realtime import DT_CTRL
from openpilot.selfdrive.locationd.calibrationd import MIN_SPEED_FILTER
from openpilot.system.version import get_short_branch

params = Params()
params_memory = Params("/dev/shm/params")

AlertSize = log.ControlsState.AlertSize
AlertStatus = log.ControlsState.AlertStatus
VisualAlert = car.CarControl.HUDControl.VisualAlert
AudibleAlert = car.CarControl.HUDControl.AudibleAlert
EventName = car.CarEvent.EventName


# Alert priorities
class Priority(IntEnum):
  LOWEST = 0
  LOWER = 1
  LOW = 2
  MID = 3
  HIGH = 4
  HIGHEST = 5


# Event types
class ET:
  ENABLE = '启用'
  PRE_ENABLE = '预启用'
  OVERRIDE_LATERAL = '覆盖横向'
  OVERRIDE_LONGITUDINAL = '覆盖纵向'
  NO_ENTRY = '无入口'
  WARNING = '警告'
  USER_DISABLE = '用户禁用'
  SOFT_DISABLE = '软禁用'
  IMMEDIATE_DISABLE = '立即禁用'
  PERMANENT = '永久'


# get event name from enum
EVENT_NAME = {v: k for k, v in EventName.schema.enumerants.items()}


class Events:
  def __init__(self):
    self.events: list[int] = []
    self.static_events: list[int] = []
    self.events_prev = dict.fromkeys(EVENTS.keys(), 0)

  @property
  def names(self) -> list[int]:
    return self.events

  def __len__(self) -> int:
    return len(self.events)

  def add(self, event_name: int, static: bool=False) -> None:
    if static:
      self.static_events.append(event_name)
    self.events.append(event_name)

  def clear(self) -> None:
    self.events_prev = {k: (v + 1 if k in self.events else 0) for k, v in self.events_prev.items()}
    self.events = self.static_events.copy()

  def contains(self, event_type: str) -> bool:
    return any(event_type in EVENTS.get(e, {}) for e in self.events)

  def create_alerts(self, event_types: list[str], callback_args=None):
    if callback_args is None:
      callback_args = []

    ret = []
    for e in self.events:
      types = EVENTS[e].keys()
      for et in event_types:
        if et in types:
          alert = EVENTS[e][et]
          if not isinstance(alert, Alert):
            alert = alert(*callback_args)

          if DT_CTRL * (self.events_prev[e] + 1) >= alert.creation_delay:
            alert.alert_type = f"{EVENT_NAME[e]}/{et}"
            alert.event_type = et
            ret.append(alert)
    return ret

  def add_from_msg(self, events):
    for e in events:
      self.events.append(e.name.raw)

  def to_msg(self):
    ret = []
    for event_name in self.events:
      event = car.CarEvent.new_message()
      event.name = event_name
      for event_type in EVENTS.get(event_name, {}):
        setattr(event, event_type, True)
      ret.append(event)
    return ret


class Alert:
  def __init__(self,
               alert_text_1: str,
               alert_text_2: str,
               alert_status: log.ControlsState.AlertStatus,
               alert_size: log.ControlsState.AlertSize,
               priority: Priority,
               visual_alert: car.CarControl.HUDControl.VisualAlert,
               audible_alert: car.CarControl.HUDControl.AudibleAlert,
               duration: float,
               alert_rate: float = 0.,
               creation_delay: float = 0.):

    self.alert_text_1 = alert_text_1
    self.alert_text_2 = alert_text_2
    self.alert_status = alert_status
    self.alert_size = alert_size
    self.priority = priority
    self.visual_alert = visual_alert
    self.audible_alert = audible_alert

    self.duration = int(duration / DT_CTRL)

    self.alert_rate = alert_rate
    self.creation_delay = creation_delay

    self.alert_type = ""
    self.event_type: str | None = None

  def __str__(self) -> str:
    return f"{self.alert_text_1}/{self.alert_text_2} {self.priority} {self.visual_alert} {self.audible_alert}"

  def __gt__(self, alert2) -> bool:
    if not isinstance(alert2, Alert):
      return False
    return self.priority > alert2.priority


class NoEntryAlert(Alert):
  def __init__(self, alert_text_2: str,
               alert_text_1: str = "openpilot 不可用",
               visual_alert: car.CarControl.HUDControl.VisualAlert=VisualAlert.none):
    super().__init__(alert_text_1, alert_text_2, AlertStatus.normal,
                     AlertSize.mid, Priority.LOW, visual_alert,
                     AudibleAlert.refuse, 3.)


class SoftDisableAlert(Alert):
  def __init__(self, alert_text_2: str):
    super().__init__("立即接管控制", alert_text_2,
                     AlertStatus.userPrompt, AlertSize.full,
                     Priority.MID, VisualAlert.steerRequired,
                     AudibleAlert.warningSoft, 2.),


# less harsh version of SoftDisable, where the condition is user-triggered
class UserSoftDisableAlert(SoftDisableAlert):
  def __init__(self, alert_text_2: str):
    super().__init__(alert_text_2),
    self.alert_text_1 = "openpilot 将解除控制"


class ImmediateDisableAlert(Alert):
  def __init__(self, alert_text_2: str):
    super().__init__("立即接管控制", alert_text_2,
                     AlertStatus.critical, AlertSize.full,
                     Priority.HIGHEST, VisualAlert.steerRequired,
                     AudibleAlert.warningImmediate, 4.),


class EngagementAlert(Alert):
  def __init__(self, audible_alert: car.CarControl.HUDControl.AudibleAlert):
    super().__init__("", "",
                     AlertStatus.normal, AlertSize.none,
                     Priority.MID, VisualAlert.none,
                     audible_alert, .2),


class NormalPermanentAlert(Alert):
  def __init__(self, alert_text_1: str, alert_text_2: str = "", duration: float = 0.2, priority: Priority = Priority.LOWER, creation_delay: float = 0.):
    super().__init__(alert_text_1, alert_text_2,
                     AlertStatus.normal, AlertSize.mid if len(alert_text_2) else AlertSize.small,
                     priority, VisualAlert.none, AudibleAlert.none, duration, creation_delay=creation_delay),


class StartupAlert(Alert):
  def __init__(self, alert_text_1: str, alert_text_2: str = "请始终保持双手在方向盘上，眼睛注视道路", alert_status=AlertStatus.normal):
    super().__init__(alert_text_1, alert_text_2,
                     alert_status, AlertSize.mid,
                     Priority.LOWER, VisualAlert.none, AudibleAlert.none, 5.),

# ********** helper functions **********
def get_display_speed(speed_ms: float, metric: bool) -> str:
  speed = int(round(speed_ms * (CV.MS_TO_KPH if metric else CV.MS_TO_MPH)))
  unit = 'km/h' if metric else 'mph'
  return f"{speed} {unit}"


# ********** alert callback functions **********

AlertCallbackType = Callable[[car.CarParams, car.CarState, messaging.SubMaster, bool, int], Alert]


def soft_disable_alert(alert_text_2: str) -> AlertCallbackType:
  def func(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
    if soft_disable_time < int(0.5 / DT_CTRL):
      return ImmediateDisableAlert(alert_text_2)
    return SoftDisableAlert(alert_text_2)
  return func

def user_soft_disable_alert(alert_text_2: str) -> AlertCallbackType:
  def func(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
    if soft_disable_time < int(0.5 / DT_CTRL):
      return ImmediateDisableAlert(alert_text_2)
    return UserSoftDisableAlert(alert_text_2)
  return func

def startup_master_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  branch = get_short_branch()  # Ensure get_short_branch is cached to avoid lags on startup
  if "REPLAY" in os.environ:
    branch = "replay"

  return StartupAlert("Hippity hoppity this is my property", "so I do what I want 🐸", alert_status=AlertStatus.frogpilot)

def below_engage_speed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  return NoEntryAlert(f"Drive above {get_display_speed(CP.minEnableSpeed, metric)} to engage")

def below_steer_speed_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  return Alert(
    f"转向在 {get_display_speed(CP.minSteerSpeed, metric)} 之下不可用",
    "",
    AlertStatus.userPrompt, AlertSize.small,
    Priority.LOW, VisualAlert.steerRequired, AudibleAlert.prompt, 0.4)


def calibration_incomplete_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  first_word = '重新校准' if sm['liveCalibration'].calStatus == log.LiveCalibrationData.Status.recalibrating else '校准'
  return Alert(
    f"{first_word} 进行中: {sm['liveCalibration'].calPerc:.0f}%",
    f"请驾驶超过 {get_display_speed(MIN_SPEED_FILTER, metric)}",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2)


def no_gps_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  return Alert(
    "GPS信号差",
    "如果天空可见，则硬件故障",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWER, VisualAlert.none, AudibleAlert.none, .2, creation_delay=300.)

def torque_nn_load_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  model_name = params.get("NNFFModelName", encoding='utf-8')
  if model_name == "":
    return Alert(
      "NNFF扭矩控制器不可用",
      "请捐赠日志给Twilsonco以支持您的车辆！",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 5.0)
  else:
    return Alert(
      "NNFF扭矩控制器已加载",
      model_name,
      AlertStatus.frogpilot, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.engage, 5.0)

# *** debug alerts ***

def out_of_space_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  full_perc = round(100. - sm['deviceState'].freeSpacePercent)
  return NormalPermanentAlert("存储空间不足", f"{full_perc}% 已满")


def posenet_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  mdl = sm['modelV2'].velocity.x[0] if len(sm['modelV2'].velocity.x) else math.nan
  err = CS.vEgo - mdl
  msg = f"速度误差: {err:.1f} m/s"
  return NoEntryAlert(msg, alert_text_1="姿态网络速度无效")


def process_not_running_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  not_running = [p.name for p in sm['managerState'].processes if not p.running and p.shouldBeRunning]
  msg = ', '.join(not_running)
  return NoEntryAlert(msg, alert_text_1="进程未运行")


def comm_issue_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  bs = [s for s in sm.data.keys() if not sm.all_checks([s, ])]
  msg = ', '.join(bs[:4])  # can't fit too many on one line
  return NoEntryAlert(msg, alert_text_1="进程间通信问题")


def camera_malfunction_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  all_cams = ('roadCameraState', 'driverCameraState', 'wideRoadCameraState')
  bad_cams = [s.replace('State', '') for s in all_cams if s in sm.data.keys() and not sm.all_checks([s, ])]
  return NormalPermanentAlert("摄像头故障", ', '.join(bad_cams))


def calibration_invalid_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  rpy = sm['liveCalibration'].rpyCalib
  yaw = math.degrees(rpy[2] if len(rpy) == 3 else math.nan)
  pitch = math.degrees(rpy[1] if len(rpy) == 3 else math.nan)
  angles = f"重新安装设备 (俯仰: {pitch:.1f}°, 偏航: {yaw:.1f}°)"
  return NormalPermanentAlert("校准无效", angles)


def overheat_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  cpu = max(sm['deviceState'].cpuTempC, default=0.)
  gpu = max(sm['deviceState'].gpuTempC, default=0.)
  temp = max((cpu, gpu, sm['deviceState'].memoryTempC))
  return NormalPermanentAlert("系统过热", f"{temp:.0f} °C")


def low_memory_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  return NormalPermanentAlert("内存不足", f"{sm['deviceState'].memoryUsagePercent}% 已使用")


def high_cpu_usage_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  x = max(sm['deviceState'].cpuUsagePercent, default=0.)
  return NormalPermanentAlert("CPU使用率高", f"{x}% 已使用")

def modeld_lagging_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  return NormalPermanentAlert("驾驶模型滞后", f"{sm['modelV2'].frameDropPerc:.1f}% 帧丢失")


def wrong_car_mode_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  text = "启用自适应巡航以进行接入"
  if CP.carName == "honda":
    text = "启用主开关以进行接入"
  return NoEntryAlert(text)


def joystick_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  axes = sm['testJoystick'].axes
  gb, steer = list(axes)[:2] if len(axes) else (0., 0.)
  vals = f"油门: {round(gb * 100.)}%, 转向: {round(steer * 100.)}%"
  return NormalPermanentAlert("操纵杆模式", vals)

# FrogPilot Alerts
def holiday_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  holiday_messages = {
    1: ("Happy April Fool's Day! 🤡", "aprilFoolsAlert"),
    2: ("Merry Christmas! 🎄", "christmasAlert"),
    3: ("¡Feliz Cinco de Mayo! 🌮", "cincoDeMayoAlert"),
    4: ("Happy Easter! 🐰", "easterAlert"),
    5: ("Happy Fourth of July! 🎆", "fourthOfJulyAlert"),
    6: ("Happy Halloween! 🎃", "halloweenAlert"),
    7: ("Happy New Year! 🎉", "newYearsDayAlert"),
    8: ("Happy St. Patrick's Day! 🍀", "stPatricksDayAlert"),
    9: ("Happy Thanksgiving! 🦃", "thanksgivingAlert"),
    10: ("Happy Valentine's Day! ❤️", "valentinesDayAlert"),
    11: ("Happy World Frog Day! 🐸", "worldFrogDayAlert"),
  }

  theme_id = params_memory.get_int("CurrentHolidayTheme")
  message, alert_type = holiday_messages.get(theme_id, ("", ""))

  return Alert(
    message,
    "",
    AlertStatus.normal, AlertSize.small,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, 5.)

def no_lane_available_alert(CP: car.CarParams, CS: car.CarState, sm: messaging.SubMaster, metric: bool, soft_disable_time: int) -> Alert:
  lane_width = sm['frogpilotPlan'].laneWidthLeft if CS.leftBlinker else sm['frogpilotPlan'].laneWidthRight
  lane_width_msg = f"{lane_width:.1f} 米" if metric else f"{lane_width * CV.METER_TO_FOOT:.1f} 英尺"

  return Alert(
    "没有可用车道",
    f"检测到的车道宽度仅为 {lane_width_msg}",
    AlertStatus.normal, AlertSize.mid,
    Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2)

EVENTS: dict[int, dict[str, Alert | AlertCallbackType]] = {
  # ********** events with no alerts **********

  EventName.stockFcw: {},

  # ********** events only containing alerts displayed in all states **********

  EventName.joystickDebug: {
    ET.WARNING: joystick_alert,
    ET.PERMANENT: NormalPermanentAlert("Joystick Mode"),
  },

  EventName.controlsInitializing: {
    ET.NO_ENTRY: NoEntryAlert("System Initializing"),
  },

  EventName.startup: {
    ET.PERMANENT: StartupAlert("Be ready to take over at any time")
  },

  EventName.startupMaster: {
    ET.PERMANENT: startup_master_alert,
  },

  # 车辆已识别，但仅标记为行车记录仪模式
  EventName.startupNoControl: {
    ET.PERMANENT: StartupAlert("行车记录仪模式"),
    ET.NO_ENTRY: NoEntryAlert("行车记录仪模式"),
  },

  # 车辆未被识别
  EventName.startupNoCar: {
    ET.PERMANENT: StartupAlert("不支持的车辆的行车记录仪模式"),
  },

  EventName.startupNoFw: {
    ET.PERMANENT: StartupAlert("车辆未识别",
                               "检查逗号电源连接",
                               alert_status=AlertStatus.userPrompt),
  },

  EventName.dashcamMode: {
    ET.PERMANENT: NormalPermanentAlert("行车记录仪模式",
                                       priority=Priority.LOWEST),
  },

  EventName.invalidLkasSetting: {
    ET.PERMANENT: NormalPermanentAlert("库存LKAS已开启",
                                       "关闭库存LKAS以启用"),
  },

  EventName.cruiseMismatch: {
    #ET.PERMANENT: ImmediateDisableAlert("openpilot未能取消巡航"),
  },

  # openpilot未能识别车辆。这将使openpilot切换到一个
  # read-only mode. This can be solved by adding your fingerprint.
  # See https://github.com/commaai/openpilot/wiki/Fingerprinting for more information
  EventName.carUnrecognized: {
    ET.PERMANENT: NormalPermanentAlert("行车记录仪模式",
                                       "车辆未识别",
                                       priority=Priority.LOWEST),
  },

  EventName.stockAeb: {
    ET.PERMANENT: Alert(
      "刹车！",
      "库存AEB：碰撞风险",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.none, 2.),
    ET.NO_ENTRY: NoEntryAlert("库存AEB：碰撞风险"),
  },

  EventName.fcw: {
    ET.PERMANENT: Alert(
      "刹车！",
      "碰撞风险",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGHEST, VisualAlert.fcw, AudibleAlert.warningSoft, 2.),
  },

  EventName.ldw: {
    ET.PERMANENT: Alert(
      "检测到车道偏离",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.ldw, AudibleAlert.prompt, 3.),
  },

  # ********** events only containing alerts that display while engaged **********

  EventName.steerTempUnavailableSilent: {
    ET.WARNING: Alert(
      "转向暂时不可用",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.prompt, 1.8),
  },

  EventName.preDriverDistracted: {
    ET.WARNING: Alert(
      "请注意",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.promptDriverDistracted: {
    ET.WARNING: Alert(
      "请注意",
      "驾驶员分心",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, .1),
  },

  EventName.driverDistracted: {
    ET.WARNING: Alert(
      "立即脱离控制",
      "驾驶员分心",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.warningImmediate, .1),
  },

  EventName.preDriverUnresponsive: {
    ET.WARNING: Alert(
      "触摸方向盘：未检测到面部",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.none, .1, alert_rate=0.75),
  },

  EventName.promptDriverUnresponsive: {
    ET.WARNING: Alert(
      "触摸方向盘",
      "驾驶员未响应",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.MID, VisualAlert.steerRequired, AudibleAlert.promptDistracted, .1),
  },

  EventName.driverUnresponsive: {
    ET.WARNING: Alert(
      "立即脱离控制",
      "驾驶员未响应",
      AlertStatus.critical, AlertSize.full,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.warningImmediate, .1),
  },

  EventName.manualRestart: {
    ET.WARNING: Alert(
      "接管控制",
      "手动恢复驾驶",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.resumeRequired: {
    ET.WARNING: Alert(
      "按下恢复以退出静止状态",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.MID, VisualAlert.none, AudibleAlert.none, .2),
  },

  EventName.belowSteerSpeed: {
    ET.WARNING: below_steer_speed_alert,
  },

  EventName.preLaneChangeLeft: {
    ET.WARNING: Alert(
      "向左转动以在安全时开始变道",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1, alert_rate=0.75),
  },

  EventName.preLaneChangeRight: {
    ET.WARNING: Alert(
      "向右转动以在安全时开始变道",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1, alert_rate=0.75),
  },

  EventName.laneChangeBlocked: {
    ET.WARNING: Alert(
      "盲区内检测到车辆",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, .1),
  },

  EventName.laneChange: {
    ET.WARNING: Alert(
      "正在变道",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.steerSaturated: {
    ET.WARNING: Alert(
      "接管控制",
      "转向超过限制",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.promptRepeat, 2.),
  },

  # Thrown when the fan is driven at >50% but is not rotating
  EventName.fanMalfunction: {
    ET.PERMANENT: NormalPermanentAlert("风扇故障", "可能的硬件问题"),
  },

  # Camera is not outputting frames
  EventName.cameraMalfunction: {
    ET.PERMANENT: camera_malfunction_alert,
    ET.SOFT_DISABLE: soft_disable_alert("相机故障"),
    ET.NO_ENTRY: NoEntryAlert("相机故障：重启设备"),
  },
  # Camera framerate too low
  EventName.cameraFrameRate: {
    ET.PERMANENT: NormalPermanentAlert("相机帧率过低", "重启设备"),
    ET.SOFT_DISABLE: soft_disable_alert("相机帧率过低"),
    ET.NO_ENTRY: NoEntryAlert("相机帧率过低：重启设备"),
  },

  # Unused
  EventName.gpsMalfunction: {
    ET.PERMANENT: NormalPermanentAlert("GPS故障", "可能的硬件问题"),
  },

  EventName.locationdTemporaryError: {
    ET.NO_ENTRY: NoEntryAlert("locationd临时错误"),
    ET.SOFT_DISABLE: soft_disable_alert("locationd临时错误"),
  },

  EventName.locationdPermanentError: {
    ET.NO_ENTRY: NoEntryAlert("locationd永久错误"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("locationd永久错误"),
    ET.PERMANENT: NormalPermanentAlert("locationd永久错误"),
  },

  # openpilot tries to learn certain parameters about your car by observing
  # how the car behaves to steering inputs from both human and openpilot driving.
  # This includes:
  # - steer ratio: gear ratio of the steering rack. Steering angle divided by tire angle
  # - tire stiffness: how much grip your tires have
  # - angle offset: most steering angle sensors are offset and measure a non zero angle when driving straight
  # This alert is thrown when any of these values exceed a sanity check. This can be caused by
  # bad alignment or bad sensor data. If this happens consistently consider creating an issue on GitHub
  EventName.paramsdTemporaryError: {
    ET.NO_ENTRY: NoEntryAlert("paramsd 临时错误"),
    ET.SOFT_DISABLE: soft_disable_alert("paramsd 临时错误"),
  },

  EventName.paramsdPermanentError: {
    ET.NO_ENTRY: NoEntryAlert("paramsd 永久错误"),
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("paramsd 永久错误"),
    ET.PERMANENT: NormalPermanentAlert("paramsd 永久错误"),
  },

  # ********** events that affect controls state transitions **********

  EventName.pcmEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.engage),
  },

  EventName.buttonEnable: {
    ET.ENABLE: EngagementAlert(AudibleAlert.engage),
  },

  EventName.pcmDisable: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
  },

  EventName.buttonCancel: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("取消按下"),
  },

  EventName.brakeHold: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("刹车保持激活"),
  },

  EventName.parkBrake: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("驻车制动已启用"),
  },

  EventName.pedalPressed: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("踏板已按下",
                              visual_alert=VisualAlert.brakePressed),
  },

  EventName.preEnableStandstill: {
    ET.PRE_ENABLE: Alert(
      "释放刹车以启用",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1, creation_delay=1.),
  },

  EventName.gasPressedOverride: {
    ET.OVERRIDE_LONGITUDINAL: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.steerOverride: {
    ET.OVERRIDE_LATERAL: Alert(
      "",
      "",
      AlertStatus.normal, AlertSize.none,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1),
  },

  EventName.wrongCarMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: wrong_car_mode_alert,
  },

  EventName.resumeBlocked: {
    ET.NO_ENTRY: NoEntryAlert("按下设置以启用"),
  },

  EventName.wrongCruiseMode: {
    ET.USER_DISABLE: EngagementAlert(AudibleAlert.disengage),
    ET.NO_ENTRY: NoEntryAlert("自适应巡航已禁用"),
  },

  EventName.steerTempUnavailable: {
    ET.SOFT_DISABLE: soft_disable_alert("转向暂时不可用"),
    ET.NO_ENTRY: NoEntryAlert("转向暂时不可用"),
  },

  EventName.steerTimeLimit: {
    ET.SOFT_DISABLE: soft_disable_alert("车辆转向时间限制"),
    ET.NO_ENTRY: NoEntryAlert("车辆转向时间限制"),
  },

  EventName.outOfSpace: {
    ET.PERMANENT: out_of_space_alert,
    ET.NO_ENTRY: NoEntryAlert("存储空间不足"),
  },

  EventName.belowEngageSpeed: {
    ET.NO_ENTRY: below_engage_speed_alert,
  },

  EventName.sensorDataInvalid: {
    ET.PERMANENT: Alert(
      "传感器数据无效",
      "可能的硬件问题",
      AlertStatus.normal, AlertSize.mid,
      Priority.LOWER, VisualAlert.none, AudibleAlert.none, .2, creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("传感器数据无效"),
    ET.SOFT_DISABLE: soft_disable_alert("传感器数据无效"),
  },

  EventName.noGps: {
    ET.PERMANENT: no_gps_alert,
  },

  EventName.soundsUnavailable: {
    ET.PERMANENT: NormalPermanentAlert("未找到扬声器", "请重启设备"),
    ET.NO_ENTRY: NoEntryAlert("未找到扬声器"),
  },

  EventName.tooDistracted: {
    ET.NO_ENTRY: NoEntryAlert("分心程度过高"),
  },

  EventName.overheat: {
    ET.PERMANENT: overheat_alert,
    ET.SOFT_DISABLE: soft_disable_alert("System Overheated"),
    ET.NO_ENTRY: NoEntryAlert("System Overheated"),
  },

  EventName.wrongGear: {
    ET.SOFT_DISABLE: user_soft_disable_alert("Gear not D"),
    ET.NO_ENTRY: NoEntryAlert("Gear not D"),
  },

  # This alert is thrown when the calibration angles are outside of the acceptable range.
  # For example if the device is pointed too much to the left or the right.
  # Usually this can only be solved by removing the mount from the windshield completely,
  # and attaching while making sure the device is pointed straight forward and is level.
  # See https://comma.ai/setup for more information
  EventName.calibrationInvalid: {
    ET.PERMANENT: calibration_invalid_alert,
    ET.SOFT_DISABLE: soft_disable_alert("校准无效：重新安装设备并重新校准"),
    ET.NO_ENTRY: NoEntryAlert("校准无效：重新安装设备并重新校准"),
  },

  EventName.calibrationIncomplete: {
    ET.PERMANENT: calibration_incomplete_alert,
    ET.SOFT_DISABLE: soft_disable_alert("校准不完整"),
    ET.NO_ENTRY: NoEntryAlert("校准进行中"),
  },

  EventName.calibrationRecalibrating: {
    ET.PERMANENT: calibration_incomplete_alert,
    ET.SOFT_DISABLE: soft_disable_alert("检测到设备重新安装：正在重新校准"),
    ET.NO_ENTRY: NoEntryAlert("检测到重新安装：正在重新校准"),
  },

  EventName.doorOpen: {
    ET.SOFT_DISABLE: user_soft_disable_alert("车门打开"),
    ET.NO_ENTRY: NoEntryAlert("车门打开"),
  },

  EventName.seatbeltNotLatched: {
    ET.SOFT_DISABLE: user_soft_disable_alert("安全带未扣好"),
    ET.NO_ENTRY: NoEntryAlert("安全带未扣好"),
  },

  EventName.espDisabled: {
    ET.SOFT_DISABLE: soft_disable_alert("电子稳定控制已禁用"),
    ET.NO_ENTRY: NoEntryAlert("电子稳定控制已禁用"),
  },

  EventName.lowBattery: {
    ET.SOFT_DISABLE: soft_disable_alert("电池电量低"),
    ET.NO_ENTRY: NoEntryAlert("电池电量低"),
  },

  # Different openpilot services communicate between each other at a certain
  # interval. If communication does not follow the regular schedule this alert
  # is thrown. This can mean a service crashed, did not broadcast a message for
  # ten times the regular interval, or the average interval is more than 10% too high.
  EventName.commIssue: {
    ET.SOFT_DISABLE: soft_disable_alert("进程间通信问题"),
    ET.NO_ENTRY: comm_issue_alert,
  },
  EventName.commIssueAvgFreq: {
    ET.SOFT_DISABLE: soft_disable_alert("进程间通信速率低"),
    ET.NO_ENTRY: NoEntryAlert("进程间通信速率低"),
  },

  EventName.controlsdLagging: {
    ET.SOFT_DISABLE: soft_disable_alert("控制延迟"),
    ET.NO_ENTRY: NoEntryAlert("控制进程延迟：请重启设备"),
  },

  # Thrown when manager detects a service exited unexpectedly while driving
  EventName.processNotRunning: {
    ET.NO_ENTRY: process_not_running_alert,
    ET.SOFT_DISABLE: soft_disable_alert("进程未运行"),
  },

  EventName.radarFault: {
    ET.SOFT_DISABLE: soft_disable_alert("雷达错误：请重启汽车"),
    ET.NO_ENTRY: NoEntryAlert("雷达错误：请重启汽车"),
  },

  # Every frame from the camera should be processed by the model. If modeld
  # is not processing frames fast enough they have to be dropped. This alert is
  # thrown when over 20% of frames are dropped.
  EventName.modeldLagging: {
    ET.SOFT_DISABLE: soft_disable_alert("驾驶模型延迟"),
    ET.NO_ENTRY: NoEntryAlert("驾驶模型延迟"),
    ET.PERMANENT: modeld_lagging_alert,
  },

  # Besides predicting the path, lane lines and lead car data the model also
  # predicts the current velocity and rotation speed of the car. If the model is
  # very uncertain about the current velocity while the car is moving, this
  # usually means the model has trouble understanding the scene. This is used
  # as a heuristic to warn the driver.
  EventName.posenetInvalid: {
    ET.SOFT_DISABLE: soft_disable_alert("姿态网络速度无效"),
    ET.NO_ENTRY: posenet_invalid_alert,
  },

  # When the localizer detects an acceleration of more than 40 m/s^2 (~4G) we
  # alert the driver the device might have fallen from the windshield.
  EventName.deviceFalling: {
    ET.SOFT_DISABLE: soft_disable_alert("设备从支架上掉落"),
    ET.NO_ENTRY: NoEntryAlert("设备从支架上掉落"),
  },

  EventName.lowMemory: {
    ET.SOFT_DISABLE: soft_disable_alert("内存不足：请重启设备"),
    ET.PERMANENT: low_memory_alert,
    ET.NO_ENTRY: NoEntryAlert("内存不足：请重启设备"),
  },

  EventName.highCpuUsage: {
    #ET.SOFT_DISABLE: soft_disable_alert("System Malfunction: Reboot Your Device"),
    #ET.PERMANENT: NormalPermanentAlert("System Malfunction", "Reboot your Device"),
    ET.NO_ENTRY: high_cpu_usage_alert,
  },

  EventName.accFaulted: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("巡航故障：重启汽车"),
    ET.PERMANENT: NormalPermanentAlert("巡航故障：重启汽车以启用"),
    ET.NO_ENTRY: NoEntryAlert("巡航故障：重启汽车"),
  },

  EventName.controlsMismatch: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("控制不匹配"),
    ET.NO_ENTRY: NoEntryAlert("控制不匹配"),
  },

  EventName.roadCameraError: {
    ET.PERMANENT: NormalPermanentAlert("摄像头 CRC 错误 - 道路",
                                       duration=1.,
                                       creation_delay=30.),
  },

  EventName.wideRoadCameraError: {
    ET.PERMANENT: NormalPermanentAlert("摄像头 CRC 错误 - 道路鱼眼",
                                       duration=1.,
                                       creation_delay=30.),
  },

  EventName.driverCameraError: {
    ET.PERMANENT: NormalPermanentAlert("摄像头 CRC 错误 - 驾驶员",
                                       duration=1.,
                                       creation_delay=30.),
  },

  # 有时设备上的 USB 堆栈可能会进入不良状态
  # 导致与 panda 的连接丢失
  EventName.usbError: {
    ET.SOFT_DISABLE: soft_disable_alert("USB 错误：重启您的设备"),
    ET.PERMANENT: NormalPermanentAlert("USB 错误：重启您的设备", ""),
    ET.NO_ENTRY: NoEntryAlert("USB 错误：重启您的设备"),
  },

  # 此警报可能因以下原因触发：
  # - 根本没有接收到 CAN 数据
  # - 收到了 CAN 数据，但某些消息未按正确频率接收
  # 如果您没有编写新的汽车端口，这通常是由于接线故障
  EventName.canError: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("CAN 错误"),
    ET.PERMANENT: Alert(
      "CAN 错误：检查连接",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1., creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("CAN 错误：检查连接"),
  },

  EventName.canBusMissing: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("CAN 总线断开"),
    ET.PERMANENT: Alert(
      "CAN 总线断开：可能是故障电缆",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.none, 1., creation_delay=1.),
    ET.NO_ENTRY: NoEntryAlert("CAN 总线断开：检查连接"),
  },

  EventName.steerUnavailable: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("LKAS 故障：重启汽车"),
    ET.PERMANENT: NormalPermanentAlert("LKAS 故障：重启汽车以启用"),
    ET.NO_ENTRY: NoEntryAlert("LKAS 故障：重启汽车"),
  },

  EventName.reverseGear: {
    ET.PERMANENT: Alert(
      "倒车\n档",
      "",
      AlertStatus.normal, AlertSize.full,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .2, creation_delay=0.5),
    ET.USER_DISABLE: ImmediateDisableAlert("倒车档"),
    ET.NO_ENTRY: NoEntryAlert("倒车档"),
  },

  # On cars that use stock ACC the car can decide to cancel ACC for various reasons.
  # When this happens we can no long control the car so the user needs to be warned immediately.
  EventName.cruiseDisabled: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("巡航已关闭"),
  },

  EventName.relayMalfunction: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("线束继电器故障"),
    ET.PERMANENT: NormalPermanentAlert("线束继电器故障", "检查硬件"),
    ET.NO_ENTRY: NoEntryAlert("线束继电器故障"),
  },

  EventName.speedTooLow: {
    ET.IMMEDIATE_DISABLE: Alert(
      "openpilot已取消",
      "速度过低",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGH, VisualAlert.none, AudibleAlert.disengage, 3.),
  },

  EventName.speedTooHigh: {
    ET.WARNING: Alert(
      "速度过高",
      "在此速度下模型不确定",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.HIGH, VisualAlert.steerRequired, AudibleAlert.promptRepeat, 4.),
    ET.NO_ENTRY: NoEntryAlert("减速以启用"),
  },

  EventName.lowSpeedLockout: {
    ET.PERMANENT: NormalPermanentAlert("巡航故障：重启汽车以启用"),
    ET.NO_ENTRY: NoEntryAlert("巡航故障：重启汽车"),
  },

  EventName.lkasDisabled: {
    ET.PERMANENT: NormalPermanentAlert("LKAS已禁用：启用LKAS以启用"),
    ET.NO_ENTRY: NoEntryAlert("LKAS已禁用"),
  },

  EventName.vehicleSensorsInvalid: {
    ET.IMMEDIATE_DISABLE: ImmediateDisableAlert("车辆传感器无效"),
    ET.PERMANENT: NormalPermanentAlert("车辆传感器正在校准", "驾驶以校准"),
    ET.NO_ENTRY: NoEntryAlert("车辆传感器正在校准"),
  },

  EventName.blockUser: {
    ET.NO_ENTRY: NoEntryAlert("请不要使用 'Development' 分支！"),
  },

  EventName.goatSteerSaturated: {
    ET.WARNING: Alert(
      "转向超过限制",
      "耶稣，请掌舵！！",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.goat, 2.),
  },

  EventName.greenLight: {
    ET.PERMANENT: Alert(
      "灯变为绿色",
      "",
      AlertStatus.frogpilot, AlertSize.small,
      Priority.MID, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

  EventName.holidayActive: {
    ET.PERMANENT: holiday_alert,
  },

  EventName.laneChangeBlockedLoud: {
    ET.WARNING: Alert(
      "盲区检测到车辆",
      "",
      AlertStatus.userPrompt, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.warningSoft, .1),
  },

  EventName.leadDeparting: {
    ET.PERMANENT: Alert(
      "前车已离开",
      "",
      AlertStatus.frogpilot, AlertSize.small,
      Priority.MID, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

  EventName.noLaneAvailable : {
    ET.PERMANENT: no_lane_available_alert,
  },

  EventName.openpilotCrashed: {
    ET.PERMANENT: Alert(
      "openpilot 崩溃",
      "请在 FrogPilot Discord 中发布错误日志！",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGHEST, VisualAlert.none, AudibleAlert.none, 10.),
  },

  EventName.pedalInterceptorNoBrake: {
    ET.WARNING: Alert(
      "刹车不可用",
      "切换到 L",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.HIGH, VisualAlert.wrongGear, AudibleAlert.promptRepeat, 4.),
  },

  EventName.speedLimitChanged: {
    ET.PERMANENT: Alert(
      "速度限制已更改",
      "",
      AlertStatus.frogpilot, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.prompt, 3.),
  },

  EventName.torqueNNLoad: {
    ET.PERMANENT: torque_nn_load_alert,
  },

  EventName.turningLeft: {
    ET.WARNING: Alert(
      "左转",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1, alert_rate=0.75),
  },

  EventName.turningRight: {
    ET.WARNING: Alert(
      "右转",
      "",
      AlertStatus.normal, AlertSize.small,
      Priority.LOWEST, VisualAlert.none, AudibleAlert.none, .1, alert_rate=0.75),
  },

  # Random Events
  EventName.accel30: {
    ET.WARNING: Alert(
      "哇，你开得有点快！",
      "(⁄ ⁄•⁄ω⁄•⁄ ⁄)",
      AlertStatus.frogpilot, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.uwu, 4.),
  },

  EventName.accel35: {
    ET.WARNING: Alert(
      "我不会给你树五十的",
      "你这个该死的尼斯湖水怪！",
      AlertStatus.frogpilot, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.nessie, 4.),
  },

  EventName.accel40: {
    ET.WARNING: Alert(
      "太棒了，斯科特！",
      "🚗💨",
      AlertStatus.frogpilot, AlertSize.mid,
      Priority.LOW, VisualAlert.none, AudibleAlert.doc, 4.),
  },

  EventName.firefoxSteerSaturated: {
    ET.WARNING: Alert(
      "转向超过限制",
      "IE 已停止响应...",
      AlertStatus.userPrompt, AlertSize.mid,
      Priority.LOW, VisualAlert.steerRequired, AudibleAlert.firefox, 4.),
  },

  EventName.openpilotCrashedRandomEvents: {
    ET.PERMANENT: Alert(
      "openpilot 崩溃 💩",
      "请在 FrogPilot Discord 中发布错误日志！",
      AlertStatus.normal, AlertSize.mid,
      Priority.HIGHEST, VisualAlert.none, AudibleAlert.fart, 10.),
  },

  EventName.vCruise69: {
    ET.PERMANENT: Alert(
      "哈哈 69",
      "",
      AlertStatus.frogpilot, AlertSize.small,
      Priority.LOW, VisualAlert.none, AudibleAlert.noice, 2.),
  },

  EventName.yourFrogTriedToKillMe: {
    ET.PERMANENT: Alert(
      "你的青蛙试图杀了我...",
      "👺",
      AlertStatus.frogpilot, AlertSize.mid,
      Priority.MID, VisualAlert.none, AudibleAlert.angry, 5.),
  },
}


if __name__ == '__main__':
  # print all alerts by type and priority
  from cereal.services import SERVICE_LIST
  from collections import defaultdict

  event_names = {v: k for k, v in EventName.schema.enumerants.items()}
  alerts_by_type: dict[str, dict[Priority, list[str]]] = defaultdict(lambda: defaultdict(list))

  CP = car.CarParams.new_message()
  CS = car.CarState.new_message()
  sm = messaging.SubMaster(list(SERVICE_LIST.keys()))

  for i, alerts in EVENTS.items():
    for et, alert in alerts.items():
      if callable(alert):
        alert = alert(CP, CS, sm, False, 1)
      alerts_by_type[et][alert.priority].append(event_names[i])

  all_alerts: dict[str, list[tuple[Priority, list[str]]]] = {}
  for et, priority_alerts in alerts_by_type.items():
    all_alerts[et] = sorted(priority_alerts.items(), key=lambda x: x[0], reverse=True)

  for status, evs in sorted(all_alerts.items(), key=lambda x: x[0]):
    print(f"**** {status} ****")
    for p, alert_list in evs:
      print(f"  {repr(p)}:")
      print("   ", ', '.join(alert_list), "\n")
