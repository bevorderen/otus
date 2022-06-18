from optparse import OptionParser
import logging
import socket
import string
import random
import threading
import urllib.parse
import os
from datetime import datetime, timezone
import mimetypes

OK = 200
NOT_FOUND = 404
FORBIDDEN = 403
BAD_REQUEST = 400
NOT_ALLOWED = 405
ALLOWED_CONTENT_TYPE = [
    mimetypes.types_map['.html'],
    mimetypes.types_map['.css'],
    mimetypes.types_map['.js'],
    mimetypes.types_map['.jpg'],
    mimetypes.types_map['.jpeg'],
    mimetypes.types_map['.png'],
    mimetypes.types_map['.gif'],
    mimetypes.types_map['.swf'],
]
MAP_STATUS_TO_TEXT = {
    OK: "OK",
    NOT_FOUND: "Not Found",
    FORBIDDEN: "Forbidden",
    BAD_REQUEST: "Bad Request",
    NOT_ALLOWED: "Not Allowed"
}


class Response:
    def __init__(self, raw_data, document_root):
        self.raw_data = raw_data
        self.document_root = document_root
        self.status = None
        self.response_headers = {}
        self.method = None
        self.body = b''
        self.protocol_version = "HTTP/1.1"

    def parse_data(self):
        try:
            first_string = self.raw_data[:self.raw_data.find("\r\n")].split()
        except (KeyError, IndexError):
            self.status = BAD_REQUEST
            return

        if len(first_string) == 3:
            self.method, url, self.protocol_version = first_string
        elif len(first_string) == 2:
            self.method, url = first_string
        elif len(first_string) == 1:
            self.method = first_string

        request = urllib.parse.unquote(url)
        self.path = self.document_root + request + "index.html" if request.endswith('/') else self.document_root + os.path.realpath(request)

        if "?" in self.path:
            self.path = self.path.split("?")[0]

        all_lines = self.raw_data.split('\r\n')
        for header_line in all_lines[1:]:
            if not header_line:
                break
            header, value = header_line.split(":", 1)
            if header == "Connection":
                self.response_headers[header] = value.strip()

    def handle(self):
        self.parse_data()
        if self.method not in ["GET", "HEAD"]:
            self.status = NOT_ALLOWED

        self.set_headers()

        if self.method == "HEAD":
            return
        
        if self.status != OK:
            return
        
        if self.method == "GET":
            with open(self.path, "rb") as file:
                self.body = file.read()

        self.status = OK

    def set_headers(self):
        if os.path.isfile(self.path):
            try:
                size = os.stat(self.path).st_size
            except OSError:
                self.status = NOT_FOUND
                return

            filename = self.path.split("/")[-1]
            content_type, _ = mimetypes.guess_type(filename)
            if content_type not in ALLOWED_CONTENT_TYPE:
                self.status = NOT_ALLOWED
                return
            self.response_headers['Content-Type'] = content_type
            self.response_headers['Content-Length'] = str(size)
            self.status = OK
        elif not os.path.exists(self.path):
            self.status = NOT_FOUND
        else:
            self.status = FORBIDDEN

    def send(self, connection):
        self.response_headers['Connection'] = 'close'
        headers = "\r\n".join(
            f"{key}: {value}" for key, value in self.response_headers.items()
        )

        headers += "\r\nServer: OTUS\r\n"
        headers += f"Date: {datetime.now(timezone.utc)}\n\n"

        response = f"\r\n{self.protocol_version} {self.status} {MAP_STATUS_TO_TEXT[self.status]}\r\n"
        response += headers
        response = response.encode("utf-8")
        body = self.body if self.status == OK else b''

        try:
            connection.sendall(response + body)
            connection.close()
        except socket.error as e:
            logging.error('%s: socket error %s ' % (self.worker, e))


class Worker:
    def __init__(self, host, port, server_socket, document_root):
        self.host = host
        self.port = port
        self.server_socket = server_socket
        self.worker_name = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=5))
        self.tread = threading.Thread(
            target=self.listen, name=self.worker_name)
        self.document_root = document_root

    def read_data(self, client_connection):
        raw_data = ''
        while True:
            part = client_connection.recv(1024).decode('utf-8')
            raw_data += part
            if raw_data.find('\r\n\r\n') != -1 or not part:
                break
        return raw_data

    def listen(self):
        while True:
            try:
                client_connection, client_address = self.server_socket.accept()
            except socket.error as e:
                logging.exception("An error when accept connection")

            data = self.read_data(client_connection)
            if data:
                response = Response(
                    raw_data=data, document_root=self.document_root)
                response.handle()
                response.send(client_connection)


class HTTPServer:
    def __init__(self, document_root, host, port, workers):
        self.document_root = document_root
        self.host = host
        self.port = port
        self.workers = workers
        self.tread_poll = []

    def run(self):
        self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server_socket.setsockopt(
            socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.server_socket.bind((self.host, self.port))
        self.server_socket.listen()
        for _ in range(self.workers):
            worker = Worker(
                self.host, self.port,
                self.server_socket,
                self.document_root
            )
            worker.tread.daemon = True
            worker.tread.start()
            self.tread_poll.append(worker.tread)

        while True:
            pass


if __name__ == "__main__":
    op = OptionParser()
    op.add_option("--host", action="store", type=str, default="localhost")
    op.add_option("-p", "--port", action="store", type=int, default=8080)
    op.add_option("-l", "--log", action="store", default=None)
    op.add_option("-w", "--workers", action="store", type=int, default=2)
    op.add_option("-r", "--document_root",
                  action="store", type=str, default="")
    (opts, args) = op.parse_args()
    logging.basicConfig(filename=opts.log, level=logging.INFO,
                        format='[%(asctime)s] %(levelname).1s %(message)s', datefmt='%Y.%m.%d %H:%M:%S')
    server = HTTPServer(
        document_root=opts.document_root,
        host=opts.host,
        port=opts.port,
        workers=opts.workers,
    )
    server.run()
