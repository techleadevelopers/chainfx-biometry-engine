from __future__ import annotations

import unittest

from kyc_local_ai.ocr import analyze_document


class OCRContractTest(unittest.TestCase):
    def test_returns_structured_ocr_fields_even_before_real_model(self) -> None:
        _score, details = analyze_document(None, None)
        ocr = details["ocr"]

        for field in ("name", "cpf", "birth_date", "document_number", "issuer", "issue_date", "expiry_date"):
            self.assertIn(field, ocr)
            self.assertIn("value", ocr[field])
            self.assertIn("confidence", ocr[field])


if __name__ == "__main__":
    unittest.main()
