import json
import sys
import time
from typing import Union
from urllib.parse import parse_qs


def convert_value(value: bytes) -> Union[str, float, int]:
    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value.decode("utf-8")


def application(environ, start_response):

    request_method = environ["REQUEST_METHOD"]
    if request_method == "POST":
        try:
            request_body_size = int(environ.get("CONTENT_LENGTH", 0))
        except (ValueError):
            request_body_size = 0

        environment = [f"{key}: {value}" for key, value in environ.items()]

        request_body = environ["wsgi.input"].read(request_body_size)
        entered_data = parse_qs(request_body)

        result = "\n".join(
            [f"{key}: {value}" for key, value in entered_data.items()])

        json_data = {
            key.decode("utf-8"): convert_value(value[0]) for key, value in entered_data.items()
        }

        file_name = str(time.time())
        with open(file_name, "x") as f:
            json.dump(json_data, f)

        status = "200 OK"
        output = [
            f"Referenz: {file_name}\n".encode("utf-8"),
            "\n".join(environment).encode("utf-8"),
            result.encode("utf-8")
        ]

    else:

        status = "400 BAD REQUEST"
        output = ["Only post method allowed".encode("utf-8")]

    output_lenght = sum([len(line) for line in output])
    response_headers = [('Content-type', 'text/plain'),
                        ('Content-Length', str(output_lenght))]
    start_response(status, response_headers)

    return output
