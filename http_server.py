import connect
import socket
import logging
import enum
import functools


class HTTPServer(connect.Server):

    def __init__(self, hostname: str, port: int):
        super().__init__(hostname, port)
        self.route_table = {}

    def client_connection_handler(self, client: socket.socket):
        try:
            while True:
                data = self.receive_from(client)
                if len(data) != 0:
                    request = self.parse_http_request(data)

                    if request:
                        logging.info(f"[ {self.client_addr_table[client][0]}:{self.client_addr_table[client][1]} ] request: METHOD = {request['method']}, route = {request['route']}")

                        content = ""
                        if "route" in request.keys():
                            if request["route"] in self.route_table.keys():
                                target = self.route_table[request["route"]]
                                content = target[0](request)
                                mime_type = target[1]
                                response = self.construct_http_response(200, content, MIME_type = mime_type)
                            else:
                                target = self.route_table["/static/html/404.html"]
                                content = target[0](request)
                                mime_type = target[1]
                                response = self.construct_http_response(404, content, MIME_type=mime_type)
                        else:
                            target = self.route_table["/static/html/404.html"]
                            content = target[0](request)
                            mime_type = target[1]
                            response = self.construct_http_response(200, content, MIME_type=mime_type)

                        self.send(client, response)
        except connect.ConnectionDropException:
            self.connection_drop_handler(client)

    def register_route(self, route: str, aliases: list = None, MIME_type: str = "text/plain"):
        def decorate(func):
            logging.info(f"registering route {route}, type = [{MIME_type}], function_id = {hex(id(func))}")
            self.route_table[route] = [func, MIME_type]
            if aliases:
                for alias in aliases:
                    logging.info(f"registering route {alias} (as alias of {route}), type = [{MIME_type}], function_id = {hex(id(func))}")
                    self.route_table[alias] =[func, MIME_type]
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                return func(*args, **kwargs)

            return wrapper

        return decorate

    def parse_http_request(self, HTTPRequest: str):
        if HTTPRequest:
            try:
                data = HTTPRequest.replace('\r\n', '\n')
                attr = data.split('\n')

                head = attr.pop(0).split(' ')

                attr_dict = {}
                attr_dict["method"] = head[0]
                url = head[1].split('?')
                attr_dict["route"] = url[0]
                attr_dict["protocol"] = head[2]
                attr_dict["parameters"] = {}

                if len(url) > 1:
                    for p in url[1].split('&'):
                        p = p.split("=")
                        attr_dict["parameters"][p[0]] = p[1]

                for a in attr:
                    if a == '':
                        continue
                    else:
                        line = a.split(': ')
                        if len(line) < 2:
                            continue
                        else:
                            attr_dict[line[0]] = line[1]
            except Exception:
                return {}
        else:
            return {}

        return attr_dict

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
