#!/usr/bin/env python3
"""
Fetch Freesounds - Download CC0-licensed notification sounds from freesound.org.

Usage:
    export FREESOUND_API_KEY="your-api-key"
    python fetch-freesounds.py                    # Download default set
    python fetch-freesounds.py --query "chime"    # Search specific sounds
    python fetch-freesounds.py --list-only        # Preview without downloading

Get your API key at: https://freesound.org/apiv2/apply/

This script downloads sounds licensed under CC0 (public domain) so they can
be freely included in any project.
"""

import argparse
import json
import os
import sys
import urllib.request
import urllib.parse
from pathlib import Path

API_BASE = "https://freesound.org/apiv2"

DEFAULT_QUERIES = [
    ("completion", "notification chime positive"),
    ("acknowledgment", "UI click confirm"),
    ("attention", "alert bell notification"),
    ("warning", "warning alert beep"),
    ("greeting", "startup welcome chime"),
]

def search_sounds(query: str, api_key: str, max_results: int = 5) -> list:
    """Search freesound.org for CC0-licensed sounds."""
    params = urllib.parse.urlencode({
        "query": query,
        "filter": "license:\"Creative Commons 0\"",
        "fields": "id,name,duration,previews,tags,avg_rating",
        "sort": "rating_desc",
        "page_size": max_results,
        "token": api_key
    })
    
    url = f"{API_BASE}/search/text/?{params}"
    
    try:
        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read())
            return data.get("results", [])
    except Exception as e:
        print(f"Error searching: {e}", file=sys.stderr)
        return []


def download_sound(sound: dict, output_dir: Path, prefix: str, api_key: str) -> bool:
    """Download a sound preview to the output directory."""
    previews = sound.get("previews", {})
    # Prefer HQ MP3 preview
    url = previews.get("preview-hq-mp3") or previews.get("preview-lq-mp3")
    
    if not url:
        print(f"  No preview URL for {sound['name']}", file=sys.stderr)
        return False
    
    filename = f"{prefix}-{sound['id']}.mp3"
    output_path = output_dir / filename
    
    try:
        urllib.request.urlretrieve(url, output_path)
        print(f"  ✓ Downloaded: {filename} ({sound['duration']:.1f}s) - {sound['name']}")
        return True
    except Exception as e:
        print(f"  ✗ Failed: {filename} - {e}", file=sys.stderr)
        return False


def main():
    parser = argparse.ArgumentParser(description="Download CC0 notification sounds from freesound.org")
    parser.add_argument("--query", help="Custom search query")
    parser.add_argument("--output", default="config/themes/default", help="Output directory")
    parser.add_argument("--max", type=int, default=3, help="Max sounds per category")
    parser.add_argument("--list-only", action="store_true", help="List sounds without downloading")
    args = parser.parse_args()
    
    api_key = os.environ.get("FREESOUND_API_KEY")
    if not api_key:
        print("Error: Set FREESOUND_API_KEY environment variable")
        print("Get your key at: https://freesound.org/apiv2/apply/")
        sys.exit(1)
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    queries = [(args.query, args.query)] if args.query else DEFAULT_QUERIES
    
    total = 0
    for prefix, query in queries:
        print(f"\n🔍 Searching: \"{query}\" (category: {prefix})")
        sounds = search_sounds(query, api_key, args.max)
        
        if not sounds:
            print("  No CC0 sounds found.")
            continue
        
        for sound in sounds:
            if args.list_only:
                print(f"  [{sound['id']}] {sound['name']} ({sound['duration']:.1f}s) ★{sound.get('avg_rating', 0):.1f}")
            else:
                if download_sound(sound, output_dir, prefix, api_key):
                    total += 1
    
    if not args.list_only:
        print(f"\n✅ Downloaded {total} sounds to {output_dir}/")
        print("Add filenames (without .mp3) to your sound-config.yaml pools.")


if __name__ == "__main__":
    main()
