from test_autolens.integration.tests.lens_only import lens_light__hyper_bg
from test_autolens.integration.tests.runner import run_a_mock


class TestCase:
    def _test__lens_light__hyper_bg(self):
        run_a_mock(lens_light__hyper_bg)
