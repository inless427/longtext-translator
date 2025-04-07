import json
import requests
from PyQt5.QtCore import pyqtSignal
import time

def detect_ollama_models(host="http://localhost:11434"):
    """Detect available Ollama models."""
    try:
        response = requests.get(f"{host}/api/tags")
        if response.status_code == 200:
            data = response.json()
            models = [model["name"] for model in data.get("models", [])]
            return models
        else:
            raise Exception(f"Failed to get models: {response.status_code}")
    except Exception as e:
        raise Exception(f"Error detecting Ollama models: {str(e)}")

def translate_with_ollama(content, model_name, source_lang="auto", target_lang="en", progress_signal=None):
    """Translate content using Ollama model."""
    try:
        host = "http://localhost:11434"
        
        # For subtitle files, we need to handle them differently
        if isinstance(content, list) or hasattr(content, '__iter__') and not isinstance(content, (str, bytes, dict)):
            # This is likely a subtitle file
            translated_content = content.__class__()  # Create a new instance of the same class
            
            total_items = len(content)
            for i, item in enumerate(content):
                # Create a system prompt for translation
                system_prompt = f"Translate the following text from {source_lang} to {target_lang}. Preserve the original meaning and style."
                
                # Prepare the prompt with the subtitle text
                prompt = f"Translate: {item.text}"
                
                # Make the API call
                response = requests.post(
                    f"{host}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": prompt,
                        "system": system_prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    translated_text = result.get("response", "").strip()
                    
                    # Create a new subtitle item with the translated text
                    new_item = item.__class__(
                        index=item.index,
                        start=item.start,
                        end=item.end,
                        text=translated_text
                    )
                    translated_content.append(new_item)
                else:
                    raise Exception(f"Translation failed: {response.status_code}")
                
                # Update progress
                if progress_signal:
                    progress_value = int((i + 1) / total_items * 100)
                    progress_signal.emit(progress_value)
                
                # Add a small delay to avoid overwhelming the API
                time.sleep(0.1)
            
            return translated_content
        else:
            # This is a text file
            # Split the content into chunks to avoid token limits
            chunks = split_text_into_chunks(content, 1000)  # 1000 characters per chunk
            translated_chunks = []
            
            total_chunks = len(chunks)
            for i, chunk in enumerate(chunks):
                # Create a system prompt for translation
                system_prompt = f"Translate the following text from {source_lang} to {target_lang}. Preserve the original meaning and style."
                
                # Make the API call
                response = requests.post(
                    f"{host}/api/generate",
                    json={
                        "model": model_name,
                        "prompt": f"Translate: {chunk}",
                        "system": system_prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    result = response.json()
                    translated_chunk = result.get("response", "").strip()
                    translated_chunks.append(translated_chunk)
                else:
                    raise Exception(f"Translation failed: {response.status_code}")
                
                # Update progress
                if progress_signal:
                    progress_value = int((i + 1) / total_chunks * 100)
                    progress_signal.emit(progress_value)
                
                # Add a small delay to avoid overwhelming the API
                time.sleep(0.1)
            
            return "\n".join(translated_chunks)
    except Exception as e:
        raise Exception(f"Error translating with Ollama: {str(e)}")

def translate_with_api(content, api_url, api_key, source_lang="auto", target_lang="en", progress_signal=None):
    """Translate content using an external API."""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # For subtitle files, we need to handle them differently
        if isinstance(content, list) or hasattr(content, '__iter__') and not isinstance(content, (str, bytes, dict)):
            # This is likely a subtitle file
            translated_content = content.__class__()  # Create a new instance of the same class
            
            total_items = len(content)
            for i, item in enumerate(content):
                # Prepare the request data
                data = {
                    "text": item.text,
                    "source_language": source_lang,
                    "target_language": target_lang
                }
                
                # Make the API call
                response = requests.post(api_url, json=data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    translated_text = result.get("translated_text", "").strip()
                    
                    # Create a new subtitle item with the translated text
                    new_item = item.__class__(
                        index=item.index,
                        start=item.start,
                        end=item.end,
                        text=translated_text
                    )
                    translated_content.append(new_item)
                else:
                    raise Exception(f"Translation failed: {response.status_code}")
                
                # Update progress
                if progress_signal:
                    progress_value = int((i + 1) / total_items * 100)
                    progress_signal.emit(progress_value)
                
                # Add a small delay to avoid overwhelming the API
                time.sleep(0.1)
            
            return translated_content
        else:
            # This is a text file
            # Split the content into chunks to avoid token limits
            chunks = split_text_into_chunks(content, 1000)  # 1000 characters per chunk
            translated_chunks = []
            
            total_chunks = len(chunks)
            for i, chunk in enumerate(chunks):
                # Prepare the request data
                data = {
                    "text": chunk,
                    "source_language": source_lang,
                    "target_language": target_lang
                }
                
                # Make the API call
                response = requests.post(api_url, json=data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    translated_chunk = result.get("translated_text", "").strip()
                    translated_chunks.append(translated_chunk)
                else:
                    raise Exception(f"Translation failed: {response.status_code}")
                
                # Update progress
                if progress_signal:
                    progress_value = int((i + 1) / total_chunks * 100)
                    progress_signal.emit(progress_value)
                
                # Add a small delay to avoid overwhelming the API
                time.sleep(0.1)
            
            return "\n".join(translated_chunks)
    except Exception as e:
        raise Exception(f"Error translating with API: {str(e)}")

def split_text_into_chunks(text, chunk_size=1000):
    """Split text into chunks of approximately chunk_size characters."""
    chunks = []
    current_chunk = ""
    
    # Split by paragraphs first
    paragraphs = text.split("\n")
    
    for paragraph in paragraphs:
        # If adding this paragraph would exceed chunk size, save current chunk and start a new one
        if len(current_chunk) + len(paragraph) > chunk_size and current_chunk:
            chunks.append(current_chunk)
            current_chunk = paragraph + "\n"
        else:
            current_chunk += paragraph + "\n"
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks
