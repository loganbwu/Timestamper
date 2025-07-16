import pytest
from src.timestamper.utils import float_to_shutterspeed, parse_lensinfo

# Test float_to_shutterspeed
@pytest.mark.parametrize("value, expected_speed", [
    (0.5, "1/2s"),
    (1/60, "1/60s"),
    (1.0, "1s"),
    (2.0, "2s"),
    (0.001, "1/1000s"),
])
def test_float_to_shutterspeed(value, expected_speed):
    assert float_to_shutterspeed(value) == expected_speed

# Test parse_lensinfo
def test_parse_lensinfo():
    assert parse_lensinfo("18 55 3.5 5.6") == ["18", "55", "3.5", "5.6"]
