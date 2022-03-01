import hashlib
import json
import os
import sys
import time
import subprocess
from pathlib import Path
from traceback import format_exception
from typing import Dict, List, Tuple, Union
from urllib.parse import parse_qs

from jinja2 import Environment, select_autoescape


DATASET_ROOT_KEY = "de.inm7.sfb1451.entry.dataset_root"
HOME_KEY = "de.inm7.sfb1451.entry.home"
TEMPLATE_DIRECTORY_KEY = "de.inm7.sfb1451.entry.templates"


# The following fields are required in the user input. They can either
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
    "go-nogo-wrong-errors",
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


# Fields that are required, if subject-group == "patient" is True
required_patient_fields = [
    "patient-year-first-symptom",
    "patient-month-first-symptom",
    "patient-day-first-symptom",
    "patient-year-diagnosis",
    "patient-month-diagnosis",
    "patient-day-diagnosis",
    "patient-main-disease",
    "patient-stronger-impacted-hand"
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
    "jtt-incorrectly-executed": ["off"],

    "arat-left": [""],
    "arat-right": [""],

    "tug-executed": [""],
    "tug-a-incorrectly-executed": ["off"],
    "tug-a-tools-required": ["off"],
    "tug-imagined": [""],

    "go-nogo-block-count": [""],
    "go-nogo-total-errors": [""],
    "go-nogo-wrong-errors": [""],
    "go-nogo-recognized-errors": [""],
    "go-nogo-correct-answer-time": [""],
    "go-nogo-recognized-error-time": [""],
    "go-nogo-incorrectly-executed": ["off"],

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
    "tmt-a-incorrectly-executed": ["off"],
    "time-tmt-b": [""],
    "tmt-b-incorrectly-executed": ["off"],

    "mrs-score": [""],
    "euroqol-code": [""],
    "euroqol-vas": [""],
    "isced-value": [""],

    "additional-mrt-url": [""],
    "additional-mrt-resting-state": ["off"],
    "additional-mrt-tapping-task": ["off"],
    "additional-mrt-anatomical-representation": ["off"],
    "additional-mrt-dti": ["off"],

    "additional-eeg-url": [""],

    "additional-blood-sampling-url": [""],

    "additional-remarks": [""],

    "signature-data": [""],
}


optional_checkbox_fields = [
    "jtt-incorrectly-executed",
    "tug-a-incorrectly-executed",
    "tug-a-tools-required",
    "go-nogo-incorrectly-executed",
    "tmt-a-incorrectly-executed",
    "tmt-b-incorrectly-executed",
    "additional-mrt-resting-state",
    "additional-mrt-tapping-task",
    "additional-mrt-anatomical-representation",
    "additional-mrt-dti"
]


def correct_optional_checkbox_fields(data):
    for name in optional_checkbox_fields:
        if name + "-valid" not in data:
            data[name] = [""]


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
        env={
            **os.environ,
            "HOME": str(home)
        })

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


def subject_group_message(value):
    return {
        "healthy": "Gesund",
        "patient": "Patient"
    }[value]


def hand_message(value):
    return {
        "left": "links",
        "right": "rechts",
        "none": "keine"
    }[value]


def disease_message(value):
    return {
        "stroke": "Schlaganfall",
        "parkinson": "Parkinson",
        "tic": "Tic",
        "depression": "Depression",
        "alzheimer": "Alzheimer",
    }[value]


def date_message(year, month, day):
    return "-".join([
        str(x)
        for x in [year, month, day]
        if x is not None
    ])


def create_result_page(commit_hash: str,
                       time_stamp: float,
                       json_top_data: dict,
                       templates_directory: Path):

    jinja_template_path = templates_directory / "success.html.jinja2"
    jinja_template = Environment(autoescape=select_autoescape()).from_string(jinja_template_path.read_text())
    return jinja_template.render(
        sub_project="Z03",
        reference=f"{time_stamp}-{commit_hash}",
        record=json_top_data["data"],
        date_message=date_message,
        disease_message=disease_message,
        hand_message=hand_message,
        sex_message=sex_message,
        subject_group_message=subject_group_message,
        checkbox_message=checkbox_message)


def get_string_content(_: str, field_content: List[str]) -> str:
    return field_content[0]


def get_checkbox_content(_: str, field_content: List[str]) -> str:
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
    ["go-nogo-wrong-errors", get_number_content],
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
    number = float(value)
    if number != int(number):
        raise ValueError(f"Not an integer: {value}")
    return int(number)


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
    "go-nogo-wrong-errors": get_int_value,
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
    "kopss-speech": get_float_value,
    "kopss-praxie": get_int_value,
    "kopss-visual-spatial-performance": get_int_value,
    "kopss-calculating": get_int_value,
    "kopss-executive-performance": get_float_value,
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


def encode_result_strings(result_strings: List[str]) -> List[bytes]:
    return [element.encode("utf-8") for element in result_strings]


def add_auto_fields(existing_fields: dict):
    """Add auto fields to existing_fields, if they are not already present"""
    for key, value in auto_fields.items():
        if key not in existing_fields:
            existing_fields[key] = value


def read_mandatory_fields(mandatory_fields: List[str],
                          input_data: Dict
                          ) -> Tuple[Dict[str, str], List[str]]:

    resulting_data = dict()
    missing_keys = []
    for key in mandatory_fields:
        if key not in input_data:
            missing_keys.append(key)
        else:
            resulting_data[key] = get_field_value(input_data, key)
    return resulting_data, missing_keys


def create_bad_request_result(lines: List[str]):
    return (
        "400 BAD REQUEST",
        "text/plain; charset=utf-8",
        encode_result_strings(lines))


def create_missing_key_result(missing_keys: List[str]):
    return create_bad_request_result([
        "The following keys are missing from the request:\n",
        "\n".join(missing_keys),
        "\n"])


def application(environ, start_response):

    try:
        request_body_size = int(environ.get("CONTENT_LENGTH", 0))
        request_body = environ["wsgi.input"].read(request_body_size).decode("utf-8")
    except (ValueError, KeyError):
        request_body_size = 0
        request_body = ""

    try:
        status, content_type, content = protected_application(environ, request_body)
    except:
        status = "500 INTERNAL ERROR"
        content_type = "text/plain; charset=utf-8"
        content_strings = [
            "An unexpected error occured during processing. If this error\n",
            "persists, please send an email with the following information\n",
            "to <c.moench@fz-juelich.de> or <m.szczepanik@fz-juelich.de>:\n",
            "\n",
            "--------\n",
            "1. Stacktrace:\n",
            "".join(format_exception(*sys.exc_info())),
            "2. Environment:\n",
            str(environ),
            "\n",
            f"3. WSGI input data ({request_body_size}):\n",
            request_body,
            "\n",
            "--------\n"
        ]
        content = encode_result_strings(content_strings)

    content_length = sum([len(line) for line in content])
    response_headers = [
        ('Content-type', content_type),
        ('Content-Length', str(content_length))]

    start_response(status, response_headers)
    return content


def protected_application(environ, request_body):

    request_method = environ["REQUEST_METHOD"]
    if request_method != "POST":
        return create_bad_request_result(["Only POST is supported\n"])

    dataset_root = Path(environ[DATASET_ROOT_KEY])
    home = Path(environ[HOME_KEY])
    template_directory = Path(environ[TEMPLATE_DIRECTORY_KEY])

    # Parse data and check value structure
    received_data = parse_qs(request_body)
    for value in received_data.values():
        if not isinstance(value, list) or not len(value) == 1:
            raise ValueError(f"expected list of length one, got: {repr(value)}")

    # Add auto fields to the received data
    add_auto_fields(received_data)

    # Correct the optional checkbox field in the received data
    correct_optional_checkbox_fields(received_data)

    # Read the mandatory keys into the result dictionary
    entered_data_object, missing_keys = read_mandatory_fields(
        required_fields,
        received_data)

    if missing_keys:
        return create_missing_key_result(missing_keys)

    if entered_data_object["subject-group"] == "patient":
        entered_patient_data, missing_patient_keys = read_mandatory_fields(
            required_patient_fields,
            received_data)

        entered_data_object.update(entered_patient_data)
        missing_keys.extend(missing_patient_keys)

    if missing_keys:
        return create_missing_key_result(missing_keys)

    # Check the hash value
    local_hash_string = get_canonic_content_string(received_data)
    if local_hash_string != received_data["hashed-string"][0]:
        return create_bad_request_result([
            "Local hash input-string does not match submitted values\n",
            "LOCAL: " + local_hash_string + "\n",
            "SENT:  " + received_data["hashed-string"][0] + "\n"])

    local_hash_value = hashlib.sha256(local_hash_string.encode()).hexdigest()
    if local_hash_value != received_data["hash-value"][0]:
        return create_bad_request_result([
            "Server side hash value does not match submitted hash value\n"])

    time_stamp = time.time()

    result_object = {
        "source": {
            "time_stamp": time_stamp,
            "version": received_data["form-data-version"][0],
            "remote_address": environ["REMOTE_ADDR"],
            "hashed-string": received_data["hashed-string"][0],
            "hash-value": received_data["hash-value"][0],
            "signature-data": (
                None
                if received_data["signature-data"][0] == ""
                else received_data["signature-data"][0]
            )
        },
        "data": entered_data_object
    }

    directory = dataset_root / "input" / result_object["source"]["version"]
    directory.mkdir(parents=True, exist_ok=True)

    output_file = directory / (str(time_stamp) + ".json")
    with output_file.open("x") as f:
        json.dump(result_object, f)

    commit_hash = add_file_to_dataset(dataset_root, directory / output_file, home)

    result_message = create_result_page(commit_hash, time_stamp, result_object, template_directory)
    return (
        "200 OK",
        "text/html; charset=utf-8",
        encode_result_strings([result_message]))
