import connect
import socket
import logging
import enum
import functools


class BadHTTPRequestException(SyntaxError):
    pass


class HTTPRequest():
    def __init__(self, client_IP: str, HTTP_request_plain: str):
        self.client_IP = client_IP
        self.plain = HTTP_request_plain
        try:
            request_replaced_lnbrk = HTTP_request_plain.replace('\r\n', '\n')
            request_replaced_lnbrk = request_replaced_lnbrk.split("\n\n")

            # http header
            request_headers = request_replaced_lnbrk[0]
            header_lines = request_headers.split('\n')

            # first line in header
            first_line = header_lines.pop(0).split(' ')

            self.method = first_line[0]
            self.protocol = first_line[2]
            self.url = first_line[1].split('?')
            self.route = self.url[0]
            self.parameters = {}
            self.headers = {}

            # request url with parameters
            if len(self.url) > 1:
                for param in self.url[1].split('&'):
                    param = param.split("=")
                    self.parameters[param[0]] = param[1]

            for a in header_lines:
                line = a.split(': ')
                self.headers[line[0]] = line[1]

            # http body
            self.body = request_replaced_lnbrk[1]
        except Exception as e:
            raise BadHTTPRequestException


class HTTPServer(connect.Server):

    def __init__(self, hostname: str, port: int):
        super().__init__(hostname, port)
        self.route_table = {}

    def client_connection_handler(self, client: socket.socket):
        try:
            while True:
                data = self.receive_from(client)
                request = HTTPRequest(self.client_addr_table[client][0], data)

                if request:
                    logging.info(f"[ {self.client_addr_table[client][0]}:{self.client_addr_table[client][1]} ] HTTP request: METHOD = {request.method}, route = {request.route}")

                    if request.route in self.route_table.keys():
                        target = self.route_table[request.route]
                        content = target[0](request)
                        mime_type = target[1]
                        response = self.construct_http_response(200, content, MIME_type=mime_type)
                    else:
                        response = self.construct_http_response(404, "")

                    self.send(client, response)
        except BadHTTPRequestException:
            logging.warning(f"Unable to resolve HTTP request from [ {self.client_addr_table[client][0]}:{self.client_addr_table[client][1]} ]")
        except connect.ConnectionDropException:
            self.connection_drop_handler(client)

    def register_route(self, route: str, aliases: list = None, MIME_type: str = "text/plain"):
        def decorate(func):
            logging.info(f"registering route {route}, type = [{MIME_type}], function_id = {hex(id(func))}")
            self.route_table[route] = [func, MIME_type]
            if aliases:
                for alias in aliases:
                    logging.info(f"registering route {alias} (as alias of {route}), type = [{MIME_type}], function_id = {hex(id(func))}")
                    self.route_table[alias] = [func, MIME_type]

            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorate


    def construct_http_response(self, status_code: int, body: str or bytes, MIME_type: str = "text/html"):
        if type(body) is str:
            body.encode('utf-8')

        status_code_dict = {
            200: "200 OK",
            403: "403 Forbidden",
            404: "404 Not Found",
            500: "500 Internal Server Error"
            }

        response = f"""
HTTP/1.1 {status_code_dict[status_code]}\r
Server: FKU Server\r
Content-Length: {len(body)}\r
Content-Type: {MIME_type}\r
Connection: Keep-Alive\r
Keep-Alive: timeout=5, max=1000\r
\r
{body}
"""
        return response
