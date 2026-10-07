# tests/test_data_fusion.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from data_fusion import fuse


def test_all_sensors():
    result = fuse(
        gps={'lat': 29.0, 'lon': 121.0},
        compass={'heading': 90.0},
        ais=[{'mmsi': 1}, {'mmsi': 2}],
    )
    assert result['lat'] == 29.0
    assert result['heading'] == 90.0
    assert result['targets'] == 2


def test_missing_compass():
    result = fuse(gps={'lat': 29.0, 'lon': 121.0}, compass=None, ais=None)
    assert result['heading'] == 0.0
    assert result['targets'] == 0


def test_missing_gps():
    with pytest.raises(ValueError):
        fuse(gps=None, compass={}, ais=[])


@pytest.mark.parametrize("ais_count", [0, 1, 10, 100])
def test_ais_count(ais_count):
    result = fuse(
        gps={'lat': 0, 'lon': 0},
        compass=None,
        ais=[{'mmsi': i} for i in range(ais_count)],
    )
    assert result['targets'] == ais_count