import json
import os
import subprocess
import sys
import unittest
import tempfile
from pathlib import Path
from typing import List
from unittest.mock import patch

from webtest import TestApp
from webtest.app import AppError


server_dir = Path(__file__).parents[1]
template_dir = Path(__file__).parents[2] / "templates"

sys.path.insert(0, str(server_dir))


import store_data
from store_data import (
    get_int_value,
    DATASET_ROOT_KEY,
    HOME_KEY,
    TEMPLATE_DIRECTORY_KEY,
)


minimal_form_data = """form-data-version=2.2&data-entry-domain=de.sfb1451.z03&data-entry-employee=cm-test&project-code=b4&subject-pseudonym=test-111&date-of-birth=2000-01-01&sex=male&date-of-test=2020-01-01&subject-group=healthy&patient-year-first-symptom=&patient-month-first-symptom=&patient-day-first-symptom=&patient-year-diagnosis=&patient-month-diagnosis=&patient-day-diagnosis=&additional-remarks=&hashed-string=form-data-version%3A2.2%3Bdata-entry-domain%3Ade.sfb1451.z03%3Bdata-entry-employee%3Acm-test%3Bproject-code%3Ab4%3Bsubject-pseudonym%3Atest-111%3Bdate-of-birth%3A2000-01-01%3Bsex%3Amale%3Bdate-of-test%3A2020-01-01%3Brepeated-test%3AFalse%3Bpatient-year-first-symptom%3A%3Bpatient-month-first-symptom%3A%3Bpatient-day-first-symptom%3A%3Bpatient-year-diagnosis%3A%3Bpatient-month-diagnosis%3A%3Bpatient-day-diagnosis%3A%3Bpatient-main-disease%3A%3Bpatient-stronger-impacted-hand%3A%3Blaterality-quotient%3A%3Bmaximum-ftf-left%3A%3Bmaximum-ftf-right%3A%3Bmaximum-gs-left%3A%3Bmaximum-gs-right%3A%3Bpurdue-pegboard-left%3A%3Bpurdue-pegboard-right%3A%3Bturn-cards-left%3A%3Bturn-cards-right%3A%3Bsmall-things-left%3A%3Bsmall-things-right%3A%3Bsimulated-feeding-left%3A%3Bsimulated-feeding-right%3A%3Bcheckers-left%3A%3Bcheckers-right%3A%3Blarge-light-things-left%3A%3Blarge-light-things-right%3A%3Blarge-heavy-things-left%3A%3Blarge-heavy-things-right%3A%3Bjtt-incorrectly-executed%3A%3Barat-left%3A%3Barat-right%3A%3Btug-executed%3A%3Btug-a-incorrectly-executed%3A%3Btug-a-tools-required%3A%3Btug-imagined%3A%3Bgo-nogo-block-count%3A%3Bgo-nogo-total-errors%3A%3Bgo-nogo-wrong-errors%3A%3Bgo-nogo-recognized-errors%3A%3Bgo-nogo-correct-answer-time%3A%3Bgo-nogo-recognized-error-time%3A%3Bgo-nogo-incorrectly-executed%3A%3Bkas-pantomime-bukko-facial%3A%3Bkas-pantomime-arm-hand%3A%3Bkas-imitation-bukko-facial%3A%3Bkas-imitation-arm-hand%3A%3Bkopss-orientation%3A%3Bkopss-speech%3A%3Bkopss-praxie%3A%3Bkopss-visual-spatial-performance%3A%3Bkopss-calculating%3A%3Bkopss-executive-performance%3A%3Bkopss-memory%3A%3Bkopss-affect%3A%3Bkopss-behavior-observation%3A%3Bacl-k-loud-reading%3A%3Bacl-k-color-form-test%3A%3Bacl-k-supermarket-task%3A%3Bacl-k-communication-ability%3A%3Bbdi-ii-score%3A%3Bmadrs-score%3A%3Bdemtect-wordlist%3A%3Bdemtect-convert-numbers%3A%3Bdemtect-supermarket-task%3A%3Bdemtect-numbers-reverse%3A%3Bdemtect-wordlist-recall%3A%3Btime-tmt-a%3A%3Btmt-a-incorrectly-executed%3A%3Btime-tmt-b%3A%3Btmt-b-incorrectly-executed%3A%3Bmrs-score%3A%3Beuroqol-code%3A%3Beuroqol-vas%3A%3Bisced-value%3A%3Badditional-mrt-url%3A%3Badditional-mrt-resting-state%3A%3Badditional-mrt-tapping-task%3A%3Badditional-mrt-anatomical-representation%3A%3Badditional-mrt-dti%3A%3Badditional-eeg-url%3A%3Badditional-blood-sampling-url%3A%3Badditional-remarks%3A&hash-value=3bb998f5acf11ad82a17b3cef2c14258712a3b50c5efe7261e7792158e058ebe&signature-data="""


class TestStoreData(unittest.TestCase):

    def _test_exception_caught(self,
                               app_tester,
                               params,
                               extra_environ,
                               patterns: List[str]):

        with self.assertRaises(AppError) as context_manager:
            app_tester.post(
                url="/store-data",
                params=params,
                extra_environ=extra_environ)
        error_message = context_manager.exception.args[0]
        print(error_message)
        for pattern in patterns:
            self.assertTrue(error_message.find(pattern) > 0)

    def test_missing_environ_catching(self):
        app_tester = TestApp(store_data.application)
        self._test_exception_caught(
            app_tester=app_tester,
            params="Hello",
            extra_environ={},
            patterns=[
                "<c.moench@fz-juelich.de>",
                f"KeyError: '{DATASET_ROOT_KEY}'"])

    def test_missing_data_catching(self):
        app_tester = TestApp(store_data.application)
        self._test_exception_caught(
            app_tester=app_tester,
            params="Hello",
            extra_environ={
                DATASET_ROOT_KEY: "",
                HOME_KEY: "",
                TEMPLATE_DIRECTORY_KEY: ""
            },
            patterns=[
                "keys are missing",
                "project-code"])

    def test_data_storage(self):
        app_tester = TestApp(store_data.application)
        with tempfile.TemporaryDirectory() as temp_dir:

            with \
                    patch("store_data.add_file_to_dataset") as add_file_mock, \
                    patch("time.time") as time_mock:

                add_file_mock.return_value = 0
                time_mock.return_value = 0.0

                app_tester.post(
                    url="/store-data",
                    params=minimal_form_data,
                    extra_environ={
                        DATASET_ROOT_KEY: temp_dir,
                        HOME_KEY: os.environ["HOME"],
                        TEMPLATE_DIRECTORY_KEY: str(template_dir),
                        "REMOTE_ADDR": "1.2.3.4"
                    })

            expected_path = Path(temp_dir) / "input/2.2/0.0.json"
            with expected_path.open() as f:
                json_object = json.load(f)
        print(json_object)

    def test_datalad_saving(self):
        app_tester = TestApp(store_data.application)
        with tempfile.TemporaryDirectory() as temp_dir:

            dataset_path = Path(temp_dir) / "dataset"
            subprocess.run(
                ["datalad", "create", "--no-annex", str(dataset_path)],
                check=True
            )

            sibling_path = Path(temp_dir) / "entrystore"
            sibling_path.mkdir()
            subprocess.run(
                [
                    "datalad", "create-sibling", "-d", str(dataset_path), "-s",
                    "entrystore", str(sibling_path)
                ],
                check=True
            )

            with patch("time.time") as time_mock:
                time_mock.return_value = 0.0
                app_tester.post(
                    url="/store-data",
                    params=minimal_form_data,
                    extra_environ={
                        DATASET_ROOT_KEY: str(dataset_path),
                        HOME_KEY: os.environ["HOME"],
                        TEMPLATE_DIRECTORY_KEY: str(template_dir),
                        "REMOTE_ADDR": "1.2.3.4"
                    })

            expected_path = dataset_path / "input/2.2/0.0.json"
            with expected_path.open() as f:
                json_object_1 = json.load(f)
            expected_sibling_path = sibling_path / "input/2.2/0.0.json"
            with expected_sibling_path.open() as f:
                json_object_2 = json.load(f)
            assert json_object_1 == json_object_2

    def test_get_int(self):
        self.assertEqual(get_int_value(".0"), 0)
        self.assertEqual(get_int_value("1.0"), 1)
        self.assertEqual(get_int_value("2"), 2)

        # Empty fields should be mapped to None
        self.assertEqual(get_int_value(""), None)

        # Non-int should raise a ValueError
        self.assertRaises(ValueError, get_int_value, "3.4")
        self.assertRaises(ValueError, get_int_value, "a")
