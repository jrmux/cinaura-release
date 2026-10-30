"""Shared utilities: logging, constants, and helpers."""

import logging
import os

# Supported video file extensions
VIDEO_EXTENSIONS = {
    ".mkv", ".mp4", ".avi", ".mov", ".wmv", ".flv", ".webm",
    ".m4v", ".mpg", ".mpeg", ".ts", ".m2ts", ".vob", ".iso",
    ".3gp", ".ogv", ".divx", ".asf", ".rm", ".rmvb",
}

# Supported image extensions for artwork
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}

# TMDb image base URL
TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/"

# Default image sizes
POSTER_SIZE = "w780"
BACKDROP_SIZE = "w1280"

# TMDb API base URL
TMDB_API_BASE = "https://api.themoviedb.org/3"


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure and return the application logger."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%H:%M:%S",
    )
    return logging.getLogger("cinaura-metadata-helper")


def is_video_file(path: str) -> bool:
    """Check if a file path has a recognized video extension."""
    _, ext = os.path.splitext(path)
    return ext.lower() in VIDEO_EXTENSIONS


def has_existing_nfo(video_path: str) -> bool:
    """Check if an NFO sidecar already exists for this video file."""
    nfo_path = os.path.splitext(video_path)[0] + ".nfo"
    return os.path.isfile(nfo_path)


def has_existing_artwork(directory: str) -> bool:
    """Check if poster artwork already exists in the directory."""
    for name in ("poster.jpg", "poster.png", "poster.webp"):
        if os.path.isfile(os.path.join(directory, name)):
            return True
    return False


def sanitize_filename(name: str) -> str:
    """Remove characters that are invalid in filenames."""
    invalid_chars = '<>:"/\\|?*'
    for ch in invalid_chars:
        name = name.replace(ch, "")
    return name.strip()

