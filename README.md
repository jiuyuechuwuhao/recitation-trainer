# 🎙️ PPT PrePal · 英语 Pre 带读训练器

> 一款面向中国博士生的英文 Presentation 带读训练工具。输入 PPT，输出一个带语音跟读、逐句高亮、语速可控的交互式网页。

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Codex Ready](https://img.shields.io/badge/Codex-✓-blue)](https://github.com/jiuyuechuwuhao/ppt-prepal)
[![Claude Code Ready](https://img.shields.io/badge/Claude%20Code-✓-orange)](https://github.com/jiuyuechuwuhao/ppt-prepal)

---

## 🎯 解决的问题

中国的博士生、研究人员在准备国际学术会议或英文课程 Pre 时，面临三个核心痛点：

| 痛点 | 传统方式 | 本工具 |
|------|----------|--------|
| **记不住稿子** | 死记硬背，上台卡壳 | 逐拍拆解 + TTS 带读，科学熟记 |
| **发音不自信** | 自己录音，反复纠错 | 原生英语 TTS，逐句高亮跟读 |
| **练习不方便** | 电脑前对着 PPT 练 | **手机也能练**——部署网页后随时随地打开 |

## 🚀 核心功能

- **PPT → 带读网页**：输入 PPTX，全自动生成交互式练习页面
- **逐拍口述表**：每页 PPT 拆解为多个口述节拍，配有动作指引
- **TTS 语音带读**：微软 Edge TTS 引擎，免费，神经网络音质
- **逐句高亮**：播放音频时，当前句子高亮 + 自动滚动
- **全局语速控制**：0.5x ~ 2.0x，适应不同熟练度
- **手机可用**：部署到 Vercel 后，在任何设备上打开
- **零依赖部署**：纯静态 HTML，无后端，无数据库

## 📸 效果预览

![Demo](https://img.shields.io/badge/Live%20Demo-jiuyuechuwuhao.github.io/ufo--presentation-blue)

> 实际案例：[Disclosure Day 带读训练器](https://jiuyuechuwuhao.github.io/ufo-presentation/recitation_trainer.html)（21 页学术英文 Pre）

## 🛠️ 快速开始

### 安装

```bash
# 1. 克隆仓库
git clone https://github.com/jiuyuechuwuhao/ppt-prepal.git
cd ppt-prepal

# 2. 一键环境检测 + 自动安装
python3 scripts/check_env.py
# 自动检测 OS、安装缺失的 Python 包、报告系统工具状态

# 3. 在智能体中安装 Skill
# 下载 Releases 中的 .skill 包导入 Codex / Claude Code / Gemini CLI 等
```

**支持的操作系统：** macOS ✅ | Linux ✅ | Windows ⚠️（手动导出PPT截图）

### 使用流程

```bash
# Step 1: 提取 PPT 内容，AI 据此生成导演台本
python3 scripts/extract_pptx_text.py my_presentation.pptx

# Step 2: AI 智能体根据提取的内容，生成导演台本 director_script.md
# （由 AI 自动完成——分析每页内容，编写逐拍口述 + 连贯全文）

# Step 3: 导出 PPT 幻灯片截图
# （macOS Keynote 自动导出为 PNG，见 SKILL.md）

# Step 4: 生成 TTS 音频
python3 scripts/generate_tts.py --script director_script.md --output audio/

# Step 5: 构建带读网页
python3 scripts/build_trainer.py \
    --script director_script.md \
    --slides slides/ \
    --audio audio/ \
    --output recitation_trainer.html \
    --compress

# Step 6: （可选）部署到 Vercel
# 见 SKILL.md 中的详细步骤
```

## 🎓 应用场景

### 场景一：博士生英文 Pre

> 博士课程中需要做 20 分钟英文 Presentation，稿子写好了但总是背不熟。
>
> → 用本工具生成带读页面，手机打开，上下课路上随时跟读练习。

### 场景二：国际学术会议

> 投稿被接收，需要在 300 人面前做 15 分钟英文报告。发音不自信，害怕忘词。
>
> → 逐拍口述表帮你理解每页 PPT 的逻辑流，TTS 带读训练发音和节奏。

### 场景三：论文答辩

> 英文答辩前需要熟记研究背景、方法论和结论。
>
> → 语速调到 0.75x 精听，再调到 1.0x 跟读，最后调 1.25x 检测熟练度。

## 📂 项目结构

```
ppt-prepal/
├── SKILL.md                          # AI 智能体指令（核心）
├── README.md                         # 本文件
├── scripts/
│   ├── check_env.py                  # 🔍 环境检测 + 自动安装依赖
│   ├── check_env.py                  # 🔍 环境检测 + 自动安装依赖
│   ├── export_slides.py              # 🖼️ 一键 PPTX → PNG（纯 Python）
│   ├── extract_pptx_text.py          # 从 PPTX 提取文字内容
│   ├── generate_tts.py               # Edge TTS 音频生成
│   └── build_trainer.py              # HTML 构建 + 图片压缩
└── assets/
    └── trainer_template.html         # 网页模板
```

## 🔧 技术栈

| 组件 | 技术 | 说明 |
|------|------|------|
| TTS 引擎 | Edge TTS | 免费，微软神经网络语音 |
| 图片处理 | python-pptx + Pillow | 一键导出一页不落 |
| PPT 解析 | python-pptx | 提取文字内容 |
| 前端 | 纯 HTML + CSS + JS | 零框架，零构建 |
| 部署 | Vercel | 免费，全球 CDN |

## 🤝 兼容的 AI 智能体

- **Codex** (OpenAI)
- **Claude Code** (Anthropic)
- **Gemini CLI** (Google)
- **OpenCode**
- **Hermes**
- 任何支持 Skill/Agent 规范的 AI 编程助手

## 📄 许可证

MIT License — 自由使用、修改、分发。

---

**Made with ❤️ for Chinese PhD students preparing for the world stage.**
