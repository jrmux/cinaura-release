"""TMDb API v3 client for searching and fetching movie/TV metadata."""

import logging
import time
from typing import Any, Dict, List, Optional

import requests

from .utils import TMDB_API_BASE

logger = logging.getLogger("cinaura-metadata-helper")

# Rate limiting: max requests per second
_MAX_RPS = 35
_MIN_INTERVAL = 1.0 / _MAX_RPS
_last_request_time = 0.0


class TMDbError(Exception):
    """Raised when TMDb API returns an error."""
    pass


class TMDbClient:
    """Client for The Movie Database (TMDb) API v3."""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.session = requests.Session()
        self.session.params = {"api_key": api_key}  # type: ignore[assignment]
        self.session.headers.update({
            "Accept": "application/json",
            "User-Agent": "cinaura-metadata-helper/1.0",
        })
        self._verify_key()

    def _verify_key(self) -> None:
        """Verify the API key is valid."""
        try:
            resp = self._get("/configuration")
            if "images" not in resp:
                raise TMDbError("Invalid API key or unexpected response")
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code == 401:
                raise TMDbError(
                    "Invalid TMDb API key. Get a free key at: "
                    "https://www.themoviedb.org/settings/api"
                ) from e
            raise

    def _get(self, endpoint: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Make a rate-limited GET request to TMDb."""
        global _last_request_time
        now = time.monotonic()
        elapsed = now - _last_request_time
        if elapsed < _MIN_INTERVAL:
            time.sleep(_MIN_INTERVAL - elapsed)
        _last_request_time = time.monotonic()

        url = f"{TMDB_API_BASE}{endpoint}"
        resp = self.session.get(url, params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    # ── Search ────────────────────────────────────────────────────────────

    def search_movie(
        self, title: str, year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for movies by title, optionally filtered by year."""
        params: Dict[str, Any] = {"query": title, "include_adult": False}
        if year:
            params["year"] = year
        data = self._get("/search/movie", params)
        results = data.get("results", [])

        # If year-filtered search returned nothing, retry without year
        if not results and year:
            params.pop("year")
            data = self._get("/search/movie", params)
            results = data.get("results", [])

        return results

    def search_tv(
        self, title: str, year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Search for TV shows by title, optionally filtered by first air year."""
        params: Dict[str, Any] = {"query": title, "include_adult": False}
        if year:
            params["first_air_date_year"] = year
        data = self._get("/search/tv", params)
        results = data.get("results", [])

        # Retry without year filter if no results
        if not results and year:
            params.pop("first_air_date_year")
            data = self._get("/search/tv", params)
            results = data.get("results", [])

        return results

    # ── Details ───────────────────────────────────────────────────────────

    def get_movie_details(self, movie_id: int) -> Dict[str, Any]:
        """Fetch full movie details including credits and external IDs."""
        return self._get(
            f"/movie/{movie_id}",
            params={"append_to_response": "credits,external_ids,images"},
        )

    def get_tv_details(self, tv_id: int) -> Dict[str, Any]:
        """Fetch full TV show details including credits and external IDs."""
        return self._get(
            f"/tv/{tv_id}",
            params={"append_to_response": "credits,external_ids,images"},
        )

    def get_tv_season_details(self, tv_id: int, season_number: int) -> Dict[str, Any]:
        """Fetch season details including episode list."""
        return self._get(
            f"/tv/{tv_id}/season/{season_number}",
            params={"append_to_response": "credits,images"},
        )

    def get_tv_episode_details(
        self, tv_id: int, season_number: int, episode_number: int
    ) -> Dict[str, Any]:
        """Fetch individual episode details."""
        return self._get(
            f"/tv/{tv_id}/season/{season_number}/episode/{episode_number}",
            params={"append_to_response": "credits,images"},
        )

    # ── Images ────────────────────────────────────────────────────────────

    def get_movie_images(self, movie_id: int) -> Dict[str, Any]:
        """Fetch all images for a movie (posters, backdrops, logos)."""
        return self._get(f"/movie/{movie_id}/images")

    def get_tv_images(self, tv_id: int) -> Dict[str, Any]:
        """Fetch all images for a TV show."""
        return self._get(f"/tv/{tv_id}/images")

    # ── High-level helpers ────────────────────────────────────────────────

    def find_best_movie_match(
        self, title: str, year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Search for a movie and return the best match with full details."""
        results = self.search_movie(title, year)
        if not results:
            logger.warning("No TMDb results for movie: %s (%s)", title, year or "no year")
            return None

        # Pick the best result: prefer exact title + year match
        best = results[0]
        for r in results:
            r_title = (r.get("title") or "").lower()
            r_year = (r.get("release_date") or "")[:4]
            if r_title == title.lower():
                if year and r_year == str(year):
                    best = r
                    break
                elif not year:
                    best = r
                    break

        movie_id = best["id"]
        logger.info(
            "  → Matched: %s (%s) [TMDb ID: %d]",
            best.get("title"),
            (best.get("release_date") or "")[:4],
            movie_id,
        )
        return self.get_movie_details(movie_id)

    def find_best_tv_match(
        self, title: str, year: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Search for a TV show and return the best match with full details."""
        results = self.search_tv(title, year)
        if not results:
            logger.warning("No TMDb results for TV show: %s (%s)", title, year or "no year")
            return None

        best = results[0]
        for r in results:
            r_title = (r.get("name") or "").lower()
            r_year = (r.get("first_air_date") or "")[:4]
            if r_title == title.lower():
                if year and r_year == str(year):
                    best = r
                    break
                elif not year:
                    best = r
                    break

        tv_id = best["id"]
        logger.info(
            "  → Matched: %s (%s) [TMDb ID: %d]",
            best.get("name"),
            (best.get("first_air_date") or "")[:4],
            tv_id,
        )
        return self.get_tv_details(tv_id)

