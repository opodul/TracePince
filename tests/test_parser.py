import unittest
from unittest.mock import patch
from pathlib import Path

from app.protocol_parser import ProtocolParser, parse_text


class ProtocolParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample = Path(__file__).parents[1].joinpath("log_example.txt").read_text()

    def test_sample_contains_all_modes(self):
        measurements = parse_text(self.sample)
        self.assertEqual([item.mode for item in measurements], ["VOLTAGE_ACDC"] * 5 + ["CURRENT_DC"] * 3 + ["POWER_1PH_DC"] * 3)
        self.assertEqual(measurements[0].voltage, 1.43)
        self.assertIsNone(measurements[0].current)
        self.assertEqual(measurements[6].current, 2.08)
        self.assertEqual(measurements[6].ripple, 19.8)
        self.assertEqual(measurements[-1].power, 3.0)
        self.assertEqual(measurements[-1].voltage, 1.42)

    def test_streaming_waits_for_next_block(self):
        parser = ProtocolParser()
        self.assertEqual(parser.feed("* CURRENT DC\n ELAPSED TIME: 00:00\n DC (A) = + 2.08\n"), [])
        self.assertIsNone(parser.flush().current_peak_positive)
        parser = ProtocolParser()
        result = parser.feed("* CURRENT DC\n ELAPSED TIME: 00:00\n DC (A) = + 2.08\n\nELAPSED TIME: 00:01\n DC (A) = - 1.25\n")
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].current, 2.08)
        self.assertEqual(parser.flush().current, -1.25)

    def test_variable_spacing_and_unknown_values(self):
        text = "* POWER-1Ph DC\nELAPSED TIME: 00:03\nP ( W ) = -  2.9\nA (A)=+2.11\nV ( V ) = + 1.42\nFreq ( Hz ) = 0\n"
        measurement = parse_text(text)[0]
        self.assertEqual(measurement.power, -2.9)
        self.assertEqual(measurement.current, 2.11)
        self.assertEqual(measurement.frequency, 0.0)
        self.assertIn("P ( W )", measurement.raw_block)

    def test_split_line_across_serial_reads(self):
        parser = ProtocolParser()
        self.assertEqual(parser.feed("* CURRENT DC\nELAPSED TIME: 00:00\nDC (A) = + 2."), [])
        self.assertEqual(parser.feed("08\n"), [])
        measurement = parser.flush()
        self.assertIsNotNone(measurement)
        self.assertEqual(measurement.current, 2.08)

    def test_acdc_log_keeps_received_columns(self):
        text = Path(__file__).parents[1].joinpath("logs/examples/CURRENT_ACDC.log").read_text()
        measurements = parse_text(text)
        self.assertEqual(len(measurements), 3)
        self.assertEqual(list(measurements[0].values), ["RMS (A)", "Peak+ (A)", "Peak- (A)", "CF", "DC (A)", "Freq (Hz)", "THDF"])
        self.assertEqual(measurements[0].values["DC (A)"], -2.12)

    def test_unknown_mode_and_field_are_generic(self):
        text = "* CUSTOM-MODE DC\nELAPSED TIME: 00:00\nReading (unit) = + 4.2\n"
        measurement = parse_text(text)[0]
        self.assertEqual(measurement.mode, "CUSTOM_MODE_DC")
        self.assertEqual(measurement.values, {"Reading (unit)": 4.2})

    def test_idle_block_flushes_after_timeout(self):
        parser = ProtocolParser()
        with patch("app.protocol_parser.time.monotonic", side_effect=(10.0, 10.0, 10.0, 10.0, 10.6)):
            parser.feed("* CURRENT DC\nELAPSED TIME: 00:00\nDC (A) = + 2.08\n")
            self.assertIsNone(parser.flush_if_idle(timeout=0.5))
            measurement = parser.flush_if_idle(timeout=0.5)
        self.assertIsNotNone(measurement)
        self.assertEqual(measurement.current, 2.08)

    def test_mode_is_inferred_when_connected_mid_session(self):
        text = "ELAPSED TIME: 12:37\nDC (A) = - 2.08\nPeak+ (A) = - 1.89\n"
        measurement = parse_text(text)[0]
        self.assertEqual(measurement.mode, "CURRENT_DC")
        self.assertEqual(measurement.elapsed_time, "12:37")

    def test_acdc_mode_is_inferred_without_header(self):
        text = "ELAPSED TIME: 03:14\nRMS (A) = 2.10\nDC (A) = - 2.12\n"
        measurement = parse_text(text)[0]
        self.assertEqual(measurement.mode, "CURRENT_ACDC")


if __name__ == "__main__":
    unittest.main()