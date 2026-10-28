from parking import parking_fee


def test_parking_fee():
    assert parking_fee(2) == 10.0
