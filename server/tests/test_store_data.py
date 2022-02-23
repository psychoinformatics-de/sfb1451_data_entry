import sys
import unittest
from pathlib import Path

from webtest import TestApp


server_dir = Path(__file__).parents[1]
template_dir = Path(__file__).parents[2] / "templates"


sys.path.insert(0, str(server_dir))


class TestFileTree(unittest.TestCase):

    def test_simple(self):
        import store_data

        app = TestApp(store_data.application)
        app.post(
            url="/store-data",
            params="Hello",
            extra_environ={
                "de.inm7.sfb1451.entry.dataset_root": "/tmp/sfb-test",
                "de.inm7.sfb1451.entry.home": "/etc",
                "de.inm7.sfb1451.entry.templates": str(template_dir)
            }
        )
