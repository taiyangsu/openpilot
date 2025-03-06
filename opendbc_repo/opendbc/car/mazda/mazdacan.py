from opendbc.car.mazda.values import Buttons, MazdaFlags, CAR
from opendbc.car.common.conversions import Conversions as CV


def create_steering_control(packer, CP, frame, apply_steer, lkas):
  """
  Create steering control CAN message

  Args:
    packer: CAN message packer
    CP: Car Parameters
    frame: Current frame number
    apply_steer: Steering torque to apply
    lkas: LKAS information

  Returns:
    Packed CAN message
  """
  tmp = apply_steer + 2048

  lo = tmp & 0xFF
  hi = tmp >> 8

  # Copy values from camera
  b1 = int(lkas["BIT_1"])
  er1 = int(lkas["ERR_BIT_1"])
  lnv = 0
  ldw = 0
  er2 = int(lkas["ERR_BIT_2"])

  # Some older models have these fields, newer ones don't
  # Setting to 0 is fine either way
  steering_angle = 0
  b2 = 0

  tmp = steering_angle + 2048
  ahi = tmp >> 10
  amd = (tmp & 0x3FF) >> 2
  amd = (amd >> 4) | (( amd & 0xF) << 4)
  alo = (tmp & 0x3) << 2

  ctr = frame % 16
  # Byte:     [    1  ] [ 2 ] [             3               ]  [           4         ]
  csum = 249 - ctr - hi - lo - (lnv << 3) - er1 - (ldw << 7) - ( er2 << 4) - (b1 << 5)

  # Byte      [ 5 ] [ 6 ] [    7   ]
  csum = csum - ahi - amd - alo - b2

  if ahi == 1:
    csum = csum + 15

  if csum < 0:
    if csum < -256:
      csum = csum + 512
    else:
      csum = csum + 256

  csum = csum % 256

  # Create different CAN message based on car model
  values = {}
  if CP.flags & MazdaFlags.GEN1:
    values = {
      "LKAS_REQUEST": apply_steer,
      "CTR": ctr,
      "ERR_BIT_1": er1,
      "LINE_NOT_VISIBLE" : lnv,
      "LDW": ldw,
      "BIT_1": b1,
      "ERR_BIT_2": er2,
      "STEERING_ANGLE": steering_angle,
      "ANGLE_ENABLED": b2,
      "CHKSUM": csum
    }

  return packer.make_can_msg("CAM_LKAS", 0, values)


def create_alert_command(packer, cam_msg: dict, ldw: bool, steer_required: bool):
  """
  Create alert command CAN message

  Args:
    packer: CAN message packer
    cam_msg: Camera message
    ldw: Lane departure warning flag
    steer_required: Steering wheel warning flag

  Returns:
    Packed CAN message
  """
  values = {s: cam_msg[s] for s in [
    "LINE_VISIBLE",
    "LINE_NOT_VISIBLE",
    "LANE_LINES",
    "BIT1",
    "BIT2",
    "BIT3",
    "NO_ERR_BIT",
    "S1",
    "S1_HBEAM",
  ]}
  values.update({
    # Warning related fields
    "HANDS_WARN_3_BITS": 0b111 if steer_required else 0,
    "HANDS_ON_STEER_WARN": steer_required,
    "HANDS_ON_STEER_WARN_2": steer_required,

    # Lane departure warning
    "LDW_WARN_LL": 0,
    "LDW_WARN_RL": 0,
  })
  return packer.make_can_msg("CAM_LANEINFO", 0, values)


def create_button_cmd(packer, CP, counter, button):
  """
  Create button command CAN message

  Args:
    packer: CAN message packer
    CP: Car Parameters
    counter: Counter value
    button: Button type

  Returns:
    Packed CAN message
  """
  # Check if car is CX5 2022
  is_cx5_2022 = CP.carFingerprint == CAR.MAZDA_CX5_2022

  # Set flags for different buttons
  can = int(button == Buttons.CANCEL)
  res = int(button == Buttons.RESUME)
  inc = int(button == Buttons.SET_PLUS)
  dec = int(button == Buttons.SET_MINUS)

  if CP.flags & MazdaFlags.GEN1:
    values = {
      "CAN_OFF": can,
      "CAN_OFF_INV": (can + 1) % 2,

      "SET_P": inc,
      "SET_P_INV": (inc + 1) % 2,

      "RES": res,
      "RES_INV": (res + 1) % 2,

      "SET_M": dec,
      "SET_M_INV": (dec + 1) % 2,

      "DISTANCE_LESS": 0,
      "DISTANCE_LESS_INV": 1,

      "DISTANCE_MORE": 0,
      "DISTANCE_MORE_INV": 1,

      "MODE_X": 0,
      "MODE_X_INV": 1,

      "MODE_Y": 0,
      "MODE_Y_INV": 1,

      "BIT1": 1,
      "BIT2": 1,
      "BIT3": 1,
      "CTR": (counter + 1) % 16,
    }

    # Special handling for CX5 2022 buttons
    if is_cx5_2022:
      # Adjust CTR field growth rate for better responsiveness in CX5 2022
      if button != Buttons.NONE:
        values["CTR"] = (counter + 2) % 16

      # For CX5 2022, we need to set additional fields for better button recognition
      if CP.flags & MazdaFlags.CX5_2022:
        # Set special bit patterns for CX5 2022
        if button == Buttons.RESUME:
          values["BIT1"] = 0
          values["BIT2"] = 1
        elif button == Buttons.SET_PLUS:
          values["BIT1"] = 1
          values["BIT2"] = 0
        elif button == Buttons.SET_MINUS:
          values["BIT1"] = 0
          values["BIT2"] = 0

    return packer.make_can_msg("CRZ_BTNS", 0, values)


def create_cx5_2022_button_cmd(packer, counter, button):
  """
  Create CX5 2022 specific button command

  Args:
    packer: CAN message packer
    counter: Counter value
    button: Button type

  Returns:
    Packed CAN message
  """
  # This function creates CX5 2022 specific button commands
  # These are sent on a different CAN ID

  values = {
    "CTR": counter % 16,
    "BTN_STATE": 0,
    "RESPONSE_FACTOR": 0,
    "CX5_2022_STATUS": 0,
  }

  # Set button state based on button type
  if button == Buttons.RESUME:
    values["BTN_STATE"] = 1
    values["CX5_2022_RES_BTN"] = 1
    values["RESPONSE_FACTOR"] = 2
  elif button == Buttons.SET_PLUS:
    values["BTN_STATE"] = 2
    values["CX5_2022_RES_BTN"] = 0
    values["RESPONSE_FACTOR"] = 1
  elif button == Buttons.SET_MINUS:
    values["BTN_STATE"] = 3
    values["CX5_2022_RES_BTN"] = 0
    values["RESPONSE_FACTOR"] = 1
  else:
    values["BTN_STATE"] = 0
    values["CX5_2022_RES_BTN"] = 0
    values["RESPONSE_FACTOR"] = 0

  values["CX5_2022_STATUS"] = 1 if button != Buttons.NONE else 0

  return packer.make_can_msg("CX5_2022_BTNS", 0, values)


def create_mazda_acc_spam_command(packer, CP, CS, target_speed_ms, current_speed_ms, is_metric=True, experimental_mode=False, accel=0):
  """
  Create automatic speed control CAN messages

  Args:
    packer: CAN message packer
    CP: Car Parameters
    CS: Car State
    target_speed_ms: Target speed (m/s)
    current_speed_ms: Current speed (m/s)
    is_metric: Whether to use metric units
    experimental_mode: Whether to use experimental mode
    accel: Acceleration value

  Returns:
    List of CAN messages
  """
  cruiseBtn = Buttons.NONE
  can_sends = []

  # Check if car is CX5 2022
  is_cx5_2022 = CP.carFingerprint == CAR.MAZDA_CX5_2022
  has_cx5_2022_flag = CP.flags & MazdaFlags.CX5_2022

  # Unit conversion factor
  MS_CONVERT = CV.MS_TO_KPH if is_metric else CV.MS_TO_MPH

  # Get current and target speed values
  current_speed_units = current_speed_ms * MS_CONVERT
  cruise_speed_units = CS.cruiseState.speed * MS_CONVERT if hasattr(CS, 'cruiseState') and hasattr(CS.cruiseState, 'speed') else 0
  target_speed_units = target_speed_ms * MS_CONVERT

  # Handle vehicle standstill
  if CS.standstill:
    # For CX5 2022 with experimental mode, send both standard and CX5-specific RESUME
    if is_cx5_2022 and has_cx5_2022_flag and experimental_mode:
      can_sends.append(create_button_cmd(packer, CP, CS.crz_btns_counter, Buttons.RESUME))
      can_sends.append(create_cx5_2022_button_cmd(packer, CS.crz_btns_counter, Buttons.RESUME))
      return can_sends
    else:
      return [create_button_cmd(packer, CP, CS.crz_btns_counter, Buttons.RESUME)]

  # Adjust target speed in experimental mode
  if experimental_mode:
    # More responsive speed adjustment based on acceleration
    accel_factor = 5.0 if is_cx5_2022 else 4.0
    target_speed_units = int(round((current_speed_ms + accel_factor * accel) * MS_CONVERT))

    # Limit maximum speed change rate
    max_change = 15.0 if is_metric else 10.0
    if abs(target_speed_units - cruise_speed_units) > max_change:
      if target_speed_units > cruise_speed_units:
        target_speed_units = cruise_speed_units + max_change
      else:
        target_speed_units = cruise_speed_units - max_change

  # Adjust speed step based on units
  if is_metric:  # 5km/h steps in metric
    step = 5.0
  else:  # 5mph steps in imperial
    step = 5.0

  # Special adjustment for CX5 2022
  if is_cx5_2022:
    # Increase threshold to reduce excessive adjustments
    threshold = 6.0 if is_metric else 3.5

    # For CX5 2022 with experimental mode, use smaller steps for finer control
    if experimental_mode:
      step = 5.0 if is_metric else 3.0
  else:
    threshold = 5.0 if is_metric else 3.0

  # Round speeds to step increments
  target_speed_units = int(round(target_speed_units / step) * step)
  cruise_speed_units = int(round(cruise_speed_units / step) * step)

  # Choose button command based on speed difference
  speed_diff = target_speed_units - cruise_speed_units

  if abs(speed_diff) >= threshold:
    if speed_diff < 0 and cruise_speed_units > (30 if is_metric else 20):
      cruiseBtn = Buttons.SET_MINUS
    elif speed_diff > 0:
      cruiseBtn = Buttons.SET_PLUS

  # Only send message when there's a button operation
  if cruiseBtn != Buttons.NONE:
    # For CX5 2022 with experimental mode, send both standard and CX5-specific buttons
    if is_cx5_2022 and has_cx5_2022_flag and experimental_mode:
      can_sends.append(create_button_cmd(packer, CP, CS.crz_btns_counter, cruiseBtn))
      can_sends.append(create_cx5_2022_button_cmd(packer, CS.crz_btns_counter, cruiseBtn))
      return can_sends
    else:
      return [create_button_cmd(packer, CP, CS.crz_btns_counter, cruiseBtn)]
  else:
    return []


def create_radar_command(packer, CP, CS, lead_distance, lead_rel_speed, lead_status):
  """
  Create radar command for CX5 2022 with radar support

  Args:
    packer: CAN message packer
    CP: Car Parameters
    CS: Car State
    lead_distance: Distance to lead car (m)
    lead_rel_speed: Relative speed of lead car (m/s)
    lead_status: Lead car status (True/False)

  Returns:
    List of CAN messages
  """
  # Only for CX5 2022 with radar support
  if not (CP.carFingerprint == CAR.MAZDA_CX5_2022 and CP.flags & MazdaFlags.CX5_2022):
    return []

  can_sends = []

  # Create ACC control message
  values = {
    "CTR": CS.crz_btns_counter % 16,
    "ACC_ACTIVE": 1 if CS.cruiseState.enabled else 0,
    "ACC_SET_ALLOWED": 1 if CS.cruiseState.available else 0,
    "CRZ_ENDED": 0,
    "ACCEL_CMD": 0,
  }

  # Set acceleration command based on lead car status
  if lead_status and lead_distance > 0:
    # Calculate desired acceleration based on lead distance and relative speed
    # This is a simple proportional control
    desired_distance = max(10.0, CS.vEgo * 1.8)  # Time gap of 1.8 seconds
    distance_error = lead_distance - desired_distance

    # Adjust acceleration based on distance error and relative speed
    accel_from_distance = distance_error * 0.05
    accel_from_rel_speed = lead_rel_speed * 0.2

    # Combine both factors with limits
    accel_cmd = accel_from_distance + accel_from_rel_speed
    accel_cmd = max(-2.0, min(2.0, accel_cmd))  # Limit acceleration

    values["ACCEL_CMD"] = int(accel_cmd * 100)  # Scale for CAN message

  can_sends.append(packer.make_can_msg("CRZ_INFO", 1, values))

  return can_sends
