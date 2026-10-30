"""Tests for NFO XML generation."""

import os
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from cinaura_metadata_helper.nfo_generator import (
    generate_episode_nfo,
    generate_movie_nfo,
    generate_tvshow_nfo,
)


class TestNfoGenerator(unittest.TestCase):
    """Test generating valid XML NFO files."""

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_generate_movie_nfo(self):
        metadata = {
            "id": 27205,
            "title": "Inception",
            "original_title": "Inception",
            "overview": "A thief who steals corporate secrets...",
            "tagline": "Your mind is the scene of the crime.",
            "runtime": 148,
            "release_date": "2010-07-15",
            "vote_average": 8.4,
            "vote_count": 35000,
            "poster_path": "/edv5CZvWj09upOsy2Y6IwDhK8bt.jpg",
            "backdrop_path": "/s3TBrRGB1ivVW5ICX13JihZiZGM.jpg",
            "genres": [{"name": "Action"}, {"name": "Sci-Fi"}],
            "production_countries": [{"name": "United States"}],
            "credits": {
                "crew": [{"job": "Director", "name": "Christopher Nolan"}],
                "cast": [
                    {"name": "Leonardo DiCaprio", "character": "Cobb", "order": 0}
                ],
            },
            "external_ids": {"imdb_id": "tt1375666"},
        }

        output_path = os.path.join(self.temp_dir.name, "Inception (2010).nfo")
        xml_content = generate_movie_nfo(metadata, output_path, dry_run=False)

        self.assertTrue(os.path.isfile(output_path))

        # Parse and verify XML structure
        root = ET.fromstring(xml_content)
        self.assertEqual(root.tag, "movie")
        self.assertEqual(root.find("title").text, "Inception")
        self.assertEqual(root.find("year").text, "2010")

        # Verify TMDb ID
        tmdb_el = root.find("./uniqueid[@type='tmdb']")
        self.assertIsNotNone(tmdb_el)
        self.assertEqual(tmdb_el.text, "27205")

        # Verify IMDb ID
        imdb_el = root.find("./uniqueid[@type='imdb']")
        self.assertIsNotNone(imdb_el)
        self.assertEqual(imdb_el.text, "tt1375666")

        # Verify director & actor
        self.assertEqual(root.find("director").text, "Christopher Nolan")
        actor = root.find("actor")
        self.assertEqual(actor.find("name").text, "Leonardo DiCaprio")
        self.assertEqual(actor.find("role").text, "Cobb")

    def test_generate_tvshow_nfo(self):
        metadata = {
            "id": 1396,
            "name": "Breaking Bad",
            "original_name": "Breaking Bad",
            "overview": "A chemistry teacher diagnosed with cancer...",
            "status": "Ended",
            "first_air_date": "2008-01-20",
            "vote_average": 8.9,
            "vote_count": 13000,
            "poster_path": "/ggFHVNu6YYI5L9pCfOacjizRGt.jpg",
            "number_of_seasons": 5,
            "number_of_episodes": 62,
            "genres": [{"name": "Drama"}],
            "credits": {"cast": [{"name": "Bryan Cranston", "character": "Walter White"}]},
            "external_ids": {"imdb_id": "tt0903747"},
        }

        output_path = os.path.join(self.temp_dir.name, "tvshow.nfo")
        xml_content = generate_tvshow_nfo(metadata, output_path, dry_run=False)

        self.assertTrue(os.path.isfile(output_path))
        root = ET.fromstring(xml_content)
        self.assertEqual(root.tag, "tvshow")
        self.assertEqual(root.find("title").text, "Breaking Bad")
        self.assertEqual(root.find("year").text, "2008")
        self.assertEqual(root.find("./uniqueid[@type='tmdb']").text, "1396")

    def test_generate_episode_nfo(self):
        show_meta = {"id": 1396, "name": "Breaking Bad"}
        ep_meta = {
            "id": 62085,
            "name": "Pilot",
            "season_number": 1,
            "episode_number": 1,
            "overview": "When an unassuming chemistry teacher...",
            "air_date": "2008-01-20",
            "runtime": 58,
            "vote_average": 8.3,
            "vote_count": 120,
            "still_path": "/ydlY3iPbg5GvNCv1UMu0A1DvmEG.jpg",
            "guest_stars": [],
            "crew": [{"job": "Director", "name": "Vince Gilligan"}],
        }

        output_path = os.path.join(self.temp_dir.name, "Breaking.Bad.S01E01.nfo")
        xml_content = generate_episode_nfo(show_meta, ep_meta, output_path, dry_run=False)

        self.assertTrue(os.path.isfile(output_path))
        root = ET.fromstring(xml_content)
        self.assertEqual(root.tag, "episodedetails")
        self.assertEqual(root.find("title").text, "Pilot")
        self.assertEqual(root.find("showtitle").text, "Breaking Bad")
        self.assertEqual(root.find("season").text, "1")
        self.assertEqual(root.find("episode").text, "1")
        self.assertEqual(root.find("director").text, "Vince Gilligan")


if __name__ == "__main__":
    unittest.main()

