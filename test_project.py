from helpers import calculate_interest, check_frequency, convert_nominal_to_monthly_effective, TYPES, PERIODS


def test_calculate_interest():
    assert calculate_interest(1.0, 100.0) == 1.00


def test_check_frequency():
    assert check_frequency(6, "semi-annually") == True


def test_convert_nominal_to_monthly_effective():
    assert convert_nominal_to_monthly_effective(3.0, "quarterly") == 0.2494

