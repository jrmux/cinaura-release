"""Media file scanner and filename parser.

Scans directories for video files and extracts title, year, season, and
episode information from filenames and folder names.
"""

import os
import re
from dataclasses import dataclass, field
from typing import List, Optional

from .utils import is_video_file, VIDEO_EXTENSIONS


@dataclass
class MediaItem:
    """Represents a parsed media file."""
    filepath: str
    title: str
    year: Optional[int] = None
    media_type: str = "movie"  # "movie" or "tv"
    season: Optional[int] = None
    episode: Optional[int] = None
    show_title: Optional[str] = None
    # Populated after TMDb lookup
    tmdb_id: Optional[int] = None
    imdb_id: Optional[str] = None
    metadata: Optional[dict] = field(default=None, repr=False)

    @property
    def directory(self) -> str:
        return os.path.dirname(self.filepath)

    @property
    def basename(self) -> str:
        return os.path.splitext(os.path.basename(self.filepath))[0]


# Patterns for extracting season/episode
_SE_PATTERNS = [
    # S01E01, S1E1, s01e01
    re.compile(r"[Ss](\d{1,2})\s*[Ee](\d{1,3})"),
    # 1x01, 01x01
    re.compile(r"(\d{1,2})[Xx](\d{1,3})"),
    # Season 1 Episode 1
    re.compile(r"[Ss]eason\s*(\d{1,2})\s*[Ee]pisode\s*(\d{1,3})", re.IGNORECASE),
]

# Patterns for extracting year
# Release years are realistic: 1888 to current/near-future (~2035)
_BRACKETED_YEAR = re.compile(r"[\(\[]((?:18[8-9]\d|19\d{2}|20[0-2]\d|203[0-5]))[\)\]]")
_STANDALONE_YEAR = re.compile(
    r"(?:^|[._\s\-\(\[])((?:18[8-9]\d|19\d{2}|20[0-2]\d|203[0-5]))(?=[._\s\-\)\]]|$)"
)

# Junk tokens to strip from titles
_JUNK_TOKENS = re.compile(
    r"\b("
    r"720p|1080p|2160p|4[Kk]|UHD|"
    r"[Hh]\.?264|[Hh]\.?265|[Hh][Ee][Vv][Cc]|[Xx]264|[Xx]265|"
    r"[Bb][Ll][Uu][Rr][Aa][Yy]|[Bb][Dd][Rr][Ii][Pp]|[Ww][Ee][Bb]-?[DdRr][LlIi][Pp]?|"
    r"[Hh][Dd][Rr](?:10)?|[Dd][Vv]|[Dd]olby.?[Vv]ision|"
    r"[Rr][Ee][Mm][Uu][Xx]|[Pp][Rr][Oo][Pp][Ee][Rr]|"
    r"[Dd][Tt][Ss](?:-[Hh][Dd])?(?:-[Mm][Aa])?|"
    r"[Aa][Aa][Cc]|[Ff][Ll][Aa][Cc]|[Aa][Cc]3|[Ee][Aa][Cc]3|"
    r"[Aa][Tt][Mm][Oo][Ss]|[Tt][Rr][Uu][Ee][Hh][Dd]|"
    r"[Mm][Uu][Ll][Tt][Ii]|[Dd][Uu][Aa][Ll]|"
    r"[Nn][Ff]|[Aa][Mm][Zz][Nn]|[Hh][Mm][Aa][Xx]|[Dd][Ss][Nn][Pp]|[Aa][Pp][Tt][Vv]|"
    r"REPACK|PROPER|INTERNAL|LIMITED|EXTENDED|UNRATED|"
    r"DIRECTORS.?CUT|THEATRICAL|IMAX"
    r")\b",
    re.IGNORECASE,
)

# Characters to normalize in titles
_SEPARATORS = re.compile(r"[._]")


def _clean_title(raw: str) -> str:
    """Clean a raw filename/foldername into a human-readable title."""
    # Replace dots and underscores with spaces
    cleaned = _SEPARATORS.sub(" ", raw)
    # Remove junk tokens
    cleaned = _JUNK_TOKENS.sub("", cleaned)
    # Remove any leftover brackets/parentheses content that's now empty
    cleaned = re.sub(r"[\(\[]\s*[\)\]]", "", cleaned)
    # Collapse whitespace
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    # Remove trailing hyphens or dashes
    cleaned = cleaned.rstrip("- ")
    return cleaned


def _extract_year_and_title(text: str) -> tuple:
    """Extract (title_part, year) from a string. If year is found, returns the title part before it."""
    # First priority: explicitly bracketed year, e.g. (2010) or [2010]
    bracketed = list(_BRACKETED_YEAR.finditer(text))
    if bracketed:
        last = bracketed[-1]
        title_cand = text[: last.start()]
        if len(_clean_title(title_cand)) >= 2:
            return title_cand, int(last.group(1))

    # Second priority: standalone year separated by word boundaries/delimiters
    standalone = list(_STANDALONE_YEAR.finditer(text))
    if standalone:
        for match in reversed(standalone):
            year_val = int(match.group(1))
            g_start = match.start(1)
            title_cand = text[:g_start]
            if len(_clean_title(title_cand)) >= 2:
                return title_cand, year_val

    return text, None


def parse_movie_filename(filepath: str) -> MediaItem:
    """Parse a movie video file path into a MediaItem."""
    basename = os.path.splitext(os.path.basename(filepath))[0]
    dirname = os.path.basename(os.path.dirname(filepath))

    # Try to get year from basename first
    title_part, year = _extract_year_and_title(basename)
    if year is None:
        # Try the parent directory name
        dir_title_part, dir_year = _extract_year_and_title(dirname)
        if dir_year is not None:
            year = dir_year
            title_part = dir_title_part

    title = _clean_title(title_part)

    # If title is empty or too short, try the directory name
    if len(title) < 2:
        title = _clean_title(dirname.split("(")[0] if "(" in dirname else dirname)

    return MediaItem(
        filepath=filepath,
        title=title,
        year=year,
        media_type="movie",
    )


def parse_tv_filename(filepath: str) -> MediaItem:
    """Parse a TV show video file path into a MediaItem."""
    basename = os.path.splitext(os.path.basename(filepath))[0]

    season = None
    episode = None

    # Extract season/episode
    for pattern in _SE_PATTERNS:
        match = pattern.search(basename)
        if match:
            season = int(match.group(1))
            episode = int(match.group(2))
            title_part = basename[: match.start()]
            break
    else:
        title_part = basename

    title = _clean_title(title_part)

    # For TV shows, try to get the show title from parent directories
    # Common structures:
    #   Show Name/Season 01/Show.Name.S01E01.mkv
    #   Show Name/Show.Name.S01E01.mkv
    parts = filepath.replace("\\", "/").split("/")
    show_title = title  # default to parsed title

    # Walk up looking for a "Season" folder
    for i, part in enumerate(parts):
        if re.match(r"[Ss]eason\s*\d+", part) or re.match(r"[Ss]\d{1,2}$", part):
            if i > 0:
                show_title = _clean_title(parts[i - 1])
            break

    # Extract year from show title if present
    clean_show_title, year = _extract_year_and_title(show_title)
    show_title = _clean_title(clean_show_title)

    return MediaItem(
        filepath=filepath,
        title=show_title,
        year=year,
        media_type="tv",
        season=season,
        episode=episode,
        show_title=show_title,
    )


def scan_directory(
    root_path: str,
    media_type: str = "movie",
    skip_existing: bool = True,
) -> List[MediaItem]:
    """
    Recursively scan a directory for video files and parse them.

    Args:
        root_path: Root directory to scan.
        media_type: Either "movie" or "tv".
        skip_existing: If True, skip files that already have an NFO sidecar.

    Returns:
        List of parsed MediaItem objects.
    """
    items = []
    root_path = os.path.abspath(root_path)

    if not os.path.isdir(root_path):
        raise FileNotFoundError(f"Directory not found: {root_path}")

    for dirpath, _dirnames, filenames in os.walk(root_path):
        for filename in sorted(filenames):
            filepath = os.path.join(dirpath, filename)
            if not is_video_file(filepath):
                continue

            # Skip sample files
            if "sample" in filename.lower() and os.path.getsize(filepath) < 100_000_000:
                continue

            # Skip extras/trailers/featurettes
            lower_name = filename.lower()
            if any(
                tag in lower_name
                for tag in ("-trailer", "-featurette", "-behindthescenes", "-scene", "-short")
            ):
                continue

            if skip_existing:
                nfo_path = os.path.splitext(filepath)[0] + ".nfo"
                if os.path.isfile(nfo_path):
                    continue

            if media_type == "tv":
                item = parse_tv_filename(filepath)
            else:
                item = parse_movie_filename(filepath)

            items.append(item)

    return items

