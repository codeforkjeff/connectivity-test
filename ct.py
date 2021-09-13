
import datetime
import shutil
import subprocess
import sys

# 67.218.102.107 = first hop after wifi router
host = "67.218.102.107"

interval = 3
acceptable_time = 4

ping_path = shutil.which("ping")

proc = subprocess.Popen([ping_path, host, "-i", str(interval), "-D"], stdout=subprocess.PIPE, bufsize=0)

last_timestamp = 0
last_icmp_seq = None

while proc.poll() is None:
    line = proc.stdout.readline()
    line = line.decode('utf-8').strip()

    #print(f"{line}")

    if line.startswith("["):
        timestamp = line[line.index("[")+1:line.index("]")]
        timestamp = timestamp[:timestamp.index(".")]
        timestamp = int(timestamp)

        icmp_str = "icmp_seq="
        pos = line.index(icmp_str) + len(icmp_str)
        icmp_seq = line[pos:line.index(" ", pos)]
        icmp_seq = int(icmp_seq)

        if last_icmp_seq and icmp_seq - last_icmp_seq != 1:
            print(f"WARNING: lost a packet, skipped icmp_seq {last_icmp_seq + 1}")
        last_icmp_seq = icmp_seq

        elapsed = timestamp - last_timestamp
        if last_timestamp and elapsed > acceptable_time:
            print(f"{datetime.datetime.now()} {elapsed} seconds elapsed! Possible problem with connection")

        last_timestamp = timestamp
    elif line.startswith("PING"):
        pass
    else:
        # unrecognized line, print it
        print(line.strip())
        #sys.exit(1)
