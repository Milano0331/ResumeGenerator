# AI 简历生成器 (AI Resume Generator)

这是一个使用 OpenAI API 生成专业简历的 Python 脚本。它模拟了一位拥有 10+ 年经验的资深招聘专家，为您打造 ATS 兼容、成就导向的现代简历。

## 功能特点
- **ATS 兼容**：优化格式，通过简历筛选系统。
- **成就导向**：强调量化成果（百分比、金额、增长）。
- **专业排版**：生成 Markdown 格式，清晰易读。
- **多语言支持**：支持中文或英文简历生成。

## 快速开始

### 1. 安装依赖
确保您已安装 Python，然后运行：
```bash
pip install -r requirements.txt
```

### 2. 配置 API Key
您可以通过 `.env` 文件配置 API Key，支持 OpenAI 及其他兼容接口（如 DeepSeek, Moonshot 等）。

创建 `.env` 文件并添加配置：
```env
# 必填
OPENAI_API_KEY=sk-您的APIKey

# 可选：如果使用其他服务商
# OPENAI_BASE_URL=https://api.deepseek.com/v1
# OPENAI_MODEL=deepseek-chat
```

### 3. 运行程序
```bash
python generate_resume.py
```

### 4. 输入信息
程序会引导您输入：
1. **API Key** (如果未配置环境变量)
2. **简历语言** (中文/英文)
3. **目标职位** (例如：高级软件工程师)
4. **个人信息** (经历、教育、技能等)
   - 支持多行输入
   - 输入 `END` 并回车结束输入

## 输出
程序将在当前目录下生成 `generated_resume.md` 文件，包含排版好的简历内容。

## 示例输入
**目标职位**: 产品经理
**个人信息**:
```text
3年电商产品经验，负责过用户增长项目。
熟练使用 SQL, Python, Axure。
教育背景：某某大学计算机学士。
项目A：优化了注册流程，转化率提升 15%。
END
```

## 注意事项
- 请确保您的 API Key 有足够的余额。
- 生成的内容仅供参考，建议根据实际情况进行微调。
- dist文件夹中有已打包好的.exe可执行文件，可以直接使用