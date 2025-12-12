#!/usr/bin/env python3
"""
broker_server.py
A socket broker that implements a bounded buffer (max size 10) for producer/consumer clients.

Usage:
    python broker_server.py [host] [port]
Defaults: host=127.0.0.1 port=6000
"""
import socket
import threading
import struct
import os
from collections import deque

SHARED_DIR = "shared"
MAX_BUFFER = 10

HOST = "127.0.0.1"
PORT = 6000

buffer = deque()
buffer_lock = threading.Lock()
not_empty = threading.Condition(buffer_lock)
not_full = threading.Condition(buffer_lock)

def ensure_shared_dir():
    if not os.path.exists(SHARED_DIR):
        os.makedirs(SHARED_DIR)

def recv_exact(conn, n):
    data = b""
    while len(data) < n:
        pkt = conn.recv(n - len(data))
        if not pkt:
            raise ConnectionError("Connection closed while receiving")
        data += pkt
    return data

def handle_producer(conn, addr):
    try:
        # read index (4), xml length (4), xml bytes
        idx_bytes = recv_exact(conn, 4)
        idx = struct.unpack("!I", idx_bytes)[0]
        ln_bytes = recv_exact(conn, 4)
        ln = struct.unpack("!I", ln_bytes)[0]
        xml = recv_exact(conn, ln)

        # wait for space in buffer
        with not_full:
            while len(buffer) >= MAX_BUFFER:
                # block until not full
                not_full.wait()
            # write file
            filename = os.path.join(SHARED_DIR, f"student{idx}.xml")
            with open(filename, "wb") as f:
                f.write(xml)
            buffer.append(idx)
            print(f"[Broker] Produced student{idx}.xml -> buffer (size={len(buffer)})")
            # notify consumers
            not_empty.notify()
        # done, close connection
    except Exception as e:
        print(f"[Broker] Producer handler error from {addr}: {e}")
    finally:
        conn.close()

def handle_consumer(conn, addr):
    try:
        # block until item available
        with not_empty:
            while len(buffer) == 0:
                not_empty.wait()
            idx = buffer.popleft()
            # notify producers that there's space
            not_full.notify()

        filename = os.path.join(SHARED_DIR, f"student{idx}.xml")
        if not os.path.exists(filename):
            # If file missing, send error status (E) and return
            conn.sendall(b'E')
            print(f"[Broker] WARNING: expected {filename} but not found.")
            conn.close()
            return

        with open(filename, "rb") as f:
            xml = f.read()

        # delete file from disk (broker manages lifecycle)
        try:
            os.remove(filename)
            print(f"[Broker] removed {filename}")
        except Exception as e:
            print(f"[Broker] failed to delete {filename}: {e}")

        # send success: 1-byte 'K', 4-byte idx, 4-byte len, xml bytes
        payload = struct.pack("!I", idx) + struct.pack("!I", len(xml)) + xml
        conn.sendall(b'K' + payload)
        print(f"[Broker] Sent student{idx}.xml to consumer {addr} (buffer size now {len(buffer)})")
    except Exception as e:
        print(f"[Broker] Consumer handler error from {addr}: {e}")
    finally:
        conn.close()

def client_thread(conn, addr):
    try:
        # first byte: action
        action = recv_exact(conn, 1)
        if action == b'P':
            handle_producer(conn, addr)
        elif action == b'C':
            handle_consumer(conn, addr)
        else:
            print(f"[Broker] Unknown action {action} from {addr}")
            conn.close()
    except Exception as e:
        print(f"[Broker] client thread error {addr}: {e}")
        try:
            conn.close()
        except:
            pass

def start_server(host=HOST, port=PORT):
    ensure_shared_dir()
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((host, port))
    s.listen(32)
    print(f"[Broker] Listening on {host}:{port}. Shared dir: {SHARED_DIR}, buffer max = {MAX_BUFFER}")
    try:
        while True:
            conn, addr = s.accept()
            t = threading.Thread(target=client_thread, args=(conn, addr), daemon=True)
            t.start()
    finally:
        s.close()

if __name__ == "__main__":
    import sys
    host = HOST
    port = PORT
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        port = int(sys.argv[2])
    start_server(host, port)
