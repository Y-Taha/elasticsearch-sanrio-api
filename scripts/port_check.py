#!/usr/bin/env python3
import socket
import argparse

def check_port(host: str, port: int, timeout: float = 3.0) -> bool:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(timeout)
    try:
        s.connect((host, port))
        s.close()
        return True
    except Exception:
        return False

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Check port availability')
    parser.add_argument('--host', required=True)
    parser.add_argument('--port', type=int, required=True)
    args = parser.parse_args()
    ok = check_port(args.host, args.port)
    print(f'Port {args.port} on {args.host} is', 'OPEN' if ok else 'CLOSED')
