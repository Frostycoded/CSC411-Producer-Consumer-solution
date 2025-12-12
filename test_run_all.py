#!/usr/bin/env python3
"""
test_run_all.py

Launch broker_server.py, multiple consumer_client.py instances, and a producer_client.py
to demonstrate a full socket-based Producer-Consumer run.

Usage:
    python test_run_all.py [produce_count] [num_consumers] [host] [port]

Defaults:
    produce_count = 20
    num_consumers = 1
    host = 127.0.0.1
    port = 6000

Notes:
- Requires these files in the same directory:
    - broker_server.py
    - producer_client.py
    - consumer_client.py  (save the consumer code provided earlier into this filename)
- The script will stream subprocess output to the console (inherit stdout/stderr).
"""
import os
import sys
import time
import subprocess
import signal

SHARED_DIR = "shared"

def check_files_exist(files):
    missing = [f for f in files if not os.path.exists(f)]
    if missing:
        print("ERROR: Missing required files:", ", ".join(missing))
        sys.exit(2)

def wait_for_shared_empty(timeout=30, poll=0.5):
    """Wait until shared dir has no .xml files (or until timeout)."""
    start = time.time()
    while True:
        if not os.path.isdir(SHARED_DIR):
            return True
        files = [f for f in os.listdir(SHARED_DIR) if f.endswith(".xml")]
        if not files:
            return True
        if (time.time() - start) > timeout:
            return False
        time.sleep(poll)

def terminate_process(proc, name):
    if proc is None:
        return
    try:
        print(f"[TestRunner] Terminating {name} (pid={proc.pid})...")
        proc.terminate()
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass

def main():
    produce_count = 20
    num_consumers = 1
    host = "127.0.0.1"
    port = "6000"

    if len(sys.argv) >= 2:
        try:
            produce_count = int(sys.argv[1])
        except:
            pass
    if len(sys.argv) >= 3:
        try:
            num_consumers = int(sys.argv[2])
        except:
            pass
    if len(sys.argv) >= 4:
        host = sys.argv[3]
    if len(sys.argv) >= 5:
        port = sys.argv[4]

    required = ["broker_server.py", "producer_client.py", "consumer_client.py"]
    check_files_exist(required)

    python = sys.executable

    broker_proc = None
    producer_proc = None
    consumer_procs = []

    try:
        # 1) Start broker
        print(f"[TestRunner] Starting broker: {python} broker_server.py {host} {port}")
        broker_proc = subprocess.Popen([python, "broker_server.py", host, port],
                                       stdout=None, stderr=None)

        # give broker a moment to start
        time.sleep(0.6)

        # 2) Start consumers
        for i in range(num_consumers):
            print(f"[TestRunner] Starting consumer #{i+1}: {python} consumer_client.py {host} {port} 0.2")
            p = subprocess.Popen([python, "consumer_client.py", host, port, "0.2"],
                                 stdout=None, stderr=None)
            consumer_procs.append(p)
            time.sleep(0.1)

        # 3) Start producer
        print(f"[TestRunner] Starting producer (produce_count={produce_count}): {python} producer_client.py {produce_count} {host} {port}")
        producer_proc = subprocess.Popen([python, "producer_client.py", str(produce_count), host, port],
                                         stdout=None, stderr=None)

        # 4) Wait for producer to finish
        producer_proc.wait()
        print("[TestRunner] Producer finished. Waiting for consumers to process remaining files...")

        # 5) Wait for shared folder to be emptied (files processed and removed)
        ok = wait_for_shared_empty(timeout=60)
        if ok:
            print("[TestRunner] shared/ folder is empty. Consumers likely processed all items.")
        else:
            print("[TestRunner] Timeout waiting for shared/ to be emptied. There may be leftover files.")

        # brief pause to allow consumers to print final messages
        time.sleep(1.0)

    except KeyboardInterrupt:
        print("\n[TestRunner] Interrupted by user.")
    finally:
        # Terminate consumer processes
        for i, p in enumerate(consumer_procs):
            terminate_process(p, f"consumer#{i+1}")

        # Terminate broker
        terminate_process(broker_proc, "broker")

        print("[TestRunner] All subprocesses terminated. Test run complete.")

if __name__ == "__main__":
    main()
