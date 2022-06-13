#!/usr/bin/env python
# -*- coding: utf-8 -*-


# log_format ui_short '$remote_addr  $remote_user $http_x_real_ip [$time_local] "$request" '
#                     '$status $body_bytes_sent "$http_referer" '
#                     '"$http_user_agent" "$http_x_forwarded_for" "$http_X_REQUEST_ID" "$http_X_RB_USER" '
#                     '$request_time';

config = {
    "REPORTS_DIR": "./reports",
    "LOG_DIR": "./log",
    "LOG_FILE": "./log/log.log",
    "LOGS_DIR": "./nginx/logs",
    "ERRORS_LIMIT": 25,
    "MAX_REPORT_SIZE": 1000
}


def main():
    pass


if __name__ == "__main__":
    main()
