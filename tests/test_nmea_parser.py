# tests/test_nmea_parser.py
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import pytest
from nmea_parser import parse_nmea


# 场景1：正常
def test_normal():
    result = parse_nmea(b"$GPGGA,123519,4807.038,N\r\n")
    assert result['type'] == '$GPGGA'


# 场景2：异常-空
def test_empty():
    with pytest.raises(ValueError):
        parse_nmea(b"")


# 场景3：异常-格式错
def test_missing_prefix():
    with pytest.raises(ValueError):
        parse_nmea(b"GPGGA,123519\r\n")


def test_non_ascii():
    with pytest.raises(ValueError):
        parse_nmea(b"\xff\xfe")


def test_too_few_fields():
    with pytest.raises(ValueError):
        parse_nmea(b"$GPGGA\r\n")


# 场景4：边界值
@pytest.mark.parametrize("raw", [
    b"$GPGGA,\r\n",                    # 最少字段
    b"$GPGGA," + b"x" * 1000 + b"\r\n",  # 超长字段
    b"$GPGGA,123519\r\n",              # 两个字段
])
def test_boundary(raw):
    try:
        result = parse_nmea(raw)
        assert result['type'] == '$GPGGA'
    except ValueError:
        pass  # 允许抛异常，但不应崩溃