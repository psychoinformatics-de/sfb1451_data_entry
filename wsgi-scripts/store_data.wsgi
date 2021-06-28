import json
import time
import subprocess
from pathlib import Path
from typing import Union
from urllib.parse import parse_qs


# Those fields are required in the user input. They can either
# come from the posted data or from the auto_fields-array.
required_fields = [
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
    "additional-remarks"
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
            "kopss-sum",
            "kopss-affect",
            "kopss-behavior-observation",
        ]
    },
    "subject-group": {
        "healthy": [],
        "patient": [
            "patient-main-disease",
            "patient-stronger-impacted-hand",
            # The following are added by auto_fields
            "patient-year-first-symptom",
            "patient-month-first-symptom",
            "patient-day-first-symptom",
            "patient-year-diagnosis",
            "patient-month-diagnosis",
            "patient-day-diagnosis"
        ]
    }
}


auto_fields = {
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
    "go-nogo-recognized-error-time": [""],
    "kopss-applicable": ["off"],
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
            "-m", f"adding file {file}",
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
        "on": "ja",
        "off": "nein"
    }[value]


def sex_message(value):
    return {
        "male": "männlich",
        "female": "weiblich",
        "diverse": "sonstiges"
    }[value]


def date_message(year, month, day):
    return "-".join([
        x
        for x in [year, month, day]
        if x != ""
    ])


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
Stärker betroffene Hand:    {json_data["patient-stronger-impacted-hand"]}
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
Anzahl erkannte Fehler:                     {json_data["go-nogo-recognized-errors"]}
"""
    if int(json_data["go-nogo-recognized-errors"]) > 0:
        message += f"""Reaktionszeit erkannte Fehler:              {json_data["go-nogo-recognized-error-time"]}
"""

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
Zahlenwert nach ISCED:      {json_data["isced-value"]}


-- Weitere Diagnostik --
MRT: {checkbox_message(json_data["additional-mrt"])}
   Link zu MRT-Daten:           {json_data["additional-mrt-url"]}
   Resting State:               {checkbox_message(json_data["additional-mrt-resting-state"])}
   Tapping Task:                {checkbox_message(json_data["additional-mrt-tapping-task"])}
   Anatomische Darstellung:     {checkbox_message(json_data["additional-mrt-anatomical-representation"])}
   DTI:                         {checkbox_message(json_data["additional-mrt-dti"])}

EEG: {checkbox_message(json_data["additional-eeg"])}
   Link zu EEG-Daten:           {json_data["additional-eeg-url"]}

Blutproben:                     {checkbox_message(json_data["additional-blood-sampling"])}
   Link zu Blutproblendaten:    {json_data["additional-blood-sampling-url"]}

   
-- Weitere Bemerkungen --
{json_data["additional-remarks"]}
"""

    return message


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

        # Create posted data dictionary
        json_object = dict()

        # Read the mandatory keys
        for key in required_fields:
            # This will throw an error, if the key is not available
            json_object[key] = entered_data[key][0]

        # Check for dependent keys:
        for controlling_variable in dependent_fields:
            control_value = entered_data[controlling_variable][0]
            for key in dependent_fields[controlling_variable][control_value]:
                json_object[key] = entered_data[key][0]

        time_stamp = str(time.time())

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

        directory = dataset_root / "input" / json_data["source"]["version"]
        directory.mkdir(parents=True, exist_ok=True)

        output_file = directory / (time_stamp + ".json")
        with output_file.open("x") as f:
            json.dump(json_data, f)

        commit_hash = add_file_to_dataset(dataset_root, directory / output_file, home)

        result_message = create_result_message(commit_hash, time_stamp, json_data)

        status = "200 OK"

        output = [
            result_message.encode(),
            #"2-------------\n".encode(),
            #("\n".join(environment) + "\n").encode("utf-8"),
            #"3-------------\n".encode(),
            #(posted_data_string + "\n").encode("utf-8"),
            #"4-------------\n".encode(),
            #json.dumps(json_data, indent=4).encode()
        ]

    else:

        status = "400 BAD REQUEST"
        output = ["Only post method allowed".encode("utf-8")]

    output_lenght = sum([len(line) for line in output])
    response_headers = [('Content-type', 'text/plain; charset=utf-8'),
                        ('Content-Length', str(output_lenght))]
    start_response(status, response_headers)

    return output
