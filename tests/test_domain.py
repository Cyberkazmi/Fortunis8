import unittest
from datetime import date

from app.services.domain import (
    SAFETY_DISCLAIMER,
    check_skill_answer,
    fortune,
    horoscope_reading,
    menu_translations,
    palm_reading,
    skill_game,
    sun_sign,
    supported_personas,
    tarot,
)


class DomainTests(unittest.TestCase):
    def test_safety_disclaimers_are_present_in_readings(self):
        for language in ("en", "ur"):
            self.assertIn(SAFETY_DISCLAIMER[language], fortune(language, "x"))
            self.assertIn(SAFETY_DISCLAIMER[language], tarot(language, "x"))
            self.assertIn(SAFETY_DISCLAIMER[language], palm_reading("career", language))
            self.assertIn(SAFETY_DISCLAIMER[language], horoscope_reading("2000-03-21", "12:00", "Lahore", language))

    def test_supported_translations_have_same_menu_keys(self):
        english = menu_translations("en")
        urdu = menu_translations("ur")
        self.assertEqual(set(english), set(urdu))
        self.assertNotEqual(english["fortune"], urdu["fortune"])
        with self.assertRaises(ValueError):
            menu_translations("fr")

    def test_persona_names_are_exact_and_complete(self):
        self.assertEqual(
            supported_personas(),
            ("Mario", "Tarzan", "Hercules", "Dragon", "Ninja", "Wizard", "Phoenix", "Spartan", "Viking", "Samurai", "Pirate", "Jedi"),
        )

    def test_sun_sign_boundary_examples(self):
        self.assertEqual(sun_sign(date(2024, 3, 20)), "Pisces")
        self.assertEqual(sun_sign(date(2024, 3, 21)), "Aries")
        self.assertEqual(sun_sign(date(2024, 4, 19)), "Aries")
        self.assertEqual(sun_sign(date(2024, 4, 20)), "Taurus")
        self.assertEqual(sun_sign(date(2024, 12, 21)), "Sagittarius")
        self.assertEqual(sun_sign(date(2024, 12, 22)), "Capricorn")

    def test_horoscope_is_deterministic_for_same_inputs(self):
        inputs = ("1990-07-23", "08:30", "Karachi", "en")
        self.assertEqual(horoscope_reading(*inputs), horoscope_reading(*inputs))
        self.assertIn("Leo", horoscope_reading(*inputs))
        self.assertNotEqual(horoscope_reading(*inputs), horoscope_reading("1990-07-23", "09:30", "Karachi", "en"))

    def test_palm_reading_uses_focus_and_does_not_claim_image_processing(self):
        self.assertIn("career", palm_reading("career"))
        self.assertIn("No image processing", palm_reading("career", premium=True))
        with self.assertRaises(ValueError):
            palm_reading(" ")

    def test_hard_skill_reward_exceeds_easy_and_wrong_answers_score_zero(self):
        self.assertGreater(skill_game("hard")["points"], skill_game("easy")["points"])
        self.assertEqual(check_skill_answer("easy", "4"), skill_game("easy")["points"])
        self.assertEqual(check_skill_answer("hard", "wrong"), 0)


if __name__ == "__main__":
    unittest.main()
