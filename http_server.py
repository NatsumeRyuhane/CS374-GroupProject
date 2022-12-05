import connect
import socket
import logging
import enum

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
                            if request["route"] == "/":
                                with open("./templates/index.html") as f:
                                    content = f.read()

                        response = self.construct_http_response(200, content, MIMEType="text/html")
                        self.send(client, response)
        except connect.ConnectionDropException:
            self.connection_drop_handler(client)

    def parse_http_request(self, HTTPRequest: str):
        if HTTPRequest:
            data = HTTPRequest.replace('\r\n', '\n')
            attr = data.split('\n')

            head = attr.pop(0).split(' ')

            attr_dict = {}
            attr_dict["method"] = head[0]
            attr_dict["route"] = head[1]
            attr_dict["protocol"] = head[2]

            for a in attr:
                if a == '':
                    continue
                else:
                    line = a.split(': ')
                    attr_dict[line[0]] = line[1]
        else:
            return {}

        return attr_dict

    def construct_http_response(self, status_code: int, body: str or bytes, MIMEType: str = "text/html"):
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
Content-Type: {MIMEType}\r
Connection: Keep-Alive\r
Keep-Alive: timeout=5, max=1000\r
\r
{body}
"""

        return response

    def add_route(self, route: str):
        pass