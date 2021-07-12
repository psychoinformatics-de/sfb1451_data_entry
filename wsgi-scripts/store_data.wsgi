import hashlib
import json
import time
import subprocess
from pathlib import Path
from typing import Dict, List, Union
from urllib.parse import parse_qs

from jinja2 import Environment, PackageLoader, select_autoescape


# Those fields are required in the user input. They can either
# come from the posted data or from the auto_fields-array.
required_fields = [
    "form-data-version",
    "data-entry-domain",
    "data-entry-employee",
    "project-code",
    "subject-pseudonym",
    "date-of-birth",
    "sex",
    "date-of-test",
    "repeated-test",
    "subject-group",
    "laterality-quotient",
    "maximum-ftf-left",
    "maximum-ftf-right",
    "maximum-gs-left",
    "maximum-gs-right",
    "purdue-pegboard-left",
    "purdue-pegboard-right",
    "turn-cards-left",
    "turn-cards-right",
    "small-things-left",
    "small-things-right",
    "simulated-feeding-left",
    "simulated-feeding-right",
    "checkers-left",
    "checkers-right",
    "large-light-things-left",
    "large-light-things-right",
    "large-heavy-things-left",
    "large-heavy-things-right",
    "jtt-incorrectly-executed",
    "arat-left",
    "arat-right",
    "tug-executed",
    "tug-a-incorrectly-executed",
    "tug-a-tools-required",
    "tug-imagined",
    "go-nogo-block-count",
    "go-nogo-total-errors",
    "go-nogo-recognized-errors",
    "go-nogo-correct-answer-time",
    "go-nogo-recognized-error-time",
    "go-nogo-incorrectly-executed",
    "kas-pantomime-bukko-facial",
    "kas-pantomime-arm-hand",
    "kas-imitation-bukko-facial",
    "kas-imitation-arm-hand",
    "kopss-orientation",
    "kopss-speech",
    "kopss-praxie",
    "kopss-visual-spatial-performance",
    "kopss-calculating",
    "kopss-executive-performance",
    "kopss-memory",
    "kopss-affect",
    "kopss-behavior-observation",
    "acl-k-loud-reading",
    "acl-k-color-form-test",
    "acl-k-supermarket-task",
    "acl-k-communication-ability",
    "bdi-ii-score",
    "madrs-score",
    "demtect-wordlist",
    "demtect-convert-numbers",
    "demtect-supermarket-task",
    "demtect-numbers-reverse",
    "demtect-wordlist-recall",
    "time-tmt-a",
    "tmt-a-incorrectly-executed",
    "time-tmt-b",
    "tmt-b-incorrectly-executed",
    "mrs-score",
    "euroqol-code",
    "euroqol-vas",
    "isced-value",
    "additional-mrt-url",
    "additional-mrt-resting-state",
    "additional-mrt-tapping-task",
    "additional-mrt-anatomical-representation",
    "additional-mrt-dti",
    "additional-eeg-url",
    "additional-blood-sampling-url",
    "additional-remarks",
    "hash-value"
]


# Browsers might not send disabled or empty input fields at all.
# All entries in auto_fields will be added to the incoming field
# set, if they are not present.
auto_fields = {
    "repeated-test": ["off"],

    "patient-year-first-symptom": [""],
    "patient-month-first-symptom": [""],
    "patient-day-first-symptom": [""],
    "patient-year-diagnosis": [""],
    "patient-month-diagnosis": [""],
    "patient-day-diagnosis": [""],
    "patient-main-disease": [""],
    "patient-stronger-impacted-hand": [""],

    "laterality-quotient": [""],
    "maximum-ftf-left": [""],
    "maximum-ftf-right": [""],

    "maximum-gs-left": [""],
    "maximum-gs-right": [""],
    "purdue-pegboard-left": [""],
    "purdue-pegboard-right": [""],
    "turn-cards-left": [""],
    "turn-cards-right": [""],
    "small-things-left": [""],
    "small-things-right": [""],
    "simulated-feeding-left": [""],
    "simulated-feeding-right": [""],
    "checkers-left": [""],
    "checkers-right": [""],
    "large-light-things-left": [""],
    "large-light-things-right": [""],
    "large-heavy-things-left": [""],
    "large-heavy-things-right": [""],
    "jtt-incorrectly-executed": [""],

    "arat-left": [""],
    "arat-right": [""],

    "tug-executed": [""],
    "tug-a-incorrectly-executed": [""],
    "tug-a-tools-required": [""],
    "tug-imagined": [""],

    "go-nogo-block-count": [""],
    "go-nogo-total-errors": [""],
    "go-nogo-recognized-errors": [""],
    "go-nogo-correct-answer-time": [""],
    "go-nogo-recognized-error-time": [""],
    "go-nogo-incorrectly-executed": [""],

    "kas-pantomime-bukko-facial": [""],
    "kas-pantomime-arm-hand": [""],
    "kas-imitation-bukko-facial": [""],
    "kas-imitation-arm-hand": [""],

    "kopss-orientation": [""],
    "kopss-speech": [""],
    "kopss-praxie": [""],
    "kopss-visual-spatial-performance": [""],
    "kopss-calculating": [""],
    "kopss-executive-performance": [""],
    "kopss-memory": [""],
    "kopss-affect": [""],
    "kopss-behavior-observation": [""],

    "acl-k-loud-reading": [""],
    "acl-k-color-form-test": [""],
    "acl-k-supermarket-task": [""],
    "acl-k-communication-ability": [""],

    "bdi-ii-score": [""],
    "madrs-score": [""],

    "demtect-wordlist": [""],
    "demtect-convert-numbers": [""],
    "demtect-supermarket-task": [""],
    "demtect-numbers-reverse": [""],
    "demtect-wordlist-recall": [""],

    "time-tmt-a": [""],
    "tmt-a-incorrectly-executed": [""],
    "time-tmt-b": [""],
    "tmt-b-incorrectly-executed": [""],

    "mrs-score": [""],
    "euroqol-code": [""],
    "euroqol-vas": [""],
    "isced-value": [""],

    "additional-mrt-url": [""],
    "additional-mrt-resting-state": [""],
    "additional-mrt-tapping-task": [""],
    "additional-mrt-anatomical-representation": [""],
    "additional-mrt-dti": [""],

    "additional-eeg-url": [""],

    "additional-blood-sampling-url": [""],

    "additional-remarks": [""],

    "signature-data": [""],
}


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


def add_file_to_dataset(dataset_root: Path, file: Path, home: Path):
    subprocess.run(
        [
            "datalad",
            "save",
            "-d", str(dataset_root),
            "-m", f"adding file {file.relative_to(dataset_root)}",
            str(file)
        ],
        check=True,
        env={"HOME": str(home)})

    return subprocess.run(
        [
            "git",
            "--git-dir", str(dataset_root / ".git"),
            "rev-parse",
            "HEAD"
        ],
        check=True,
        stdout=subprocess.PIPE).stdout.decode().strip()


def checkbox_message(value):
    return {
        True: "ja",
        False: "nein",
        None: "--"
    }[value]


def sex_message(value):
    return {
        "male": "männlich",
        "female": "weiblich",
        "diverse": "sonstiges"
    }[value]


def hand_message(value):
    return {
        "left": "links",
        "right": "rechts",
        "none": "keine"
    }[value]


def date_message(year, month, day):
    return "-".join([
        str(x)
        for x in [year, month, day]
        if x is not None
    ])



def create_result_page(commit_hash: str, time_stamp: float, json_top_data: dict, templates_directory: Path):

    jinja_template_path = templates_directory / "success.html.jinja2"
    jinja_template = Environment(autoescape=select_autoescape()).from_string(jinja_template_path.read_text())
    return jinja_template.render(
        sub_project="Z03",
        reference=f"{time_stamp}-{commit_hash}",
        record=json_top_data["data"],
        date_message=date_message,
        hand_message=hand_message,
        sex_message=sex_message,
        checkbox_message=checkbox_message)


def get_string_content(_: str, field_content: List[str]) -> str:
    return field_content[0]


def get_checkbox_content(field_name: str, field_content: List[str]) -> str:
    return {
        "": "",
        "off": "False",
        "on": "True"
    }[field_content[0]]


def get_number_content(_: str, field_content: List[str]) -> str:
    if field_content[0] == "":
        return ""
    number = float(field_content[0])
    if number == int(number):
        number = int(number)
    return str(number)


hashed_content_fields = [
    ["form-data-version", get_string_content],
    ["data-entry-domain", get_string_content],
    ["data-entry-employee", get_string_content],
    ["project-code", get_string_content],
    ["subject-pseudonym", get_string_content],
    ["date-of-birth", get_string_content],
    ["sex", get_string_content],
    ["date-of-test", get_string_content],
    ["repeated-test", get_checkbox_content],
    ["patient-year-first-symptom", get_string_content],
    ["patient-month-first-symptom", get_string_content],
    ["patient-day-first-symptom", get_string_content],
    ["patient-year-diagnosis", get_string_content],
    ["patient-month-diagnosis", get_string_content],
    ["patient-day-diagnosis", get_string_content],
    ["patient-main-disease", get_string_content],
    ["patient-stronger-impacted-hand", get_string_content],
    ["laterality-quotient", get_number_content],
    ["maximum-ftf-left", get_number_content],
    ["maximum-ftf-right", get_number_content],
    ["maximum-gs-left", get_number_content],
    ["maximum-gs-right", get_number_content],
    ["purdue-pegboard-left", get_number_content],
    ["purdue-pegboard-right", get_number_content],
    ["turn-cards-left", get_number_content],
    ["turn-cards-right", get_number_content],
    ["small-things-left", get_number_content],
    ["small-things-right", get_number_content],
    ["simulated-feeding-left", get_number_content],
    ["simulated-feeding-right", get_number_content],
    ["checkers-left", get_number_content],
    ["checkers-right", get_number_content],
    ["large-light-things-left", get_number_content],
    ["large-light-things-right", get_number_content],
    ["large-heavy-things-left", get_number_content],
    ["large-heavy-things-right", get_number_content],
    ["jtt-incorrectly-executed", get_checkbox_content],
    ["arat-left", get_number_content],
    ["arat-right", get_number_content],
    ["tug-executed", get_number_content],
    ["tug-a-incorrectly-executed", get_checkbox_content],
    ["tug-a-tools-required", get_checkbox_content],
    ["tug-imagined", get_number_content],
    ["go-nogo-block-count", get_number_content],
    ["go-nogo-total-errors", get_number_content],
    ["go-nogo-recognized-errors", get_number_content],
    ["go-nogo-correct-answer-time", get_number_content],
    ["go-nogo-recognized-error-time", get_number_content],
    ["go-nogo-incorrectly-executed", get_checkbox_content],
    ["kas-pantomime-bukko-facial", get_number_content],
    ["kas-pantomime-arm-hand", get_number_content],
    ["kas-imitation-bukko-facial", get_number_content],
    ["kas-imitation-arm-hand", get_number_content],
    ["kopss-orientation", get_number_content],
    ["kopss-speech", get_number_content],
    ["kopss-praxie", get_number_content],
    ["kopss-visual-spatial-performance", get_number_content],
    ["kopss-calculating", get_number_content],
    ["kopss-executive-performance", get_number_content],
    ["kopss-memory", get_number_content],
    ["kopss-affect", get_number_content],
    ["kopss-behavior-observation", get_number_content],
    ["acl-k-loud-reading", get_number_content],
    ["acl-k-color-form-test", get_number_content],
    ["acl-k-supermarket-task", get_number_content],
    ["acl-k-communication-ability", get_number_content],
    ["bdi-ii-score", get_number_content],
    ["madrs-score", get_number_content],
    ["demtect-wordlist", get_number_content],
    ["demtect-convert-numbers", get_number_content],
    ["demtect-supermarket-task", get_number_content],
    ["demtect-numbers-reverse", get_number_content],
    ["demtect-wordlist-recall", get_number_content],
    ["time-tmt-a", get_number_content],
    ["tmt-a-incorrectly-executed", get_checkbox_content],
    ["time-tmt-b", get_number_content],
    ["tmt-b-incorrectly-executed", get_checkbox_content],
    ["mrs-score", get_number_content],
    ["euroqol-code", get_string_content],
    ["euroqol-vas", get_number_content],
    ["isced-value", get_number_content],
    ["additional-mrt-url", get_string_content],
    ["additional-mrt-resting-state", get_checkbox_content],
    ["additional-mrt-tapping-task", get_checkbox_content],
    ["additional-mrt-anatomical-representation", get_checkbox_content],
    ["additional-mrt-dti", get_checkbox_content],
    ["additional-eeg-url", get_string_content],
    ["additional-blood-sampling-url", get_string_content],
    ["additional-remarks", get_string_content]
]


def get_string_value(value: str):
    if len(value) == 0:
        return None
    return value


def get_int_value(value: str):
    if len(value) == 0:
        return None
    return int(value)


def get_float_value(value: str):
    if len(value) == 0:
        return None
    return float(value)


def get_checkbox_value(value: str):
    return {
        "on": True,
        "off": False,
        "": None
    }[value]


field_value_fetcher = {
    "form-data-version": get_string_value,
    "data-entry-domain": get_string_value,
    "data-entry-employee": get_string_value,
    "project-code": get_string_value,
    "subject-pseudonym": get_string_value,
    "date-of-birth": get_string_value,
    "sex": get_string_value,
    "date-of-test": get_string_value,
    "repeated-test": get_checkbox_value,
    "subject-group": get_string_value,
    "patient-year-first-symptom": get_string_value,
    "patient-month-first-symptom": get_string_value,
    "patient-day-first-symptom": get_string_value,
    "patient-year-diagnosis": get_string_value,
    "patient-month-diagnosis": get_string_value,
    "patient-day-diagnosis": get_string_value,
    "patient-main-disease": get_string_value,
    "patient-stronger-impacted-hand": get_string_value,
    "laterality-quotient": get_int_value,
    "maximum-ftf-left": get_float_value,
    "maximum-ftf-right": get_float_value,
    "maximum-gs-left": get_float_value,
    "maximum-gs-right": get_float_value,
    "purdue-pegboard-left": get_float_value,
    "purdue-pegboard-right": get_float_value,
    "turn-cards-left": get_float_value,
    "turn-cards-right": get_float_value,
    "small-things-left": get_float_value,
    "small-things-right": get_float_value,
    "simulated-feeding-left": get_float_value,
    "simulated-feeding-right": get_float_value,
    "checkers-left": get_float_value,
    "checkers-right": get_float_value,
    "large-light-things-left": get_float_value,
    "large-light-things-right": get_float_value,
    "large-heavy-things-left": get_float_value,
    "large-heavy-things-right": get_float_value,
    "jtt-incorrectly-executed": get_checkbox_value,
    "arat-left": get_int_value,
    "arat-right": get_int_value,
    "tug-executed": get_float_value,
    "tug-a-incorrectly-executed": get_checkbox_value,
    "tug-a-tools-required": get_checkbox_value,
    "tug-imagined": get_float_value,
    "tug-v-not-executable": get_checkbox_value,
    "go-nogo-block-count": get_int_value,
    "go-nogo-total-errors": get_int_value,
    "go-nogo-recognized-errors": get_int_value,
    "go-nogo-correct-answer-time": get_float_value,
    "go-nogo-recognized-error-time": get_float_value,
    "go-nogo-incorrectly-executed": get_checkbox_value,
    "kas-pantomime-bukko-facial": get_int_value,
    "kas-pantomime-arm-hand": get_int_value,
    "kas-imitation-bukko-facial": get_int_value,
    "kas-imitation-arm-hand": get_int_value,
    "kopss-applicable": get_checkbox_value,
    "kopss-orientation": get_int_value,
    "kopss-speech": get_int_value,
    "kopss-praxie": get_int_value,
    "kopss-visual-spatial-performance": get_int_value,
    "kopss-calculating": get_int_value,
    "kopss-executive-performance": get_int_value,
    "kopss-memory": get_int_value,
    "kopss-affect": get_int_value,
    "kopss-behavior-observation": get_int_value,
    "acl-k-loud-reading": get_float_value,
    "acl-k-color-form-test": get_int_value,
    "acl-k-supermarket-task": get_int_value,
    "acl-k-communication-ability": get_int_value,
    "bdi-ii-score": get_int_value,
    "madrs-score": get_int_value,
    "demtect-wordlist": get_int_value,
    "demtect-convert-numbers": get_int_value,
    "demtect-supermarket-task": get_int_value,
    "demtect-numbers-reverse": get_int_value,
    "demtect-wordlist-recall": get_int_value,
    "time-tmt-a": get_float_value,
    "tmt-a-incorrectly-executed": get_checkbox_value,
    "time-tmt-b": get_float_value,
    "tmt-b-incorrectly-executed": get_checkbox_value,
    "mrs-score": get_int_value,
    "euroqol-code": get_string_value,
    "euroqol-vas": get_int_value,
    "isced-value": get_int_value,
    "additional-mrt": get_checkbox_value,
    "additional-mrt-url": get_string_value,
    "additional-mrt-resting-state": get_checkbox_value,
    "additional-mrt-tapping-task": get_checkbox_value,
    "additional-mrt-anatomical-representation": get_checkbox_value,
    "additional-mrt-dti": get_checkbox_value,
    "additional-eeg": get_checkbox_value,
    "additional-eeg-url": get_string_value,
    "additional-blood-sampling": get_checkbox_value,
    "additional-blood-sampling-url": get_string_value,
    "additional-remarks": get_string_value
}


def get_field_value(fields, field_name):
    value = fields[field_name][0]
    if field_name in field_value_fetcher:
        return field_value_fetcher[field_name](value)
    return value


def get_canonic_content_string(field_set: Dict[str, List[str]]) -> str:
    field_strings = [
        f"{field_name}:{processor(field_name, field_set[field_name])}"
        for field_name, processor in hashed_content_fields
    ]
    return ";".join(field_strings)


def application(environ, start_response):

    dataset_root = Path(environ["de.inm7.sfb1451.entry.dataset_root"])
    home = Path(environ["de.inm7.sfb1451.entry.home"])
    template_directory = Path(environ["de.inm7.sfb1451.entry.templates"])

    request_method = environ["REQUEST_METHOD"]
    if request_method == "POST":
        try:
            request_body_size = int(environ.get("CONTENT_LENGTH", 0))
        except ValueError:
            request_body_size = 0

        environment = [f"{key}: {value}" for key, value in environ.items()]

        request_body = environ["wsgi.input"].read(request_body_size).decode("utf-8")
        entered_data = parse_qs(request_body)

        posted_data_string = "\n".join(
            [f"{key}: {value}" for key, value in entered_data.items()])

        import sys
        print(posted_data_string, file=sys.stderr)

        # Check single results
        for value in entered_data.values():
            assert isinstance(value, list)
            assert len(value) == 1

        # Add auto fields to the entered data, if they are not already present
        for key, value in auto_fields.items():
            if key not in entered_data:
                entered_data[key] = value

        # Check the hash value
        local_hash_string = get_canonic_content_string(entered_data)
        if local_hash_string != entered_data["hashed-string"][0]:
            status = "400 BAD REQUEST"
            output = [
                "Local hash input-string does not match submitted values\n".encode("utf-8"),
                ("LOCAL: " + local_hash_string + "\n").encode(),
                ("SENT:  " + entered_data["hashed-string"][0] + "\n").encode(),
                #(hashlib.sha256(local_hash_string.encode()).hexdigest() + "\n").encode(),
                #f"==: {local_hash_string == entered_data['hashed-string'][0]}\n".encode()
            ]
            output_length = sum([len(line) for line in output])
            response_headers = [('Content-type', 'text/plain; charset=utf-8'),
                                ('Content-Length', str(output_length))]
            start_response(status, response_headers)
            return output

        local_hash_value = hashlib.sha256(local_hash_string.encode()).hexdigest()
        if local_hash_value != entered_data["hash-value"][0]:
            status = "400 BAD REQUEST"
            output = ["Server side hash value does not match submitted hash value".encode("utf-8")]
            output_length = sum([len(line) for line in output])
            response_headers = [('Content-type', 'text/plain; charset=utf-8'),
                                ('Content-Length', str(output_length))]
            start_response(status, response_headers)
            return output

        # Create posted data dictionary
        json_object = dict()

        # Read the mandatory keys
        for key in required_fields:
            # This will throw an error, if the key is not available
            json_object[key] = get_field_value(entered_data, key)

        time_stamp = time.time()

        json_data = {
            "source": {
                "time_stamp": time_stamp,
                "version": entered_data["form-data-version"][0],
                "remote_address": environ["REMOTE_ADDR"],
                "hashed-string": entered_data["hashed-string"][0],
                "hash-value": entered_data["hash-value"][0],
                "signature-data": (
                    None
                    if entered_data["signature-data"][0] == ""
                    else entered_data["signature-data"][0]
                )
            },
            "data": json_object
        }

        import sys
        print(repr(json_object), file=sys.stderr)

        directory = dataset_root / "input" / json_data["source"]["version"]
        directory.mkdir(parents=True, exist_ok=True)

        output_file = directory / (str(time_stamp) + ".json")
        with output_file.open("x") as f:
            json.dump(json_data, f)

        commit_hash = add_file_to_dataset(dataset_root, directory / output_file, home)

        result_message = create_result_page(commit_hash, time_stamp, json_data, template_directory)

        status = "200 OK"

        output = [
            result_message.encode(),
            #"2-------------\n".encode(),
            #("\n".join(environment) + "\n").encode("utf-8"),
            #"3-------------\n".encode(),
            #(posted_data_string + "\n").encode("utf-8"),
            #"4-------------\n".encode(),
            #json.dumps(json_data, indent=4).encode(),
            #"5-------------\n".encode(),
            #(local_hash_string + "\n").encode(),
            #(entered_data["hashed-string"][0] + "\n").encode(),
            #(hashlib.sha256(local_hash_string.encode()).hexdigest() + "\n").encode(),
            #f"==: {local_hash_string == entered_data['hashed-string'][0]}\n".encode()
        ]

    else:

        status = "400 BAD REQUEST"
        output = ["Only post method allowed".encode("utf-8")]

    output_length = sum([len(line) for line in output])
    response_headers = [('Content-type', 'text/html; charset=utf-8'),
                        ('Content-Length', str(output_length))]
    start_response(status, response_headers)

    return output
