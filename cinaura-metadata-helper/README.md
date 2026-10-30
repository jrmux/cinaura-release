# Cinaura Metadata Helper

A companion CLI tool for [Cinaura](https://cinaura.tv) that fetches free metadata from [TMDb](https://www.themoviedb.org), generates `.nfo` sidecar files, and downloads poster & backdrop artwork — so Cinaura displays rich, accurate metadata for every title in your library automatically.

> **Why?** Cinaura fetches metadata from TMDb on its own, but sometimes files with unusual names, foreign titles, or ambiguous matches get stuck with wrong or missing data. This tool pre-generates the local metadata files that Cinaura prioritizes, giving you full control.

---

## Features

- 🎬 **Movie & TV show support** — handles both libraries with proper folder structures
- 🔍 **Smart filename parsing** — extracts title, year, season, and episode from common naming patterns
- 📝 **NFO generation** — creates Kodi/Cinaura-compatible XML sidecar files with TMDb IDs, plot, cast, genres, ratings
- 🖼️ **Artwork download** — fetches high-quality poster (780px) and backdrop (1280px) images
- 🏃 **Dry run mode** — preview what would be created without writing anything
- ⚡ **Skip existing** — won't overwrite metadata you've already curated (use `--force` to override)
- 🔄 **Force refresh** — re-fetch everything when you need to update

---

## Requirements

- **Python 3.7+**
- A **free TMDb API key** → [Get one here](https://www.themoviedb.org/settings/api)

---

## Installation

```bash
# Clone the repo (if you haven't)
git clone https://github.com/jrmux/cinaura-release.git
cd cinaura-release/cinaura-metadata-helper

# Install dependencies
pip install -r requirements.txt
```

---

## Usage

### Set your TMDb API key

```bash
# Option 1: Environment variable (recommended)
export TMDB_API_KEY=your_api_key_here

# Option 2: Pass it directly
python -m cinaura_metadata_helper /path/to/movies --api-key YOUR_KEY
```

### Scan a movie library

```bash
python -m cinaura_metadata_helper /path/to/Movies
```

### Scan a TV show library

```bash
python -m cinaura_metadata_helper /path/to/TVShows --type tv
```

### Preview without writing (dry run)

```bash
python -m cinaura_metadata_helper /path/to/Movies --dry-run
```

### Force re-fetch everything

```bash
python -m cinaura_metadata_helper /path/to/Movies --force
```

### Download artwork only (no NFO files)

```bash
python -m cinaura_metadata_helper /path/to/Movies --no-nfo
```

### Generate NFOs only (no artwork)

```bash
python -m cinaura_metadata_helper /path/to/Movies --no-artwork
```

---

## What it creates

### For movies

```
Movies/
├── Inception (2010)/
│   ├── Inception (2010).mkv          ← your existing file
│   ├── Inception (2010).nfo          ← NEW: metadata sidecar
│   ├── poster.jpg                     ← NEW: cover image (780px)
│   └── backdrop.jpg                   ← NEW: background art (1280px)
```

### For TV shows

```
TV Shows/
├── Breaking Bad/
│   ├── tvshow.nfo                     ← NEW: show-level metadata
│   ├── poster.jpg                     ← NEW: show poster
│   ├── backdrop.jpg                   ← NEW: show backdrop
│   ├── Season 01/
│   │   ├── Breaking.Bad.S01E01.mkv
│   │   ├── Breaking.Bad.S01E01.nfo   ← NEW: episode metadata
│   │   ├── Breaking.Bad.S01E02.mkv
│   │   └── Breaking.Bad.S01E02.nfo
```

---

## Recommended file naming

For best results, name your files following these patterns:

### Movies
```
Movie Title (Year).ext
```
Examples:
- `Inception (2010).mkv`
- `The Dark Knight (2008).mp4`
- `Blade Runner 2049 (2017).mkv`

### TV Shows
```
Show Name/Season XX/Show.Name.SxxExx.ext
```
Examples:
- `Breaking Bad/Season 01/Breaking.Bad.S01E01.mkv`
- `Game of Thrones/Season 08/Game.of.Thrones.S08E06.mkv`

---

## CLI options

| Flag | Description |
|------|-------------|
| `path` | Root directory of your media library |
| `--type`, `-t` | Media type: `movie` (default) or `tv` |
| `--api-key`, `-k` | TMDb API key (or use `TMDB_API_KEY` env var) |
| `--dry-run`, `-n` | Preview without writing files |
| `--force`, `-f` | Overwrite existing NFO/artwork |
| `--no-artwork` | Skip downloading images |
| `--no-nfo` | Skip generating NFO files |
| `--verbose`, `-v` | Enable debug logging |
| `--version`, `-V` | Show version number |

---

## How it works with Cinaura

1. **You run this tool** on your media files (on a computer that can access your NAS/drive)
2. **NFO files and artwork** are written next to your video files
3. **Cinaura detects them** on its next library scan and uses the local metadata instead of searching TMDb
4. **Pinned matches** — because the NFO contains the exact TMDb ID, Cinaura won't ever mismatch the title

> Cinaura prioritizes local `.nfo` files and artwork over online lookups. This tool generates exactly what Cinaura expects.

---

## Troubleshooting

### "No TMDb results" for a title
- Check if the filename is parseable (use `--verbose` to see what was extracted)
- Rename the file to `Title (Year).ext` format
- For foreign titles, use the English title TMDb recognizes

### Metadata still wrong in Cinaura after running the tool
- In Cinaura: go to the title → **File actions** → **Fix metadata** → select the correct match
- Or run this tool with `--force` after renaming the file correctly

### Rate limiting
The tool respects TMDb's rate limits (~35 req/s). Large libraries may take a few minutes.

---

## Attribution

This product uses the TMDb API but is not endorsed or certified by TMDb.

[![TMDb Logo](https://www.themoviedb.org/assets/2/v4/logos/v2/blue_short-8e7b30f73a4020692ccca9c88bafe5dcb6f8a62a4c6bc55cd9ba82bb2cd95f6c.svg)](https://www.themoviedb.org)

---

## License

MIT — see the main repository for details.

