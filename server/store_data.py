import json
import time
import subprocess
import sys
from pathlib import Path
from typing import Union
from urllib.parse import parse_qs


def convert_value(value: str) -> Union[str, float, int]:
    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


def add_file_to_dataset(dataset_root: Path, file: Path):
    subprocess.run(
        [
            "datalad",
            "save",
            "-d", str(dataset_root),
            "-m", f"adding file {file}",
            str(file)
        ],
        check=True)

    return subprocess.run(
        [
            "git",
            "rev-parse",
            "HEAD"
        ],
        check=True,
        stdout=subprocess.PIPE).stdout.decode().strip()


def application(environ, start_response):

    dataset_root = Path(environ["de.inm7.sfb1451.entry.dataset_root"])

    request_method = environ["REQUEST_METHOD"]
    if request_method == "POST":
        try:
            request_body_size = int(environ.get("CONTENT_LENGTH", 0))
        except ValueError:
            request_body_size = 0

        environment = [f"{key}: {value}" for key, value in environ.items()]

        request_body = environ["wsgi.input"].read(request_body_size).decode("utf-8")
        entered_data = parse_qs(request_body)

        result = "\n".join(
            [f"{key}: {value}" for key, value in entered_data.items()])

        time_stamp = str(time.time())

        json_data = {
            "source": {
                "time_stamp": time_stamp,
                "version": entered_data["form-data-version"][0],
                "remote_address": environ["REMOTE_ADDR"]
            },
            "data": {
                **{
                    key: convert_value(value[0])
                    for key, value in entered_data.items()
                    if key != "form-data-version"
                }
            }
        }

        directory = dataset_root / "input" / json_data["source"]["version"]
        directory.mkdir(parents=True, exist_ok=True)

        output_file = directory / (time_stamp + ".json")
        with output_file.open("x") as f:
            json.dump(json_data, f)

        commit_hash = add_file_to_dataset(dataset_root, directory / output_file)

        status = "200 OK"
        output = [
            f"Referenz: {time_stamp}-{commit_hash}\n".encode("utf-8"),
            ("\n".join(environment) + "\n").encode("utf-8"),
            result.encode("utf-8")
        ]

    else:

        status = "400 BAD REQUEST"
        output = ["Only post method allowed".encode("utf-8")]

    output_lenght = sum([len(line) for line in output])
    response_headers = [('Content-type', 'text/plain; charset=utf-8'),
                        ('Content-Length', str(output_lenght))]
    start_response(status, response_headers)

    return output
