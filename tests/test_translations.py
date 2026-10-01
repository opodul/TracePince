import unittest

from app.translations import translate


class TranslationTests(unittest.TestCase):
    def test_french_translation(self):
        self.assertEqual(translate("Connect", "fr"), "Connecter")

    def test_german_translation(self):
        self.assertEqual(translate("Connect", "de"), "Verbinden")

    def test_measurement_action_translations(self):
        self.assertEqual(translate("Save Measurement", "fr"), "Enregistrer la mesure")
        self.assertEqual(translate("Save Measurement", "de"), "Messung speichern")

    def test_english_and_unknown_text_fall_back(self):
        self.assertEqual(translate("Connect", "en"), "Connect")
        self.assertEqual(translate("Measurement field", "fr"), "Measurement field")

    def test_formatted_status_translation(self):
        translated = translate("Connected - {port} ({log})", "fr")
        self.assertEqual(translated.format(port="COM1", log="capture.log"), "Connecté - COM1 (capture.log)")

    def test_formatted_german_status_translation(self):
        translated = translate("Connected - {port} ({log})", "de")
        self.assertEqual(translated.format(port="COM1", log="capture.log"), "Verbunden - COM1 (capture.log)")


if __name__ == "__main__":
    unittest.main()