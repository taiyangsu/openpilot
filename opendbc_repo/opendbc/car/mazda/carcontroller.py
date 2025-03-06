from opendbc.can.packer import CANPacker
from opendbc.car import Bus, apply_driver_steer_torque_limits, structs
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.mazda import mazdacan
from opendbc.car.mazda.values import CarControllerParams, Buttons
from opendbc.car.common.conversions import Conversions as CV
from openpilot.common.params import Params
# 移除V_CRUISE_MAX导入，自己定义常量
# from openpilot.selfdrive.controls.lib.drive_helpers import V_CRUISE_MAX
import os

# 定义CSLC相关常量
V_CRUISE_MAX = 144  # 144 km/h = 90 mph
V_CRUISE_MIN = 30   # 30 km/h
V_CRUISE_DELTA = 5  # 5 km/h增量

VisualAlert = structs.CarControl.HUDControl.VisualAlert

# 使用共享内存参数，提高性能
params_memory = Params("/dev/shm/params")

class CarController(CarControllerBase):
  def __init__(self, dbc_names, CP):
    super().__init__(dbc_names, CP)
    self.apply_steer_last = 0
    self.packer = CANPacker(dbc_names[Bus.pt])
    self.brake_counter = 0
    self.frame = 0

    # 初始化CSLC相关参数
    self.activateCruise = 0
    self.speed_from_pcm = 1
    self.is_metric = True
    self.experimental_mode = False
    self.cslc_enabled = self._read_cslc_param()

  def _read_cslc_param(self):
    """读取CSLCEnabled参数的值"""
    try:
        if os.path.exists("/data/params/d/CSLCEnabled"):
            with open("/data/params/d/CSLCEnabled", "rb") as f:
                value = f.read()
                # 如果值为1（二进制01），则启用CSLC
                return (value == b'\x01')
        return False
    except Exception as e:
        print(f"读取CSLCEnabled参数时出错: {e}")
        return False

  def update(self, CC, CS, now_nanos):
    # 每50帧更新一次参数
    if self.frame % 50 == 0:
      try:
        params = Params()
        # 使用安全的方式获取参数，提供默认值
        try:
          self.speed_from_pcm = params.get_int("SpeedFromPCM")
        except:
          self.speed_from_pcm = 1

        try:
          self.is_metric = params.get_bool("IsMetric")
        except:
          self.is_metric = True

        # 读取CSLC参数值，而不是检查文件存在
        self.cslc_enabled = self._read_cslc_param()

        try:
          self.experimental_mode = params.get_bool("ExperimentalMode")
        except:
          self.experimental_mode = False
      except Exception as e:
        print(f"更新参数时出错: {e}")
        # 使用默认值
        self.speed_from_pcm = 1
        self.is_metric = True
        self.cslc_enabled = False
        self.experimental_mode = False

    hud_control = CC.hudControl
    hud_v_cruise = hud_control.setSpeed
    if hud_v_cruise > 70:
      hud_v_cruise = 0

    actuators = CC.actuators
    accel = actuators.accel if hasattr(actuators, 'accel') else 0

    can_sends = []

    apply_steer = 0

    if CC.latActive:
      # calculate steer and also set limits due to driver torque
      new_steer = int(round(CC.actuators.steer * CarControllerParams.STEER_MAX))
      apply_steer = apply_driver_steer_torque_limits(new_steer, self.apply_steer_last,
                                                     CS.out.steeringTorque, CarControllerParams)

    if CC.cruiseControl.cancel:
      # If brake is pressed, let us wait >70ms before trying to disable crz to avoid
      # a race condition with the stock system, where the second cancel from openpilot
      # will disable the crz 'main on'. crz ctrl msg runs at 50hz. 70ms allows us to
      # read 3 messages and most likely sync state before we attempt cancel.
      self.brake_counter = self.brake_counter + 1
      if self.frame % 10 == 0 and not (CS.out.brakePressed and self.brake_counter < 7):
        # Cancel Stock ACC if it's enabled while OP is disengaged
        # Send at a rate of 10hz until we sync with stock ACC state
        can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, Buttons.CANCEL))
    else:
      self.brake_counter = 0
      if CC.cruiseControl.resume and self.frame % 5 == 0:
        # Mazda Stop and Go requires a RES button (or gas) press if the car stops more than 3 seconds
        # Send Resume button when planner wants car to move
        can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, Buttons.RESUME))
      elif CS.out.activateCruise and CS.cruiseStateActive and CS.out.brakeLights:
        can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, Buttons.RESUME))
      # CSLC功能 - 自动控制车速
      elif self.cslc_enabled:
        if CC.enabled and self.frame % 10 == 0 and getattr(CS, 'cruise_buttons', Buttons.NONE) == Buttons.NONE and not CS.out.gasPressed and not getattr(CS, 'distance_button', 0):
          slcSet = get_set_speed(self, hud_v_cruise)
          if slcSet != Buttons.NONE:
            can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, slcSet))
      else:
        # 原有的按钮控制逻辑
        if self.frame % 20 == 0:
          spam_button = self.make_spam_button(CC, CS)
          if spam_button > 0:
            self.brake_counter = 0
            can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, self.frame // 10, spam_button))

    self.apply_steer_last = apply_steer

    # send HUD alerts
    if self.frame % 50 == 0:
      ldw = CC.hudControl.visualAlert == VisualAlert.ldw
      steer_required = CC.hudControl.visualAlert == VisualAlert.steerRequired
      # TODO: find a way to silence audible warnings so we can add more hud alerts
      steer_required = steer_required and CS.lkas_allowed_speed
      can_sends.append(mazdacan.create_alert_command(self.packer, CS.cam_laneinfo, ldw, steer_required))

    # send steering command
    can_sends.append(mazdacan.create_steering_control(self.packer, self.CP,
                                                      self.frame, apply_steer, CS.cam_lkas))

    new_actuators = CC.actuators.as_builder()
    new_actuators.steer = apply_steer / CarControllerParams.STEER_MAX
    new_actuators.steerOutputCan = apply_steer

    self.frame += 1
    return new_actuators, can_sends

  def make_spam_button(self, CC, CS):
    hud_control = CC.hudControl
    set_speed_in_units = hud_control.setSpeed * (CV.MS_TO_KPH if CS.is_metric else CV.MS_TO_MPH)
    target = int(set_speed_in_units+0.5)
    target = int(round(target / 5.0) * 5.0)
    current = int(CS.out.cruiseState.speed*CV.MS_TO_KPH + 0.5)
    current = int(round(current / 5.0) * 5.0)
    v_ego_kph = CS.out.vEgo * CV.MS_TO_KPH

    cant_activate = CS.out.brakePressed or CS.out.gasPressed

    if CC.enabled:
      if not CS.out.cruiseState.enabled:
        if (hud_control.leadVisible or v_ego_kph > 10.0) and self.activateCruise == 0 and not cant_activate:
          self.activateCruise = 1
          print("RESUME")
          return Buttons.RESUME
      elif CC.cruiseControl.resume:
        return Buttons.RESUME
      elif target < current and current>= 31 and self.speed_from_pcm != 1:
        print(f"SET_MINUS target={target}, current={current}")
        return Buttons.SET_MINUS
      elif target > current and current < 160 and self.speed_from_pcm != 1:
        print(f"SET_PLUS target={target}, current={current}")
        return Buttons.SET_PLUS
    elif CS.out.activateCruise:
      if (hud_control.leadVisible or v_ego_kph > 10.0) and self.activateCruise == 0 and not cant_activate:
        self.activateCruise = 1
        print("RESUME")
        return Buttons.RESUME

    return 0

def get_set_speed(self, hud_v_cruise):
  """
  获取目标速度

  参数:
  - hud_v_cruise: HUD显示的巡航速度

  返回:
  - 目标速度(m/s)
  """
  v_cruise = min(hud_v_cruise, V_CRUISE_MAX * CV.KPH_TO_MS)

  v_cruise_slc = params_memory.get_float("CSLCSpeed")

  if v_cruise_slc > 0.:
    v_cruise = v_cruise_slc

  return v_cruise
