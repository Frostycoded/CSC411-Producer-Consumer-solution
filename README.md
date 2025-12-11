# CSC411-Producer-Consumer-solution
Producer-Consumer (shared buffer + semaphores) example. Writes XML files student1.xml .. student10.xml to ./shared/ Producer inserts file index (1..10) into buffer (max size 10). Consumer reads index from buffer, parses XML, prints student info, computes average and pass/fail, then deletes the file. Usage: python pc_shared.py 


 Producer–Consumer XML Student System

This project is a Python demonstration of the Producer–Consumer problem using:

Threads

Semaphores

A shared buffer

XML file generation and processing


The producer creates random student XML files and places their file indexes into a bounded buffer.
The consumer reads these indexes, processes the corresponding XML files, prints student details, and then deletes the files.

 Purpose

This program was built to demonstrate:

Thread synchronisation

Safe communication between producer and consumer threads

Proper use of semaphores (empty, full, mutex)

Realistic file I/O operations (creating, reading, deleting XML student records)


It shows how concurrency issues like overproduction, over-consumption, and race conditions are solved.

 Project Structure

Project/
│
├── pc_shared.py       # Main Producer–Consumer program
└── shared/            # Directory where XML student files are stored

How It Works (High-Level)

🔵 Producer

Generates random student data

Writes it to XML files: student1.xml … student10.xml

Inserts the file index into the shared buffer

Uses:

Empty semaphore (waits if buffer is full)

Mutex (exclusive access)

Full semaphore (signals consumer)



🔴 Consumer

Waits for a file index to become available

Reads and parses the XML file

Prints:

Name

Student ID

Programme

Course marks

Average + pass/fail status


Deletes the XML file

Uses:

Full semaphore (waits if buffer empty)

Mutex (exclusive access)

Empty semaphore (signals space freed)



 How the Code Solves the Producer–Consumer Problem

This program prevents:

✔️ Producer from overfilling the buffer

Handled by empty.acquire() — producer waits when no space is available.

✔️ Consumer from reading an empty buffer

Handled by full.acquire() — consumer waits when nothing is available.

✔️ Both threads from accessing buffer at the same time

Handled by semaphore mutex — ensures mutual exclusion.

✔️ Lost updates / race conditions

The buffer is always locked before modification.

 Running the Program

Default (produce 20 students)

Python pc_shared.py

Producing a custom number of students

Python pc_shared.py 50

XML files will appear in the shared/ folder and will be removed after processing.



Output Example

[Producer] produced student3.xml -> buffer (size=5)
----- Student Record -----
Name: Thabani Dlamini
Student ID: 12345678
Programme: BSc.IT
Courses and marks:
  Programming 2: 75
  Database Design: 62
Average: 68.50
Result: PASS
[Consumer] removed shared/student3.xml




