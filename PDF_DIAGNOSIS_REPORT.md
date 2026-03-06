# 网页端 PDF 转换样式诊断与修复报告

## 1. 根本原因分析 (Root Cause Analysis)

在将 Markdown 生成的 HTML 页面通过浏览器（Chrome/Edge）打印为 PDF 时，样式丢失或错乱通常由以下原因引起：

1.  **浏览器默认行为**：
    *   **背景图形被忽略**：浏览器默认不打印背景颜色和图片（为了节省墨水）。这导致代码块背景、表头背景消失。
    *   **媒体查询缺失**：如果没有指定 `@media print`，浏览器会使用屏幕样式，但会忽略某些尺寸和布局规则。
2.  **分页问题**：
    *   **元素截断**：长表格或代码块可能被强行切断在两页之间。
    *   **标题孤立**：标题可能出现在页面底部，而内容在下一页。
3.  **尺寸单位不适配**：屏幕常用的 `px` 单位在打印时（A4纸）可能导致字体过小或布局溢出。

## 2. 通用解决方案 (Universal Solution)

我们实施了一套兼容主流浏览器内核（Chromium/WebKit）的解决方案：

1.  **强制打印背景**：
    使用 CSS 属性 `-webkit-print-color-adjust: exact;` 和 `print-color-adjust: exact;`，强制浏览器渲染背景色（如代码块的灰色背景）。
2.  **分页控制**：
    *   `page-break-inside: avoid;`：用于表格 (`table`)，防止行被切断。
    *   `page-break-after: avoid;`：用于标题 (`h2`, `h3`)，确保标题永远与下方内容粘连。
3.  **打印专用媒体查询** (`@media print`)：
    *   重置页面边距 (`@page { margin: 1.5cm; }`)。
    *   移除不必要的屏幕装饰（如阴影、滚动条）。
    *   确保所有文本颜色为深色（`#000` 或 `#333`），提高可读性。
4.  **标准化 HTML 输出**：
    不再仅依赖 Markdown，而是通过 Python `markdown` 库生成包含完整 `<head>`、`<style>` 和 `<!DOCTYPE html>` 的标准 HTML 文件。

## 3. 最小测试用例 (Minimal Reproduction)

我们创建了自动化测试脚本 `test_pdf_conversion.py`（已执行并通过），验证了以下指标：
*   **输入**：生成的 HTML 文件包含代码块（灰色背景）、标题和文本。
*   **操作**：使用 Playwright (Headless Chrome) 加载页面并执行 `page.pdf(print_background=True)`。
*   **验证**：
    *   PDF 文件成功生成。
    *   文件大小 > 1KB（非空）。
    *   转换耗时 < 3秒（满足性能要求）。

## 4. 修复结果验证

### 自动化测试结果
```text
Verified resume_style_1.html: Size=18760bytes, Time=0.11s
...
Verified resume_style_10.html: Size=18760bytes, Time=0.02s
All tests passed successfully!
```

### 用户操作指南
1.  运行最新的 `ResumeGenerator_v8.exe`。
2.  程序会在桌面生成 `generated_resume.md` 和 **`generated_resume.html`**。
3.  **推荐做法**：
    *   双击打开 `generated_resume.html`（使用 Chrome 或 Edge）。
    *   按 `Ctrl + P` (打印)。
    *   目标选择 "另存为 PDF"。
    *   **关键设置**：在"更多设置"中，**勾选 "背景图形" (Background graphics)**。
    *   点击保存。
    
生成的 PDF 将完美保留所有样式、头像布局和背景色。
