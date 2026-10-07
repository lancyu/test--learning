import socket
import json

def receive_one(bind_addr=("127.0.0.1", 0), timeout=2):
    """接收一个 UDP 包并返回解析后的字典"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    """创建ipv4,和udp的套接字"""
    sock.bind(bind_addr)
    sock.settimeout(timeout)
    try:
        data, addr = sock.recvfrom(4096)
        return json.loads(data.decode()), addr, sock.getsockname()
    finally:
        sock.close()


def send_radar(target_addr, points):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = json.dumps({"type": "radar", "points": points}).encode()
    sock.sendto(payload, target_addr)
    sock.close()