"""雷达/传感器数据解析模块，模拟盛洋设备上的数据解析逻辑"""

def parse_radar(data: str) -> list:
    """
    解析格式: "角度,距离,强度;角度,距离,强度;..."
    - 角度: 0~360 度
    - 距离: >= 0
    - 强度: 0~255
    非法数据跳过
    """
    points = []
    if not data:
        return points

    for seg in data.split(';'):
        seg = seg.strip()
        if not seg:
            continue

        fields = seg.split(',')
        if len(fields) != 3:
            continue

        try:
            angle = float(fields[0])
            distance = float(fields[1])
            intensity = int(fields[2])
        except ValueError:
            continue

        if not (0 <= angle <= 360):
            continue
        if distance < 0:
            continue
        if not (0 <= intensity <= 255):
            continue

        points.append({
            'angle': angle,
            'distance': distance,
            'intensity': intensity,
        })

    return points


def parse_gps(nmea: str) -> dict:
    """
    解析 $GPGGA NMEA 语句，返回经纬度、海拔
    格式: $GPGGA,time,lat,N,lon,E,fix,sats,hdop,alt,M,...
    """
    if not nmea or not nmea.startswith('$GPGGA'):
        raise ValueError("invalid GGA sentence")

    parts = nmea.split(',')
    if len(parts) < 10:
        raise ValueError("incomplete GGA sentence")

    def to_float(s):
        return float(s) if s else 0.0

    return {
        'time': parts[1],
        'lat': to_float(parts[2]),
        'lat_dir': parts[3],
        'lon': to_float(parts[4]),
        'lon_dir': parts[5],
        'altitude': to_float(parts[9]),
    }