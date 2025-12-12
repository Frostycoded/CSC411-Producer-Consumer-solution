#!/usr/bin/env python3
"""
producer_client.py
Connects to broker and sends produced XML student files.

Usage:
    python producer_client.py [produce_count] [host] [port]
Defaults: produce_count=20 host=127.0.0.1 port=6000
"""
import socket
import struct
import random
import time
import sys
import xml.etree.ElementTree as ET

HOST = "127.0.0.1"
PORT = 6000

PROGRAMMES = ["BSc.IT", "CS", "Software Engineering", "Information Systems"]
COURSES = ["Programming 2", "Calculus", "Data Structures and Algorithms", "Database Design", "Networks", "Modern OS", "Web Technology and Development"]

def random_name():
    first = ["Temalungelo", "Sakhizwe", "Nomcebo", "Sebenele", "Thabani", "Lindelani", "Themba", "Skhandziso", "Skhanyiso", "Sphesihle"]
    last = ["Malaza", "Ngwenya", "Dlamini", "Mhlanga", "Mamba", "Khumalo", "Mabuza", "Shongwe"]
    return f"{random.choice(first)} {random.choice(last)}"

def random_id():
    return "{:08d}".format(random.randint(0, 99999999))

def random_programme():
    return random.choice(PROGRAMMES)

def random_courses():
    n = random.randint(3, 6)
    chosen = random.sample(COURSES, n)
    return [(c, random.randint(30, 100)) for c in chosen]

def itstudent_to_xml(name, sid, programme, courses):
    student = ET.Element("ITstudent")
    ET.SubElement(student, "Name").text = name
    ET.SubElement(student, "StudentID").text = sid
    ET.SubElement(student, "Programme").text = programme
    courses_el = ET.SubElement(student, "Courses")
    for cname, mark in courses:
        c = ET.SubElement(courses_el, "Course")
        ET.SubElement(c, "CourseName").text = cname
        ET.SubElement(c, "Mark").text = str(mark)
    return ET.tostring(student, encoding="utf-8", method="xml")

def send_item(idx, xml_bytes, host=HOST, port=PORT):
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    try:
        # action byte 'P', then idx (4), xml len (4), xml
        header = b'P' + struct.pack("!I", idx) + struct.pack("!I", len(xml_bytes))
        s.sendall(header + xml_bytes)
        # we don't expect a response for produce
    finally:
        s.close()

def main(produce_count=20, host=HOST, port=PORT):
    file_index = 1
    produced = 0
    while produced < produce_count:
        name = random_name()
        sid = random_id()
        prog = random_programme()
        courses = random_courses()
        xml_bytes = itstudent_to_xml(name, sid, prog, courses)
        try:
            send_item(file_index, xml_bytes, host, port)
            print(f"[Producer] sent student{file_index}.xml to broker")
        except Exception as e:
            print(f"[Producer] failed to send to broker: {e}")
        produced += 1
        file_index += 1
        if file_index > 10:
            file_index = 1
        time.sleep(random.uniform(0.2, 1.0))
    print("[Producer] finished producing.")

if __name__ == "__main__":
    produce_count = 20
    host = HOST
    port = PORT
    if len(sys.argv) >= 2:
        try:
            produce_count = int(sys.argv[1])
        except:
            pass
    if len(sys.argv) >= 3:
        host = sys.argv[2]
    if len(sys.argv) >= 4:
        port = int(sys.argv[3])
    main(produce_count, host, port)
