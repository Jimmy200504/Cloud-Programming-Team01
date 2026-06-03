from __future__ import annotations

import unittest

from ml.errors import MLError, MLErrorCode
from ml.media import SUPPORTED_IMAGE_TYPES, validate_media


class MediaValidationTest(unittest.TestCase):
    def test_local_path_requires_existing_file(self) -> None:
        with self.assertRaises(MLError) as ctx:
            validate_media(
                {"type": "local_path", "value": "./does-not-exist.jpg"},
                field_name="image",
                supported_types=SUPPORTED_IMAGE_TYPES,
            )

        self.assertEqual(ctx.exception.code, MLErrorCode.FILE_NOT_FOUND)

    def test_rejects_unsupported_media_type(self) -> None:
        with self.assertRaises(MLError) as ctx:
            validate_media(
                {"type": "ftp", "value": "x"},
                field_name="image",
                supported_types=SUPPORTED_IMAGE_TYPES,
            )

        self.assertEqual(ctx.exception.code, MLErrorCode.UNSUPPORTED_MEDIA_TYPE)


if __name__ == "__main__":
    unittest.main()

