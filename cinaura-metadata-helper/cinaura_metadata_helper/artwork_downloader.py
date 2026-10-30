"""Download poster and backdrop artwork from TMDb image CDN."""

import logging
import os
from typing import Any, Dict, Optional

import requests

from .utils import TMDB_IMAGE_BASE, POSTER_SIZE, BACKDROP_SIZE

logger = logging.getLogger("cinaura-metadata-helper")

# Reuse a session for connection pooling
_session = requests.Session()
_session.headers.update({"User-Agent": "cinaura-metadata-helper/1.0"})


def _download_image(url: str, output_path: str, dry_run: bool = False) -> bool:
    """
    Download an image from a URL to a local file.

    Args:
        url: Full image URL.
        output_path: Local path to save the image.
        dry_run: If True, log but don't download.

    Returns:
        True if the image was downloaded (or would be in dry-run), False on failure.
    """
    if dry_run:
        logger.info("  [DRY RUN] Would download: %s → %s", url, output_path)
        return True

    try:
        resp = _session.get(url, timeout=30, stream=True)
        resp.raise_for_status()

        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        with open(output_path, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                f.write(chunk)

        size_kb = os.path.getsize(output_path) / 1024
        logger.info("  ✓ Downloaded: %s (%.0f KB)", os.path.basename(output_path), size_kb)
        return True

    except requests.RequestException as e:
        logger.warning("  ✗ Failed to download %s: %s", url, e)
        return False


def download_poster(
    metadata: Dict[str, Any],
    output_dir: str,
    filename: str = "poster.jpg",
    size: str = POSTER_SIZE,
    dry_run: bool = False,
    force: bool = False,
) -> Optional[str]:
    """
    Download the poster image for a movie or TV show.

    Args:
        metadata: TMDb metadata dict (must contain 'poster_path').
        output_dir: Directory to save the poster in.
        filename: Name for the poster file.
        size: TMDb image size string (e.g., 'w780', 'original').
        dry_run: If True, log but don't download.
        force: If True, overwrite existing poster.

    Returns:
        Path to the downloaded poster, or None if unavailable/skipped.
    """
    poster_path = metadata.get("poster_path")
    if not poster_path:
        logger.debug("  No poster available")
        return None

    output_path = os.path.join(output_dir, filename)

    if os.path.isfile(output_path) and not force:
        logger.debug("  Poster already exists: %s", output_path)
        return output_path

    url = f"{TMDB_IMAGE_BASE}{size}{poster_path}"
    if _download_image(url, output_path, dry_run):
        return output_path
    return None


def download_backdrop(
    metadata: Dict[str, Any],
    output_dir: str,
    filename: str = "backdrop.jpg",
    size: str = BACKDROP_SIZE,
    dry_run: bool = False,
    force: bool = False,
) -> Optional[str]:
    """
    Download the backdrop/fanart image for a movie or TV show.

    Args:
        metadata: TMDb metadata dict (must contain 'backdrop_path').
        output_dir: Directory to save the backdrop in.
        filename: Name for the backdrop file.
        size: TMDb image size string (e.g., 'w1280', 'original').
        dry_run: If True, log but don't download.
        force: If True, overwrite existing backdrop.

    Returns:
        Path to the downloaded backdrop, or None if unavailable/skipped.
    """
    backdrop_path = metadata.get("backdrop_path")
    if not backdrop_path:
        logger.debug("  No backdrop available")
        return None

    output_path = os.path.join(output_dir, filename)

    if os.path.isfile(output_path) and not force:
        logger.debug("  Backdrop already exists: %s", output_path)
        return output_path

    url = f"{TMDB_IMAGE_BASE}{size}{backdrop_path}"
    if _download_image(url, output_path, dry_run):
        return output_path
    return None


def download_all_artwork(
    metadata: Dict[str, Any],
    output_dir: str,
    base_name: Optional[str] = None,
    is_dedicated: bool = True,
    dry_run: bool = False,
    force: bool = False,
) -> Dict[str, Optional[str]]:
    """
    Download both poster and backdrop for a title.
    Handles both dedicated folders (poster.jpg, backdrop.jpg)
    and shared/flat directories (<basename>-poster.jpg, <basename>-backdrop.jpg).

    Args:
        metadata: TMDb metadata dict.
        output_dir: Directory to save artwork in.
        base_name: Basename of the media file (for flat folders).
        is_dedicated: Whether the folder is dedicated to only this title.
        dry_run: If True, log but don't download.
        force: If True, overwrite existing artwork.

    Returns:
        Dict with 'poster' and 'backdrop' keys pointing to file paths (or None).
    """
    results: Dict[str, Optional[str]] = {"poster": None, "backdrop": None}

    if is_dedicated:
        results["poster"] = download_poster(
            metadata, output_dir, filename="poster.jpg", dry_run=dry_run, force=force
        )
        results["backdrop"] = download_backdrop(
            metadata, output_dir, filename="backdrop.jpg", dry_run=dry_run, force=force
        )
        if base_name:
            download_poster(
                metadata, output_dir, filename=f"{base_name}-poster.jpg", dry_run=dry_run, force=force
            )
            download_backdrop(
                metadata, output_dir, filename=f"{base_name}-backdrop.jpg", dry_run=dry_run, force=force
            )
    else:
        p_name = f"{base_name}-poster.jpg" if base_name else "poster.jpg"
        b_name = f"{base_name}-backdrop.jpg" if base_name else "backdrop.jpg"
        results["poster"] = download_poster(
            metadata, output_dir, filename=p_name, dry_run=dry_run, force=force
        )
        results["backdrop"] = download_backdrop(
            metadata, output_dir, filename=b_name, dry_run=dry_run, force=force
        )

    return results

