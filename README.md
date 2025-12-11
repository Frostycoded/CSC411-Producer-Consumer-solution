# CSC411-Producer-Consumer-solution
Producer-Consumer (shared buffer + semaphores) example. Writes XML files student1.xml .. student10.xml to ./shared/ Producer inserts file index (1..10) into buffer (max size 10). Consumer reads index from buffer, parses XML, prints student info, computes average and pass/fail, then deletes the file. Usage: python pc_shared.py 
