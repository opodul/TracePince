import unittest
from pathlib import Path

from app.protocol_parser import ProtocolParser, parse_text


class ProtocolParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sample = Path(__file__).parents[1].joinpath("log_example.txt").read_text()

    def test_sample_contains_all_modes(self):
        measurements = parse_text(self.sample)
        self.assertEqual([item.mode for item in measurements], ["VOLTAGE"] * 5 + ["CURRENT"] * 3 + ["POWER-1PH"] * 3)
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


if __name__ == "__main__":
    unittest.main()