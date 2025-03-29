#!/usr/bin/env python3
import json
import socket
import threading
import time
from datetime import datetime
import argparse
from flask import Flask, render_template_string, jsonify

class CommaWebListener:
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

# HTML模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CommaAssist 数据监视器</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
            color: #333;
        }
        .container {
            max-width: 1000px;
            margin: 0 auto;
        }
        .header {
            text-align: center;
            margin-bottom: 20px;
        }
        .status {
            text-align: center;
            padding: 10px;
            margin-bottom: 20px;
            border-radius: 5px;
        }
        .waiting {
            background-color: #fff3cd;
            color: #856404;
        }
        .connected {
            background-color: #d4edda;
            color: #155724;
        }
        .expired {
            background-color: #f8d7da;
            color: #721c24;
        }
        .card {
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 20px;
            padding: 15px;
        }
        .card-header {
            font-weight: bold;
            font-size: 18px;
            border-bottom: 1px solid #eee;
            padding-bottom: 10px;
            margin-bottom: 10px;
        }
        .section {
            margin-bottom: 10px;
        }
        .row {
            display: flex;
            flex-wrap: wrap;
            margin: 0 -10px;
        }
        .col {
            flex: 1;
            padding: 0 10px;
            min-width: 300px;
        }
        .data-item {
            margin-bottom: 5px;
        }
        .battery-good {
            color: #28a745;
        }
        .battery-warning {
            color: #ffc107;
        }
        .battery-danger {
            color: #dc3545;
        }
        .map-container {
            height: 300px;
            width: 100%;
            background-color: #eee;
            margin-top: 10px;
            border-radius: 5px;
        }
        @media (max-width: 768px) {
            .row {
                flex-direction: column;
            }
        }
        .refresh-button {
            background-color: #007bff;
            color: white;
            border: none;
            padding: 8px 15px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            margin-bottom: 10px;
            float: right;
        }
        .refresh-button:hover {
            background-color: #0069d9;
        }
        .auto-refresh {
            display: inline-block;
            margin-right: 15px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>CommaAssist 数据监视器</h1>
        </div>

        <div id="status-container" class="status waiting">
            等待来自comma3的数据...
        </div>

        <div class="controls">
            <label class="auto-refresh">
                <input type="checkbox" id="auto-refresh" checked> 自动刷新 (1秒)
            </label>
            <button class="refresh-button" onclick="fetchData()">刷新数据</button>
            <div style="clear: both;"></div>
        </div>

        <div class="row">
            <div class="col">
                <div class="card">
                    <div class="card-header">设备信息</div>
                    <div class="section">
                        <div class="data-item" id="device-ip">IP: --</div>
                        <div class="data-item" id="device-battery">电池: --</div>
                        <div class="data-item" id="device-system">系统: --</div>
                    </div>
                </div>

                <div class="card">
                    <div class="card-header">车辆信息</div>
                    <div class="section">
                        <div class="data-item" id="car-speed">速度: -- km/h</div>
                        <div class="data-item" id="car-steering">方向盘: --</div>
                        <div class="data-item" id="car-status">状态: --</div>
                        <div class="data-item" id="car-signals">信号: --</div>
                    </div>
                </div>
            </div>

            <div class="col">
                <div class="card">
                    <div class="card-header">GPS位置</div>
                    <div class="section">
                        <div class="data-item" id="location-coords">位置: --</div>
                        <div class="data-item" id="location-details">详情: --</div>
                    </div>
                    <div id="map" class="map-container"></div>
                </div>

                <div class="card">
                    <div class="card-header">导航信息</div>
                    <div class="section">
                        <div class="data-item" id="nav-distance">剩余距离: --</div>
                        <div class="data-item" id="nav-time">剩余时间: --</div>
                        <div class="data-item" id="nav-speed">限速: -- km/h</div>
                        <div class="data-item" id="nav-maneuver">下一个动作: --</div>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <div class="card-header">数据详情</div>
            <pre id="raw-data" style="overflow-x: auto; white-space: pre-wrap;"></pre>
        </div>
    </div>

    <script>
        let map, marker;
        let lastValidLatLng = null;

        function initMap() {
            if (typeof google !== 'undefined') {
                const defaultPos = {lat: 39.9042, lng: 116.4074}; // 默认位置：北京
                map = new google.maps.Map(document.getElementById('map'), {
                    zoom: 16,
                    center: defaultPos,
                    mapTypeId: 'roadmap'
                });

                marker = new google.maps.Marker({
                    position: defaultPos,
                    map: map,
                    title: 'Comma3位置'
                });
            }
        }

        function updateMap(lat, lng, bearing) {
            if (typeof google !== 'undefined' && map && marker) {
                const latLng = new google.maps.LatLng(lat, lng);

                // 更新标记位置
                marker.setPosition(latLng);

                // 根据方向旋转标记
                if (bearing !== undefined) {
                    // 如果我们有自定义的带方向的标记图标，可以在这里设置
                }

                // 平滑移动地图中心
                map.panTo(latLng);

                lastValidLatLng = {lat, lng};
            }
        }

        function fetchData() {
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    const statusContainer = document.getElementById('status-container');

                    if (!data || Object.keys(data).length === 0) {
                        statusContainer.className = 'status waiting';
                        statusContainer.textContent = '等待来自comma3的数据...';
                        return;
                    }

                    const currentTime = new Date().getTime() / 1000;
                    if (currentTime - data.last_update > 5) {
                        statusContainer.className = 'status expired';
                        statusContainer.textContent = `数据已过期! 上次更新: ${new Date(data.last_update * 1000).toLocaleTimeString()}`;
                        return;
                    }

                    // 数据有效，更新UI
                    statusContainer.className = 'status connected';
                    statusContainer.textContent = `已连接到 ${data.device_ip || 'Comma3设备'} - 最后更新: ${new Date(data.last_update * 1000).toLocaleTimeString()}`;

                    // 更新设备信息
                    const device = data.data.device || {};
                    document.getElementById('device-ip').textContent = `IP: ${device.ip || 'N/A'}`;

                    const bat = device.battery || {};
                    const batPercent = bat.percent || 0;
                    let batClass = 'battery-danger';
                    if (batPercent > 50) batClass = 'battery-good';
                    else if (batPercent > 20) batClass = 'battery-warning';

                    document.getElementById('device-battery').innerHTML =
                        `电池: <span class="${batClass}">${batPercent}%</span> (${(bat.voltage || 0).toFixed(2)}V, ${(bat.status || 0).toFixed(2)}A)`;

                    document.getElementById('device-system').textContent =
                        `CPU温度: ${(device.cpu_temp || 0).toFixed(1)}°C | 内存使用: ${(device.mem_usage || 0).toFixed(1)}% | 剩余空间: ${(device.free_space || 0).toFixed(1)}%`;

                    // 更新车辆信息
                    const car = data.data.car || {};
                    document.getElementById('car-speed').textContent =
                        `当前速度: ${(car.speed || 0).toFixed(1)} km/h | 巡航速度: ${(car.cruise_speed || 0).toFixed(1)} km/h`;

                    document.getElementById('car-steering').textContent =
                        `方向盘角度: ${(car.steering_angle || 0).toFixed(1)}° | 转向力矩: ${(car.steering_torque || 0).toFixed(1)}`;

                    document.getElementById('car-status').textContent =
                        `档位: ${car.gear_shifter || 'N/A'} | 制动: ${car.brake_pressed ? '按下' : '释放'} | 油门: ${car.gas_pressed ? '按下' : '释放'}`;

                    let blinkerStr = '';
                    if (car.left_blinker) blinkerStr += '← ';
                    if (car.right_blinker) blinkerStr += '→';
                    document.getElementById('car-signals').textContent =
                        blinkerStr ? `转向灯: ${blinkerStr}` : '转向灯: 无';

                    // 更新位置信息
                    const location = data.data.location || {};
                    if (location.gps_valid) {
                        document.getElementById('location-coords').textContent =
                            `位置: 纬度 ${location.latitude.toFixed(6)}, 经度 ${location.longitude.toFixed(6)}`;

                        document.getElementById('location-details').textContent =
                            `方向: ${location.bearing.toFixed(1)}° | 海拔: ${location.altitude.toFixed(1)}m | 精度: ${location.accuracy.toFixed(1)}m`;

                        // 更新地图
                        updateMap(location.latitude, location.longitude, location.bearing);
                    } else {
                        document.getElementById('location-coords').textContent = 'GPS位置: 无效';
                        document.getElementById('location-details').textContent = '';
                    }

                    // 更新导航信息
                    const nav = data.data.navigation || {};
                    if (nav && Object.keys(nav).length > 0) {
                        const distRemaining = nav.distance_remaining || 0;
                        let distText = '';
                        if (distRemaining > 1000) {
                            distText = `${(distRemaining / 1000).toFixed(1)} km`;
                        } else {
                            distText = `${Math.round(distRemaining)} m`;
                        }
                        document.getElementById('nav-distance').textContent = `剩余距离: ${distText}`;

                        const timeRemaining = nav.time_remaining || 0;
                        const minutes = Math.floor(timeRemaining / 60);
                        const seconds = timeRemaining % 60;
                        document.getElementById('nav-time').textContent = `剩余时间: ${minutes}分${seconds}秒`;

                        document.getElementById('nav-speed').textContent = `限速: ${(nav.speed_limit || 0).toFixed(1)} km/h`;

                        if (nav.maneuver_distance > 0) {
                            document.getElementById('nav-maneuver').textContent =
                                `下一个动作: ${nav.maneuver_text} (距离 ${nav.maneuver_distance}m)`;
                        } else {
                            document.getElementById('nav-maneuver').textContent = '下一个动作: 无';
                        }
                    } else {
                        document.getElementById('nav-distance').textContent = '剩余距离: --';
                        document.getElementById('nav-time').textContent = '剩余时间: --';
                        document.getElementById('nav-speed').textContent = '限速: -- km/h';
                        document.getElementById('nav-maneuver').textContent = '下一个动作: --';
                    }

                    // 更新原始数据
                    document.getElementById('raw-data').textContent = JSON.stringify(data.data, null, 2);
                })
                .catch(error => {
                    console.error('获取数据出错:', error);
                    document.getElementById('status-container').className = 'status expired';
                    document.getElementById('status-container').textContent = '连接错误: ' + error.message;
                });
        }

        // 页面加载完成后执行
        document.addEventListener('DOMContentLoaded', function() {
            fetchData();

            // 设置自动刷新
            const autoRefreshCheckbox = document.getElementById('auto-refresh');
            let refreshInterval;

            function setAutoRefresh() {
                if (autoRefreshCheckbox.checked) {
                    refreshInterval = setInterval(fetchData, 1000);
                } else {
                    clearInterval(refreshInterval);
                }
            }

            autoRefreshCheckbox.addEventListener('change', setAutoRefresh);
            setAutoRefresh();
        });
    </script>

    <!-- 加载Google地图API (需要替换为您自己的API密钥) -->
    <script async defer
        src="https://maps.googleapis.com/maps/api/js?key=YOUR_API_KEY&callback=initMap">
    </script>
</body>
</html>
"""

def create_app(listener):
    app = Flask(__name__)

    @app.route('/')
    def index():
        """主页"""
        return render_template_string(HTML_TEMPLATE)

    @app.route('/api/data')
    def get_data():
        """提供JSON数据API"""
        return jsonify({
            'data': listener.data,
            'last_update': listener.last_update,
            'device_ip': listener.device_ip
        })

    return app

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='CommaAssist Web监视器')
    parser.add_argument('-p', '--port', type=int, default=8088, help='监听comma设备的UDP端口(默认: 8088)')
    parser.add_argument('-w', '--web-port', type=int, default=5000, help='Web服务器端口(默认: 5000)')
    parser.add_argument('--host', default='0.0.0.0', help='Web服务器监听地址(默认: 0.0.0.0)')
    args = parser.parse_args()

    # 创建监听器
    listener = CommaWebListener(port=args.port)

    # 启动接收线程
    receiver_thread = threading.Thread(target=listener.start_listening)
    receiver_thread.daemon = True
    receiver_thread.start()

    # 创建Flask应用
    app = create_app(listener)

    # 启动Web服务器
    try:
        print(f"Web服务已启动，请访问 http://{args.host}:{args.web_port}/")
        app.run(host=args.host, port=args.web_port)
    except KeyboardInterrupt:
        print("\n退出...")
    finally:
        listener.running = False
        receiver_thread.join(timeout=1.0)

if __name__ == "__main__":
    main()