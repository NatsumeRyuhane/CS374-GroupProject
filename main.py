import logging
import os
import threading
import json
import time
import urllib.parse

if not os.path.exists("./logs/"):
    os.mkdir("./logs/")

with open('./logs/server.log', 'w', encoding='utf-8') as f:
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

class Chatroom:

    def __init__(self):
        self.message_ID = 1000
        self.chat_file = "./data/chat.json"
        self.user_data_file = "./user_data.json"


        self.chat_file_lock = threading.Lock()
        self.user_data_file_lock = threading.Lock()
        self.active_users = {}
        self.nickname_table = {}

        with open(self.chat_file, "w+") as f:
            f.truncate(0)

            f.write("""{
"messages" : [
    {
      "id": 0,
      "type": "system",
      "timestamp": 0,
      "sender": null,
      "private_recipient": null,
      "content": "This is the start of the channel."
    }
  ]
}""")
            self.user_status_monitor = threading.Thread(target=self.monitor_active_user, args=())
            self.user_status_monitor.start()


    def add_new_message(self, type, sender, content, private_recipient = "null"):
        self.chat_file_lock.acquire()
        with open("./data/chat.json", "r") as f:
            chat_log = json.load(f)
            f.close()

        new_message = {
            "id": self.message_ID,
            "type": type,
            "timestamp": int(time.time() * 1000),
            "sender": sender,
            "content": content,
            "private_recipient": "null"
        }

        chat_log["messages"].append(new_message)
        with open(self.chat_file, "w") as f:
            json.dump(chat_log, f)

        self.message_ID += 1

        self.chat_file_lock.release()
        return 0


    def get_chat_message(self, request_client, filter_before: int = 0):
        filter_before = int(filter_before)

        self.chat_file_lock.acquire()
        with open(self.chat_file, "r") as f:
            chat_log = json.load(f)
            f.close()

        message_list = chat_log["messages"]
        outgoing_message_list = []

        for idx in range(0, len(message_list)):
            if message_list[idx]["id"] > filter_before:
                outgoing_message_list.append(message_list[idx])

        self.chat_file_lock.release()
        return outgoing_message_list

    def refresh_user_status(self, user):
        self.active_users[user] = time.time()

    def monitor_active_user(self):
        while True:
            time_now = time.time()

            for user in list(self.active_users):
                if time.time() - self.active_users[user] >= 2:
                    del self.active_users[user]
                    chatroom.add_new_message(type="system", sender=0, content=f"{user} left the chat.")

            time.sleep(1)

    def set_nickname(self, user_ip, nickname):
        if user_ip in self.nickname_table.keys():
            chatroom.add_new_message(type="system", sender=0, content=f"{self.nickname_table[user_ip]} changed their nickname to \"{nickname}\".")
        else:
            chatroom.add_new_message(type="system", sender=0, content=f"{user_ip} set their nickname to \"{nickname}\".")
        self.nickname_table[user_ip] = nickname
        return ""

chatroom = Chatroom()

@serv.register_route(route="/api/post-message", MIME_type="text/plain")
def post_message(request: http_server.HTTPRequest):
    chatroom.refresh_user_status(request.client_IP)
    if request.client_IP in chatroom.nickname_table.keys():
        chatroom.add_new_message(type="plain", sender=chatroom.nickname_table[request.client_IP], content=request.body)
    else:
        chatroom.add_new_message(type="plain", sender=request.client_IP, content=request.body)
    return ""

@serv.register_route(route="/api/get-message", MIME_type="application/json")
def get_message(request: http_server.HTTPRequest):
    chatroom.refresh_user_status(request.client_IP)
    if "maxMessageID" in request.parameters.keys():
        message_list = chatroom.get_chat_message(request.client_IP, filter_before=request.parameters["maxMessageID"])
    else:
        message_list = chatroom.get_chat_message(request.client_IP, filter_before=-1)
    return json.dumps(message_list)

@serv.register_route(route="/api/get-configs", MIME_type="application/json")
def get_config(request: http_server.HTTPRequest):
    chatroom.refresh_user_status(request.client_IP)
    config_data = {}
    if request.client_IP in chatroom.nickname_table.keys():
        config_data["username"] = chatroom.nickname_table[request.client_IP]
        chatroom.add_new_message(type="system", sender=0, content=f"{chatroom.nickname_table[request.client_IP]} joined the chat.")
    else:
        config_data["username"] = request.client_IP
        chatroom.add_new_message(type="system", sender=0, content=f"{request.client_IP} joined the chat.")

    return json.dumps(config_data)

@serv.register_route(route="/api/set-nickname", MIME_type="application/json")
def set_nickname(request: http_server.HTTPRequest):
    chatroom.refresh_user_status(request.client_IP)
    chatroom.set_nickname(request.client_IP, request.body)
    return request.client_IP

init.init_server(serv)
serv.run()
