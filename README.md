# AI 简历生成器 (AI Resume Generator)

一款基于 AI 的专业简历生成工具，模拟 10+ 年经验的资深招聘专家，为您打造 **ATS 兼容**、**成就导向** 且 **排版精美** 的现代简历。支持一键生成 Markdown 和可打印的 HTML 格式。

## ✨ 核心功能

*   **智能内容生成**：基于 GPT-4o/DeepSeek 等大模型，自动优化简历措辞，强调量化成果（增长率、金额、效率提升）。
*   **ATS 友好**：结构化内容，确保能顺利通过招聘系统的自动筛选。
*   **精美排版**：
    *   **自动排版**：内置专业 CSS 样式，生成类似 LaTeX 的高质量排版。
    *   **头像支持**：支持自动裁剪并居中显示圆形头像。
    *   **打印优化**：专为 A4 纸打印设计，智能分页，保留背景色和样式。
*   **多格式输出**：同时生成 `.md` (Markdown) 和 `.html` (网页/PDF源) 文件。
*   **网络支持**：完整支持 HTTP/HTTPS 代理，方便国内用户连接 OpenAI/DeepSeek API。

## 🚀 快速开始

### 方式一：直接运行 (Windows)
下载最新版本的 `dist/ResumeGenerator_v8.exe`，直接双击运行即可。

### 方式二：源码运行

1.  **安装依赖**
    ```bash
    pip install -r requirements.txt
    ```

2.  **配置 (可选)**
    创建 `.env` 文件配置 API Key（也可以在运行时输入）：
    ```env
    OPENAI_API_KEY=sk-您的APIKey
    # 可选：自定义 Base URL (例如 DeepSeek)
    # OPENAI_BASE_URL=https://api.deepseek.com
    # OPENAI_MODEL=deepseek-chat
    ```

3.  **运行程序**
    ```bash
    python demoX/generate_resume.py
    ```

## 📖 使用指南

### 1. 命令行参数
程序支持丰富的命令行参数，方便自动化或批处理：

```bash
# 基本用法
python demoX/generate_resume.py

# 指定头像和代理
python demoX/generate_resume.py --avatar "C:\Photos\me.jpg" --proxy "http://127.0.0.1:7890"

# 完整参数列表
--api_key      OpenAI API Key
--base_url     API Base URL (如 https://api.deepseek.com)
--model        模型名称 (默认: gpt-4o)
--language     简历语言 (默认: 中文)
--position     目标职位
--info_file    包含用户信息的文本文件路径
--avatar       头像 URL 或本地路径 (默认: 占位图)
--proxy        HTTP/HTTPS 代理地址
--output_md    Markdown 输出路径
```

### 2. 如何生成完美 PDF
程序运行后会在桌面生成 `generated_resume.html`。为了获得最佳效果，请按照以下步骤转换为 PDF：

1.  **打开文件**：使用 **Chrome** 或 **Edge** 浏览器双击打开 `generated_resume.html`。
2.  **打印**：按下 `Ctrl + P` (或右键 -> 打印)。
3.  **设置**：
    *   **目标打印机**：选择 **"另存为 PDF"** (Save as PDF)。
    *   **更多设置**：务必勾选 **"背景图形"** (Background graphics) 以保留代码块背景和样式。
    *   **边距**：建议选择 "默认" 或 "无" (样式表中已内置 A4 边距)。
4.  **保存**：点击保存即可获得一份排版完美的 PDF 简历。

## 🛠️ 常见问题

**Q: 连接 API 失败/超时？**
A: 如果您在中国大陆，请务必使用 `--proxy` 参数设置代理（如 `http://127.0.0.1:7890`），或使用国内的大模型服务（如 DeepSeek, Moonshot）。

**Q: 身份验证失败 (401 Unauthorized)？**
A: 请检查：
1. API Key 是否有多余空格。
2. Key 是否与 Base URL 匹配（例如：不要在 OpenAI 官方 URL 使用 DeepSeek 的 Key）。

**Q: 头像不显示？**
A: 请确保 `--avatar` 路径正确。如果是本地图片，建议使用绝对路径；如果是网络图片，请确保 URL 可访问。

## 📄 许可证
MIT License
