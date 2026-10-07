import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from radar_parser import parse_radar, parse_gps


# ========== 雷达解析测试 ==========

def test_radar_normal_single():
    result = parse_radar("45.0,100.5,200")
    assert len(result) == 1
    assert result[0]['angle'] == 45.0
    assert result[0]['distance'] == 100.5
    assert result[0]['intensity'] == 200


def test_radar_normal_multiple():
    result = parse_radar("45.0,100.5,200;90.0,50.0,100")
    assert len(result) == 2
    assert result[1]['angle'] == 90.0


def test_radar_empty():
    assert parse_radar("") == []


def test_radar_malformed_field_count():
    assert parse_radar("45.0,100.5") == []


def test_radar_non_numeric():
    assert parse_radar("abc,100,200") == []


def test_radar_extra_semicolons():
    result = parse_radar("45,100,200;;90,50,100")
    assert len(result) == 2


def test_radar_only_semicolons():
    assert parse_radar(";;;") == []


# ========== 数据驱动测试（parametrize） ==========

@pytest.mark.parametrize("data,expected_len", [
    ("0,0,0", 1),                    # 边界最小
    ("360,100,255", 1),              # 边界最大
    ("361,100,200", 0),              # 角度越界
    ("-1,100,200", 0),               # 角度负数
    ("45,-5,200", 0),                # 距离负数
    ("45,100,256", 0),               # 强度越界
    ("45,100,-1", 0),                # 强度负数
    ("45, 100, 200", 1),             # 带空格
])
def test_radar_parametrized(data, expected_len):
    assert len(parse_radar(data)) == expected_len


# ========== GPS解析测试 ==========

def test_gps_normal():
    nmea = "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"
    result = parse_gps(nmea)
    assert result['lat'] == 4807.038
    assert result['lon'] == 1131.000
    assert result['altitude'] == 545.4


def test_gps_invalid_prefix():
    with pytest.raises(ValueError):
        parse_gps("$GPRMC,123519,...")


def test_gps_empty():
    with pytest.raises(ValueError):
        parse_gps("")


def test_gps_incomplete():
    with pytest.raises(ValueError):
        parse_gps("$GPGGA,123519,4807.038")