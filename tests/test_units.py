import io
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest.mock import patch

from multitool import main
from multitool.units import convert


class UnitConversionTests(unittest.TestCase):
    def test_length_conversions(self) -> None:
        conversions = (
            (1000.0, "m", "km", 1.0),
            (1.0, "ft", "m", 0.3048),
            (1.0, "mi", "ft", 5280.0),
        )

        for value, from_unit, to_unit, expected in conversions:
            with self.subTest(from_unit=from_unit, to_unit=to_unit):
                self.assertAlmostEqual(convert(value, from_unit, to_unit), expected)

    def test_negative_forty_celsius_is_negative_forty_fahrenheit(self) -> None:
        self.assertEqual(convert(-40.0, "C", "F"), -40.0)

    def test_zero_celsius_is_273_15_kelvin(self) -> None:
        self.assertEqual(convert(0.0, "C", "K"), 273.15)

    def test_units_command(self) -> None:
        output = io.StringIO()

        with patch.object(sys, "argv", ["mt", "units", "1", "km", "m"]):
            with redirect_stdout(output):
                main()

        self.assertEqual(output.getvalue(), "1000.0\n")

    def test_unknown_unit_exits_with_code_2(self) -> None:
        self.assert_cli_error("1", "unknown", "m")

    def test_length_to_temperature_exits_with_code_2(self) -> None:
        self.assert_cli_error("1", "m", "C")

    def assert_cli_error(self, value: str, from_unit: str, to_unit: str) -> None:
        with patch.object(sys, "argv", ["mt", "units", value, from_unit, to_unit]):
            with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
                main()

        self.assertEqual(raised.exception.code, 2)
