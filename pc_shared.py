

import os
import random
import threading
import time
import xml.etree.ElementTree as ET
import sys
from collections import deque

SHARED_DIR = "shared"
MAX_BUFFER = 10


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

def xml_to_itstudent(xml_bytes):
    root = ET.fromstring(xml_bytes)
    name = root.findtext("Name")
    sid = root.findtext("StudentID")
    programme = root.findtext("Programme")
    courses = []
    for c in root.find("Courses").findall("Course"):
        cname = c.findtext("CourseName")
        mark = int(c.findtext("Mark"))
        courses.append((cname, mark))
    return name, sid, programme, courses


buffer = deque()
empty = threading.Semaphore(MAX_BUFFER)  
full = threading.Semaphore(0)            
mutex = threading.Semaphore(1)          


def ensure_shared_dir():
    if not os.path.exists(SHARED_DIR):
        os.makedirs(SHARED_DIR)


def producer_thread(produce_count=20, produce_delay=(0.2, 1.0)):
   
    ensure_shared_dir()
    file_index = 1  # will cycle 1..10 for file naming
    produced = 0
    while produced < produce_count:
        
        name = random_name()
        sid = random_id()
        prog = random_programme()
        courses = random_courses()
        xml_bytes = itstudent_to_xml(name, sid, prog, courses)

        
        filename = os.path.join(SHARED_DIR, f"student{file_index}.xml")
        with open(filename, "wb") as f:
            f.write(xml_bytes)

        
        empty.acquire()    
        mutex.acquire()
        try:
            buffer.append(file_index)
            print(f"[Producer] produced student{file_index}.xml -> buffer (size={len(buffer)})")
        finally:
            mutex.release()
            full.release()  

        produced += 1
        file_index += 1
        if file_index > 10:
            file_index = 1

        time.sleep(random.uniform(*produce_delay))

    print("[Producer] finished producing.")


def consumer_thread(consume_delay=(0.1, 0.7)):
    while True:
        # wait for item
        full.acquire()
        mutex.acquire()
        try:
            if len(buffer) == 0:
            
                mutex.release()
                continue
            idx = buffer.popleft()
        finally:
            mutex.release()
            empty.release()  

        filename = os.path.join(SHARED_DIR, f"student{idx}.xml")
        if not os.path.exists(filename):
            print(f"[Consumer] WARNING: expected {filename} but file not found.")
            continue

        # read xml
        try:
            with open(filename, "rb") as f:
                xml_bytes = f.read()
            name, sid, programme, courses = xml_to_itstudent(xml_bytes)
            
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

            # delete file (clear content)
            try:
                os.remove(filename)
                print(f"[Consumer] removed {filename}")
            except Exception as e:
                print(f"[Consumer] failed to delete {filename}: {e}")

        except Exception as e:
            print(f"[Consumer] error processing {filename}: {e}")

        time.sleep(random.uniform(*consume_delay))


if __name__ == "__main__":
    
    produce_count = 20
    if len(sys.argv) >= 2:
        try:
            produce_count = int(sys.argv[1])
        except:
            pass


    consumer = threading.Thread(target=consumer_thread, daemon=True)
    consumer.start()

    producer = threading.Thread(target=producer_thread, args=(produce_count,), daemon=False)
    producer.start()

    # Wait for producer to finish
    producer.join()
    # allow consumer to finish processing any remaining items
    while True:
        # if buffer empty, break
        mutex.acquire()
        bsize = len(buffer)
        mutex.release()
        if bsize == 0:
            break
        time.sleep(0.2)
    print("THE CLASSICAL PRODUCERR-CONSUMER PROBLEM CSC 411")
