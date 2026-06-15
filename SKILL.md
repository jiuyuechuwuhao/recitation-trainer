---
name: ppt-prepal
description: Build an interactive English presentation recitation trainer for Chinese speakers. Takes a PPTX file as input and produces a self-contained static HTML web app with slide previews, beat-by-beat oral scripts, TTS audio playback with sentence-level highlighting, and speed control — accessible on both desktop and mobile via Vercel. Use this skill when the user mentions "PPT PrePal", "PPTPrePal", "带读训练器", "英语pre带读", "presentation recitation", "背诵训练", "pre练习", "英文演讲稿熟记", "国际会议pre", "博士生英语pre", "TTS带读", or wants to build a presentation practice tool for academic conferences or doctoral English presentations.
---

# PPT PrePal · 英语 Pre 带读训练器

A complete end-to-end pipeline that turns a PowerPoint presentation into an interactive English recitation practice web app — designed for Chinese PhD students and researchers preparing for international academic conferences.

**Target users**: Chinese speakers who need to memorize and practice English presentations.
**Key scenarios**: Doctoral English pre, international conference presentations, thesis defense rehearsals.

## What this skill does

Starting from any input (PPTX / PDF / just a topic), this skill:

1. **Generates a director script** (导演台本) — AI analyzes each slide and writes a beat-by-beat oral English script with flowing full text
2. **Exports slide screenshots** — render each PPTX slide as a high-quality PNG image
3. **Generates TTS audio** — use free Edge TTS to narrate each slide's full text as MP3
4. **Compresses images** — optimize PNG to JPEG for fast mobile loading
5. **Builds the trainer HTML** — a self-contained, dark-themed web app with:
   - Collapsible panels (one per slide)
   - PPT slide preview images
   - Beat-by-beat oral script table (4 columns: beat #, PPT guide, English, action)
   - Flowing full text with per-sentence highlighting synced to audio
   - Play/pause button per slide
   - Global speed control (0.5x–2.0x)
   - Keyboard shortcuts (Space, Arrow keys)
6. **Deploys to Vercel** (optional) — get a public URL accessible on any device
   - PPT slide preview images
   - Beat-by-beat oral script table (4 columns: beat #, PPT guide, English, action)
   - Flowing full text with per-sentence highlighting synced to audio
   - Play/pause button per slide
   - Global speed control (0.5x–2.0x)
   - Keyboard shortcuts (Space, Arrow keys)


## Prerequisites

The user needs:
- A presentation topic, a PDF paper, or a PPTX file (this skill adapts to all three)
- Python 3 with `pip3` (for Edge TTS, Pillow, python-pptx)
- `pdftoppm` (for PDF→PNG conversion, install via `brew install poppler` on macOS)
- macOS with Keynote (for PPTX→PDF export)
- Git and GitHub account (for optional deployment)
- `vercel` CLI (for optional deployment, install via `npm install -g vercel`)

No API keys, no paid services. Everything is free and runs locally.

## Complete Workflow


### Step 0: Input auto-detection & environment setup

**This is the routing step.** The AI agent must FIRST determine what the user has, then choose the correct branch.

Run environment check in parallel with input detection:

```bash
# 0a. Environment check (always run first)
# Find a working Python 3 with pip. Try common paths in order:
# 1. /opt/homebrew/bin/python3 (macOS Homebrew)
# 2. /usr/bin/python3 (macOS system)
# 3. which python3 (whatever is in PATH)
for py in /opt/homebrew/bin/python3 /usr/bin/python3 $(which python3 2>/dev/null) python3; do
    $py --version >/dev/null 2>&1 && { SYSTEM_PYTHON=$py; break; }
done
$SYSTEM_PYTHON --version >/dev/null 2>&1 || { echo "ERROR: No working Python found"; exit 1; }
echo "Using Python: $SYSTEM_PYTHON ($($SYSTEM_PYTHON --version))" 
$SYSTEM_PYTHON SKILL_DIR/scripts/check_env.py
```

`check_env.py` output is a JSON summary. Read it, and if Python packages are missing, re-run to confirm auto-install. If system tools (pdftoppm, Keynote) are missing, follow the fallback table below.

#### 0b. Input classification

The AI agent scans the user's files and classifies the starting state into exactly one of these branches:

| Branch | What the user has | What the agent does |
|--------|-------------------|---------------------|
| **A: Full PPTX** | A .pptx file with slides already designed | Go to Step 1A (extract text → generate script) |
| **B: PDF only** | A .pdf (paper/article) | Go to Step 1B (extract text → generate script → `pdftoppm` exports slide images directly from PDF) |
| **C: Nothing** | Just a topic or a vague idea | Go to Step 1C (AI designs slide outline → generates script → guides user to create slides) |

**Branch C user guidance template:**

> "I've designed an X-slide presentation outline and director script. Now create your slides:
> 1. Open WPS/PowerPoint/Keynote
> 2. Create X slides matching the titles in the script
> 3. Content on each slide should match the beat-by-beat notes
> 4. Save as `.pptx` and give me the path — I'll auto-export images and build the trainer." 

**How the agent decides:**

```
LOOK at the user's message and any attached/files they mentioned.
  - Contains a .pptx path? → Branch A
  - Contains a .pdf path (no .pptx)? → Branch B
  - No file reference, just a topic name? → Branch C
```

**⚠️ Critical routing rules:**

- **Branch B (PDF):** Export slides directly with `pdftoppm`. The PDF IS the slide source. DO NOT ask the user to create a PPTX.
- **Branch C (nothing):** The user MUST create a PPTX. The AI gives them the slide outline from the script, they build slides, then the pipeline continues with `export_slides.py`. DO NOT proceed to Step 2 without the PPTX.

For Branch B, the slide export happens inside Step 2, using `pdftoppm` instead of `export_slides.py` (see Step 2 instructions).

### ⚠️ Shell Safety: Handling user-provided file paths

User file paths may contain spaces, Chinese characters, or special characters (like vertical tabs ``). **Never hardcode a user-provided path in shell commands.** Instead:

1. **Always quote variables**: `"$PDF"`, `"$TEST_DIR"`, never bare `$PDF`
2. **Use find/ls to locate files** rather than relying on exact path strings:
   ```bash
   # Safe: let the shell glob and capture the result
   PDF=$(ls "$HOME/Downloads/"*王小明*.pdf 2>/dev/null | head -1)
   ```
3. **Prefer Python for file operations** when possible. All scripts use `open()` and `Path()` which handle arbitrary Unicode natively.
4. **If a path contains unusual characters**, copy the file to a safe temp name before processing:
   ```bash
   SAFE_PDF="/tmp/input_$(date +%s).pdf"
   cp "$PDF" "$SAFE_PDF"
   ```



#### Legacy: Quick environment summary for the AI agent

After `check_env.py`, refer to this table when tools are missing:

| If missing... | Action |
|---------------|--------|
| Python packages | Auto-installed by the script — re-run to verify |
| `pdftoppm` | `brew install poppler` (macOS) / `sudo apt install poppler-utils` (Linux) |
| Keynote (macOS missing) | Fallback A: manual PNG export, or Python-based slide rendering |
| LibreOffice (Linux missing) | Fallback B: `python-pptx` + Pillow simple previews |
| `gh` CLI | Skip Vercel deployment — local HTML still works |

#### Fallback slide export methods

When Keynote/LibreOffice is unavailable:

Fallback A — Manual:
> "Please export your PPTX slides as PNG images: open in PowerPoint/Google Slides → File → Export → PNG. Save as Slide01.png through SlideNN.png in a `slides/` folder."

Fallback B — Python-based (basic quality):
```bash
python3 SKILL_DIR/scripts/export_slides.py --method python-pptx presentation.pptx slides/
```



### Step 1: Generate the director script (导演台本)

This step produces `director_script.md` — a structured oral script that follows the JSON Schema at `assets/director_script_schema.json`.

**The format is strict.** Every slide must have:

```
## Slide N — TITLE

| 拍 | PPT 指引 | 英文口述 | 动作 |
|---|---|---|---|
| 1 | 手指向… | One short English sentence. | gesture |
| 2 | … | … | … |

**连贯全文**：
> All english lines concatenated into one flowing paragraph. This becomes the TTS input.
```

**The `连贯全文` paragraph is critical** — it's what Edge TTS reads and what the player highlights sentence-by-sentence. It must be a natural, conversational monologue (not a list, not bullet points).

#### Branch 1A: From PPTX (user has slides)

```bash
# Step 1A: Extract slide text for the AI to read
$SYSTEM_PYTHON SKILL_DIR/scripts/extract_pptx_text.py presentation.pptx
```

The agent reads this output and generates `director_script.md` directly — the slide structure already exists, so the agent writes beats that match each slide's content.

#### Branch 1B: From PDF (user has a paper/article, no slides)

```bash
# Step 1B.i: Get page count (MANDATORY — this determines the script length)
PAGES=$(pdfinfo paper.pdf | grep Pages | awk '{print $2}')
echo "PDF has $PAGES pages — script will have exactly $PAGES slides"

# Step 1B.ii: Extract text from PDF WITH PAGE MARKERS
# Use -layout to preserve layout, form feeds (^L) mark page breaks
pdftotext -layout paper.pdf source_text.txt
```

The agent reads `source_text.txt` and finds page boundaries by the `` (form feed) character between pages. Each page becomes one slide.

1. **MUST use the PDF page count** — the director script has exactly N slides where N = PDF pages. One slide per PDF page, in strict order. Each page's visible title/header becomes the slide title. DO NOT summarize, consolidate, or reduce.
2. **Generates `director_script.md`** — each slide's `full_text` is the oral delivery for that page's content. Format: `## Slide N — TITLE` followed by beat table and full text.
3. **Proceeds directly to Step 2** — `pdftoppm` exports slide images (N pages → N PNGs).

#### Branch 1C: From nothing (just a topic)

The agent asks the user for:

1. The presentation topic/title
2. Estimated duration (e.g., 10 min / 20 min)
3. Any key points they want to cover

Then the agent:
1. **Designs a slide outline** from scratch
2. **Generates `director_script.md`**
3. **Prompts the user to create PPTX slides** (same as 1B)

#### Schema enforcement

All branches produce output that conforms to `assets/director_script_schema.json`. The key rules:

- Each slide is one entry in the `slides` array
- `full_text` = all `english` lines concatenated, natural flowing prose
- `beats` array: minimum 1 beat per slide, each beat has `ppt_guide` (Chinese) and `english`
- The Markdown format above is the canonical representation


### Step 2: Export slide screenshots

**The export method depends on which Branch we're on:**

#### Branch A & C: From PPTX

Guide the user to export slides from their PPTX. The manual guide covers all major tools:

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

Automated fallback (lower quality, loses backgrounds):

```bash
python3 scripts/export_slides.py presentation.pptx slides/
```

The AI agent should present the manual guide by default. Only offer the automated fallback if the user explicitly says they don't care about visual quality.

#### Branch B: From PDF

Use `pdftoppm` — converts each PDF page to a PNG image directly. No user intervention needed:

```bash
mkdir -p slides
pdftoppm -png -r 200 paper.pdf slides/Slide

# Rename: pdftoppm outputs Slide-1.png etc. → Slide01.png
cd slides
i=1
for f in Slide-*.png; do
    mv "$f" $(printf "Slide%02d.png" "$i")
    ((i++))
done
```

This produces `slides/Slide01.png` through `slides/SlideNN.png` — identical to what Step 4's `build_trainer.py` expects.



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

### Step 5: Deliver — open locally and verify

Build is complete. The deliverables are in the output folder:

```
recitation-trainer-product/
├── recitation_trainer.html   ← Double-click to open
├── audio/                    ← TTS MP3 files
└── slides/                   ← Compressed JPEG images
```

Open the HTML and check:

```bash
open recitation_trainer.html
```

The AI agent should tell the user: **"The trainer is ready. Open `recitation_trainer.html` and check: slide images, audio playback, beat table, sentence highlighting. If anything is off, tell me and I'll fix it."**

**⚠️ STOP HERE.** Do not proceed to Step 6 until the user confirms everything is correct.

### Step 6: (Optional) Deploy for public access

Only run this step if the user explicitly asks to deploy. Ask first:

> "The trainer looks good locally. Would you like me to deploy it so you can access it on your phone? Two free options: GitHub Pages (accessible in China, slightly more steps) or Vercel (one-command deploy, faster, but **blocked in China** — requires VPN)."

#### Option A · GitHub Pages (default, accessible in China)

```bash
# 0. (one-time) Set up SSH for GitHub — each user generates their OWN key
ssh-keygen -t ed25519 -C "your.email@example.com"
cat ~/.ssh/id_ed25519.pub  # Copy the output → paste at GitHub → Settings → SSH Keys → New

# 1. Create a GitHub repo (public) and push the product folder
cd recitation-trainer-product/
git init
git checkout -b main
git add .
git commit -m "Initial recitation trainer deploy"
git remote add origin git@github.com:YOUR_USERNAME/YOUR_REPO.git
GIT_SSH_COMMAND="ssh -o StrictHostKeyChecking=accept-new" git push -u origin main

# 2. Enable GitHub Pages via API (gh repo edit does NOT support --pages-source-branch)
gh api repos/YOUR_USERNAME/YOUR_REPO/pages -X POST -f "source[branch]=main"
gh api repos/YOUR_USERNAME/YOUR_REPO/pages --jq '.html_url'

# 3. Wait for GitHub to build (~1 min), then verify
gh api repos/YOUR_USERNAME/YOUR_REPO/pages --jq '.status'
# Expected: "built"
```

> ⚠️ **Git Push Issues**: If `git add` fails with "pathspec did not match", use directory globs: `git add audio/ slides/ recitation_trainer.html` instead of `git add .`. This happens when filenames contain CJK characters.

#### Option B · Vercel (one-command, blocked in China — VPN required)

```bash
# Install Vercel CLI if needed
which vercel || npm install -g vercel

# Login (one-time, browser-based OAuth)
vercel login

# Deploy — all files at once, no batching needed
cd recitation-trainer-product/
vercel --prod --yes
```

**Public URL**: `https://PROJECT-NAME.vercel.app`

### Deployment comparison

| | GitHub Pages | Vercel |
|---|---|---|
| **China access** | ✅ Yes | ❌ Blocked (needs VPN) |
| **Deploy speed** | ~1 min | ~10 sec |
| **File count limit** | None (batching needed) | None |
| **One-time setup** | `gh repo create` + enable Pages | `npm install -g vercel` + `vercel login` |
| **SSO protection** | None | **Must disable** (see below) |

### ⚠️ Known issues from live testing (Step 6: Deployment)

**Vercel SSO Protection** — Vercel free-tier static deployments default to "Vercel Authentication" (SSO login wall). This cannot be disabled via CLI. The user must:

1. 打开浏览器 → `https://vercel.com` → 选择对应项目 → Settings → Deployment Protection
2. 找到 **"Vercel Authentication"** 区块（"Visitors must be logged in…"），将 **"Require Log In"** 开关关闭
3. 终端重新 `vercel --prod --yes` 重部署

> ⚠️ 此操作仅需一次。长哈希 URL 同样受 SSO 保护，不可绕过。

**Vercel blocked in China** — Vercel 使用海外 CDN（AWS/Google Cloud），国内无 VPN 无法访问。中国用户应优先使用 GitHub Pages。

**Alternative: consider not deploying.** Step 5 delivers a working local HTML. Many users may not need public deployment. The AI agent should ask whether deployment is truly needed before attempting Step 6.

### Known constraints (general pipeline)

These are hard constraints discovered during testing. The AI agent should be aware of them:

| Issue | Root Cause | Status |
|-------|-----------|--------|
| `--rate "-8%"` in shell: `%` gets swallowed by argparse | `--rate` default contains `%`, Python's `%%` in help string interferes | **Fixed** (v2.9.1): use `-8` without `%`, append `%` in code |
| Chinese filenames break `git add` pathspec | Git encodes CJK characters as octal escapes | **Mitigated**: use `git add audio/` (directory glob), or prefer Vercel |
| HTTPS `git push` to GitHub fails with RPC 400 from China | GitHub blocks large HTTPS POST requests via GFW | **Fixed**: use SSH remote (`git@github.com:...`) instead of HTTPS |
| Which `python3` has `edge-tts`? | macOS has multiple Pythons; `pip3 install` target ≠ runtime | **Fixed** (v3.0.0): `SYSTEM_PYTHON` now tries `/opt/homebrew/bin/python3` first |
| PDF font mismatch warnings clutter output | `pdftotext` and `pdftoppm` emit "Syntax Warning: Mismatch between font type" for some Chinese PDFs | **Harmless** — output is fine, just noisy. Ignore. |## Notes for the AI agent

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
| Vercel blocked in China (can't open page) | Use GitHub Pages instead — see Step 6 Option A |
| Audio won't play on mobile | Ensure MP3 files are < 1MB each |
