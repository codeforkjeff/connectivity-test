
# connectivity-test

Small wrapper script around ping that reports periods of connectivity loss
and rates of packet loss.

Just run `python ct.py google.com`

Best to use the IP address of the first hop after your router to test your
line connectivity.

Output looks like this:

```
2021-09-29 13:49:44 Packet loss (last 15 mins): 0.0%
2021-09-29 14:02:06 possible lost packet(s): last icmp_seq received was 35345, just received 35347
2021-09-29 14:02:06 7 seconds elapsed since last successful ping
2021-09-29 14:04:45 Packet loss (last 15 mins): 0.33%
```

Run with `-h` to see options.
