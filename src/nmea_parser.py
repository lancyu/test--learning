# src/nmea_parser.py
def parse_nmea(raw: bytes) -> dict:
    """解析 NMEA 语句"""
    if not raw:#空数据直接拒绝。注意 b'' 和 None 都能被 if not 抓住。
        raise ValueError("empty")
    try:
        line = raw.decode('ascii').strip()
    except UnicodeDecodeError:
        raise ValueError("non-ascii")
    if not line.startswith('$'):#NMEA 协议规定每条语句必须以 $ 开头，没有就是非法数据。
        raise ValueError("missing $")
    parts = line.split(',')#按逗号切分。至少要切出 2 段（比如 $GPGGA 单独没有逗号，说明语句残缺）。
    if len(parts) < 2:
        raise ValueError("too few fields")
    return {'type': parts[0], 'fields': parts[1:]}
#b'' 是 空的字节串（bytes）——就是"长度为 0 的字节数据"。