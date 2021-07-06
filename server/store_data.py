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
    "ftf-incorrectly-executed",
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
    "tug-v-not-executable",
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
    "kopss-applicable",
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
    "additional-mrt",
    "additional-mrt-url",
    "additional-mrt-resting-state",
    "additional-mrt-tapping-task",
    "additional-mrt-anatomical-representation",
    "additional-mrt-dti",
    "additional-eeg",
    "additional-eeg-url",
    "additional-blood-sampling",
    "additional-blood-sampling-url",
    "additional-remarks",
    "hash-value"
]


dependent_fields = {
    "kopss-applicable": {
        "off": [],
        "on": [
            "kopss-orientation",
            "kopss-speech",
            "kopss-praxie",
            "kopss-visual-spatial-performance",
            "kopss-calculating",
            "kopss-executive-performance",
            "kopss-memory",
            "kopss-affect",
            "kopss-behavior-observation",
        ]
    },
    "subject-group": {
        "healthy": [],
        "patient": [
            "patient-main-disease",
            "patient-stronger-impacted-hand",
            "patient-year-first-symptom",
            "patient-month-first-symptom",
            "patient-day-first-symptom",
            "patient-year-diagnosis",
            "patient-month-diagnosis",
            "patient-day-diagnosis"
        ]
    }
}

# Browsers might not send disabled or empty input fields at all.
# All entries in auto_fields will be added to the incoming field
# set, if they are not present.
auto_fields = {
    "patient-main-disease": [""],
    "patient-stronger-impacted-hand": [""],
    "patient-year-first-symptom": [""],
    "patient-month-first-symptom": [""],
    "patient-day-first-symptom": [""],
    "patient-year-diagnosis": [""],
    "patient-month-diagnosis": [""],
    "patient-day-diagnosis": [""],
    "repeated-test": ["off"],
    "ftf-incorrectly-executed": ["off"],
    "jtt-incorrectly-executed": ["off"],
    "tug-a-incorrectly-executed": ["off"],
    "tug-a-tools-required": ["off"],
    "tug-v-not-executable": ["off"],
    "go-nogo-incorrectly-executed": ["off"],
    "go-nogo-recognized-errors": [""],
    "go-nogo-recognized-error-time": [""],
    "kopss-applicable": ["off"],
    "kopss-orientation": [""],
    "kopss-speech": [""],
    "kopss-praxie": [""],
    "kopss-visual-spatial-performance": [""],
    "kopss-calculating": [""],
    "kopss-executive-performance": [""],
    "kopss-memory": [""],
    "kopss-affect": [""],
    "kopss-behavior-observation": [""],
    "tmt-a-incorrectly-executed": ["off"],
    "tmt-b-incorrectly-executed": ["off"],
    "additional-mrt": ["off"],
    "additional-mrt-url": [""],
    "additional-mrt-resting-state": ["off"],
    "additional-mrt-tapping-task": ["off"],
    "additional-mrt-anatomical-representation": ["off"],
    "additional-mrt-dti": ["off"],
    "additional-eeg": ["off"],
    "additional-eeg-url": [""],
    "additional-blood-sampling": ["off"],
    "additional-blood-sampling-url": [""],
    "additional-remarks": [""],
    "signature-data": [""],
    "hash-value": [""]
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
        False: "nein"
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



def create_result_page(commit_hash: str, time_stamp: float, json_top_data: dict):

    jinja_template_path = Path("server/templates/success.html.jinja2")
    jinja_template = Environment(autoescape=select_autoescape()).from_string(jinja_template_path.read_text())
    return jinja_template.render(
        sub_project="Z03",
        reference=f"{time_stamp}-{commit_hash}",
        record=json_top_data["data"],
        date_message=date_message,
        hand_message=hand_message,
        sex_message=sex_message,
        checkbox_message=checkbox_message)


def create_result_message(commit_hash, time_stamp, json_top_data):

    json_data = json_top_data["data"]
    message = f"""DATEN GESPEICHERT:

Referenz:   {time_stamp}-{commit_hash}

Datenerfasser:  {json_data["data-entry-employee"]}

Project-Code:   {json_data["project-code"]}

Probanden-Pseudonym:    {json_data["subject-pseudonym"]}
Geburtsdatum:           {json_data["date-of-birth"]}
Geschlecht:             {sex_message(json_data["sex"])}

Test-Datum:             {json_data["date-of-test"]}
Wiederholte Testung:    {checkbox_message(json_data["repeated-test"])}

Probandengruppe:            {json_data["subject-group"]}
"""

    if json_data["subject-group"] == "patient":
        message += f"""Haupterkrankung:            {json_data["patient-main-disease"]}
Erstsymptome:               {date_message(json_data["patient-year-first-symptom"], json_data["patient-month-first-symptom"], json_data["patient-day-first-symptom"])}
Diagnose:                   {date_message(json_data["patient-year-diagnosis"], json_data["patient-month-diagnosis"], json_data["patient-day-diagnosis"])}
Stärker betroffene Hand:    {hand_message(json_data["patient-stronger-impacted-hand"])}
"""

    message += f"""
-- Motorische Testung: Basisfähigkeiten --

Händigkeitsfragebogen: Lateralitäts-Quotient:   {json_data["laterality-quotient"]}
Maximale Fingertipp-Geschwindigkeit (FTF):      L: {json_data["maximum-ftf-left"]}    R: {json_data["maximum-ftf-right"]}
Kein korrektes Tippen möglich:                  {checkbox_message(json_data["ftf-incorrectly-executed"])}
Maximale Griffkraft:                            L: {json_data["maximum-gs-left"]}    R: {json_data["maximum-gs-left"]}


-- Motorische Testung: Komplexe Fähigkeiten --

--- Purdue Pegboard Test ---
Anzahl gesteckter Stäbchen:     L: {json_data["purdue-pegboard-left"]}    R: {json_data["purdue-pegboard-right"]}

--- Jebsen Taylor Hand Function Test (JTT) ---
Karten drehen:                  L: {json_data["turn-cards-left"]}    R: {json_data["turn-cards-right"]}
Kleine Gegenstände:             L: {json_data["small-things-left"]}    R: {json_data["small-things-right"]}
Simuliertes Füttern:            L: {json_data["simulated-feeding-left"]}    R: {json_data["simulated-feeding-right"]}
Damesteine stapeln:             L: {json_data["checkers-left"]}    R: {json_data["checkers-right"]}
Große, leichte Gegenstände:     L: {json_data["large-light-things-left"]}    R: {json_data["large-light-things-right"]}
Große, schwere Gegenstände:     L: {json_data["large-heavy-things-left"]}    R: {json_data["large-heavy-things-right"]}
Zeitüberschreitung bei Durchführung der Aufgaben: {checkbox_message(json_data["jtt-incorrectly-executed"])}

--- Action Research Arm Test (ARAT) ---
Punktzahl:      L: {json_data["arat-left"]}   R: {json_data["arat-right"]}

--- Timed-Up-and-Go test (TUG) ---
ausgeführter TUG (aTug):                    {json_data["tug-executed"]}
Zeitüberschreitung bei aTUG Durchführung:   {checkbox_message(json_data["tug-a-incorrectly-executed"])}
Hilfmittel bei aTUG Durchführung notwendig: {checkbox_message(json_data["tug-a-tools-required"])}
vorgestellter TUG (vTUG):                   {json_data["tug-imagined"]}
vTUG nicht durchführbar:                    {checkbox_message(json_data["tug-v-not-executable"])}


-- Motorische Testung: Kognitive Fähigkeiten --

--- Go/Nogo-Task ---
Durchgeführte Blöcke:                       {json_data["go-nogo-block-count"]}
Reaktionszeit korrekte Antwort:             {json_data["go-nogo-correct-answer-time"]}
Anzahl Fehler insgesamt:                    {json_data["go-nogo-total-errors"]}
"""

    if int(json_data["go-nogo-total-errors"]) > 0:
        message += f"Anzahl erkannte Fehler:                     {json_data['go-nogo-recognized-errors']}\n"
        if int(json_data["go-nogo-recognized-errors"]) > 0:
            message += f"Reaktionszeit erkannte Fehler:              {json_data['go-nogo-recognized-error-time']}\n"

    message += f"""Unkorrekte Durchführung des Go/Nogo-Tasks:  {checkbox_message(json_data["go-nogo-incorrectly-executed"])}

--- Cologne Apraxie Screening (KAS) ---
Pantomime: Bukko-Facial:    {json_data["kas-pantomime-bukko-facial"]}
Pantomime: Arm-Hand:        {json_data["kas-pantomime-arm-hand"]}
Imitation: Bukko-Facial:    {json_data["kas-imitation-bukko-facial"]}
Imitation: Arm-Hand:        {json_data["kas-imitation-arm-hand"]}


-- Neuropsychologische/kognitive Testung --

--- Kölner neuropsychologisches Screening für Schlaganfallpatienten (KöpSS) ---
Durchführbar:                       {checkbox_message(json_data["kopss-applicable"])}
"""

    if json_data["kopss-applicable"] == "on":
        message += f"""Orientierung:                       {json_data["kopss-orientation"]}
Sprache:                            {json_data["kopss-speech"]}
Praxie:                             {json_data["kopss-praxie"]}
Visuell Räumliche Leistung:         {json_data["kopss-visual-spatial-performance"]}
Rechnen:                            {json_data["kopss-calculating"]}
Exekutive Leistung/Aufmerksamkeit:  {json_data["kopss-executive-performance"]}
Gedächtnis:                         {json_data["kopss-memory"]}
Affekt:                             {json_data["kopss-affect"]}
Verhaltensbeobachtung:              {json_data["kopss-behavior-observation"]}
"""

    message += f"""
--- Aphasia Check Liste (short version, ACL-K) ---
Lautes Lesen:               {json_data["acl-k-loud-reading"]}
Farb-Figur-Test:            {json_data["acl-k-color-form-test"]}
Supermarktaufgabe:          {json_data["acl-k-supermarket-task"]}
Kommunikationsfähigkeit:    {json_data["acl-k-communication-ability"]}

--- Beck Depression Inventory (BDI II) ---
Punktzahl:  {json_data["bdi-ii-score"]}

--- Montgomery-Asberg Depression rating Scale (MADRS) ---
Punktzahl:  {json_data["madrs-score"]}

--- DemTect ---
Wortliste:                      {json_data["demtect-wordlist"]}
Zahlen umwandeln:               {json_data["demtect-convert-numbers"]}
Supermarktaufgabe:              {json_data["demtect-supermarket-task"]}
Zahlenfolge rückwärts:          {json_data["demtect-numbers-reverse"]}
Erneute Abfrage der Wortliste:  {json_data["demtect-wordlist-recall"]}

--- Trail Making Test (TMT) ---
Zeit TMT A:                                     {json_data["time-tmt-a"]}
Zeitüberschreitung bei Durchführung von TMT A:  {checkbox_message(json_data["tmt-a-incorrectly-executed"])}
Zeit TMT B:                                     {json_data["time-tmt-b"]}
Zeitüberschreitung bei Durchführung von TMT B:  {checkbox_message(json_data["tmt-b-incorrectly-executed"])}


-- Allgemeneine Scores --

--- Modified Rankin scale (mRS) ---
Punktzahl:  {json_data["mrs-score"]}

--- EuroQol 5 (5Q-5D) ---
Code aus Antworten:             {json_data["euroqol-code"]}
Visuelle Analogskala (VAS):     {json_data["euroqol-vas"]}

--- Anzahl Ausbildungsjahre ---
Zahlenwert nach ISCED:          {json_data["isced-value"]}


-- Weitere Diagnostik --
MRT:                            {checkbox_message(json_data["additional-mrt"])}
   Link zu MRT-Daten:           {json_data["additional-mrt-url"]}
   Resting State:               {checkbox_message(json_data["additional-mrt-resting-state"])}
   Tapping Task:                {checkbox_message(json_data["additional-mrt-tapping-task"])}
   Anatomische Darstellung:     {checkbox_message(json_data["additional-mrt-anatomical-representation"])}
   DTI:                         {checkbox_message(json_data["additional-mrt-dti"])}

EEG:                            {checkbox_message(json_data["additional-eeg"])}
   Link zu EEG-Daten:           {json_data["additional-eeg-url"]}

Blutproben:                     {checkbox_message(json_data["additional-blood-sampling"])}
   Link zu Blutproblendaten:    {json_data["additional-blood-sampling-url"]}

   
-- Weitere Bemerkungen --
{json_data["additional-remarks"]}
"""

    return message


def get_string_content(_: str, field_content: List[str]) -> str:
    return field_content[0]


def get_checkbox_content(field_name: str, field_content: List[str]) -> str:
    if field_content[0] == "off":
        return "False"
    elif field_content[0] == "on":
        return "True"
    raise ValueError(
        f"illegal value for checkbox field {field_name}: {field_content[0]}")


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
    ["ftf-incorrectly-executed", get_checkbox_content],
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
    ["tug-v-not-executable", get_checkbox_content],
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
    ["kopss-applicable", get_checkbox_content],
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
    ["additional-mrt", get_checkbox_content],
    ["additional-mrt-url", get_string_content],
    ["additional-mrt-resting-state", get_checkbox_content],
    ["additional-mrt-tapping-task", get_checkbox_content],
    ["additional-mrt-anatomical-representation", get_checkbox_content],
    ["additional-mrt-dti", get_checkbox_content],
    ["additional-eeg", get_checkbox_content],
    ["additional-eeg-url", get_string_content],
    ["additional-blood-sampling", get_checkbox_content],
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
        "off": False
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
    "ftf-incorrectly-executed": get_checkbox_value,
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
            output = ["Hashed string does not match submitted values".encode("utf-8")]
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

        # Check for dependent keys:
        for controlling_variable in dependent_fields:
            control_value = entered_data[controlling_variable][0]
            for key in dependent_fields[controlling_variable][control_value]:
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

        result_message = create_result_message(commit_hash, time_stamp, json_data)
        result_message = create_result_page(commit_hash, time_stamp, json_data)

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
