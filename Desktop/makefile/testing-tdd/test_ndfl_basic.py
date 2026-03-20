def calculate_tax(income):
    return None

def test_basic_ndfl():
    assert calculate_tax(200_000) == 26_000

def test_basic_ndfl2():
    # 312_000 + 0.15 * 600_000
    assert calculate_tax(3_000_000) == 402_000

def test_basic_ndfl3():
    # 702_000 + 0.18 * 2_000_000
    assert calculate_tax(7_000_000) == 1_062_000

def test_basic_ndfl4():
    # 702_000 + 0.18 * 2_000_000
    assert calculate_tax(7_000_000) == 1_062_000

def test_basic_ndfl5():
    # 702_000 + 0.18 * 2_000_000
    assert calculate_tax(7_000_000) == 1_062_000