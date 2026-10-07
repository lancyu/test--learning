# src/data_fusion.py
def fuse(gps: dict, compass: dict, ais: list) -> dict:
    """融合多传感器数据"""
    if not gps:
        raise ValueError("gps required")
    return {
        'lat': gps.get('lat', 0.0),
        'lon': gps.get('lon', 0.0),
        'heading': compass.get('heading', 0.0) if compass else 0.0,
        'targets': len(ais) if ais else 0,
    }