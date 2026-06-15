---
name: recitation-trainer
description: Build an interactive English presentation recitation trainer for Chinese speakers. Takes a PPTX file as input and produces a self-contained static HTML web app with slide previews, beat-by-beat oral scripts, TTS audio playback with sentence-level highlighting, and speed control — accessible on both desktop and mobile via GitHub Pages. Use this skill when the user mentions "带读训练器", "英语pre带读", "presentation recitation", "背诵训练", "pre练习", "英文演讲稿熟记", "国际会议pre", "博士生英语pre", "TTS带读", or wants to build a presentation practice tool for academic conferences or doctoral English presentations.
---

# Recitation Trainer · 英语 Pre 带读训练器

A complete end-to-end pipeline that turns a PowerPoint presentation into an interactive English recitation practice web app — designed for Chinese PhD students and researchers preparing for international academic conferences.

**Target users**: Chinese speakers who need to memorize and practice English presentations.
**Key scenarios**: Doctoral English pre, international conference presentations, thesis defense rehearsals.

## What this skill does

Given a PPTX file, this skill:

1. **Generates a director script** (导演台本) — AI analyzes each slide and writes a beat-by-beat oral English script with flowing full text
2. **Exports slide screenshots** — render each PPTX slide as a high-quality PNG image
3. **Generates TTS audio** — use free Edge TTS to narrate each slide's full text as MP3
4. **Compresses images** — optimize PNG to JPEG for fast mobile loading
5. **Builds the trainer HTML** — a self-contained, dark-themed web app with:
   - 21+ collapsible panels (one per slide)
   - PPT slide preview images
   - Beat-by-beat oral script table (4 columns: beat #, PPT guide, English, action)
   - Flowing full text with per-sentence highlighting synced to audio
   - Play/pause button per slide
   - Global speed control (0.5x–2.0x)
   - Keyboard shortcuts (Space, Arrow keys)
6. **Deploys to GitHub Pages** (optional) — get a public URL accessible on any device

## Prerequisites

The user needs:
- A PPTX file (the presentation slides)
- Python 3 with `pip3` (for Edge TTS, Pillow, python-pptx)
- `pdftoppm` (for PDF→PNG conversion, install via `brew install poppler` on macOS)
- macOS with Keynote (for PPTX→PDF export)
- Git and GitHub account (for deployment)
- `gh` CLI (for GitHub Pages deployment, install via `brew install gh`)

No API keys, no paid services. Everything is free and runs locally.

## Complete Workflow

### Step 0: Environment check & auto-setup

**IMPORTANT — Python environment**: The scripts in this skill MUST run with the system Python (`/usr/bin/python3` or `which python3`), NOT a virtualenv Python. Virtualenvs often lack `pip` and have incompatible site-packages. The AI agent should detect this:

```bash
# Check if python3 is a venv
python3 -c "import sys; print('VENV' if sys.prefix != sys.base_prefix else 'SYSTEM')"

# If VENV, find and use system python3 instead
SYSTEM_PYTHON=$(/usr/bin/python3 -c "print('ok')" 2>/dev/null && echo "/usr/bin/python3" || echo "python3")
# Then run all scripts with: $SYSTEM_PYTHON scripts/check_env.py
```

**The AI agent MUST run this as the very first step:**

```bash
$SYSTEM_PYTHON scripts/check_env.py
```

This script:
- Detects OS (macOS / Linux / Windows)
- Checks all required Python packages (edge-tts, Pillow, python-pptx)
- **Auto-installs** missing Python packages via pip
- Checks system tools (pdftoppm, Keynote/LibreOffice, gh CLI)
- Reports what's missing with OS-specific install commands
- Outputs a JSON summary for the AI agent to parse

**After running, the AI agent reads the JSON output and acts:**

| If missing... | Action |
|---------------|--------|
| Python packages | Auto-installed by the script — just re-run to verify |
| `pdftoppm` | Tell user to install: `brew install poppler` (macOS) or `sudo apt install poppler-utils` (Linux) |
| Keynote (macOS missing) | Use **Fallback A**: manual PNG export from PowerPoint, or Python-based slide rendering |
| LibreOffice (Linux missing) | Use **Fallback B**: `python-pptx` + Pillow to render simple slide previews |
| `gh` CLI | Skip GitHub Pages deployment — local HTML still works fine |

**Fallback slide export methods (when Keynote/LibreOffice unavailable):**

Fallback A — Manual export:
> "Keynote isn't available on this machine. Please export your PPTX slides as PNG images manually: open the PPTX in PowerPoint/Google Slides → File → Export → PNG. Save them as Slide01.png through SlideNN.png in a `slides/` folder."

Fallback B — Python-based (limited quality, text-only previews):
```python
# Generate simple text-based previews when no real export tool exists
from pptx import Presentation
from PIL import Image, ImageDraw, ImageFont

prs = Presentation("presentation.pptx")
for i, slide in enumerate(prs.slides):
    img = Image.new('RGB', (1280, 720), (13, 17, 23))  # dark bg
    draw = ImageDraw.Draw(img)
    y = 40
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                if para.text.strip():
                    draw.text((60, y), para.text.strip()[:80], fill=(201, 209, 217))
                    y += 30
                    if y > 680: break
        if y > 680: break
    img.save(f"slides/Slide{i+1:02d}.png")
```

### Step 1: Generate the director script from PPTX

This is the most critical step. The AI agent must analyze each slide in the PPTX file and produce a structured Markdown director script.

**First, extract text from the PPTX:**

```python
from pptx import Presentation

prs = Presentation("presentation.pptx")
for i, slide in enumerate(prs.slides):
    print(f"\n=== Slide {i+1} ===")
    for shape in slide.shapes:
        if shape.has_text_frame:
            for para in shape.text_frame.paragraphs:
                text = para.text.strip()
                if text:
                    print(f"  {text}")
```

**Then, for each slide, the AI agent writes:**

1. A slide section header: `## Slide N — TITLE`
2. A beat-by-beat table with these columns: `| 拍 | PPT 指引 | 英文口述 | 动作 |`
3. A flowing full text section: `**连贯全文**：> Full text...`

**Script writing guidelines for the AI agent:**

- **Simple sentences.** Break complex ideas into short, spoken English. No long subordinate clauses.
- **Conversational tone.** Write like you're explaining to a friend, not reading an academic paper.
- **Beat-by-beat.** Each row = one speaking beat with a physical gesture. ~3-8 beats per slide for quick slides, ~8-12 for content-heavy slides.
- **PPT guide column.** What the speaker points to on screen ("手指向标题", "手扫过三栏").
- **Action column.** Physical gestures and timing notes ("微笑", "看观众", "停一拍").
- **Flowing full text.** Concatenate all oral lines into one continuous paragraph — this becomes the TTS input.

**Example output format:**

```markdown
## Slide 1 — COVER

| 拍 | PPT 指引 | 英文口述 | 动作 |
|---|---|---|---|
| 1 | 面向观众 | Hi, everyone. | 微笑，停一拍 |
| 2 | 手指向大标题 | Today — "Disclosure Day." | 单手指屏幕 |
| 3 | 看观众 | Is it really happening? | |
| 4 | 转身切页 | Let's find out. | |

**连贯全文**：
> Hi, everyone. Today — "Disclosure Day." Is it really happening? Let's find out.
```

Save as `director_script.md` in the working directory.

### Step 2: Export slide screenshots

**Guide the user to export slides manually** — this is the only reliable way to get pixel-perfect previews across all platforms:

> "Now I need your slide images. It takes about 2 minutes:
> 
> **WPS** (most Chinese users): 文件 → 另存为 → 文件类型选 PNG → 保存到 `slides/` 文件夹。WPS 自动批量导出所有页面。导出后将文件名重命名为 Slide01.png, Slide02.png ...
> 
> **PowerPoint** (Windows/Mac): File → Export → Change File Type → PNG
> 
> **Keynote** (Mac): 文件 → 导出到 → 图像 → 格式: PNG → 勾选"所有幻灯片" → 一键批量导出
> 
> **Google Slides**: 文件 → 下载 → PNG 图像（所有幻灯片）
> 
> After export, rename files to: slides/Slide01.png, slides/Slide02.png, ... slides/SlideNN.png"

If the user wants a quick automated alternative (lower quality, loses backgrounds), run:

```bash
python3 scripts/export_slides.py presentation.pptx slides/
```

The AI agent should present the manual guide by default. Only offer the automated fallback if the user explicitly says they don't care about visual quality.



### Step 3: Generate TTS audio

Use Edge TTS (free, no API key, neural voice quality). **Default settings** are suitable for most academic presentations:

```bash
python3 scripts/generate_tts.py --script director_script.md --output audio/
# Defaults: en-US-EmmaNeural (warm female), rate=-8% (slightly slowed for clarity)
```

**Briefly mention to the user** before generating: "I'll generate the audio with Emma's voice (warm academic female) at a slightly slowed pace. If you'd prefer a different voice or speed, just let me know — I can also generate multiple voices so you can switch in the player." Then proceed with defaults unless the user asks otherwise.

**If the user wants to customize:**

| Request | Command |
|---------|---------|
| Different voice | `--voice en-GB-SoniaNeural` (or Jenny / Guy / Aria / Davis) |
| Faster / slower | `--rate "-5%"` (advanced) or `--rate "-12%"` (beginner) |
| Multiple voices | `--voices en-US-EmmaNeural,en-US-GuyNeural,en-GB-SoniaNeural` |
| More pauses | `--pause-ms 400 --long-pause-ms 700` |

The AI should NOT present a full menu of options unless the user asks — default and go.

```python
import asyncio
import edge_tts
import re, json

# Load parsed slide data
with open("director_script.md", "r") as f:
    script_text = f.read()

# Parse slides (see Step 0 for parser)
# For each slide's full_text, generate audio:

async def generate_audio(slide_num, text, output_path):
    communicate = edge_tts.Communicate(
        text=text,
        voice="en-US-EmmaNeural",
        rate="-8%"  # Slightly slower for clarity
    )
    await communicate.save(output_path)

# Generate for each slide:
# asyncio.run(generate_audio(1, slide1_text, "audio/Slide01_连贯全文.mp3"))
```

**Voice selection**: `en-US-EmmaNeural` (warm, clear female voice). Alternatives:
- `en-US-JennyNeural` (bright, energetic)
- `en-US-GuyNeural` (deep, authoritative male)
- `en-GB-SoniaNeural` (British English, formal)

**Speed tuning**: Use `-8%` to `-12%` for clarity; `-5%` for simpler content.
### Voice tuning guide

The AI agent should help the user choose appropriate TTS settings based on their presentation style:

**Voice selection by scenario:**

| Scenario | Recommended Voice | Why |
|----------|-------------------|-----|
| Academic conference | `en-US-EmmaNeural` | Warm but professional, clear enunciation |
| Energetic keynote | `en-US-JennyNeural` | Bright, engaging, keeps audience attention |
| Formal defense | `en-GB-SoniaNeural` | British English, authoritative and precise |
| Story-driven talk | `en-US-GuyNeural` | Deep, narrative quality |
| Data-heavy presentation | `en-US-AriaNeural` | Confident, paces well through technical content |

**Speed tuning by proficiency:**

| User level | Rate | Effect |
|------------|------|--------|
| Beginner | `-12%` | Very slow, clear, time to process each word |
| Intermediate | `-8%` | Natural pace with slight slowing (default) |
| Advanced | `-5%` | Near-natural speed for shadowing practice |
| Native-like | `-3%` to `0%` | Full speed, rhythm training |

**Multi-voice generation:**

Generate 2-3 voice variants so the user can switch in the web player:
```bash
python3 scripts/generate_tts.py --script director_script.md --output audio/ \
    --voices en-US-EmmaNeural,en-US-GuyNeural,en-GB-SoniaNeural
```

This creates subdirectories (`audio/Emma/`, `audio/Guy/`, `audio/Sonia/`) plus a `voice_manifest.json`. The HTML player auto-detects the manifest and shows a voice selector dropdown.

**Pause tuning:**

- `--pause-ms 200` — Tight, for fast-paced slides
- `--pause-ms 300` — Natural (default), one breath between sentences
- `--pause-ms 500` — Spacious, for slides with complex concepts

The longer pause (`--long-pause-ms`) applies after slide transitions and paragraph breaks.



### Step 4: Build the HTML trainer

Run the build script:

```bash
python3 scripts/build_trainer.py \
    --script director_script.md \
    --slides slides/ \
    --audio audio/ \
    --output recitation_trainer.html \
    --compress \
    --width 1200
```

This script:
- Parses the director script into structured JSON
- Compresses slide PNGs to optimized JPEGs (85% quality, 1200px max width)
- Embeds all data into the HTML template
- Generates a self-contained `recitation_trainer.html`

**Output folder structure:**

```
recitation-trainer-product/
├── recitation_trainer.html    # Double-click to open
├── audio/                     # TTS MP3 files
│   └── Slide01_连贯全文.mp3 ~ SlideNN_连贯全文.mp3
└── slides/                    # Compressed JPEG images
    └── Slide01.jpg ~ SlideNN.jpg
```

### Step 5: (Optional) Deploy to GitHub Pages

```bash
# Prepare deployment directory (use /tmp to avoid iCloud sync issues)
mkdir -p ~/tmp/recitation-deploy
cp -r recitation-trainer-product/* ~/tmp/recitation-deploy/
cd ~/tmp/recitation-deploy

# Initialize and push
git init && git checkout -b main
echo ".DS_Store" > .gitignore
git add -A
git commit -m "Initial deploy: English recitation trainer"

# Create repo and push
gh repo create USERNAME/REPO-NAME --public --source=. --remote=origin --push

# Enable GitHub Pages
gh api repos/USERNAME/REPO-NAME/pages -X POST \
    -f "source[branch]=main" -f "source[path]=/"
```

**Public URL**: `https://USERNAME.github.io/REPO-NAME/recitation_trainer.html`

Wait ~1-2 minutes for the first build. The page is then accessible on any device (desktop, phone, tablet).

### Step 6: Verify

Open the HTML locally to test:
```bash
open recitation_trainer.html
```

Or visit the GitHub Pages URL on mobile to confirm images and audio load correctly.

## Notes for the AI agent

- **Edge TTS is the default TTS engine.** It's free, requires no API key, and produces natural-sounding audio. Always suggest it first.
- **If the user has pre-existing TTS files**, skip Step 3 and use their files.
- **If Keynote is unavailable** (Linux/Windows), suggest manual screenshot export from PowerPoint or use `python-pptx` + Pillow for simple text-based previews.
- **Git work should happen in `/tmp/`**, not iCloud-synced directories.
- **Images must be JPEG for mobile compatibility.** PNG files > 1MB will fail on mobile browsers.
- **The HTML is completely self-contained.** No Node.js, no npm, no build step. Just a browser.
- **All paths are relative.** The product folder can be moved anywhere without breaking.

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Edge TTS fails | Try `pip3 install edge-tts --upgrade` |
| No `pdftoppm` | `brew install poppler` on macOS |
| Keynote export hangs | Close Keynote first: `killall Keynote` |
| Phone can't see images | Images too large — run `--compress` |
| GitHub Pages 404 | Wait 2 min, check `gh api repos/.../pages --jq '.status'` |
| Audio won't play on mobile | Ensure MP3 files are < 1MB each |
