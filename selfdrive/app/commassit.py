#!/usr/bin/env python3
import fcntl
import json
import math
import os
import socket
import struct
import threading
import time
import zmq
from datetime import datetime

import cereal.messaging as messaging
from openpilot.common.realtime import Ratekeeper
from openpilot.common.params import Params
from openpilot.system.hardware import PC, TICI

class CommaAssist:
  def __init__(self):
    print("初始化 CommaAssist 服务...")
    # 初始化参数
    self.params = Params()
    self.params_memory = Params("/dev/shm/params")

    # 订阅需要的数据源
    self.sm = messaging.SubMaster(['deviceState', 'carState', 'controlsState',
                                   'longitudinalPlan', 'liveLocationKalman',
                                   'navInstruction', 'modelV2'])

    # 网络相关配置
    self.broadcast_ip = self.get_broadcast_address()
    self.broadcast_port = 8088
    self.ip_address = "0.0.0.0"
    self.is_running = True

    # 启动广播线程
    threading.Thread(target=self.broadcast_data).start()

  def get_broadcast_address(self):
    """获取广播地址"""
    if PC:
      iface = b'br0'
    else:
      iface = b'wlan0'
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        ip = fcntl.ioctl(
          s.fileno(),
          0x8919,  # SIOCGIFADDR
          struct.pack('256s', iface)
        )[20:24]
        return socket.inet_ntoa(ip)
    except (OSError, Exception) as e:
      print(f"获取广播地址失败: {e}")
      return None

  def get_local_ip(self):
    """获取本地IP地址"""
    try:
      with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception as e:
      print(f"获取本地IP失败: {e}")
      return "127.0.0.1"

  def make_data_message(self):
    """构建广播消息内容"""
    # 获取当前设备状态
    device_state = self.sm['deviceState']
    car_state = self.sm['carState']
    controls_state = self.sm['controlsState']

    # 获取GPS位置信息
    location = self.sm['liveLocationKalman']
    gps_valid = (location.status == 0) and location.positionGeodetic.valid

    lat = lon = bearing = 0.0
    if gps_valid:
      lat = location.positionGeodetic.value[0]
      lon = location.positionGeodetic.value[1]
      bearing = math.degrees(location.calibratedOrientationNED.value[2])

    # 构建消息内容 - 包含关键车辆和设备信息
    message = {
      "timestamp": int(time.time()),
      "device": {
        "ip": self.ip_address,
        "battery": {
          "percent": device_state.batteryPercent,
          "status": device_state.batteryCurrent,
          "voltage": device_state.batteryVoltage,
          "charging": device_state.chargingError if hasattr(device_state, 'chargingError') else False
        },
        "mem_usage": device_state.memoryUsagePercent,
        "cpu_temp": device_state.cpuTempC[0] if len(device_state.cpuTempC) > 0 else 0,
        "free_space": device_state.freeSpacePercent
      },
      "car": {
        "speed": car_state.vEgo * 3.6,  # m/s转km/h
        "cruise_speed": controls_state.vCruise,
        "gear_shifter": str(car_state.gearShifter),
        "steering_angle": car_state.steeringAngleDeg,
        "steering_torque": car_state.steeringTorque,
        "brake_pressed": car_state.brakePressed,
        "gas_pressed": car_state.gasPressed,
        "door_open": car_state.doorOpen,
        "left_blinker": car_state.leftBlinker,
        "right_blinker": car_state.rightBlinker
      },
      "location": {
        "latitude": lat,
        "longitude": lon,
        "bearing": bearing,
        "speed": car_state.vEgo * 3.6,
        "altitude": location.positionGeodetic.value[2] if gps_valid else 0,
        "accuracy": location.positionGeodeticStd.value[0] if gps_valid else 0,
        "gps_valid": gps_valid
      }
    }

    # 如果有导航指令，添加导航信息
    if self.sm.valid['navInstruction']:
      nav_instruction = self.sm['navInstruction']
      message["navigation"] = {
        "distance_remaining": nav_instruction.distanceRemaining,
        "time_remaining": nav_instruction.timeRemaining,
        "speed_limit": nav_instruction.speedLimit * 3.6,
        "maneuver_distance": nav_instruction.maneuverDistance,
        "maneuver_type": nav_instruction.maneuverType,
        "maneuver_modifier": nav_instruction.maneuverModifier,
        "maneuver_text": nav_instruction.maneuverPrimaryText
      }

    return json.dumps(message)

  def broadcast_data(self):
    """定期发送数据到广播地址"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    rk = Ratekeeper(10, print_delay_threshold=None)  # 10Hz广播频率

    while self.is_running:
      try:
        # 更新数据
        self.sm.update(0)

        # 更新IP地址
        ip_address = self.get_local_ip()
        if ip_address != self.ip_address:
          self.ip_address = ip_address
          self.params_memory.put_nonblocking("NetworkAddress", self.ip_address)

        # 构建并发送消息
        msg = self.make_data_message()
        if self.broadcast_ip is not None:
          dat = msg.encode('utf-8')
          sock.sendto(dat, (self.broadcast_ip, self.broadcast_port))
          print(f"广播数据: {self.broadcast_ip}:{self.broadcast_port}")

        rk.keep_time()
      except Exception as e:
        print(f"广播数据错误: {e}")
        time.sleep(1)

def main():
  """主函数"""
  comma_assist = CommaAssist()

  # 保持主线程运行
  try:
    while True:
      time.sleep(10)  # 主线程休眠
  except KeyboardInterrupt:
    comma_assist.is_running = False
    print("CommaAssist服务已停止")

if __name__ == "__main__":
  main()