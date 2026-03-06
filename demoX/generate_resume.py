import os
import sys
import argparse
import logging
import shutil
import httpx
from openai import OpenAI, APIConnectionError
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
try:
    from docx_generator import create_resume_docx
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False
    logger.warning("Warning: docx_generator module not found or failed to import. DOCX generation will be disabled.")

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

def generate_resume_content(api_key, base_url, model_name, language, target_position, user_info, proxy=None):
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

    system_prompt = """
你是资深招聘专家(10+年经验)。
你浏览过数千份简历，深知ATS系统如何运作。

使用以下信息创建简历：
- ATS兼容
- 吸引人眼球
- 清晰、可量化的成就导向
- 不超过1-2页
- 现代专业

规则：
- 从强势'职业总结'开始
- 每段工作用数字成果(百分比、金额、时间、增长)
- 避免不必要的陈词滥调
- 使用主动动词
- 写得让招聘者6秒内注意到
- 自然融入关键词
- 不用表格、图标、图形
- 输出格式为 Markdown，方便阅读和转换
- 第一行必须是 '# 姓名 - 职位' 格式
- 第二行必须是联系方式（电话、邮箱、地址等）
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
    default_docx_path = os.path.join(desktop_path, "generated_resume.docx")

    parser = argparse.ArgumentParser(description="AI 简历生成器")
    parser.add_argument("--api_key", help="OpenAI API Key (如果未在环境变量设置)")
    parser.add_argument("--base_url", help="API Base URL (例如: https://api.deepseek.com, https://api.moonshot.cn/v1 等)")
    parser.add_argument("--model", help="模型名称 (默认: gpt-4o，可使用 deepseek-chat, moonshot-v1-8k 等)")
    parser.add_argument("--language", default="中文", help="简历语言 (默认: 中文)")
    parser.add_argument("--position", help="目标职位")
    parser.add_argument("--info_file", help="包含用户信息的文本文件路径")
    parser.add_argument("--output_md", default=default_md_path, help=f"Markdown 输出路径 (默认: {default_md_path})")
    parser.add_argument("--output_docx", default=default_docx_path, help=f"DOCX 输出路径 (默认: {default_docx_path})")
    parser.add_argument("--proxy", help="HTTP/HTTPS 代理地址 (例如: http://127.0.0.1:7890)")
    parser.add_argument("--no_docx", action="store_true", help="跳过 DOCX 生成")
    
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
    resume_content = generate_resume_content(api_key, base_url, model_name, language, target_position, user_info, proxy=proxy)

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
    except Exception as e:
        logger.error(f"保存 Markdown 文件失败: {e}")
        return

    # 5. Generate DOCX
    if not args.no_docx and DOCX_AVAILABLE:
        output_docx = os.path.abspath(args.output_docx)
        docx_dir = os.path.dirname(output_docx)
        
        print(f"正在生成 DOCX: {output_docx}...")
        
        try:
            # Ensure directory exists
            if docx_dir and not os.path.exists(docx_dir):
                os.makedirs(docx_dir, exist_ok=True)
            
            success = create_resume_docx(resume_content, output_docx)
            if success:
                logger.info(f"DOCX 生成成功: {output_docx}")
            else:
                logger.error("DOCX 生成失败。请检查日志。")
        except Exception as e:
            logger.error(f"DOCX 生成过程发生异常: {e}")

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
