"""Tests for CLI arguments and options."""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cinaura_metadata_helper.cli import parse_args


class TestCli(unittest.TestCase):
    """Test CLI argument parsing."""

    def test_default_arguments(self):
        args = parse_args(["/path/to/media"])
        self.assertEqual(args.path, "/path/to/media")
        self.assertEqual(args.media_type, "movie")
        self.assertFalse(args.dry_run)
        self.assertFalse(args.force)
        self.assertFalse(args.no_artwork)
        self.assertFalse(args.no_nfo)
        self.assertIsNone(args.api_key)

    def test_custom_flags(self):
        args = parse_args([
            "/media/tv",
            "--type", "tv",
            "--api-key", "my_secret_key",
            "--dry-run",
            "--force",
            "--no-artwork",
            "--verbose",
        ])
        self.assertEqual(args.path, "/media/tv")
        self.assertEqual(args.media_type, "tv")
        self.assertEqual(args.api_key, "my_secret_key")
        self.assertTrue(args.dry_run)
        self.assertTrue(args.force)
        self.assertTrue(args.no_artwork)
        self.assertTrue(args.verbose)


if __name__ == "__main__":
    unittest.main()

