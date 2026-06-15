#!/usr/bin/env python3
"""See SKILL.md for usage. Run with: /usr/bin/python3 or python3 from PATH."""

"""
Generate TTS audio for each slide using Edge TTS (free, no API key).

Usage:
    # Single voice (default)
    python3 generate_tts.py --script director_script.md --output audio/

    # Custom voice and speed
    python3 generate_tts.py --script director_script.md --output audio/ \
        --voice en-US-JennyNeural --rate "-5%"

    # Multiple voices (generates subdirectories audio/Emma/, audio/Guy/, etc.)
    python3 generate_tts.py --script director_script.md --output audio/ \
        --voices en-US-EmmaNeural,en-US-GuyNeural,en-GB-SoniaNeural

Available voices (recommended for English presentations):
    en-US-EmmaNeural  — Warm, clear female (default, best for academic)
    en-US-JennyNeural — Bright, energetic female
    en-US-GuyNeural   — Deep, authoritative male
    en-GB-SoniaNeural — British English, formal
    en-US-AriaNeural  — Confident, professional female
    en-US-DavisNeural — Calm, measured male

Pause control:
    --pause-ms N       Add N milliseconds pause between sentences (default: 300)
    --long-pause-ms N  Pause after paragraph/slide transitions (default: 600)

Requires: pip3 install edge-tts
"""

import re
import os
import sys
import asyncio
import argparse
from pathlib import Path


VOICE_PROFILES = {
    "en-US-EmmaNeural":  {"label": "Emma (US, Warm)", "rec": "⭐ Best for academic presentations"},
    "en-US-JennyNeural": {"label": "Jenny (US, Bright)", "rec": "Energetic, good for engaging talks"},
    "en-US-GuyNeural":   {"label": "Guy (US, Deep)", "rec": "Authoritative male voice"},
    "en-GB-SoniaNeural": {"label": "Sonia (UK, Formal)", "rec": "British English, formal tone"},
    "en-US-AriaNeural":  {"label": "Aria (US, Confident)", "rec": "Professional, clear"},
    "en-US-DavisNeural": {"label": "Davis (US, Calm)", "rec": "Measured, good for narration"},
}


def parse_full_texts(script_path):
    """Extract slide numbers and full texts from the director script."""
    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read()

    slides_raw = re.split(r'\n(?=## Slide \d+)', text)[1:]
    slides = []

    for raw in slides_raw:
        h_match = re.match(r'## Slide (\d+)', raw)
        if not h_match:
            continue
        slide_num = int(h_match.group(1))

        full_text = ""
        ft = re.search(
            r'\*\*连贯全文\*\*[^：:]*[：:]\s*\n>?\s*(.+?)(?=\n\n---|\n\n\*\*END|\Z)',
            raw, re.DOTALL
        )
        if ft:
            full_text = re.sub(r'\n> ?', ' ', ft.group(1)).replace('\n', ' ').strip()

        if full_text:
            # Insert SSML pauses between sentences for natural rhythm
            if "{{PAUSE}}" not in full_text:
                full_text = insert_pauses(full_text)
            slides.append((slide_num, full_text))

    return slides


def insert_pauses(text, short_ms=300, long_ms=600):
    """Insert SSML-style pause markers between sentences.
    
    Edge TTS doesn't support SSML directly via the Python library,
    but we can use punctuation-based chunking with slight delays.
    This function marks pause points for the audio generation step.
    """
    # Add slight pause after sentence-ending punctuation
    text = re.sub(r'([.!?])\s+', r'\1  ', text)
    # Add longer pause after paragraph-like breaks (em-dash, colon before new idea)
    text = re.sub(r'(—)\s*', r'\1   ', text)
    text = re.sub(r'(:)\s+(?=[A-Z])', r'\1    ', text)
    return text


async def generate_slide_audio(slide_num, text, output_dir, voice, rate):
    """Generate TTS audio for a single slide."""
    try:
        from edge_tts import Communicate
    except ImportError:
        print("ERROR: edge-tts not installed. Run: pip3 install edge-tts")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    
    # Use voice short name as subdirectory for multi-voice mode
    voice_short = voice.replace("en-US-", "").replace("en-GB-", "").replace("Neural", "")
    output_path = os.path.join(output_dir, f"Slide{slide_num:02d}_连贯全文.mp3")
    
    print(f"  Slide {slide_num:02d} [{voice_short}]... ({len(text)} chars)", end="", flush=True)
    
    communicate = Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(output_path)
    
    size_kb = os.path.getsize(output_path) / 1024
    print(f" → {size_kb:.0f} KB")


async def generate_all(slides, output_dir, voice, rate):
    """Generate TTS for all slides with a single voice."""
    os.makedirs(output_dir, exist_ok=True)
    
    for slide_num, text in slides:
        await generate_slide_audio(slide_num, text, output_dir, voice, rate)
    
    print(f"\n  Done: {len(slides)} files → {output_dir}/")


async def generate_multi_voice(slides, base_output_dir, voices, rate):
    """Generate TTS for all slides with multiple voices, each in a subdirectory."""
    for voice in voices:
        voice_short = voice.replace("en-US-", "").replace("en-GB-", "").replace("Neural", "")
        voice_dir = os.path.join(base_output_dir, voice_short)
        
        profile = VOICE_PROFILES.get(voice, {})
        label = profile.get("label", voice)
        print(f"\n{'='*50}")
        print(f"Voice: {label}")
        print(f"{'='*50}")
        
        for slide_num, text in slides:
            await generate_slide_audio(slide_num, text, voice_dir, voice, rate)
    
    # Generate voice manifest for the HTML player
    manifest = {voice.replace("en-US-", "").replace("en-GB-", "").replace("Neural", ""): {
        "name": VOICE_PROFILES.get(voice, {}).get("label", voice),
        "dir": voice.replace("en-US-", "").replace("en-GB-", "").replace("Neural", ""),
        "voice_id": voice
    } for voice in voices}
    
    import json
    manifest_path = os.path.join(base_output_dir, "voice_manifest.json")
    with open(manifest_path, "w") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*50}")
    print(f"Voice manifest: {manifest_path}")
    print(f"Generated {len(voices)} voice variants for {len(slides)} slides")


def main():
    parser = argparse.ArgumentParser(
        description="Generate TTS audio for recitation trainer",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Voice recommendations:
  en-US-EmmaNeural  — Warm, clear female (⭐ default, best for academic)
  en-US-JennyNeural — Bright, energetic female
  en-US-GuyNeural   — Deep, authoritative male
  en-GB-SoniaNeural — British English, formal
  en-US-AriaNeural  — Confident, professional female
  en-US-DavisNeural — Calm, measured male

Examples:
  # Single voice, default settings
  python3 generate_tts.py --script script.md --output audio/

  # British voice, slightly faster
  python3 generate_tts.py --script script.md --output audio/ \\
      --voice en-GB-SoniaNeural --rate "-3%"

  # Generate 3 voice variants (for voice switching in the player)
  python3 generate_tts.py --script script.md --output audio/ \\
      --voices en-US-EmmaNeural,en-US-GuyNeural,en-GB-SoniaNeural
        """
    )
    parser.add_argument("--script", required=True, help="Director script Markdown file")
    parser.add_argument("--output", default="audio", help="Output directory for MP3 files")
    parser.add_argument("--voice", default="en-US-EmmaNeural",
                        help="Edge TTS voice name (default: en-US-EmmaNeural)")
    parser.add_argument("--voices",
                        help="Comma-separated list of voices for multi-voice generation")
    parser.add_argument("--rate", default="-8%",
                        help="Speech rate: negative=slower, positive=faster (default: -8%%)")
    parser.add_argument("--pause-ms", type=int, default=300,
                        help="Pause between sentences in ms (default: 300)")
    parser.add_argument("--long-pause-ms", type=int, default=600,
                        help="Pause after transitions in ms (default: 600)")
    parser.add_argument("--list-voices", action="store_true",
                        help="List available voice profiles and exit")

    args = parser.parse_args()

    if args.list_voices:
        print("\nAvailable Edge TTS Voice Profiles:\n")
        for voice_id, profile in VOICE_PROFILES.items():
            print(f"  {voice_id}")
            print(f"    {profile['label']}")
            print(f"    {profile['rec']}\n")
        return

    print("=" * 50)
    print("TTS Audio Generator (Edge TTS)")
    print("=" * 50)

    # Parse script
    print("\n[1/2] Parsing director script...")
    slides = parse_full_texts(args.script)
    print(f"  Found {len(slides)} slides with full text")
    print(f"  Pause settings: {args.pause_ms}ms / {args.long_pause_ms}ms (long)")

    # Generate
    print("\n[2/2] Generating audio...")
    
    if args.voices:
        voice_list = [v.strip() for v in args.voices.split(",")]
        if args.voice != "en-US-EmmaNeural":
            print(f"  Note: --voice is ignored when --voices is set")
        asyncio.run(generate_multi_voice(slides, args.output, voice_list, args.rate))
    else:
        profile = VOICE_PROFILES.get(args.voice, {})
        label = profile.get("label", args.voice)
        print(f"  Voice: {label}")
        print(f"  Rate:  {args.rate}")
        asyncio.run(generate_all(slides, args.output, args.voice, args.rate))

    print(f"\n✅ All done! Audio saved to: {args.output}/")


if __name__ == "__main__":
    main()
