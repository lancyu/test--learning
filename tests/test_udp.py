import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
#让src可以被发现

import threading
import time
import pytest
from udp_receiver import receive_one, send_radar


def test_udp_receive_radar():
    result = {}

    def receiver():
        data, _, _ = receive_one(("127.0.0.1", 19999))
        result['data'] = data

    t = threading.Thread(target=receiver)  #执行receiver函数
    t.start()
    time.sleep(0.2)

    send_radar(("127.0.0.1", 19999), [
        {"angle": 45.0, "distance": 100.5, "intensity": 200}
    ])

    t.join(timeout=3)
    assert 'data' in result
    assert result['data']['type'] == 'radar'
    assert len(result['data']['points']) == 1


def test_udp_timeout():
    with pytest.raises(Exception):#如果抛了异常就表示测试通过
        receive_one(("127.0.0.1", 19998), timeout=1)