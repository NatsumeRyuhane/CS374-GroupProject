import logging
import os

if not os.path.exists("../logs/"):
    os.mkdir("../logs/")

with open('../logs/server.log', 'w', encoding='utf-8') as f:
    f.truncate(0)

logging.basicConfig(level = 'DEBUG', format = '[%(asctime)s] [%(levelname)s] %(message)s', encoding = 'utf-8',
                    handlers = [
                        logging.FileHandler("../logs/server.log"),
                        logging.StreamHandler()
                    ])

from http_server import HTTPServer

serv = HTTPServer(hostname ="0.0.0.0", port = 11451)
serv.run()