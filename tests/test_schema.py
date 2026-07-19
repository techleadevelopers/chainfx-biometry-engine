from __future__ import annotations

import unittest

from kyc_local_ai.schema import validate_payload


class SchemaTest(unittest.TestCase):
    def test_accepts_minimal_valid_payload(self) -> None:
        ok, errors = validate_payload({"Level": 1, "DocumentURL": "https://cdn/front.jpg"})

        self.assertTrue(ok)
        self.assertEqual(errors, [])

    def test_rejects_bad_level_and_non_http_url(self) -> None:
        ok, errors = validate_payload({"Level": 4, "FacialVideoURL": "ftp://video"})

        self.assertFalse(ok)
        self.assertIn("Level_must_be_1_2_or_3", errors)
        self.assertIn("FacialVideoURL_must_be_http_url", errors)


if __name__ == "__main__":
    unittest.main()
