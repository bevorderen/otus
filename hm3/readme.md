## run server:
```
cd hm3
python httpd.py -p {port} -r {document root} - w {workers}
```

## Test results:
Server Software: OTUS
Server Hostname: localhost
Server Port: 80

Document Path: /httptest/dir2/
Document Length: 34 bytes

Concurrency Level:      100
Time taken for tests:   602.357 seconds
Complete requests:      50000
Failed requests:        0
Total transferred:      8550000 bytes
HTML transferred:       1700000 bytes
Requests per second:    83.01 [#/sec] (mean)
Time per request:       1204.715 [ms] (mean)
Time per request:       12.047 [ms] (mean, across all concurrent requests)
Transfer rate:          13.86 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.3      0       4
Processing:     1 1203 333.8   1290    1834
Waiting:        1 1199 332.9   1285    1834
Total:          3 1203 333.6   1290    1834

Percentage of the requests served within a certain time (ms)
  50%   1290
  66%   1338
  75%   1366
  80%   1385
  90%   1435
  95%   1478
  98%   1526
  99%   1563
 100%   1834 (longest request)
