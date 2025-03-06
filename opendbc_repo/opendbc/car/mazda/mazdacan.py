from opendbc.car.mazda.values import Buttons, MazdaFlags, CAR
from opendbc.car.common.conversions import Conversions as CV


def create_steering_control(packer, CP, frame, apply_steer, lkas):
  """
  创建转向控制CAN消息

  参数:
  - packer: CAN消息打包器
  - CP: 车辆参数
  - frame: 当前帧
  - apply_steer: 应用的转向力矩
  - lkas: LKAS相关信息

  返回:
  - 打包后的CAN消息
  """
  tmp = apply_steer + 2048

  lo = tmp & 0xFF
  hi = tmp >> 8

  # 从相机信息中复制值
  b1 = int(lkas["BIT_1"])
  er1 = int(lkas["ERR_BIT_1"])
  lnv = 0
  ldw = 0
  er2 = int(lkas["ERR_BIT_2"])

  # 某些旧款车型有这些字段，新款没有
  # 不管怎样，设为0都没问题
  steering_angle = 0
  b2 = 0

  tmp = steering_angle + 2048
  ahi = tmp >> 10
  amd = (tmp & 0x3FF) >> 2
  amd = (amd >> 4) | (( amd & 0xF) << 4)
  alo = (tmp & 0x3) << 2

  ctr = frame % 16
  # 字节:     [    1  ] [ 2 ] [             3               ]  [           4         ]
  csum = 249 - ctr - hi - lo - (lnv << 3) - er1 - (ldw << 7) - ( er2 << 4) - (b1 << 5)

  # 字节      [ 5 ] [ 6 ] [    7   ]
  csum = csum - ahi - amd - alo - b2

  if ahi == 1:
    csum = csum + 15

  if csum < 0:
    if csum < -256:
      csum = csum + 512
    else:
      csum = csum + 256

  csum = csum % 256

  # 根据车型创建不同的CAN消息
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
  创建警告命令CAN消息

  参数:
  - packer: CAN消息打包器
  - cam_msg: 相机消息
  - ldw: 是否需要车道偏离警告
  - steer_required: 是否需要方向盘警告

  返回:
  - 打包后的CAN消息
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
    # 警告相关字段
    "HANDS_WARN_3_BITS": 0b111 if steer_required else 0,
    "HANDS_ON_STEER_WARN": steer_required,
    "HANDS_ON_STEER_WARN_2": steer_required,

    # 车道偏离警告
    "LDW_WARN_LL": 0,
    "LDW_WARN_RL": 0,
  })
  return packer.make_can_msg("CAM_LANEINFO", 0, values)


def create_button_cmd(packer, CP, counter, button):
  """
  创建按钮命令CAN消息

  参数:
  - packer: CAN消息打包器
  - CP: 车辆参数
  - counter: 计数器
  - button: 按钮类型

  返回:
  - 打包后的CAN消息
  """
  # 检查是否为CX5 2022车型
  is_cx5_2022 = CP.carFingerprint == CAR.MAZDA_CX5_2022

  # 为不同按钮设置标志位
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

    # CX5 2022按钮特殊处理
    if is_cx5_2022:
      # 调整CTR字段的增长速度，为CX5 2022提高响应性
      if button != Buttons.NONE:
        values["CTR"] = (counter + 2) % 16

    return packer.make_can_msg("CRZ_BTNS", 0, values)


def create_mazda_acc_spam_command(packer, CP, CS, target_speed_ms, current_speed_ms, is_metric=True, experimental_mode=False, accel=0):
  """
  创建自动控制车速的CAN消息

  参数:
  - packer: CAN消息打包器
  - CP: 车辆参数
  - CS: 车辆状态
  - target_speed_ms: 目标速度(m/s)
  - current_speed_ms: 当前车速(m/s)
  - is_metric: 是否使用公制单位
  - experimental_mode: 是否使用实验模式
  - accel: 加速度

  返回:
  - CAN消息列表
  """
  cruiseBtn = Buttons.NONE

  # 检查是否为CX5 2022车型
  is_cx5_2022 = CP.carFingerprint == CAR.MAZDA_CX5_2022

  # 单位转换系数
  MS_CONVERT = CV.MS_TO_KPH if is_metric else CV.MS_TO_MPH

  # 获取当前和目标速度值
  current_speed_units = current_speed_ms * MS_CONVERT
  cruise_speed_units = CS.cruiseState.speed * MS_CONVERT if hasattr(CS, 'cruiseState') and hasattr(CS.cruiseState, 'speed') else 0
  target_speed_units = target_speed_ms * MS_CONVERT

  # 车辆静止状态处理
  if CS.standstill:
    return [create_button_cmd(packer, CP, CS.crz_btns_counter, Buttons.RESUME)]

  # 实验模式下调整目标速度
  if experimental_mode:
    target_speed_units = int(round((current_speed_ms + 5 * accel) * MS_CONVERT))

  # 根据单位调整速度步长
  if is_metric:  # 公制单位时按5km/h的步长调整
    step = 5.0
  else:  # 英制单位时按5mph的步长调整
    step = 5.0

  # CX5 2022特殊调整
  if is_cx5_2022:
    # 加大目标与当前速度差值的阈值，减少过度调整
    threshold = 6.0 if is_metric else 3.5
  else:
    threshold = 5.0 if is_metric else 3.0

  # 将速度调整为步长的整数倍
  target_speed_units = int(round(target_speed_units / step) * step)
  cruise_speed_units = int(round(cruise_speed_units / step) * step)

  # 根据速度差值选择按钮命令
  speed_diff = target_speed_units - cruise_speed_units

  if abs(speed_diff) >= threshold:
    if speed_diff < 0 and cruise_speed_units > (30 if is_metric else 20):
      cruiseBtn = Buttons.SET_MINUS
    elif speed_diff > 0:
      cruiseBtn = Buttons.SET_PLUS

  # 仅在有按钮操作时发送消息，避免无意义的CAN总线通信
  if cruiseBtn != Buttons.NONE:
    return [create_button_cmd(packer, CP, CS.crz_btns_counter, cruiseBtn)]
  else:
    return []
