# Cinaura – Android TV

**Cinaura is available on the Play Store** — that's the recommended way to install on most devices.

This repository contains official signed APK releases for users who prefer sideloading or are on devices where the Play Store isn't available.

[Get it on Google Play →](https://play.google.com/store/apps/details?id=com.cinaura.tv&hl=en)

---

## What is Cinaura?

A personal media library app for Android TV. Built for people who curate their own content and want a single, calm interface to watch it from.

Connect your NAS, cloud storage, and debrid services. Cinaura brings everything together into one library, properly matched, well-presented, and entirely yours. No server to run, no account required nothing injected, recommended, or added without your intent.

Your library exists because you decided it should.

---

## Why sideload instead of using the Play Store?

The APK here is identical to the Play Store release — same build, same signing key. You might prefer it if:

- Your device doesn't have the Play Store (some Android TV boxes, custom firmware)
- You prefer to manage your own updates
- You have a specific reason to install outside Google's ecosystem

Otherwise, the Play Store version is simpler and handles updates automatically.

---

## How to install

1. Download the latest APK from the **Releases** section
2. Transfer it to your Android TV device
3. Enable **Install unknown apps** on your device
4. Install using a file manager
5. Launch Cinaura from your app list

All APKs are signed by the official developer.

---

## File naming guide

Cinaura uses filenames to search TMDb and match your media with the correct metadata. Proper naming dramatically improves matching accuracy.

### Movies

Use the format: `Title (Year).ext`

```
Movies/
├── Inception (2010)/
│   └── Inception (2010).mkv
├── The Dark Knight (2008)/
│   └── The Dark Knight (2008).mp4
└── Blade Runner 2049 (2017)/
    └── Blade Runner 2049 (2017).mkv
```

### TV Shows

Use the format: `Show Name/Season XX/Show.Name.SxxExx.ext`

```
TV Shows/
├── Breaking Bad/
│   ├── Season 01/
│   │   ├── Breaking.Bad.S01E01.mkv
│   │   └── Breaking.Bad.S01E02.mkv
│   └── Season 02/
│       └── Breaking.Bad.S02E01.mkv
└── Game of Thrones/
    └── Season 08/
        └── Game.of.Thrones.S08E06.mkv
```

**Tips:**
- Always include the year in parentheses for movies — it prevents mismatches between remakes
- Use `S01E01` format (not `1x01`) for the most reliable matching
- Avoid putting quality tags (`1080p`, `BluRay`) before the year — Cinaura will skip them, but clean names match faster
- Organize each movie into its own subfolder for local artwork support

---

## Metadata troubleshooting

### Fixing a wrong or missing match

If a title shows wrong metadata (wrong poster, wrong description, or "no metadata"):

1. Navigate to the title's **Details page** on your TV
2. Open the options menu (three-dot button)
3. Select **Fix metadata**
4. Search by the exact title + release year, or paste the **TMDb ID** directly
5. Select the correct result — Cinaura will pin it so future refreshes won't overwrite it

### Refreshing metadata

- **Single title:** Details page → three-dot menu → **Refresh metadata**
- **Full library rescan:** Settings → Library → refresh your source
- After renaming files or adding new local artwork, trigger a source refresh

### "Items without metadata" diagnostic

Cinaura includes a built-in tool to find problematic files:

Settings → Library → **Items without metadata**

This shows every file that failed to match, along with the filename Cinaura tried to parse. Use this to identify naming issues.

### SMB / Network drive issues

If metadata scanning stalls or your library shows 0 items:

- **SMB1 protocol:** Older NAS devices using SMB1 have a tiny buffer that truncates file lists silently. Log into your NAS and set the minimum SMB protocol to **SMB2 or SMB3**, then remove and re-add the source in Cinaura
- **Massive flat folders:** Break a single folder with thousands of files into subfolders (e.g., `/movies/action/`, `/movies/drama/`) to speed up scanning
- **Drive went to sleep:** Cinaura v1.7.2+ waits for sleeping drives to wake before scanning

### Force update not working?

"Force update" refreshes the source file list, not necessarily re-fetching metadata for already-matched titles. To truly re-fetch metadata:

1. Use **Fix metadata** on the specific title (as described above)
2. Or, use the [Cinaura Metadata Helper](#cinaura-metadata-helper-tool) to generate local `.nfo` sidecar files that Cinaura will always prioritize

---

## Local metadata & artwork

Cinaura supports local sidecar files for full manual control over your metadata. Local files are **always prioritized** over online TMDb lookups.

### NFO sidecar files

Place an `.nfo` XML file next to your video file with the same name:

```
Inception (2010)/
├── Inception (2010).mkv
└── Inception (2010).nfo      ← Cinaura reads this first
```

A minimal NFO that pins the correct TMDb match:

```xml
<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
<movie>
    <title>Inception</title>
    <uniqueid type="tmdb" default="true">27205</uniqueid>
    <year>2010</year>
</movie>
```

For TV shows, place a `tvshow.nfo` in the show's root folder.

### Local artwork

Place images next to your media files. Cinaura detects and prioritizes them:

```
Inception (2010)/
├── Inception (2010).mkv
├── poster.jpg                 ← Cover image
└── backdrop.jpg               ← Background art
```

**Supported formats:** JPG, PNG, WEBP

---

## Cinaura Metadata Helper tool

This repository includes a **companion CLI tool** that automates metadata fetching for your entire library:

📁 **[cinaura-metadata-helper/](cinaura-metadata-helper/)**

It scans your media files, searches TMDb, and generates `.nfo` sidecar files + downloads poster & backdrop artwork — so Cinaura picks up accurate metadata on its next scan.

### Quick start

```bash
cd cinaura-metadata-helper
pip install -r requirements.txt

# Set your free TMDb API key
export TMDB_API_KEY=your_key_here

# Scan a movie library
python -m cinaura_metadata_helper /path/to/Movies

# Scan TV shows
python -m cinaura_metadata_helper /path/to/TVShows --type tv

# Preview without writing anything
python -m cinaura_metadata_helper /path/to/Movies --dry-run
```

Get a free TMDb API key at: [themoviedb.org/settings/api](https://www.themoviedb.org/settings/api)

See the [full documentation](cinaura-metadata-helper/README.md) for all options.

---

## Privacy

- No ads
- No account required
- No injected content or recommendations
- No data sold or shared

Your library stays yours.

---

## Community & feedback

Questions, bug reports, and feature requests: [r/CinauraTV](https://reddit.com/r/Cinauratv)

For issues tied to a specific release, GitHub Issues works too.
