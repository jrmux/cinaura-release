"""Generate Kodi/Cinaura-compatible NFO sidecar XML files from TMDb metadata."""

import logging
import os
from typing import Any, Dict, List, Optional
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from .utils import TMDB_IMAGE_BASE

logger = logging.getLogger("cinaura-metadata-helper")


def _add_text_element(parent: Element, tag: str, text: Optional[str]) -> None:
    """Add a text child element if the value is not None/empty."""
    if text:
        el = SubElement(parent, tag)
        el.text = str(text)


def _add_ratings(parent: Element, rating_value: float, votes: int, source: str = "themoviedb") -> None:
    """Add a <ratings> block."""
    ratings = SubElement(parent, "ratings")
    rating = SubElement(ratings, "rating", attrib={
        "name": source,
        "max": "10",
        "default": "true",
    })
    value = SubElement(rating, "value")
    value.text = f"{rating_value:.1f}"
    votes_el = SubElement(rating, "votes")
    votes_el.text = str(votes)


def _add_actors(parent: Element, cast: List[Dict[str, Any]], max_actors: int = 15) -> None:
    """Add <actor> elements for the cast."""
    for member in cast[:max_actors]:
        actor = SubElement(parent, "actor")
        _add_text_element(actor, "name", member.get("name"))
        _add_text_element(actor, "role", member.get("character"))
        order = member.get("order")
        if order is not None:
            _add_text_element(actor, "order", str(order))
        profile = member.get("profile_path")
        if profile:
            _add_text_element(actor, "thumb", f"{TMDB_IMAGE_BASE}w185{profile}")


def _add_thumb(parent: Element, path: Optional[str], aspect: str = "poster") -> None:
    """Add a <thumb> element for artwork."""
    if path:
        thumb = SubElement(parent, "thumb", attrib={"aspect": aspect})
        thumb.text = f"{TMDB_IMAGE_BASE}original{path}"


def _add_fanart(parent: Element, backdrop_path: Optional[str]) -> None:
    """Add a <fanart> block."""
    if backdrop_path:
        fanart = SubElement(parent, "fanart")
        thumb = SubElement(fanart, "thumb")
        thumb.text = f"{TMDB_IMAGE_BASE}original{backdrop_path}"


def _prettify(element: Element) -> str:
    """Return pretty-printed XML string."""
    rough_string = tostring(element, encoding="unicode")
    dom = minidom.parseString(rough_string)
    pretty = dom.toprettyxml(indent="    ", encoding=None)
    # Remove the XML declaration added by minidom (we add our own)
    lines = pretty.split("\n")
    if lines and lines[0].startswith("<?xml"):
        lines = lines[1:]
    content = "\n".join(lines).strip()
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>\n{content}\n'


def generate_movie_nfo(metadata: Dict[str, Any], output_path: str, dry_run: bool = False) -> str:
    """
    Generate a movie NFO file from TMDb metadata.

    Args:
        metadata: Full TMDb movie details dict.
        output_path: Path where the .nfo file will be written.
        dry_run: If True, generate but don't write the file.

    Returns:
        The generated XML string.
    """
    root = Element("movie")

    _add_text_element(root, "title", metadata.get("title"))
    _add_text_element(root, "originaltitle", metadata.get("original_title"))

    # Ratings
    vote_avg = metadata.get("vote_average", 0)
    vote_count = metadata.get("vote_count", 0)
    if vote_avg:
        _add_ratings(root, vote_avg, vote_count)

    # Collection / Set
    collection = metadata.get("belongs_to_collection")
    if collection:
        set_el = SubElement(root, "set", attrib={"name": collection.get("name", "")})
        _add_text_element(set_el, "overview", "")

    _add_text_element(root, "plot", metadata.get("overview"))
    _add_text_element(root, "tagline", metadata.get("tagline"))
    _add_text_element(root, "runtime", str(metadata.get("runtime", 0)))

    # Artwork references
    _add_thumb(root, metadata.get("poster_path"), "poster")
    _add_fanart(root, metadata.get("backdrop_path"))

    # Content rating
    _add_text_element(root, "mpaa", "")

    # Unique IDs
    tmdb_id = metadata.get("id")
    if tmdb_id:
        uid = SubElement(root, "uniqueid", attrib={"type": "tmdb", "default": "true"})
        uid.text = str(tmdb_id)

    # IMDb ID from external_ids or direct field
    imdb_id = metadata.get("imdb_id")
    if not imdb_id:
        ext = metadata.get("external_ids", {})
        imdb_id = ext.get("imdb_id")
    if imdb_id:
        uid_imdb = SubElement(root, "uniqueid", attrib={"type": "imdb"})
        uid_imdb.text = imdb_id

    # Genres
    for genre in metadata.get("genres", []):
        _add_text_element(root, "genre", genre.get("name"))

    # Countries
    for country in metadata.get("production_countries", []):
        _add_text_element(root, "country", country.get("name"))

    # Credits (directors and writers)
    credits_data = metadata.get("credits", {})
    crew = credits_data.get("crew", [])
    for member in crew:
        if member.get("job") == "Director":
            _add_text_element(root, "director", member.get("name"))
        elif member.get("department") == "Writing":
            _add_text_element(root, "credits", member.get("name"))

    # Release date
    release_date = metadata.get("release_date")
    _add_text_element(root, "premiered", release_date)
    if release_date:
        _add_text_element(root, "year", release_date[:4])

    # Cast
    cast = credits_data.get("cast", [])
    _add_actors(root, cast)

    xml_string = _prettify(root)

    if not dry_run:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_string)
        logger.info("  ✓ NFO written: %s", output_path)

    return xml_string


def generate_tvshow_nfo(metadata: Dict[str, Any], output_path: str, dry_run: bool = False) -> str:
    """
    Generate a tvshow.nfo file from TMDb TV show metadata.

    Args:
        metadata: Full TMDb TV show details dict.
        output_path: Path where the tvshow.nfo file will be written.
        dry_run: If True, generate but don't write the file.

    Returns:
        The generated XML string.
    """
    root = Element("tvshow")

    _add_text_element(root, "title", metadata.get("name"))
    _add_text_element(root, "originaltitle", metadata.get("original_name"))

    vote_avg = metadata.get("vote_average", 0)
    vote_count = metadata.get("vote_count", 0)
    if vote_avg:
        _add_ratings(root, vote_avg, vote_count)

    _add_text_element(root, "plot", metadata.get("overview"))
    _add_text_element(root, "status", metadata.get("status"))

    _add_thumb(root, metadata.get("poster_path"), "poster")
    _add_fanart(root, metadata.get("backdrop_path"))

    # Unique IDs
    tmdb_id = metadata.get("id")
    if tmdb_id:
        uid = SubElement(root, "uniqueid", attrib={"type": "tmdb", "default": "true"})
        uid.text = str(tmdb_id)

    ext = metadata.get("external_ids", {})
    imdb_id = ext.get("imdb_id")
    if imdb_id:
        uid_imdb = SubElement(root, "uniqueid", attrib={"type": "imdb"})
        uid_imdb.text = imdb_id

    # Genres
    for genre in metadata.get("genres", []):
        _add_text_element(root, "genre", genre.get("name"))

    # Premiere date
    first_air = metadata.get("first_air_date")
    _add_text_element(root, "premiered", first_air)
    if first_air:
        _add_text_element(root, "year", first_air[:4])

    # Seasons info
    _add_text_element(root, "season", str(metadata.get("number_of_seasons", 0)))
    _add_text_element(root, "episode", str(metadata.get("number_of_episodes", 0)))

    # Cast
    credits_data = metadata.get("credits", {})
    cast = credits_data.get("cast", [])
    _add_actors(root, cast)

    # Creators
    for creator in metadata.get("created_by", []):
        _add_text_element(root, "credits", creator.get("name"))

    xml_string = _prettify(root)

    if not dry_run:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_string)
        logger.info("  ✓ NFO written: %s", output_path)

    return xml_string


def generate_episode_nfo(
    show_metadata: Dict[str, Any],
    episode_metadata: Dict[str, Any],
    output_path: str,
    dry_run: bool = False,
) -> str:
    """
    Generate an episode NFO file.

    Args:
        show_metadata: Full TMDb TV show details.
        episode_metadata: TMDb episode details.
        output_path: Path where the .nfo file will be written.
        dry_run: If True, generate but don't write.

    Returns:
        The generated XML string.
    """
    root = Element("episodedetails")

    _add_text_element(root, "title", episode_metadata.get("name"))
    _add_text_element(root, "showtitle", show_metadata.get("name"))

    vote_avg = episode_metadata.get("vote_average", 0)
    vote_count = episode_metadata.get("vote_count", 0)
    if vote_avg:
        _add_ratings(root, vote_avg, vote_count)

    _add_text_element(root, "season", str(episode_metadata.get("season_number", 0)))
    _add_text_element(root, "episode", str(episode_metadata.get("episode_number", 0)))
    _add_text_element(root, "plot", episode_metadata.get("overview"))
    _add_text_element(root, "aired", episode_metadata.get("air_date"))
    _add_text_element(root, "runtime", str(episode_metadata.get("runtime") or 0))

    # Episode still image
    still_path = episode_metadata.get("still_path")
    if still_path:
        _add_thumb(root, still_path, "thumb")

    # TMDb unique IDs
    show_id = show_metadata.get("id")
    if show_id:
        uid = SubElement(root, "uniqueid", attrib={"type": "tmdb", "default": "true"})
        uid.text = str(episode_metadata.get("id", ""))

    # Episode cast/guest stars
    guest_stars = episode_metadata.get("guest_stars", [])
    _add_actors(root, guest_stars, max_actors=10)

    # Directors
    crew = episode_metadata.get("crew", [])
    for member in crew:
        if member.get("job") == "Director":
            _add_text_element(root, "director", member.get("name"))
        elif member.get("department") == "Writing":
            _add_text_element(root, "credits", member.get("name"))

    xml_string = _prettify(root)

    if not dry_run:
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(xml_string)
        logger.info("  ✓ NFO written: %s", output_path)

    return xml_string

