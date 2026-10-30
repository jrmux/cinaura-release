"""Tests for the media file scanner and filename parser."""

import os
import sys
import unittest

# Ensure the package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cinaura_metadata_helper.scanner import parse_movie_filename, parse_tv_filename


class TestMovieParser(unittest.TestCase):
    """Test movie filename parsing."""

    def test_basic_title_with_year(self):
        item = parse_movie_filename("/movies/Inception (2010)/Inception (2010).mkv")
        self.assertEqual(item.title, "Inception")
        self.assertEqual(item.year, 2010)
        self.assertEqual(item.media_type, "movie")

    def test_title_with_dots_and_year(self):
        item = parse_movie_filename("/movies/The.Dark.Knight.2008.1080p.BluRay.mkv")
        self.assertEqual(item.title, "The Dark Knight")
        self.assertEqual(item.year, 2008)

    def test_title_with_quality_tags(self):
        item = parse_movie_filename("/movies/Interstellar.2014.2160p.UHD.HDR.x265.mkv")
        self.assertEqual(item.title, "Interstellar")
        self.assertEqual(item.year, 2014)

    def test_title_with_brackets_year(self):
        item = parse_movie_filename("/movies/Avatar [2009]/Avatar [2009].mp4")
        self.assertEqual(item.title, "Avatar")
        self.assertEqual(item.year, 2009)

    def test_title_no_year(self):
        item = parse_movie_filename("/movies/SomeObscureFilm/SomeObscureFilm.avi")
        self.assertEqual(item.title, "SomeObscureFilm")
        self.assertIsNone(item.year)

    def test_title_with_underscores(self):
        item = parse_movie_filename("/movies/The_Matrix_1999.mkv")
        self.assertEqual(item.title, "The Matrix")
        self.assertEqual(item.year, 1999)

    def test_complex_release_name(self):
        item = parse_movie_filename(
            "/movies/Blade.Runner.2049.2017.1080p.BluRay.REMUX.AVC.DTS-HD.MA.7.1.mkv"
        )
        self.assertEqual(item.title, "Blade Runner 2049")
        self.assertEqual(item.year, 2017)


class TestTVParser(unittest.TestCase):
    """Test TV show filename parsing."""

    def test_standard_sxxexx(self):
        item = parse_tv_filename(
            "/tvshows/Breaking Bad/Season 01/Breaking.Bad.S01E01.720p.mkv"
        )
        self.assertEqual(item.show_title, "Breaking Bad")
        self.assertEqual(item.season, 1)
        self.assertEqual(item.episode, 1)
        self.assertEqual(item.media_type, "tv")

    def test_lowercase_sxxexx(self):
        item = parse_tv_filename("/tvshows/Dexter/Season 1/dexter.s01e05.mkv")
        self.assertEqual(item.season, 1)
        self.assertEqual(item.episode, 5)

    def test_numberx_format(self):
        item = parse_tv_filename("/tvshows/Friends/Season 03/Friends.3x14.mkv")
        self.assertEqual(item.season, 3)
        self.assertEqual(item.episode, 14)

    def test_show_title_from_parent_dir(self):
        item = parse_tv_filename(
            "/tvshows/Game of Thrones/Season 08/Game.of.Thrones.S08E06.mkv"
        )
        self.assertEqual(item.show_title, "Game of Thrones")
        self.assertEqual(item.season, 8)
        self.assertEqual(item.episode, 6)

    def test_show_no_season_folder(self):
        item = parse_tv_filename("/tvshows/The Office/The.Office.S02E03.mkv")
        self.assertEqual(item.season, 2)
        self.assertEqual(item.episode, 3)


if __name__ == "__main__":
    unittest.main()

