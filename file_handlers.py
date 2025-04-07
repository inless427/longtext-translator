import os
import chardet
import pysrt
from PyPDF2 import PdfReader
from docx import Document
import ebooklib
from ebooklib import epub

def detect_encoding(file_path):
    """Detect the encoding of a file."""
    with open(file_path, 'rb') as f:
        result = chardet.detect(f.read())
    return result['encoding']

def read_text_file(file_path):
    """Read a text file and return its content."""
    try:
        encoding = detect_encoding(file_path)
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except Exception as e:
        print(f"Error reading text file: {str(e)}")
        return None

def read_pdf_file(file_path):
    """Read a PDF file and return its content as text."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        return text
    except Exception as e:
        print(f"Error reading PDF file: {str(e)}")
        return None

def read_docx_file(file_path):
    """Read a DOCX file and return its content as text."""
    try:
        doc = Document(file_path)
        text = ""
        for para in doc.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        print(f"Error reading DOCX file: {str(e)}")
        return None

def read_epub_file(file_path):
    """Read an EPUB file and return its content as text."""
    try:
        book = epub.read_epub(file_path)
        text = ""
        
        for item in book.get_items():
            if item.get_type() == ebooklib.ITEM_DOCUMENT:
                content = item.get_content().decode('utf-8')
                # 简单移除HTML标签
                content = content.replace('<p>', '\n').replace('</p>', '\n')
                content = content.replace('<br>', '\n').replace('<br/>', '\n')
                
                # 移除其他HTML标签
                in_tag = False
                cleaned_content = ""
                for char in content:
                    if char == '<':
                        in_tag = True
                    elif char == '>':
                        in_tag = False
                    elif not in_tag:
                        cleaned_content += char
                
                text += cleaned_content + "\n"
        return text
    except Exception as e:
        print(f"Error reading EPUB file: {str(e)}")
        return None

def read_srt_file(file_path):
    """Read an SRT file and return its content as a list of subtitle objects."""
    try:
        encoding = detect_encoding(file_path)
        subs = pysrt.open(file_path, encoding=encoding)
        return subs
    except Exception as e:
        print(f"Error reading SRT file: {str(e)}")
        return None

def write_text_file(file_path, content):
    """Write content to a text file."""
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    except Exception as e:
        print(f"Error writing text file: {str(e)}")
        return False

def write_srt_file(file_path, subtitles):
    """Write subtitles to an SRT file."""
    try:
        subtitles.save(file_path, encoding='utf-8')
        return True
    except Exception as e:
        print(f"Error writing SRT file: {str(e)}")
        return False

def merge_subtitles(original_subs, translated_subs):
    """Merge original and translated subtitles into bilingual subtitles."""
    try:
        if len(original_subs) != len(translated_subs):
            raise ValueError("Original and translated subtitles have different lengths")
        
        merged_subs = pysrt.SubRipFile()
        
        for i, (orig, trans) in enumerate(zip(original_subs, translated_subs)):
            new_sub = pysrt.SubRipItem(
                index=orig.index,
                start=orig.start,
                end=orig.end,
                text=f"{orig.text}\n{trans.text}"
            )
            merged_subs.append(new_sub)
        
        return merged_subs
    except Exception as e:
        print(f"Error merging subtitles: {str(e)}")
        return None
