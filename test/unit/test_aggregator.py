from os import path

import pytest

from autolens import aggregator as a

directory = path.dirname(path.realpath(__file__))
aggregator_directory = "{}/test_files/aggregator".format(directory)


@pytest.fixture(name="aggregator")
def make_aggregator():
    return a.Aggregator(aggregator_directory)


def filter_aggregations(aggregator, folder):
    return list(filter(lambda ag: "/{}/.metadata".format(folder) in ag.file_path, aggregator.aggregations))[0]


@pytest.fixture(name="one")
def make_one(aggregator):
    return filter_aggregations(aggregator, "one")


@pytest.fixture(name="two")
def make_two(aggregator):
    return filter_aggregations(aggregator, "two")


@pytest.fixture(name="three")
def make_three(aggregator):
    return filter_aggregations(aggregator, "three")


class TestCase(object):
    def test_total_aggregations(self, aggregator):
        assert len(aggregator.aggregations) == 3

    def test_file_paths(self, one, two, three):
        assert three.file_path == "{}/three/.metadata".format(aggregator_directory)
        assert one.file_path == "{}/one/.metadata".format(aggregator_directory)
        assert two.file_path == "{}/two/.metadata".format(aggregator_directory)

    def test_attributes(self, one, two, three):
        assert one.pipeline == "pipeline_1"
        assert one.phase == "phase_1"
        assert one.lens == "lens_1"

        assert two.pipeline == "pipeline_2"
        assert two.phase == "phase_1"
        assert two.lens == "lens_1"

        assert three.pipeline == "pipeline_1"
        assert three.phase == "phase_2"
        assert three.lens == "lens_2"

    def test_filter_aggregations(self, aggregator, one, two, three):
        result = aggregator.aggregations_with()

        assert len(result) == 3
        assert one in result
        assert two in result
        assert three in result

        result = aggregator.aggregations_with(pipeline="pipeline_1")
        assert len(result) == 2
        assert one in result
        assert three in result

        result = aggregator.aggregations_with(lens="lens_2")
        assert [three] == result

        result = aggregator.aggregations_with(pipeline="pipeline_2", phase="phase_1")
        print(result)
        assert [two] == result
