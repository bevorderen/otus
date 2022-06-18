## run server:
'''
cd hm3
python httpd.py -p {port} -r {document root} - w {workers}
'''

Test results:
Server Software:        OTUS
Server Hostname:        localhost
Server Port:            80

Document Path:          /
Document Length:        0 bytes

Concurrency Level:      100
Time taken for tests:   292.372 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      4950000 bytes
HTML transferred:       0 bytes
Requests per second:    171.02 [#/sec] (mean)
Time per request:       584.744 [ms] (mean)
Time per request:       5.847 [ms] (mean, across all concurrent requests)
Transfer rate:          16.53 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   1.3      0      33
Processing:     2  584 260.4    694     983
Waiting:        0  580 259.0    690     977
Total:          3  584 260.0    694     983

Percentage of the requests served within a certain time (ms)
  50%    694
  66%    739
  75%    763
  80%    778
  90%    816
  95%    843
  98%    874
  99%    899
 100%    983 (longest request)