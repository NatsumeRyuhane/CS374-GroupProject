import http_server
import os

def init_server(serv: http_server.HTTPServer):
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

    for dirs in os.listdir(f"{static_root}/"):
        for file in os.listdir(f"{static_root}/{dirs}/"):
            register_static_resource(route=f"/static/{dirs}/{file}", filepath=f"./{static_root}/{dirs}/{file}", MIME_type=f"{MIME_type_dict[dirs]}")

    # register templates
    @serv.register_route(route="/index.html", aliases=["/index", "/"], MIME_type="text/html")
    def index(request):
        with open("./templates/index.html") as f:
            content = f.read()

        return content

    @serv.register_route(route="/login.html", aliases=["/login"], MIME_type="text/html")
    def index(request):
        with open("./templates/login.html") as f:
            content = f.read()

        return content