
# connectivity-test

Small wrapper script around ping that displays output when response time
exceeds a certain threshold. Useful for logging connectivity outages.

Just run `python ct.py google.com`

Best to use the IP address of the first hop after your router to test your
line connectivity.

Output looks like this:

```
2021-09-29 16:19:58 Packet loss (last 15 mins): 0.0%
```

Run with `-h` to see options.
