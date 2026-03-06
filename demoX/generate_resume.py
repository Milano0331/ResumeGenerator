import os
import sys
import argparse
import logging
import shutil
import httpx
import markdown
from openai import OpenAI, APIConnectionError, AuthenticationError
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Import DOCX generator if available
# DOCX functionality removed
DOCX_AVAILABLE = False

# Load environment variables
load_dotenv()

def check_disk_space(path, min_free_bytes=10 * 1024 * 1024):
    """Check if there is enough free disk space."""
    try:
        # Get the drive of the path
        drive = os.path.splitdrive(os.path.abspath(path))[0]
        if not drive:
            drive = "."
        
        total, used, free = shutil.disk_usage(drive)
        logger.info(f"Disk space on {drive}: {free / (1024*1024):.2f} MB free")
        
        if free < min_free_bytes:
            logger.error(f"Insufficient disk space. Required: {min_free_bytes} bytes, Available: {free} bytes")
            return False
        return True
    except Exception as e:
        logger.warning(f"Could not check disk space: {e}")
        return True # Assume space is ok if check fails

def generate_resume_content(api_key, base_url, model_name, language, target_position, user_info, avatar_path, proxy=None):
    """
    Call OpenAI API (or compatible interface) to generate resume content.
    """
    http_client = None
    if proxy:
        logger.info(f"Using proxy: {proxy}")
        http_client = httpx.Client(proxies=proxy)
    
    client = OpenAI(
        api_key=api_key, 
        base_url=base_url if base_url else None,
        http_client=http_client
    )

    system_prompt = f"""
你是资深招聘专家(10+年经验)。
你浏览过数千份简历，深知ATS系统如何运作。

使用以下信息创建简历，并严格遵守以下 Markdown 排版规范：

### 1. 结构与排版规则：
- **头像展示**：在文档最顶部插入以下 HTML 代码以显示头像：
  `<div align="center"><img src="{avatar_path}" width="120" height="120" style="border-radius: 50%; object-fit: cover; margin-bottom: 20px;"></div>`
- **标题层级**：第一行必须是 `# 姓名`。二级标题使用 `## 模块名`（如：## 职业总结, ## 工作经历）。确保标题前后有空行。
- **联系方式**：姓名下方紧跟联系方式（电话 | 邮箱 | 地址 | 链接），使用居中排版：`<div align="center">电话 | 邮箱 | 链接</div>`。
- **列表规范**：使用 `- ` 进行无序列表排版。确保列表项缩进一致，每项内容简洁有力。
- **强调样式**：关键词或重要成就使用 **粗体**。
- **间距控制**：各主要模块（##）之间保持两行空行，段落之间保持一行空行。
- **表格与代码**：如涉及技术栈，可使用 `代码块` 形式；如涉及对比数据，可使用 Markdown 表格。
- **成就导向**：每段工作必须包含数字成果（百分比、金额、时间、增长）。

### 2. 内容要求：
- ATS 兼容，现代专业，不超过 1-2 页。
- 使用主动动词，避免陈词滥调。
- 自然融入目标职位关键词。
"""

    user_prompt = f"""
简历语言: {language}
目标职位: {target_position}

我的信息：
{user_info}

请根据以上信息和规则生成一份专业的简历。
"""

    try:
        logger.info(f"Sending request to API... (Base URL: {client.base_url})")
        response = client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7
        )
        return response.choices[0].message.content
    except AuthenticationError as e:
        logger.error(f"身份验证失败 (401 Unauthorized): {e}")
        logger.error("请检查您的 API Key 是否正确。")
        logger.error("1. 确保没有多余的空格。")
        logger.error("2. 确保 API Key 与 Base URL 匹配 (例如 DeepSeek 的 Key 不能用于 Moonshot)。")
        return f"Error: Authentication failed. {str(e)}"
    except APIConnectionError as e:
        logger.error(f"连接 API 失败: {e}")
        logger.error("请检查网络连接、Base URL 配置或是否需要设置代理 (Proxy)。")
        logger.error("如果您在中国大陆，可能需要使用代理或国内的 API 镜像服务。")
        return f"Error: Connection error. {str(e)}"
    except Exception as e:
        return f"Error generating resume: {str(e)}"

def main():
    print("=== AI 简历生成器 ===")

    # 获取桌面路径
    try:
        desktop_path = os.path.join(os.path.join(os.environ['USERPROFILE']), 'Desktop')
    except Exception:
        desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
    
    # 确保使用绝对路径
    desktop_path = os.path.abspath(desktop_path)
    
    if not os.path.exists(desktop_path):
        # 如果桌面路径不存在（非常罕见），尝试创建或者回退到当前目录
        logger.warning(f"检测到桌面路径 {desktop_path} 不存在，尝试创建...")
        try:
            os.makedirs(desktop_path, exist_ok=True)
        except Exception as e:
            logger.error(f"无法创建桌面路径: {e}")
            desktop_path = os.getcwd()
            logger.warning(f"已回退输出目录至当前工作目录: {desktop_path}")

    logger.info(f"默认输出目录: {desktop_path}")
    
    default_md_path = os.path.join(desktop_path, "generated_resume.md")

    parser = argparse.ArgumentParser(description="AI 简历生成器")
    parser.add_argument("--api_key", help="OpenAI API Key (如果未在环境变量设置)")
    parser.add_argument("--base_url", help="API Base URL (例如: https://api.deepseek.com, https://api.moonshot.cn/v1 等)")
    parser.add_argument("--model", help="模型名称 (默认: gpt-4o，可使用 deepseek-chat, moonshot-v1-8k 等)")
    parser.add_argument("--language", default="中文", help="简历语言 (默认: 中文)")
    parser.add_argument("--position", help="目标职位")
    parser.add_argument("--info_file", help="包含用户信息的文本文件路径")
    parser.add_argument("--output_md", default=default_md_path, help=f"Markdown 输出路径 (默认: {default_md_path})")
    parser.add_argument("--proxy", help="HTTP/HTTPS 代理地址 (例如: http://127.0.0.1:7890)")
    parser.add_argument("--avatar", default="https://via.placeholder.com/120", help="头像 URL 或本地路径 (默认: 占位图)")
    
    args = parser.parse_args()

    # 1. Configuration
    api_key = args.api_key or os.getenv("OPENAI_API_KEY")
    base_url = args.base_url or os.getenv("OPENAI_BASE_URL")
    model_name = args.model or os.getenv("OPENAI_MODEL") or "gpt-4o"
    proxy = args.proxy or os.getenv("HTTPS_PROXY") or os.getenv("HTTP_PROXY")

    if not api_key:
        print("\n提示: 支持 OpenAI 以及所有兼容 OpenAI 接口的模型服务。")
        print("例如: DeepSeek, Moonshot (Kimi), SiliconFlow, ZhipuAI 等。")
        print("如果是第三方服务，请确保后续正确输入 Base URL 和 Model 名称。\n")
        api_key = input("请输入您的 API Key: ").strip()
        if not api_key:
            logger.error("错误: 必须提供 API Key 才能继续。")
            return

    if not base_url and not os.getenv("OPENAI_BASE_URL"):
        use_custom = input("\n是否需要设置自定义 Base URL (用于 DeepSeek/Moonshot 等第三方服务)? [y/N]: ").strip().lower()
        if use_custom == 'y':
            print("常见 Base URL 示例:")
            print("- DeepSeek: https://api.deepseek.com")
            print("- Moonshot: https://api.moonshot.cn/v1")
            base_url = input("请输入 Base URL: ").strip()

    if not proxy:
        use_proxy = input("\n是否需要设置 HTTP 代理 (如果您在中国大陆且使用 OpenAI 官方 API)? [y/N]: ").strip().lower()
        if use_proxy == 'y':
            print("例如: http://127.0.0.1:7890")
            proxy = input("请输入代理地址: ").strip()

    if not args.model and not os.getenv("OPENAI_MODEL"):
        change_model = input(f"\n当前默认模型为 '{model_name}'。是否需要修改? [y/N]: ").strip().lower()
        if change_model == 'y':
            model_name = input("请输入模型名称 (例如 deepseek-chat): ").strip()

    logger.info(f"当前配置: Base URL: {base_url if base_url else '默认 (OpenAI Official)'}, Model: {model_name}, Proxy: {proxy if proxy else '无'}")

    # 2. Input Data
    language = args.language
    if not args.position:
        target_position = input("\n请输入目标职位: ").strip()
    else:
        target_position = args.position
        
    user_info = ""
    if args.info_file:
        try:
            with open(args.info_file, 'r', encoding='utf-8') as f:
                user_info = f.read()
        except Exception as e:
            logger.error(f"读取信息文件出错: {e}")
            return
    else:
        print("\n请输入您的经历、教育、技能等信息 (输入 'END' 结束):")
        lines = []
        while True:
            try:
                line = sys.stdin.readline()
            except KeyboardInterrupt:
                break
            if not line or line.strip() == 'END':
                break
            lines.append(line)
        user_info = "".join(lines)

    if not target_position or not user_info.strip():
        logger.error("错误: 目标职位和个人信息不能为空。")
        return

    # 3. Generate Resume
    print("\n正在生成简历，请稍候...")
    resume_content = generate_resume_content(api_key, base_url, model_name, language, target_position, user_info, args.avatar, proxy=proxy)

    if resume_content.startswith("Error"):
        logger.error(resume_content)
        return

    # 4. Save Markdown
    output_md = os.path.abspath(args.output_md)
    output_dir = os.path.dirname(output_md)
    
    # 诊断: 检查输出目录
    if not check_disk_space(output_dir):
        logger.error("磁盘空间不足，无法保存文件。")
        return

    try:
        # Ensure directory exists
        if output_dir and not os.path.exists(output_dir):
            logger.info(f"输出目录不存在，尝试创建: {output_dir}")
            os.makedirs(output_dir, exist_ok=True)
            
        # Verify write permissions by trying to create a temp file
        test_file = os.path.join(output_dir, ".write_test")
        try:
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
        except Exception as e:
            logger.error(f"无法写入目标目录 {output_dir}。请检查权限。错误: {e}")
            return

        with open(output_md, "w", encoding="utf-8") as f:
            f.write(resume_content)
        logger.info(f"简历 Markdown 已保存至: {output_md}")
        
        # 6. Generate HTML with Print Styles
        output_html = output_md.replace('.md', '.html')
        html_content = markdown.markdown(resume_content, extensions=['tables', 'fenced_code'])
        
        # Enhanced CSS for Print
        full_html = f"""
<!DOCTYPE html>
<html lang="{language}">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Resume - {target_position}</title>
    <style>
    /* Reset & Base */
    body {{
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, "Microsoft YaHei", sans-serif;
        line-height: 1.6;
        color: #333;
        max-width: 800px;
        margin: 0 auto;
        padding: 40px;
        background: #fff;
    }}
    
    /* Typography */
    h1 {{
        font-size: 2.4em;
        text-align: center;
        color: #2c3e50;
        margin-bottom: 0.5em;
        line-height: 1.2;
    }}
    h2 {{
        font-size: 1.5em;
        color: #34495e;
        border-bottom: 2px solid #eaecef;
        padding-bottom: 0.3em;
        margin-top: 2em;
        margin-bottom: 1em;
        page-break-after: avoid; /* Prevent headings from being orphaned */
    }}
    h3 {{
        font-size: 1.2em;
        color: #455a64;
        margin-top: 1.2em;
        page-break-after: avoid;
    }}
    p {{
        margin-bottom: 1em;
    }}
    
    /* Components */
    ul {{
        padding-left: 20px;
        margin-bottom: 1em;
    }}
    li {{
        margin-bottom: 0.5em;
    }}
    code {{
        background-color: #f6f8fa;
        padding: 0.2em 0.4em;
        border-radius: 3px;
        font-family: Consolas, "Courier New", monospace;
        color: #e83e8c;
        -webkit-print-color-adjust: exact; /* Force print background */
        print-color-adjust: exact;
    }}
    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 1.5em 0;
        page-break-inside: avoid; /* Prevent table break */
    }}
    th, td {{
        border: 1px solid #dfe2e5;
        padding: 0.8em 1em;
    }}
    th {{
        background-color: #f6f8fa;
        font-weight: 600;
        -webkit-print-color-adjust: exact;
        print-color-adjust: exact;
    }}
    img {{
        max-width: 100%;
        display: block;
        margin: 0 auto;
    }}
    
    /* Print Specifics */
    @media print {{
        body {{
            max-width: 100%;
            padding: 0;
            margin: 0;
        }}
        @page {{
            margin: 1.5cm; /* Standard margin */
            size: A4 portrait;
        }}
        h2 {{
            margin-top: 1.5em; /* Reduce spacing for print */
        }}
        a {{
            text-decoration: none;
            color: #000;
        }}
        /* Ensure background colors are printed */
        * {{
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}
    }}
    </style>
</head>
<body>
{html_content}
</body>
</html>
"""
        with open(output_html, "w", encoding="utf-8") as f:
            f.write(full_html)
        logger.info(f"简历 HTML 已保存至: {output_html} (推荐使用浏览器打开并打印为 PDF)")
        
    except Exception as e:
        logger.error(f"保存文件失败: {e}")
        return

    print("-" * 30)
    logger.info("任务完成！")

import traceback

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("程序发生严重错误:")
        logger.error(traceback.format_exc())
    finally:
        input("\n按回车键退出...")
