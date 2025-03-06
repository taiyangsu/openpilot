from opendbc.can.packer import CANPacker
from opendbc.car import Bus, apply_driver_steer_torque_limits, structs
from opendbc.car.interfaces import CarControllerBase
from opendbc.car.mazda import mazdacan
from opendbc.car.mazda.values import CAR, CarControllerParams, Buttons
from opendbc.car.common.conversions import Conversions as CV
from openpilot.common.params import Params
from openpilot.common.realtime import DT_CTRL
from openpilot.common.filter_simple import FirstOrderFilter
import os

# 定义CSLC相关常量
V_CRUISE_MAX = 144  # 144 km/h = 90 mph
V_CRUISE_MIN = 30   # 30 km/h
V_CRUISE_DELTA = 5  # 5 km/h增量

# CX5 2022特殊常量
CX5_2022_V_CRUISE_MIN = 25   # CX5 2022可以设置更低的最小速度

VisualAlert = structs.CarControl.HUDControl.VisualAlert

# 使用共享内存参数，提高性能
params_memory = Params("/dev/shm/params")

class CarController(CarControllerBase):
  def __init__(self, dbc_names, CP):
    super().__init__(dbc_names, CP)
    self.CP = CP
    self.apply_steer_last = 0
    self.packer = CANPacker(dbc_names[Bus.pt])
    self.brake_counter = 0
    self.frame = 0

    # 初始化速度滤波器
    self.speed_filter = FirstOrderFilter(0.0, 0.2, DT_CTRL, initialized=False)
    self.filtered_speed_last = 0

    # 初始化CSLC相关参数
    self.activateCruise = 0
    self.speed_from_pcm = 1
    self.is_metric = True
    self.resume_required = False
    self.last_button_frame = 0
    self.button_counter = 0

    # 创建Params实例
    self.params = Params()

    # 初始化实验模式和CSLC状态
    try:
      self.experimental_mode = self.params.get_bool("ExperimentalMode")
    except:
      self.experimental_mode = False

    try:
      self.cslc_enabled = self.params.get_bool("CSLCEnabled")
    except:
      self.cslc_enabled = False

    # 如果实验模式已开启，确保CSLC也开启
    if self.experimental_mode and not self.cslc_enabled:
      self.params.put_bool("CSLCEnabled", True)
      self.cslc_enabled = True

  def update(self, CC, CS, now_nanos):
    # 每30帧更新一次参数，提高性能
    if self.frame % 30 == 0:
      try:
        # 使用安全的方式获取参数，提供默认值
        try:
          self.speed_from_pcm = self.params.get_int("SpeedFromPCM")
        except:
          self.speed_from_pcm = 1

        try:
          self.is_metric = self.params.get_bool("IsMetric")
        except:
          self.is_metric = True

        # 读取实验模式和CSLC状态
        try:
          self.experimental_mode = self.params.get_bool("ExperimentalMode")
        except:
          self.experimental_mode = False

        try:
          self.cslc_enabled = self.params.get_bool("CSLCEnabled")
        except:
          self.cslc_enabled = False

        # 如果实验模式已开启，确保CSLC也开启
        if self.experimental_mode and not self.cslc_enabled:
          self.params.put_bool("CSLCEnabled", True)
          self.cslc_enabled = True

      except Exception as e:
        print(f"更新参数时出错: {e}")
        # 使用默认值，不改变当前状态

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

    # 检查是否需要恢复巡航
    # 当车辆停止超过3秒后，马自达需要按下RES或踩油门才能重新启动
    is_cx5_2022 = self.CP.carFingerprint == CAR.MAZDA_CX5_2022
    car_stopping = CS.out.vEgo < 0.1
    car_starting = (not car_stopping) and (CS.out.vEgo < 1.0) and self.resume_required

    # 在车辆启动时更新状态
    if car_stopping:
      self.resume_required = True
    elif not car_stopping and self.resume_required and car_starting:
      self.resume_required = False

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

      # 特别处理CX5 2022的恢复巡航情况
      if (CC.cruiseControl.resume or car_starting) and self.frame % 5 == 0:
        # Mazda Stop and Go requires a RES button (or gas) press if the car stops more than 3 seconds
        # Send Resume button when planner wants car to move
        can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, Buttons.RESUME))
      elif CS.out.activateCruise and CS.cruiseStateActive and CS.out.brakeLights:
        can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, Buttons.RESUME))
      # 实验模式或CSLC功能 - 自动控制车速
      elif (self.experimental_mode or self.cslc_enabled) and not car_starting:
        # 避免发送过于频繁的按钮命令，特别是对于CX5 2022
        button_interval = 8 if is_cx5_2022 else 10

        if CC.enabled and (self.frame - self.last_button_frame >= button_interval) and getattr(CS, 'cruise_buttons', Buttons.NONE) == Buttons.NONE and not CS.out.gasPressed and not getattr(CS, 'distance_button', 0):
          button_cmd = self.get_speed_button(CS, hud_v_cruise)
          if button_cmd != Buttons.NONE:
            can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, button_cmd))
            self.last_button_frame = self.frame
            self.button_counter += 1
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

  def get_speed_button(self, CS, target_speed_ms):
    """
    为CX5 2022优化的速度按钮命令计算

    参数:
    - CS: 车辆状态
    - target_speed_ms: 目标速度(m/s)

    返回:
    - 按钮命令(Buttons.SET_PLUS, Buttons.SET_MINUS, Buttons.RESUME, Buttons.NONE)
    """
    # 将m/s转换为km/h
    target_speed_kph = target_speed_ms * CV.MS_TO_KPH

    # 尝试从共享内存读取CSLCSpeed
    try:
      cslc_speed = params_memory.get_float("CSLCSpeed")
      if cslc_speed > 0:
        target_speed_kph = cslc_speed
    except:
      pass

    # 检查是否为CX5 2022
    is_cx5_2022 = self.CP.carFingerprint == CAR.MAZDA_CX5_2022
    min_speed = CX5_2022_V_CRUISE_MIN if is_cx5_2022 else V_CRUISE_MIN

    # 限制目标速度在合理范围内
    target_speed_kph = min(max(target_speed_kph, min_speed), V_CRUISE_MAX)

    # 获取当前车速和巡航速度
    current_speed_kph = CS.out.vEgo * CV.MS_TO_KPH
    current_cruise_kph = CS.out.cruiseState.speed * CV.MS_TO_KPH if hasattr(CS.out.cruiseState, 'speed') else 0

    # 将速度调整为5km/h的倍数
    target_speed_kph = round(target_speed_kph / V_CRUISE_DELTA) * V_CRUISE_DELTA
    current_cruise_kph = round(current_cruise_kph / V_CRUISE_DELTA) * V_CRUISE_DELTA

    # 应用速度滤波器平滑转换
    if self.speed_filter.x != target_speed_kph:
      # 根据变化幅度调整滤波器参数
      speed_diff = abs(target_speed_kph - self.filtered_speed_last)
      alpha = 0.1 if speed_diff < 10 else (0.2 if speed_diff < 20 else 0.3)
      self.speed_filter.update_alpha(alpha)
      filtered_target = self.speed_filter.update(target_speed_kph)
      self.filtered_speed_last = filtered_target
      target_speed_kph = round(filtered_target / V_CRUISE_DELTA) * V_CRUISE_DELTA

    # 车辆停止状态下需要RESUME
    if CS.out.standstill and current_speed_kph < 0.1:
      return Buttons.RESUME

    # CX5 2022处理逻辑优化
    if is_cx5_2022:
      # CX5 2022对按钮响应比较慢，需要更大的速度差阈值
      threshold = V_CRUISE_DELTA * 1.2
      # 根据目标速度和当前速度计算按钮命令
      speed_diff = target_speed_kph - current_cruise_kph

      # 只有当速度差大于阈值时才发送命令，避免频繁切换
      if abs(speed_diff) >= threshold:
        if speed_diff > 0:
          return Buttons.SET_PLUS
        elif speed_diff < 0:
          return Buttons.SET_MINUS
    else:
      # 其他马自达车型的标准逻辑
      if target_speed_kph > current_cruise_kph:
        return Buttons.SET_PLUS
      elif target_speed_kph < current_cruise_kph:
        return Buttons.SET_MINUS

    return Buttons.NONE

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
