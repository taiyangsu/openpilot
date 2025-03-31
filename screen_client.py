#!/usr/bin/env python3
import webbrowser
import socket
import time

def get_comma3_ip():
    # 这里需要替换为实际的comma3 IP地址
    # 可以通过局域网扫描或其他方式获取
    return "192.168.1.100"  # 示例IP

def main():
    comma3_ip = get_comma3_ip()
    url = f"http://{comma3_ip}:5000"
    print(f"正在打开浏览器访问: {url}")
    webbrowser.open(url)

if __name__ == "__main__":
    main()