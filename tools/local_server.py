import sys
from pathlib import Path
from wsgiref.simple_server import WSGIRequestHandler, make_server


# Import the WSGI application and determine the template dir
server_dir = Path(__file__).parents[1] / "server"
template_dir = Path(__file__).parents[1] / "templates"

sys.path.insert(0, str(server_dir))

import store_data


class SFB1451RequestHandler(WSGIRequestHandler):
    def get_environ(self):
        wsgi_environment = WSGIRequestHandler.get_environ(self)
        wsgi_environment.update({
            "de.inm7.sfb1451.entry.dataset_root": "/tmp/sfb-test",
            "de.inm7.sfb1451.entry.home": "/tmp/sfb-test-home",
            "de.inm7.sfb1451.entry.templates": str(template_dir)
        })
        return wsgi_environment


with make_server('', 8000, store_data.application, handler_class=SFB1451RequestHandler) as httpd:
    print("Serving HTTP on port 8000...")
    httpd.serve_forever()
