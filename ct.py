
import argparse
import datetime
import logging
import shutil
import subprocess
import sys
import time


ping_path = shutil.which("ping")


def start_ping(host, interval):
    logging.info("Starting ping...")
    proc = subprocess.Popen([ping_path, host, "-i", str(interval)], stdout=subprocess.PIPE, bufsize=0)
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

    proc = start_ping(host, interval)

    while proc.poll() is None:
        line = proc.stdout.readline()
        line = line.decode('utf-8').strip()

        logging.debug(f"{line}")

        if "icmp" in line:
            timestamp = get_timestamp()

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

            if timestamp - report_last > (report_frequency*60):
                pct = round(lost_packets / total_packets * 100, 2)
                logging.info(f"Packet loss (last {report_frequency} mins): {pct}%")
                report_last = get_timestamp()
                total_packets = 0
                lost_packets = 0

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
            proc = start_ping(host, interval)

    logging.error("ping process exited unexpectedly.")


def main():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

    parser = argparse.ArgumentParser(description='Connectivity test')
    parser.add_argument('host', metavar='host', type=str,
                        help='host to ping')
    parser.add_argument('-i', dest='interval', action='store', type=int, default=3,
                        help='ping interval in seconds (default: 3s)')
    parser.add_argument('-t', dest='threshold', action='store', type=int, default=4,
                        help='show warning when time elapsed since last packet exceeds this value (default: 4s)')
    parser.add_argument('-f', dest='report_frequency', action='store', type=int, default=15,
                        help='report frequency in minutes (default: 15)')

    args = parser.parse_args()

    try:
        loop_forever(args.host, args.interval, args.threshold, args.report_frequency)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
