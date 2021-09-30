
import sys

if sys.version_info[0] < 3:
    print("This script requires Python version 3")
    sys.exit(1)

import argparse
import datetime
import logging
import queue
import shutil
import subprocess
import threading
import time

ping_path = shutil.which("ping")


def read_pipe(proc, fileobj, queue):
    for line in iter(fileobj.readline, b''):
        line = line.decode('utf-8').strip()
        queue.put(line)
    fileobj.close()
    logging.debug(f"exiting reader thread")


def start_ping(host, interval, stdout_queue, stderr_queue):
    logging.debug("Starting ping...")
    # use -c so icmp_seq never wraps around after reaching 65535
    proc = subprocess.Popen([ping_path, host, "-i", str(interval), "-c", "1024"], stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)#, close_fds=True)
    t = threading.Thread(target=read_pipe, args=(proc, proc.stdout, stdout_queue))
    t.daemon = True
    t.start()
    t = threading.Thread(target=read_pipe, args=(proc, proc.stderr, stderr_queue))
    t.daemon = True
    t.start()
    return proc


def get_timestamp():
    return int(time.time())


def loop_forever(host, interval, threshold, report_frequency):
    """
    report_frequency = in minutes
    """

    last_timestamp = 0
    last_icmp_seq = None

    total_packets = 0
    lost_packets = 0

    report_last = get_timestamp()

    stdout = queue.Queue()
    stderr = queue.Queue()
    proc = None

    while True:

        #### check if we need to start/restart ping

        if proc is None or proc.poll() is not None:
            if proc:
                logging.debug("Killing ping process...")
                proc.kill()
                try:
                    proc.wait(60)
                except subprocess.TimeoutExpired:
                    logging.error("couldn't kill ping process. oh well.")
            proc = start_ping(host, interval, stdout, stderr)
            last_icmp_seq = None

        #### read

        try:
            line = stdout.get(timeout=1)
        except queue.Empty:
            line = None

        try:
            line_err = stderr.get(timeout=0.1)
        except queue.Empty:
            line_err = None

        timestamp = get_timestamp()

        if line:

            logging.debug(f"{line}")

            if "icmp" in line:

                icmp_str = "icmp_seq="
                pos = line.index(icmp_str) + len(icmp_str)
                icmp_seq = line[pos:line.index(" ", pos)]
                icmp_seq = int(icmp_seq)

                if last_icmp_seq:
                    if icmp_seq - last_icmp_seq > 1:
                        logging.warning(f"possible lost packet(s): last icmp_seq received was {last_icmp_seq}, just received {icmp_seq}")
                        lost_packets += icmp_seq - last_icmp_seq - 1
                    elif icmp_seq < last_icmp_seq:
                        logging.warning(f"out of order delivery: last icmp_seq received was {last_icmp_seq}, just received {icmp_seq}")
                        lost_packets -= 1
                last_icmp_seq = icmp_seq

                is_response = "time=" in line

                if is_response:
                    elapsed = timestamp - last_timestamp
                    if last_timestamp and elapsed > threshold:
                        logging.warning(f"{elapsed} seconds elapsed since last successful ping")
                    last_timestamp = timestamp

                total_packets += 1

            elif line.startswith("PING") or line.startswith("rtt") or "packet loss" in line or "statistics" in line:
                # ignore these
                pass
            else:
                logging.error(f"Unrecognized ping output: {line.strip()}")

        if line_err:
            if "Network is unreachable" in line_err:
                lost_packets += 1
            else:
                logging.error(f"Unrecognized ping output (stderr): {line_err}")

        #### print a report periodically

        if timestamp - report_last > (report_frequency*60):
            expected_packets = report_frequency * 60 / interval
            pct = round(lost_packets / expected_packets * 100, 2)
            logging.info(f"Packet loss (last {report_frequency} mins): {pct}%")
            report_last = get_timestamp()
            total_packets = 0
            lost_packets = 0


def main():

    parser = argparse.ArgumentParser(description='Connectivity test')
    parser.add_argument('host', metavar='host', type=str,
                        help='host to ping')
    parser.add_argument('-i', dest='interval', action='store', type=int, default=3,
                        help='ping interval in seconds (default: 3s)')
    parser.add_argument('-t', dest='threshold', action='store', type=int, default=4,
                        help='show warning when time elapsed since last packet exceeds this value (default: 4s)')
    parser.add_argument('-f', dest='report_frequency', action='store', type=int, default=15,
                        help='report frequency in minutes (default: 15)')
    parser.add_argument('-d', dest='debug', action='store_true',
                        help='display debug logging')

    args = parser.parse_args()

    logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    try:
        loop_forever(args.host, args.interval, args.threshold, args.report_frequency)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
