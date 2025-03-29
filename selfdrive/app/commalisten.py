#!/usr/bin/env python3
import json
import socket
import sys
import threading
import time
from datetime import datetime
import curses
import argparse

class CommaListener:
    def __init__(self, port=8088):
        """初始化接收器"""
        self.port = port
        self.data = {}
        self.last_update = 0
        self.running = True
        self.device_ip = None

    def start_listening(self):
        """启动UDP监听"""
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind(('0.0.0.0', self.port))
            print(f"正在监听端口 {self.port} 的广播数据...")

            while self.running:
                try:
                    data, addr = sock.recvfrom(4096)
                    self.device_ip = addr[0]
                    try:
                        self.data = json.loads(data.decode('utf-8'))
                        self.last_update = time.time()
                    except json.JSONDecodeError:
                        print(f"接收到无效的JSON数据: {data[:100]}...")
                except Exception as e:
                    print(f"接收数据时出错: {e}")
        except Exception as e:
            print(f"无法绑定到端口 {self.port}: {e}")
        finally:
            sock.close()

    def curses_display(self, stdscr):
        """使用curses在终端中显示实时数据"""
        curses.curs_set(0)  # 隐藏光标
        curses.start_color()
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_RED, curses.COLOR_BLACK)

        stdscr.nodelay(1)  # 非阻塞模式

        while self.running:
            stdscr.clear()

            # 检查是否有数据
            if not self.data:
                stdscr.addstr(0, 0, "等待来自comma3的数据...", curses.color_pair(2))
                stdscr.refresh()
                time.sleep(0.5)
                continue

            # 检查数据是否过期
            if time.time() - self.last_update > 5:
                stdscr.addstr(0, 0, f"数据已过期! 上次更新: {datetime.fromtimestamp(self.last_update).strftime('%H:%M:%S')}",
                             curses.color_pair(3))
                stdscr.refresh()
                time.sleep(0.5)
                continue

            # 显示设备信息
            row = 0
            stdscr.addstr(row, 0, f"CommaAssist 数据监视器 (来自 {self.device_ip})", curses.A_BOLD)
            row += 2

            timestamp = self.data.get("timestamp", 0)
            stdscr.addstr(row, 0, f"数据时间: {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d %H:%M:%S')}")
            row += 1

            # 设备信息
            device = self.data.get("device", {})
            stdscr.addstr(row, 0, "设备信息:", curses.A_BOLD)
            row += 1
            stdscr.addstr(row, 2, f"IP: {device.get('ip', 'N/A')}")
            row += 1

            # 电池信息
            bat = device.get("battery", {})
            bat_percent = bat.get("percent", 0)
            color = 1 if bat_percent > 50 else (2 if bat_percent > 20 else 3)
            stdscr.addstr(row, 2, f"电池: {bat_percent}% ", curses.color_pair(color))
            stdscr.addstr(f"({bat.get('voltage', 0):.2f}V, {bat.get('status', 0):.2f}A)")
            row += 1

            # 系统信息
            stdscr.addstr(row, 2, f"CPU温度: {device.get('cpu_temp', 0):.1f}°C | 内存使用: {device.get('mem_usage', 0):.1f}% | ")
            stdscr.addstr(f"剩余空间: {device.get('free_space', 0):.1f}%")
            row += 2

            # 车辆信息
            car = self.data.get("car", {})
            stdscr.addstr(row, 0, "车辆信息:", curses.A_BOLD)
            row += 1

            speed = car.get("speed", 0)
            stdscr.addstr(row, 2, f"当前速度: {speed:.1f} km/h | 巡航速度: {car.get('cruise_speed', 0):.1f} km/h")
            row += 1

            stdscr.addstr(row, 2, f"方向盘角度: {car.get('steering_angle', 0):.1f}° | 转向力矩: {car.get('steering_torque', 0):.1f}")
            row += 1

            stdscr.addstr(row, 2, f"档位: {car.get('gear_shifter', 'N/A')} | ")
            stdscr.addstr(f"制动: {'按下' if car.get('brake_pressed', False) else '释放'} | ")
            stdscr.addstr(f"油门: {'按下' if car.get('gas_pressed', False) else '释放'}")
            row += 1

            blinker_str = ""
            if car.get("left_blinker", False): blinker_str += "← "
            if car.get("right_blinker", False): blinker_str += "→"
            if blinker_str:
                stdscr.addstr(row, 2, f"转向灯: {blinker_str}")
                row += 1

            # 位置信息
            row += 1
            location = self.data.get("location", {})
            if location.get("gps_valid", False):
                stdscr.addstr(row, 0, "GPS位置:", curses.A_BOLD)
                row += 1
                stdscr.addstr(row, 2, f"纬度: {location.get('latitude', 0):.6f} | 经度: {location.get('longitude', 0):.6f}")
                row += 1
                stdscr.addstr(row, 2, f"方向: {location.get('bearing', 0):.1f}° | 海拔: {location.get('altitude', 0):.1f}m | ")
                stdscr.addstr(f"精度: {location.get('accuracy', 0):.1f}m")
                row += 1
            else:
                stdscr.addstr(row, 0, "GPS位置: 无效", curses.color_pair(3))
                row += 1

            # 导航信息
            row += 1
            nav = self.data.get("navigation", {})
            if nav:
                stdscr.addstr(row, 0, "导航信息:", curses.A_BOLD)
                row += 1
                stdscr.addstr(row, 2, f"剩余距离: {nav.get('distance_remaining', 0):.1f}m | ")
                stdscr.addstr(f"剩余时间: {nav.get('time_remaining', 0)//60}分{nav.get('time_remaining', 0)%60}秒")
                row += 1
                stdscr.addstr(row, 2, f"限速: {nav.get('speed_limit', 0):.1f} km/h")
                row += 1
                if nav.get('maneuver_distance', 0) > 0:
                    stdscr.addstr(row, 2, f"下一个动作: {nav.get('maneuver_text', '')} ")
                    stdscr.addstr(f"(距离 {nav.get('maneuver_distance', 0)}m)")
                    row += 1

            # 操作说明
            row += 2
            stdscr.addstr(row, 0, "按 'q' 退出", curses.color_pair(2))

            stdscr.refresh()

            # 检查键盘输入
            try:
                key = stdscr.getkey()
                if key == 'q':
                    self.running = False
            except:
                pass

            time.sleep(0.1)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='接收并显示comma3广播数据')
    parser.add_argument('-p', '--port', type=int, default=8088, help='监听端口(默认: 8088)')
    args = parser.parse_args()

    listener = CommaListener(port=args.port)

    # 启动接收线程
    receiver_thread = threading.Thread(target=listener.start_listening)
    receiver_thread.daemon = True
    receiver_thread.start()

    try:
        # 使用curses显示数据
        curses.wrapper(listener.curses_display)
    except KeyboardInterrupt:
        print("\n退出...")
    finally:
        listener.running = False
        receiver_thread.join(timeout=1.0)

if __name__ == "__main__":
    main()