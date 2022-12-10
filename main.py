import logging
import os
import threading
import json
import time
import urllib.parse

if not os.path.exists("../logs/"):
    os.mkdir("../logs/")

with open('../logs/server.log', 'w', encoding='utf-8') as f:
    f.truncate(0)

logging.basicConfig(level='DEBUG', format='[%(asctime)s] [%(levelname)s] %(message)s', encoding='utf-8',
                    handlers=[
                        logging.FileHandler("./logs/server.log"),
                        logging.StreamHandler()
                        ])

import http_server
import init

os.system("ulimit -n 65535")
serv = http_server.HTTPServer(hostname="0.0.0.0", port=11451)

# register chat system logic

message_ID = 1
chat_file_lock = threading.Lock()

@serv.register_route(route="/api/post-message", MIME_type="text/plain")
def post_message(request: http_server.HTTPRequest):
    global message_ID

    chat_file_lock.acquire()
    with open("./data/chat.json", "r") as f:
        chat_log = json.load(f)
        f.close()

    new_message = {
            "id": message_ID,
            "type": "plain",
            "timestamp": int(time.time()*1000),
            "sender": request.client_IP,
            "private_recipient": "null",
            "content":  request.body
        }

    chat_log["messages"].append(new_message)
    with open("./data/chat.json", "w") as f:
        json.dump(chat_log, f)

    message_ID += 1

    chat_file_lock.release()
    return ""

@serv.register_route(route="/api/get-message", MIME_type="application/json")
def get_message(request: http_server.HTTPRequest):
    global message_ID

    chat_file_lock.acquire()
    with open("./data/chat.json", "r") as f:
        chat_log = json.load(f)
        f.close()

    message_list = chat_log["messages"]
    outgoing_message_list = []

    if "maxMessageID" in request.parameters.keys():
        for idx in range(0, len(message_list)):
            if message_list[idx]["id"] > int(request.parameters["maxMessageID"]):
                outgoing_message_list.append(message_list[idx])

    chat_file_lock.release()
    return json.dumps(outgoing_message_list)

@serv.register_route(route="/api/get-username", MIME_type="text/plain")
def get_message(request: http_server.HTTPRequest):
    return request.client_IP

init.init_server(serv)
init.init_env()
serv.run()
