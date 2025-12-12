#!/usr/bin/env python3
"""
consumer_client.py

Socket-based Consumer client for the broker_server.

Usage:
    python consumer_client.py [host] [port] [delay]

Defaults: host=127.0.0.1 port=6000 delay=0.2

Protocol (broker expects):
 - Client sends 1 byte action: b'C'
 - Broker responds:
    - b'E' -> error (no file found)
    - b'K' + 4-byte idx + 4-byte xml_length + xml_bytes

This consumer:
 - Connects to broker
 - Sends b'C'
 - Waits for broker response
 - If 'K', parses XML, computes average and pass/fail, prints details
 - Loops forever (or until interrupted)
"""
import socket
import struct
import sys
import time
import xml.etree.ElementTree as ET

HOST = "127.0.0.1"
PORT = 6000

def recv_exact(conn, n):
    """Receive exactly n bytes or raise ConnectionError."""
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed while receiving")
        data += chunk
    return data

def parse_and_print_student(xml_bytes):
    """Parse XML bytes into student fields, compute average and print record."""
    try:
        root = ET.fromstring(xml_bytes)
    except Exception as e:
        print(f"[Consumer] Failed to parse XML: {e}")
        return

    name = root.findtext("Name") or "<unknown>"
    sid = root.findtext("StudentID") or "<unknown>"
    programme = root.findtext("Programme") or "<unknown>"

    courses = []
    courses_el = root.find("Courses")
    if courses_el is not None:
        for c in courses_el.findall("Course"):
            cname = c.findtext("CourseName") or "<unknown>"
            try:
                mark = int(c.findtext("Mark") or 0)
            except:
                mark = 0
            courses.append((cname, mark))

    marks = [m for (_, m) in courses]
    avg = sum(marks) / len(marks) if marks else 0.0
    status = "PASS" if avg >= 50.0 else "FAIL"

    print("----- Student Record -----")
    print(f"Name: {name}")
    print(f"Student ID: {sid}")
    print(f"Programme: {programme}")
    print("Courses and marks:")
    for cn, mk in courses:
        print(f"  {cn}: {mk}")
    print(f"Average: {avg:.2f}")
    print(f"Result: {status}")
    print("--------------------------")

def consume_once(host, port, timeout=30):
    """
    Connect once, request an item from the broker, process it, and return.
    The broker will block the consumer until an item is available.
    """
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect((host, port))
        # Send consumer action byte
        s.sendall(b'C')

        # Read first response byte
        resp = recv_exact(s, 1)
        if resp == b'E':
            print("[Consumer] Broker reported error: expected file not found.")
            return False
        if resp != b'K':
            print(f"[Consumer] Unexpected broker response: {resp!r}")
            return False

        # Read index and xml length
        idx_bytes = recv_exact(s, 4)
        ln_bytes = recv_exact(s, 4)
        idx = struct.unpack("!I", idx_bytes)[0]
        ln = struct.unpack("!I", ln_bytes)[0]

        # Read xml bytes
        xml = recv_exact(s, ln)

        print(f"[Consumer] Received student{idx}.xml ({ln} bytes) from broker.")
        parse_and_print_student(xml)
        # broker already removed the file from disk
        return True

def main(host=HOST, port=PORT, delay=0.2):
    print(f"[Consumer] Connecting to broker at {host}:{port}. Delay between requests: {delay}s")
    try:
        while True:
            try:
                ok = consume_once(host, port)
                # If consume_once returns False, still continue and retry
            except ConnectionError as e:
                print(f"[Consumer] Connection error: {e}. Retrying in {delay} seconds...")
            except socket.timeout:
                print("[Consumer] Socket timed out waiting for broker. Retrying...")
            except Exception as e:
                print(f"[Consumer] Unexpected error: {e}")
            time.sleep(delay)
    except KeyboardInterrupt:
        print("\n[Consumer] Interrupted by user. Exiting.")

if __name__ == "__main__":
    host = HOST
    port = PORT
    delay = 0.2
    if len(sys.argv) >= 2:
        host = sys.argv[1]
    if len(sys.argv) >= 3:
        try:
            port = int(sys.argv[2])
        except:
            pass
    if len(sys.argv) >= 4:
        try:
            delay = float(sys.argv[3])
        except:
            pass
    main(host, port, delay)
