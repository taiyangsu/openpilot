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
import time

# Define CSLC related constants
V_CRUISE_MAX = 144  # 144 km/h = 90 mph
V_CRUISE_MIN = 30   # 30 km/h
V_CRUISE_DELTA = 5  # 5 km/h increments
CX5_2022_V_CRUISE_MIN = 25  # CX5 2022 can use lower min speed

VisualAlert = structs.CarControl.HUDControl.VisualAlert

# Use shared memory for parameters to improve performance
params_memory = Params("/dev/shm/params")

class CarController(CarControllerBase):
  def __init__(self, dbc_names, CP):
    super().__init__(dbc_names, CP)
    self.CP = CP
    self.apply_steer_last = 0
    self.packer = CANPacker(dbc_names[Bus.pt])
    self.brake_counter = 0
    self.frame = 0

    # Initialize speed filter for smoother transitions
    self.speed_filter = FirstOrderFilter(0.0, 0.2, DT_CTRL, initialized=False)
    self.filtered_speed_last = 0

    # Button control state tracking
    self.last_button_frame = 0
    self.button_frame_threshold = 8 if CP.carFingerprint == CAR.MAZDA_CX5_2022 else 10
    self.resuming_count = 0
    self.last_button_sent = Buttons.NONE

    # Initialize CSLC related parameters
    self.activateCruise = 0
    self.speed_from_pcm = 1
    self.is_metric = True
    self.resume_required = False
    self.last_speed_change_time = 0

    # Create Params instance
    self.params = Params()

    # Initialize experimental mode and CSLC status
    try:
      self.experimental_mode = self.params.get_bool("ExperimentalMode")
    except:
      self.experimental_mode = False

    try:
      self.cslc_enabled = self.params.get_bool("CSLCEnabled")
    except:
      self.cslc_enabled = False

    # If experimental mode is on, ensure CSLC is also on
    if self.experimental_mode and not self.cslc_enabled:
      self.params.put_bool("CSLCEnabled", True)
      self.cslc_enabled = True

    # Check if the vehicle is CX5 2022
    self.is_cx5_2022 = CP.carFingerprint == CAR.MAZDA_CX5_2022

  def update(self, CC, CS, now_nanos):
    # Update parameters every 25 frames to improve performance
    if self.frame % 25 == 0:
      try:
        # Get parameters with safe defaults
        try:
          self.speed_from_pcm = self.params.get_int("SpeedFromPCM")
        except:
          self.speed_from_pcm = 1

        try:
          self.is_metric = self.params.get_bool("IsMetric")
        except:
          self.is_metric = True

        # Read experimental mode and CSLC status
        try:
          self.experimental_mode = self.params.get_bool("ExperimentalMode")
        except:
          self.experimental_mode = False

        try:
          self.cslc_enabled = self.params.get_bool("CSLCEnabled")
        except:
          self.cslc_enabled = False

        # If experimental mode is on, ensure CSLC is also on
        if self.experimental_mode and not self.cslc_enabled:
          self.params.put_bool("CSLCEnabled", True)
          self.cslc_enabled = True

      except Exception as e:
        print(f"Error updating parameters: {e}")
        # Keep current state

    hud_control = CC.hudControl
    hud_v_cruise = hud_control.setSpeed
    if hud_v_cruise > 70:
      hud_v_cruise = 0

    actuators = CC.actuators
    accel = actuators.accel if hasattr(actuators, 'accel') else 0

    can_sends = []

    apply_steer = 0

    if CC.latActive:
      # Calculate steer and apply driver torque limits
      new_steer = int(round(CC.actuators.steer * CarControllerParams.STEER_MAX))
      apply_steer = apply_driver_steer_torque_limits(new_steer, self.apply_steer_last,
                                                    CS.out.steeringTorque, CarControllerParams)

    # Check for resume conditions
    # When vehicle stops for more than 3 seconds, Mazda requires RESUME button or gas pedal
    is_stopped = CS.out.standstill
    car_moving = not is_stopped and CS.out.vEgo < 0.5
    needs_resume = is_stopped and self.resume_required

    # Update resume state
    if is_stopped:
      self.resume_required = True
    elif car_moving and self.resume_required:
      # Only reset when car actually starts moving
      if CS.out.vEgo > 0.1:
        self.resume_required = False

    if CC.cruiseControl.cancel:
      # Wait a bit before sending cancel to avoid race condition
      self.brake_counter = self.brake_counter + 1
      if self.frame % 10 == 0 and not (CS.out.brakePressed and self.brake_counter < 7):
        # Cancel Stock ACC if enabled while OP is disengaged
        can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, Buttons.CANCEL))
        self.last_button_sent = Buttons.CANCEL
    else:
      self.brake_counter = 0

      # Special handling for resume
      if CC.cruiseControl.resume or needs_resume:
        # Only send RESUME every 5 frames and limit number of consecutive RESUME commands
        if self.frame % 5 == 0 and self.resuming_count < 6:
          can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, Buttons.RESUME))
          self.last_button_sent = Buttons.RESUME
          self.resuming_count += 1
        # Reset counter when not sending RESUME
        elif self.frame % 5 != 0:
          self.resuming_count = 0

      # Brake lights condition for cruise activation
      elif CS.out.activateCruise and CS.cruiseStateActive and CS.out.brakeLights:
        can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, Buttons.RESUME))
        self.last_button_sent = Buttons.RESUME

      # Experimental mode or CSLC function - automatic speed control
      elif (self.experimental_mode or self.cslc_enabled) and not needs_resume:
        # Rate limiting for button commands
        current_time = time.time()
        time_since_last_button = current_time - self.last_speed_change_time

        # Avoid sending buttons too frequently
        if (self.frame - self.last_button_frame > self.button_frame_threshold and
            time_since_last_button > 0.1 and
            getattr(CS, 'cruise_buttons', Buttons.NONE) == Buttons.NONE and
            not CS.out.gasPressed and
            not getattr(CS, 'distance_button', 0)):

          button_cmd = self.get_speed_button(CS, hud_v_cruise)

          if button_cmd != Buttons.NONE:
            can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, button_cmd))
            self.last_button_sent = button_cmd
            self.last_button_frame = self.frame
            self.last_speed_change_time = current_time
      else:
        # Original button control logic
        if self.frame % 20 == 0:
          spam_button = self.make_spam_button(CC, CS)
          if spam_button > 0:
            self.brake_counter = 0
            can_sends.append(mazdacan.create_button_cmd(self.packer, self.CP, CS.crz_btns_counter, spam_button))
            self.last_button_sent = spam_button

    self.apply_steer_last = apply_steer

    # Send HUD alerts
    if self.frame % 50 == 0:
      ldw = CC.hudControl.visualAlert == VisualAlert.ldw
      steer_required = CC.hudControl.visualAlert == VisualAlert.steerRequired
      # Show steer required warning only when LKAS is allowed
      steer_required = steer_required and CS.lkas_allowed_speed
      can_sends.append(mazdacan.create_alert_command(self.packer, CS.cam_laneinfo, ldw, steer_required))

    # Send steering command
    can_sends.append(mazdacan.create_steering_control(self.packer, self.CP,
                                                     self.frame, apply_steer, CS.cam_lkas))

    new_actuators = CC.actuators.as_builder()
    new_actuators.steer = apply_steer / CarControllerParams.STEER_MAX
    new_actuators.steerOutputCan = apply_steer

    self.frame += 1
    return new_actuators, can_sends

  def get_speed_button(self, CS, target_speed_ms):
    """
    Calculate speed button command with optimized logic for CX5 2022

    Args:
        CS: CarState object
        target_speed_ms: Target speed in m/s

    Returns:
        Button command (Buttons.SET_PLUS, Buttons.SET_MINUS, Buttons.RESUME, Buttons.NONE)
    """
    # Special handling for stopped vehicle
    if CS.out.standstill:
      return Buttons.RESUME

    # Convert m/s to km/h
    target_speed_kph = target_speed_ms * CV.MS_TO_KPH

    # Try to read CSLC speed from shared memory
    try:
      cslc_speed = params_memory.get_float("CSLCSpeed")
      if cslc_speed > 0:
        target_speed_kph = cslc_speed
    except:
      pass

    # Set min speed based on vehicle type
    min_speed = CX5_2022_V_CRUISE_MIN if self.is_cx5_2022 else V_CRUISE_MIN

    # Limit target speed to valid range
    target_speed_kph = min(max(target_speed_kph, min_speed), V_CRUISE_MAX)

    # Get current cruise speed
    current_cruise_kph = CS.out.cruiseState.speed * CV.MS_TO_KPH if hasattr(CS.out.cruiseState, 'speed') else 0
    current_speed_kph = CS.out.vEgo * CV.MS_TO_KPH

    # Apply speed filter for smoother transitions
    if self.speed_filter.x != target_speed_kph:
      # Adjust filter parameters based on speed difference
      speed_diff = abs(target_speed_kph - self.filtered_speed_last)
      alpha = 0.1 if speed_diff < 10 else (0.2 if speed_diff < 20 else 0.3)
      self.speed_filter.update_alpha(alpha)
      filtered_target = self.speed_filter.update(target_speed_kph)
      self.filtered_speed_last = filtered_target
      target_speed_kph = filtered_target

    # Round speeds to increments
    target_speed_kph = round(target_speed_kph / V_CRUISE_DELTA) * V_CRUISE_DELTA
    current_cruise_kph = round(current_cruise_kph / V_CRUISE_DELTA) * V_CRUISE_DELTA

    # Set threshold to avoid frequent adjustments
    threshold = 6.0 if self.is_cx5_2022 else 5.0

    # Calculate speed difference
    speed_diff = target_speed_kph - current_cruise_kph

    # Don't send command if difference is too small
    if abs(speed_diff) < threshold:
      return Buttons.NONE

    # Send SET+ or SET- based on speed difference
    if speed_diff > 0:
      return Buttons.SET_PLUS
    elif speed_diff < 0 and current_cruise_kph > (min_speed + 5):  # Ensure we don't go below min speed
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
          return Buttons.RESUME
      elif CC.cruiseControl.resume:
        return Buttons.RESUME
      elif target < current and current>= 31 and self.speed_from_pcm != 1:
        return Buttons.SET_MINUS
      elif target > current and current < 160 and self.speed_from_pcm != 1:
        return Buttons.SET_PLUS
    elif CS.out.activateCruise:
      if (hud_control.leadVisible or v_ego_kph > 10.0) and self.activateCruise == 0 and not cant_activate:
        self.activateCruise = 1
        return Buttons.RESUME

    return 0
