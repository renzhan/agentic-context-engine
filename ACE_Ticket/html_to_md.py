from typing import Optional
import logging
from markdownify import markdownify as md

class HtmlToMarkdownConverter:
    """HTML 转 Markdown 核心功能类"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def convert_html_to_md(self, html_text: str, heading_style: str = "ATX") -> str:
        """
        将 HTML 文本转换为 Markdown 格式
        
        Args:
            html_text: HTML 文本内容
            heading_style: 标题样式，可选 "ATX" (#) 或 "SETEXT" (===)
            
        Returns:
            Markdown 格式的文本
            
        Raises:
            Exception: 转换失败时抛出异常
        """
        try:
            # 使用 markdownify 库将 HTML 转换为 Markdown
            md_text = md(
                html_text,
                heading_style=heading_style,
                bullets="-",  # 使用 - 作为列表符号
                strip=['script', 'style'],  # 移除 script 和 style 标签
            )
            
            # 清理多余的空白行
            lines = md_text.split('\n')
            cleaned_lines = []
            prev_empty = False
            
            for line in lines:
                line = line.rstrip()
                if line:
                    cleaned_lines.append(line)
                    prev_empty = False
                elif not prev_empty:
                    cleaned_lines.append('')
                    prev_empty = True
            
            # 移除末尾的空行
            while cleaned_lines and not cleaned_lines[-1]:
                cleaned_lines.pop()
            
            return '\n'.join(cleaned_lines)
            
        except Exception as e:
            self.logger.exception("Failed to convert HTML to Markdown")
            raise Exception(f"Failed to convert HTML text to Markdown, error: {str(e)}")


# 便捷函数
def convert_html_to_markdown(html_text: str, heading_style: str = "ATX") -> str:
    """
    便捷函数：将 HTML 文本转换为 Markdown 格式
    
    Args:
        html_text: HTML 文本内容
        heading_style: 标题样式，可选 "ATX" (#) 或 "SETEXT" (===)
        
    Returns:
        Markdown 格式的文本
    """
    converter = HtmlToMarkdownConverter()
    return converter.convert_html_to_md(html_text, heading_style)

