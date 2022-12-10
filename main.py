import logging
import os

if not os.path.exists("../logs/"):
    os.mkdir("../logs/")

with open('../logs/server.log', 'w', encoding='utf-8') as f:
    f.truncate(0)

logging.basicConfig(level='DEBUG', format='[%(asctime)s] [%(levelname)s] %(message)s', encoding='utf-8',
                    handlers=[
                        logging.FileHandler("../logs/server.log"),
                        logging.StreamHandler()
                        ])

from http_server import HTTPServer

serv = HTTPServer(hostname="0.0.0.0", port=11451)

# register all static resources
static_root = "./static"

MIME_type_dict = {
    "html": "text/html",
    "css": "text/css",
    "js": "text/javascript",
    }


def register_static_resource(route: str, filepath: str, MIME_type: str):
    @serv.register_route(route=route, MIME_type=MIME_type)
    def register_static_resource_file(request):
        with open(filepath) as f:
            content = f.read()

        return content


for dir in os.listdir(f"{static_root}/"):
    for file in os.listdir(f"{static_root}/{dir}/"):
        register_static_resource(route=f"/static/{dir}/{file}", filepath=f"./{static_root}/{dir}/{file}", MIME_type=f"{MIME_type_dict[dir]}")


# register templates
@serv.register_route(route="/index.html", aliases=["/index", "/"], MIME_type="text/html")
def index(request):
    with open("./templates/index.html") as f:
        content = f.read()

    return content

# application logic
@serv.register_route(route="/api/post_message/", MIME_type="text/plain")

@serv.register_route(route="/api/get_message/", MIME_type="application/json")
def get_message(request):
    return "i"

serv.run()
