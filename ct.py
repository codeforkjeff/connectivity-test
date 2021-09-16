
import datetime
import logging
import shutil
import subprocess
import sys
import time

# 67.218.102.107 = first hop after wifi router
host = "67.218.102.107"

interval = 3
acceptable_time = 4

def start_ping():
    logging.info("Starting ping...")
    proc = subprocess.Popen([ping_path, host, "-i", str(interval)], stdout=subprocess.PIPE, bufsize=0)
    return proc

ping_path = shutil.which("ping")

last_timestamp = 0
last_icmp_seq = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

proc = start_ping()

while proc.poll() is None:
    line = proc.stdout.readline()
    line = line.decode('utf-8').strip()

    logging.debug(f"{line}")

    if "icmp" in line:
        timestamp = int(time.time())

        icmp_str = "icmp_seq="
        pos = line.index(icmp_str) + len(icmp_str)
        icmp_seq = line[pos:line.index(" ", pos)]
        icmp_seq = int(icmp_seq)

        if last_icmp_seq:
            if icmp_seq - last_icmp_seq > 1:
                logging.warning(f"possible lost packet(s): last icmp_seq received was {last_icmp_seq}, just received {icmp_seq}")
            elif icmp_seq < last_icmp_seq:
                logging.warning(f"out of order delivery: last icmp_seq received was {last_icmp_seq}, just received {icmp_seq}")
        last_icmp_seq = icmp_seq

        is_response = "time=" in line

        if is_response:
            elapsed = timestamp - last_timestamp
            if last_timestamp and elapsed > acceptable_time:
                logging.warning(f"{elapsed} seconds elapsed since last successful ping")
            last_timestamp = timestamp

    elif line.startswith("PING"):
        pass
    else:
        logging.error(f"Unrecognized ping output: {line.strip()}")
        logging.info("Killing ping process...")
        proc.kill()
        try:
            proc.wait(60)
        except subprocess.TimeoutExpired:
            logging.error("couldn't kill ping process. oh well.")
        proc = start_ping()

logging.error("ping process exited unexpectedly.")
