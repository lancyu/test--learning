import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from radar_parser import parse_radar, parse_gps

'''# 原来：数据藏在测试里，改格式要逐个翻测试找
result = parse_radar("45.0,100.5,200")

# 现在：数据集中管理，测试只关心"拿到一个标准数据"
result = parse_radar(radar_data)

'''
# ========== Fixtures：把重复使用的测试数据提出来 或者解决需要重复链接的==========

@pytest.fixture
def radar_data():
    """标准单目标雷达数据字符串"""
    return "45.0,100.5,200"


@pytest.fixture
def radar_points_multi():
    """多目标雷达数据字符串"""
    return "45.0,100.5,200;90.0,50.0,100"


@pytest.fixture
def gga_sentence():
    """标准 GPS GGA 语句"""
    return "$GPGGA,123519,4807.038,N,01131.000,E,1,08,0.9,545.4,M,46.9,M,,*47"


# ========== 雷达解析测试 ==========

def test_radar_normal_single(radar_data):          # ← 改了：用 fixture
    result = parse_radar(radar_data)
    assert len(result) == 1
    assert result[0]['angle'] == 45.0
    assert result[0]['distance'] == 100.5
    assert result[0]['intensity'] == 200


def test_radar_normal_multiple(radar_points_multi):  # ← 改了：用 fixture
    result = parse_radar(radar_points_multi)
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
# 注意：这部分不改！parametrize 里每条数据都不同，本来就该写在一起

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

def test_gps_normal(gga_sentence):                  # ← 改了：用 fixture
    result = parse_gps(gga_sentence)
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