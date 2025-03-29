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

    # 订阅需要的数据源
    self.sm = messaging.SubMaster(['deviceState', 'carState', 'controlsState',
                                   'longitudinalPlan', 'liveLocationKalman',
                                   'navInstruction', 'modelV2'])

    # 网络相关配置
    self.broadcast_ip = self.get_broadcast_address()
    if self.broadcast_ip is None:
      self.broadcast_ip = "255.255.255.255"  # 使用通用广播地址作为备选
    self.broadcast_port = 8088
    self.ip_address = "0.0.0.0"
    self.is_running = True

    # 启动广播线程
    threading.Thread(target=self.broadcast_data).start()

  def get_broadcast_address(self):
    """获取广播地址"""
    try:
      if PC:
        iface = b'br0'
      else:
        iface = b'wlan0'

      with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
        ip = fcntl.ioctl(
          s.fileno(),
          0x8919,  # SIOCGIFADDR
          struct.pack('256s', iface)
        )[20:24]
        ip_str = socket.inet_ntoa(ip)
        print(f"获取到IP地址: {ip_str}")
        # 从IP地址构造广播地址
        ip_parts = ip_str.split('.')
        return f"{ip_parts[0]}.{ip_parts[1]}.{ip_parts[2]}.255"
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
    # 基本消息结构
    message = {
      "timestamp": int(time.time()),
      "device": {
        "ip": self.ip_address,
        "battery": {},
        "mem_usage": 0,
        "cpu_temp": 0,
        "free_space": 0
      },
      "car": {
        "speed": 0,
        "cruise_speed": 0,
        "gear_shifter": "unknown",
        "steering_angle": 0,
        "steering_torque": 0,
        "brake_pressed": False,
        "gas_pressed": False,
        "door_open": False,
        "left_blinker": False,
        "right_blinker": False
      },
      "location": {
        "latitude": 0,
        "longitude": 0,
        "bearing": 0,
        "speed": 0,
        "altitude": 0,
        "accuracy": 0,
        "gps_valid": False
      }
    }

    # 安全地获取设备信息
    try:
      if self.sm.updated['deviceState'] and self.sm.valid['deviceState']:
        device_state = self.sm['deviceState']

        # 获取设备信息 - 使用getattr安全地访问属性
        message["device"]["mem_usage"] = getattr(device_state, 'memoryUsagePercent', 0)
        message["device"]["free_space"] = getattr(device_state, 'freeSpacePercent', 0)

        # CPU温度
        cpu_temps = getattr(device_state, 'cpuTempC', [])
        if isinstance(cpu_temps, list) and len(cpu_temps) > 0:
          message["device"]["cpu_temp"] = cpu_temps[0]

        # 电池信息
        try:  # 额外的错误处理，因为这是常见错误点
          message["device"]["battery"]["percent"] = getattr(device_state, 'batteryPercent', 0)
          message["device"]["battery"]["status"] = getattr(device_state, 'batteryCurrent', 0)
          message["device"]["battery"]["voltage"] = getattr(device_state, 'batteryVoltage', 0)
          message["device"]["battery"]["charging"] = getattr(device_state, 'chargingError', False)
        except Exception as e:
          print(f"获取电池信息失败: {e}")
    except Exception as e:
      print(f"获取设备状态出错: {e}")

    # 安全地获取车辆信息
    try:
      if self.sm.updated['carState'] and self.sm.valid['carState']:
        car_state = self.sm['carState']

        message["car"]["speed"] = getattr(car_state, 'vEgo', 0) * 3.6  # m/s转km/h
        message["car"]["gear_shifter"] = str(getattr(car_state, 'gearShifter', "unknown"))
        message["car"]["steering_angle"] = getattr(car_state, 'steeringAngleDeg', 0)
        message["car"]["steering_torque"] = getattr(car_state, 'steeringTorque', 0)
        message["car"]["brake_pressed"] = getattr(car_state, 'brakePressed', False)
        message["car"]["gas_pressed"] = getattr(car_state, 'gasPressed', False)
        message["car"]["door_open"] = getattr(car_state, 'doorOpen', False)
        message["car"]["left_blinker"] = getattr(car_state, 'leftBlinker', False)
        message["car"]["right_blinker"] = getattr(car_state, 'rightBlinker', False)

      if self.sm.updated['controlsState'] and self.sm.valid['controlsState']:
        controls_state = self.sm['controlsState']
        message["car"]["cruise_speed"] = getattr(controls_state, 'vCruise', 0)
    except Exception as e:
      print(f"获取车辆信息出错: {e}")

    # 安全地获取GPS位置信息
    try:
      if self.sm.updated['liveLocationKalman'] and self.sm.valid['liveLocationKalman']:
        location = self.sm['liveLocationKalman']

        # 检查GPS是否有效
        location_status = getattr(location, 'status', -1)
        position_valid = False
        if hasattr(location, 'positionGeodetic'):
          position_valid = getattr(location.positionGeodetic, 'valid', False)

        gps_valid = (location_status == 0) and position_valid
        message["location"]["gps_valid"] = gps_valid

        if gps_valid and hasattr(location, 'positionGeodetic') and hasattr(location.positionGeodetic, 'value'):
          # 获取位置信息
          pos_value = location.positionGeodetic.value
          if len(pos_value) >= 3:
            message["location"]["latitude"] = pos_value[0]
            message["location"]["longitude"] = pos_value[1]
            message["location"]["altitude"] = pos_value[2]

          # 获取精度信息
          if hasattr(location, 'positionGeodeticStd') and hasattr(location.positionGeodeticStd, 'value'):
            std_value = location.positionGeodeticStd.value
            if len(std_value) > 0:
              message["location"]["accuracy"] = std_value[0]

          # 获取方向信息
          if hasattr(location, 'calibratedOrientationNED') and hasattr(location.calibratedOrientationNED, 'value'):
            orientation = location.calibratedOrientationNED.value
            if len(orientation) > 2:
              message["location"]["bearing"] = math.degrees(orientation[2])

          # 设置速度信息
          if hasattr(car_state, 'vEgo'):
            message["location"]["speed"] = car_state.vEgo * 3.6
    except Exception as e:
      print(f"获取位置信息出错: {e}")

    # 如果有导航指令，添加导航信息
    try:
      if self.sm.valid['navInstruction']:
        nav_instruction = self.sm['navInstruction']

        nav_info = {}
        nav_info["distance_remaining"] = getattr(nav_instruction, 'distanceRemaining', 0)
        nav_info["time_remaining"] = getattr(nav_instruction, 'timeRemaining', 0)
        nav_info["speed_limit"] = getattr(nav_instruction, 'speedLimit', 0) * 3.6
        nav_info["maneuver_distance"] = getattr(nav_instruction, 'maneuverDistance', 0)
        nav_info["maneuver_type"] = getattr(nav_instruction, 'maneuverType', "")
        nav_info["maneuver_modifier"] = getattr(nav_instruction, 'maneuverModifier', "")
        nav_info["maneuver_text"] = getattr(nav_instruction, 'maneuverPrimaryText', "")

        message["navigation"] = nav_info
    except Exception as e:
      print(f"获取导航信息出错: {e}")

    try:
      return json.dumps(message)
    except Exception as e:
      print(f"序列化消息出错: {e}")
      return "{}"

  def broadcast_data(self):
    """定期发送数据到广播地址"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    rk = Ratekeeper(10, print_delay_threshold=None)  # 10Hz广播频率

    print(f"开始广播数据到 {self.broadcast_ip}:{self.broadcast_port}")

    while self.is_running:
      try:
        # 更新数据
        self.sm.update(0)

        # 更新IP地址
        ip_address = self.get_local_ip()
        if ip_address != self.ip_address:
          self.ip_address = ip_address
          try:
            self.params.put("NetworkAddress", ip_address)
            print(f"更新网络地址: {ip_address}")
          except Exception as e:
            print(f"无法保存网络地址: {e}")

        # 构建并发送消息
        msg = self.make_data_message()
        dat = msg.encode('utf-8')
        sock.sendto(dat, (self.broadcast_ip, self.broadcast_port))

        # 减少日志输出频率
        if rk.frame % 50 == 0:  # 每5秒打印一次日志
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