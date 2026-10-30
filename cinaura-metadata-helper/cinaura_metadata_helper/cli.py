"""Main CLI entry point for cinaura-metadata-helper."""

import argparse
import os
import sys
from typing import Dict, Optional, Set

from . import __version__
from .artwork_downloader import download_all_artwork
from .nfo_generator import generate_episode_nfo, generate_movie_nfo, generate_tvshow_nfo
from .scanner import MediaItem, scan_directory
from .tmdb_client import TMDbClient, TMDbError
from .utils import setup_logging


def parse_args(argv=None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="cinaura-metadata-helper",
        description=(
            "Fetch TMDb metadata, generate NFO sidecar files, and download "
            "poster/backdrop artwork for your media library — making Cinaura "
            "display rich metadata automatically."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""\
Examples:
  # Scan a movie library
  %(prog)s /mnt/media/Movies --api-key YOUR_KEY

  # Scan TV shows
  %(prog)s /mnt/media/TVShows --type tv --api-key YOUR_KEY

  # Preview without writing anything
  %(prog)s /mnt/media/Movies --dry-run --api-key YOUR_KEY

  # Force re-fetch everything (overwrite existing)
  %(prog)s /mnt/media/Movies --force --api-key YOUR_KEY

  # Use environment variable for API key
  export TMDB_API_KEY=your_key_here
  %(prog)s /mnt/media/Movies

Get a free TMDb API key: https://www.themoviedb.org/settings/api
""",
    )

    parser.add_argument(
        "path",
        help="Root directory of your media library to scan.",
    )
    parser.add_argument(
        "--type", "-t",
        choices=["movie", "tv"],
        default="movie",
        dest="media_type",
        help="Type of media to scan for (default: movie).",
    )
    parser.add_argument(
        "--api-key", "-k",
        default=None,
        help="TMDb API key (v3). Can also be set via TMDB_API_KEY env variable.",
    )
    parser.add_argument(
        "--dry-run", "-n",
        action="store_true",
        help="Preview what would be created without writing any files.",
    )
    parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Overwrite existing NFO files and artwork.",
    )
    parser.add_argument(
        "--no-artwork",
        action="store_true",
        help="Skip downloading poster and backdrop images.",
    )
    parser.add_argument(
        "--no-nfo",
        action="store_true",
        help="Skip generating NFO sidecar files (download artwork only).",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose/debug logging.",
    )
    parser.add_argument(
        "--version", "-V",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    return parser.parse_args(argv)


def _process_movie(
    item: MediaItem,
    client: TMDbClient,
    dry_run: bool,
    force: bool,
    no_artwork: bool,
    no_nfo: bool,
) -> bool:
    """Process a single movie item. Returns True on success."""
    logger = setup_logging()
    logger.info("Processing: %s (%s)", item.title, item.year or "no year")

    metadata = client.find_best_movie_match(item.title, item.year)
    if not metadata:
        return False

    item.tmdb_id = metadata.get("id")
    item.metadata = metadata

    # Generate NFO
    if not no_nfo:
        nfo_path = os.path.splitext(item.filepath)[0] + ".nfo"
        if force or not os.path.isfile(nfo_path):
            generate_movie_nfo(metadata, nfo_path, dry_run=dry_run)

    # Download artwork
    if not no_artwork:
        try:
            from .utils import is_video_file
            sibling_videos = [
                f for f in os.listdir(item.directory)
                if is_video_file(os.path.join(item.directory, f))
            ]
            is_dedicated = len(sibling_videos) <= 1
        except OSError:
            is_dedicated = True

        download_all_artwork(
            metadata,
            item.directory,
            base_name=item.basename,
            is_dedicated=is_dedicated,
            dry_run=dry_run,
            force=force,
        )

    return True


def _process_tv_show(
    items: list,
    client: TMDbClient,
    dry_run: bool,
    force: bool,
    no_artwork: bool,
    no_nfo: bool,
) -> int:
    """
    Process a group of TV show episodes (same show).
    Returns the count of successfully processed episodes.
    """
    logger = setup_logging()
    if not items:
        return 0

    first = items[0]
    show_title = first.show_title or first.title
    logger.info("Processing TV show: %s (%s)", show_title, first.year or "no year")

    # Look up the show once
    show_metadata = client.find_best_tv_match(show_title, first.year)
    if not show_metadata:
        return 0

    show_id = show_metadata.get("id")

    # Generate tvshow.nfo in the show's root directory
    # Find the common root among all episode paths
    dirs = sorted(set(os.path.dirname(i.filepath) for i in items))
    if dirs:
        # Try to find the show root (parent of Season folders)
        show_root = dirs[0]
        for d in dirs:
            # Walk up to find common parent
            common = os.path.commonpath([show_root, d])
            show_root = common

        if not no_nfo:
            tvshow_nfo_path = os.path.join(show_root, "tvshow.nfo")
            if force or not os.path.isfile(tvshow_nfo_path):
                generate_tvshow_nfo(show_metadata, tvshow_nfo_path, dry_run=dry_run)

        # Download show-level artwork to the root
        if not no_artwork:
            download_all_artwork(show_metadata, show_root, dry_run=dry_run, force=force)

    # Process individual episodes
    success_count = 0
    # Cache season data to avoid redundant API calls
    season_cache: Dict[int, dict] = {}

    for item in items:
        if item.season is None or item.episode is None:
            logger.warning("  Skipping (no season/episode parsed): %s", item.filepath)
            continue

        logger.info("  Episode: S%02dE%02d", item.season, item.episode)

        try:
            # Get season details (cached)
            if item.season not in season_cache:
                season_cache[item.season] = client.get_tv_season_details(show_id, item.season)

            season_data = season_cache[item.season]
            episodes = season_data.get("episodes", [])

            # Find the matching episode
            ep_data = None
            for ep in episodes:
                if ep.get("episode_number") == item.episode:
                    ep_data = ep
                    break

            if not ep_data:
                logger.warning("    Episode S%02dE%02d not found on TMDb", item.season, item.episode)
                continue

            # Generate episode NFO
            if not no_nfo:
                nfo_path = os.path.splitext(item.filepath)[0] + ".nfo"
                if force or not os.path.isfile(nfo_path):
                    generate_episode_nfo(show_metadata, ep_data, nfo_path, dry_run=dry_run)

            success_count += 1

        except Exception as e:
            logger.warning("    Error processing S%02dE%02d: %s", item.season, item.episode, e)

    return success_count


def main(argv=None) -> int:
    """Main entry point."""
    args = parse_args(argv)
    logger = setup_logging(args.verbose)

    # Resolve API key
    api_key = args.api_key or os.environ.get("TMDB_API_KEY")
    if not api_key:
        logger.error(
            "TMDb API key required. Provide via --api-key or TMDB_API_KEY env variable.\n"
            "Get a free key at: https://www.themoviedb.org/settings/api"
        )
        return 1

    # Validate path
    if not os.path.isdir(args.path):
        logger.error("Directory not found: %s", args.path)
        return 1

    # Initialize TMDb client
    try:
        client = TMDbClient(api_key)
    except TMDbError as e:
        logger.error("TMDb initialization failed: %s", e)
        return 1

    logger.info("=" * 60)
    logger.info("Cinaura Metadata Helper v%s", __version__)
    logger.info("=" * 60)
    logger.info("Scanning: %s", os.path.abspath(args.path))
    logger.info("Type: %s", args.media_type)
    if args.dry_run:
        logger.info("Mode: DRY RUN (no files will be written)")
    if args.force:
        logger.info("Mode: FORCE (overwriting existing files)")
    logger.info("-" * 60)

    # Scan directory
    items = scan_directory(
        args.path,
        media_type=args.media_type,
        skip_existing=not args.force,
    )

    if not items:
        logger.info("No media files found that need metadata.")
        logger.info("(Files with existing .nfo sidecars are skipped. Use --force to re-fetch.)")
        return 0

    logger.info("Found %d media file(s) to process", len(items))
    logger.info("-" * 60)

    success = 0
    failed = 0

    if args.media_type == "movie":
        for item in items:
            try:
                if _process_movie(item, client, args.dry_run, args.force, args.no_artwork, args.no_nfo):
                    success += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error("Error processing %s: %s", item.title, e)
                failed += 1

    elif args.media_type == "tv":
        # Group episodes by show title
        shows: Dict[str, list] = {}
        for item in items:
            key = (item.show_title or item.title).lower()
            shows.setdefault(key, []).append(item)

        for show_key, episodes in shows.items():
            try:
                count = _process_tv_show(
                    episodes, client, args.dry_run, args.force, args.no_artwork, args.no_nfo
                )
                success += count
                failed += len(episodes) - count
            except Exception as e:
                logger.error("Error processing show '%s': %s", show_key, e)
                failed += len(episodes)

    # Summary
    logger.info("=" * 60)
    logger.info("DONE  ✓ %d succeeded  ✗ %d failed  (of %d total)", success, failed, len(items))
    if args.dry_run:
        logger.info("(Dry run — no files were written)")
    logger.info("=" * 60)

    return 0 if failed == 0 else 2


if __name__ == "__main__":
    sys.exit(main())

