#!/usr/bin/env python3
"""
Build a recitation trainer HTML from a director script and slide images.

Usage:
    python3 build_trainer.py --script director_script.md --slides slides/ --audio audio/ --output recitation_trainer.html

Inputs:
    --script    Markdown director script with slide beats and full text
    --slides    Directory containing Slide01.png/jpg through SlideNN.png/jpg
    --audio     Directory containing Slide01_*.mp3 through SlideNN_*.mp3
    --output    Output HTML file path
    --compress  (flag) Compress slide images to JPEG (recommended for web)
    --width     Max image width in pixels (default: 1200)
"""

import re
import json
import os
import sys
import argparse
from pathlib import Path


def parse_script(script_path):
    """Parse the director script Markdown into structured slide data."""
    with open(script_path, "r", encoding="utf-8") as f:
        text = f.read()

    slides_raw = re.split(r'\n(?=## Slide \d+)', text)[1:]  # skip header
    slides = []

    for raw in slides_raw:
        h_match = re.match(r'## Slide (\d+) — (.+)', raw)
        if not h_match:
            continue
        slide_num = int(h_match.group(1))
        title = h_match.group(2).strip()

        # Parse beat table
        beats = []
        lines = raw.split('\n')
        in_table = False
        for line in lines:
            stripped = line.strip()
            if stripped.startswith('| 拍 |'):
                in_table = True
                continue
            if in_table and stripped.startswith('**连贯全文**'):
                in_table = False
                continue
            if in_table and stripped.startswith('|---'):
                continue
            if in_table and stripped.startswith('|'):
                cols = [c.strip() for c in stripped.split('|')[1:-1]]
                if len(cols) >= 3:
                    try:
                        beat_num = int(cols[0])
                        beats.append({
                            "beat": beat_num,
                            "ppt_guide": cols[1] if len(cols) > 1 else "",
                            "english": cols[2] if len(cols) > 2 else "",
                            "action": cols[3] if len(cols) > 3 else ""
                        })
                    except ValueError:
                        pass

        # Extract full text
        full_text = ""
        ft = re.search(
            r'\*\*连贯全文\*\*[^：:]*[：:]\s*\n>?\s*(.+?)(?=\n\n---|\n\n\*\*END|\Z)',
            raw, re.DOTALL
        )
        if ft:
            full_text = re.sub(r'\n> ?', ' ', ft.group(1)).replace('\n', ' ').strip()

        slides.append({
            "num": slide_num,
            "title": title,
            "beats": beats,
            "full_text": full_text
        })

    return slides


def compress_images(slides_dir, max_width=1200):
    """Compress slide images to JPEG and remove originals."""
    try:
        from PIL import Image
    except ImportError:
        print("Warning: Pillow not installed. Skipping image compression.")
        print("Install with: pip3 install Pillow")
        return {}

    dir_path = Path(slides_dir)
    mapping = {}  # old_name -> new_name

    for ext in ['*.png', '*.PNG']:
        for img_path in sorted(dir_path.glob(ext)):
            try:
                img = Image.open(img_path)
                if img.mode == 'RGBA':
                    bg = Image.new('RGB', img.size, (255, 255, 255))
                    bg.paste(img, mask=img.split()[3])
                    img = bg
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                w, h = img.size
                if w > max_width:
                    img = img.resize((max_width, int(h * max_width / w)), Image.LANCZOS)

                new_path = img_path.with_suffix('.jpg')
                img.save(new_path, 'JPEG', quality=85, optimize=True)
                img_path.unlink()  # remove original
                mapping[img_path.name] = new_path.name
                print(f"  Compressed: {img_path.name} -> {new_path.name} "
                      f"({img_path.stat().st_size/1024:.0f}KB -> {new_path.stat().st_size/1024:.0f}KB)")
            except Exception as e:
                print(f"  Warning: Could not process {img_path.name}: {e}")

    return mapping


def detect_image_ext(slides_dir):
    """Detect the image file extension used in the slides directory."""
    dir_path = Path(slides_dir)
    if list(dir_path.glob('Slide01.jpg')):
        return 'jpg'
    if list(dir_path.glob('Slide01.png')):
        return 'png'
    if list(dir_path.glob('Slide01.PNG')):
        return 'png'
    return 'jpg'  # default


def detect_audio_pattern(audio_dir):
    """Detect the audio file naming pattern and voice structure."""
    dir_path = Path(audio_dir)
    
    # Check for voice_manifest.json (multi-voice mode)
    manifest_path = dir_path / "voice_manifest.json"
    if manifest_path.exists():
        # Multi-voice: audio/Emma/Slide01_...mp3 etc.
        # Find first voice subdirectory and check its contents
        for subdir in sorted(dir_path.iterdir()):
            if subdir.is_dir():
                for f in sorted(subdir.iterdir()):
                    match = re.match(r'Slide(\d+)_.+\.mp3', f.name.lower())
                    if match:
                        return {"multi_voice": True, "sample": f.name, "manifest": str(manifest_path)}
        return {"multi_voice": True, "sample": None, "manifest": str(manifest_path)}
    
    # Single voice: audio/Slide01_...mp3
    for f in sorted(dir_path.iterdir()):
        if f.is_file():
            match = re.match(r'Slide(\d+)_.+\.mp3', f.name.lower())
            if match:
                return {"multi_voice": False, "sample": f.name}
    return None


def build_html(slides, slides_dir, audio_dir, output_path, template_path=None):
    """Generate the trainer HTML."""
    slides_json = json.dumps(slides, ensure_ascii=False)
    img_ext = detect_image_ext(slides_dir)
    audio_sample = detect_audio_pattern(audio_dir)

    if template_path and os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            html = f.read()
    else:
        # Read embedded template from the same directory as this script
        template_dir = Path(__file__).parent.parent / "assets"
        template_file = template_dir / "trainer_template.html"
        if template_file.exists():
            with open(template_file, "r", encoding="utf-8") as f:
                html = f.read()
        else:
            raise FileNotFoundError("trainer_template.html not found in assets/")

    # Replace the SLIDES data
    html = re.sub(
        r'const SLIDES = \[.*?\];',
        f'const SLIDES = {slides_json};',
        html,
        flags=re.DOTALL
    )

    # Update image extension
    html = html.replace(
        "Slide${String(s.num).padStart(2,'0')}.png",
        f"Slide${{String(s.num).padStart(2,'0')}}.{img_ext}"
    )
    html = html.replace(
        "Slide${String(s.num).padStart(2,'0')}.jpg",
        f"Slide${{String(s.num).padStart(2,'0')}}.{img_ext}"
    )

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"HTML written: {output_path} ({len(html)} bytes)")
    print(f"  Image extension: .{img_ext}")
    if audio_sample and isinstance(audio_sample, dict) and audio_sample.get("multi_voice"):
        print("  Audio: Multi-voice mode (manifest: " + str(audio_sample.get("manifest", "N/A")) + ")")
    else:
        sample_info = audio_sample.get("sample", "auto-detected") if isinstance(audio_sample, dict) else (audio_sample or "auto-detected")
        print("  Audio: Single voice (" + str(sample_info) + ")")

    return html


def main():
    parser = argparse.ArgumentParser(description="Build recitation trainer HTML")
    parser.add_argument("--script", required=True, help="Director script Markdown file")
    parser.add_argument("--slides", required=True, help="Directory containing slide images")
    parser.add_argument("--audio", required=True, help="Directory containing TTS audio MP3s")
    parser.add_argument("--output", default="recitation_trainer.html", help="Output HTML file")
    parser.add_argument("--compress", action="store_true", help="Compress images to JPEG")
    parser.add_argument("--width", type=int, default=1200, help="Max image width for compression")
    parser.add_argument("--template", help="Path to trainer_template.html (auto-detected if omitted)")

    args = parser.parse_args()

    print("=" * 50)
    print("Recitation Trainer Builder")
    print("=" * 50)

    # Step 1: Parse script
    print("\n[1/4] Parsing director script...")
    slides = parse_script(args.script)
    print(f"  Parsed {len(slides)} slides")
    for s in slides:
        print(f"    Slide {s['num']:02d}: {s['title'][:40]} — {len(s['beats'])} beats, {len(s['full_text'])} chars")

    # Step 2: Compress images (optional)
    if args.compress:
        print("\n[2/4] Compressing images...")
        compress_images(args.slides, args.width)
    else:
        print("\n[2/4] Skipping image compression (use --compress to enable)")

    # Step 3: Build HTML
    print("\n[3/4] Building HTML...")
    build_html(slides, args.slides, args.audio, args.output, args.template)

    # Step 4: Summary
    print("\n[4/4] Done!")
    print(f"\nFinal deliverable: {args.output}")
    print(f"  Slides: {args.slides}")
    print(f"  Audio:  {args.audio}")
    print(f"\nTo test: open {args.output} in a browser")
    print("To deploy: push the entire folder to GitHub and enable Pages")


if __name__ == "__main__":
    main()
