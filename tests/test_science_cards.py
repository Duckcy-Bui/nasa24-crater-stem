"""S2-10: thẻ phải có nguồn và không gắn pin giả vào crop."""
from __future__ import annotations

import unittest

from src.science_cards import cards_for_image


class TestScienceCards(unittest.TestCase):
    def test_verified_regions_have_one_sourced_card_without_fake_pin(self):
        examples = {"moon_ap15_hia_c01": "apollo15-hadley-region", "moon_ap16_m102064759r_c01": "apollo16-descartes-region", "moon_lunokhod1_loc_c01": "lunokhod1-mare-imbrium-region", "moon_lunokhod2_loc_c01": "lunokhod2-le-monnier-region"}
        for image_id, card_id in examples.items():
            with self.subTest(image_id=image_id):
                cards = cards_for_image(image_id)
                self.assertEqual(len(cards), 1)
                card = cards[0]
                self.assertEqual(card["card_id"], card_id)
                self.assertTrue(card["source_title"])
                self.assertTrue(card["source_url"].startswith("https://"))
                self.assertIsNone(card["position"])
                self.assertIn("crop 512×512", card["body"])
                self.assertIn("không đặt ghim", card["body"])

    def test_unverified_regions_do_not_get_an_apollo_or_rover_card(self):
        self.assertEqual(cards_for_image("moon_marefrig_loc_c01"), [])
        self.assertEqual(cards_for_image("moon_vandegraff_hia_c01"), [])
        self.assertEqual(cards_for_image("not_an_image"), [])


if __name__ == "__main__":
    unittest.main()
