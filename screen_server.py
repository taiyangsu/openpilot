#!/usr/bin/env python3
import cv2
import numpy as np
from flask import Flask, Response
from flask_socketio import SocketIO
import threading
import time
import io
import os
import struct
import fcntl
import array
import ctypes
import subprocess

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Framebuffer ioctl constants
FBIOGET_VSCREENINFO = 0x4600
FBIOGET_FSCREENINFO = 0x4602

class FrameBufferInfo(ctypes.Structure):
    _fields_ = [
        ('xres', ctypes.c_uint32),
        ('yres', ctypes.c_uint32),
        ('xres_virtual', ctypes.c_uint32),
        ('yres_virtual', ctypes.c_uint32),
        ('xoffset', ctypes.c_uint32),
        ('yoffset', ctypes.c_uint32),
        ('bits_per_pixel', ctypes.c_uint32),
        ('grayscale', ctypes.c_uint32),
        ('red', ctypes.c_uint32 * 3),
        ('green', ctypes.c_uint32 * 3),
        ('blue', ctypes.c_uint32 * 3),
        ('transp', ctypes.c_uint32 * 3),
        ('nonstd', ctypes.c_uint32),
        ('activate', ctypes.c_uint32),
        ('height', ctypes.c_uint32),
        ('width', ctypes.c_uint32),
        ('accel_flags', ctypes.c_uint32),
        ('pixclock', ctypes.c_uint32),
        ('left_margin', ctypes.c_uint32),
        ('right_margin', ctypes.c_uint32),
        ('upper_margin', ctypes.c_uint32),
        ('lower_margin', ctypes.c_uint32),
        ('hsync_len', ctypes.c_uint32),
        ('vsync_len', ctypes.c_uint32),
        ('sync', ctypes.c_uint32),
        ('vmode', ctypes.c_uint32),
        ('rotate', ctypes.c_uint32),
        ('colorspace', ctypes.c_uint32),
        ('reserved', ctypes.c_uint32 * 4),
    ]

class FrameBufferCapture:
    def __init__(self, device='/dev/fb0'):
        self.device = device
        self.fb_file = None
        self.width = 0
        self.height = 0
        self.bpp = 0
        self.initialized = False

        try:
            self.fb_file = open(device, 'rb')
            fb_var = FrameBufferInfo()

            fcntl.ioctl(self.fb_file, FBIOGET_VSCREENINFO, fb_var)

            self.width = fb_var.xres
            self.height = fb_var.yres
            self.bpp = fb_var.bits_per_pixel
            self.initialized = True

            print(f"Framebuffer info: {self.width}x{self.height}, {self.bpp} bits per pixel")
        except Exception as e:
            print(f"Failed to initialize framebuffer: {str(e)}")
            if self.fb_file:
                self.fb_file.close()
                self.fb_file = None

    def capture(self):
        if not self.initialized or not self.fb_file:
            return None

        try:
            # Seek to beginning of framebuffer
            self.fb_file.seek(0)

            # Read the entire framebuffer
            buffer_size = self.width * self.height * (self.bpp // 8)
            frame_data = self.fb_file.read(buffer_size)

            # Convert to numpy array based on bpp
            if self.bpp == 32:  # RGBA
                frame = np.frombuffer(frame_data, dtype=np.uint8).reshape(self.height, self.width, 4)
                return cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
            elif self.bpp == 24:  # RGB
                frame = np.frombuffer(frame_data, dtype=np.uint8).reshape(self.height, self.width, 3)
                return frame
            elif self.bpp == 16:  # RGB565
                frame = np.frombuffer(frame_data, dtype=np.uint16).reshape(self.height, self.width)
                # Convert RGB565 to RGB888
                r = ((frame & 0xF800) >> 11) * 8
                g = ((frame & 0x07E0) >> 5) * 4
                b = (frame & 0x001F) * 8
                frame_rgb = np.stack([r, g, b], axis=2).astype(np.uint8)
                return frame_rgb
            else:
                print(f"Unsupported bpp: {self.bpp}")
                return None
        except Exception as e:
            print(f"Error capturing framebuffer: {str(e)}")
            return None

    def close(self):
        if self.fb_file:
            self.fb_file.close()
            self.fb_file = None
            self.initialized = False

# Try to use MSS if available
try:
    from mss import mss
    has_mss = True
except ImportError:
    has_mss = False

def capture_with_mss():
    with mss() as sct:
        monitor = sct.monitors[1]
        while True:
            try:
                screenshot = sct.grab(monitor)
                frame = np.array(screenshot)
                frame = cv2.cvtColor(frame, cv2.COLOR_BGRA2BGR)
                return frame
            except Exception as e:
                print(f"MSS截图错误: {str(e)}")
                return None

def capture_screen():
    # 尝试初始化framebuffer
    fb_capture = FrameBufferCapture()
    use_fb = fb_capture.initialized

    # 如果framebuffer不可用，尝试使用mss
    use_mss = has_mss and not use_fb

    while True:
        try:
            frame = None

            if use_fb:
                frame = fb_capture.capture()
            elif use_mss:
                frame = capture_with_mss()

            if frame is None:
                print("无法捕获屏幕，尝试其他方法...")
                time.sleep(1)
                continue

            # 压缩图像
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])

            # 转换为字节
            frame_bytes = buffer.tobytes()

            # 通过WebSocket广播
            socketio.emit('screen_frame', frame_bytes)

        except Exception as e:
            print(f"截图错误: {str(e)}")

        time.sleep(0.033)  # 约30fps

    # 清理资源
    if use_fb:
        fb_capture.close()

@app.route('/')
def index():
    return """
    <html>
        <head>
            <title>OpenPilot Screen Stream</title>
            <style>
                body { margin: 0; background: #000; }
                img { width: 100%; height: 100vh; object-fit: contain; }
            </style>
        </head>
        <body>
            <img id="screen">
            <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
            <script>
                var socket = io();
                var img = document.getElementById('screen');

                socket.on('screen_frame', function(frame) {
                    var blob = new Blob([frame], {type: 'image/jpeg'});
                    var url = URL.createObjectURL(blob);
                    img.src = url;
                });
            </script>
        </body>
    </html>
    """

if __name__ == '__main__':
    # 检测环境
    print("检测屏幕捕获方法...")

    # 检查framebuffer
    if os.path.exists('/dev/fb0'):
        print("检测到framebuffer设备")
    else:
        print("未检测到framebuffer设备")

    # 检查mss
    if has_mss:
        print("检测到MSS库")
    else:
        print("未检测到MSS库")

    # 启动屏幕捕获线程
    capture_thread = threading.Thread(target=capture_screen, daemon=True)
    capture_thread.start()

    # 启动Web服务器
    socketio.run(app, host='0.0.0.0', port=5000)