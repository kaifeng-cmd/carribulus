"""
Vision Tools - Image Analysis using VLM APIs

- Gemini API (inline_data)
- HuggingFace Router API (OpenAI image_url)  
- OpenRouter API (OpenAI image_url)

Supports:
- URL links (https://...)
- Local file paths (C:\\...\\image.jpg)
- Base64 encoded strings (raw or data URI)
"""

import os
import re
import base64
import requests
import mimetypes
from pathlib import Path
from typing import Type, Tuple
from pydantic import BaseModel, Field
from crewai.tools import BaseTool
from openai import OpenAI


# Image Input Schema
# =============================================================================

class VisionToolInput(BaseModel):
    """
    Input schema for Vision Tool
    """
    image_source: str = Field(
        required=True,
        description="""The image to analyze. Can be:
        - URL: https://example.com/image.jpg
        - Local path: C:\\Users\\...\\image.jpg or /path/to/image.jpg
        - Base64 string: data:image/jpeg;base64,... or raw base64 data"""
    )
    question: str = Field(
        default="Describe the content of this image in detail.",
        description="Question or instruction about the image. Default asks for detailed description."
    )


# Provider 1: Gemini Vision (Google AI Studio)
# =============================================================================

class GeminiVisionTool(BaseTool):
    """
    Uses Google Gemini Vision API to analyze images.
    
    Inline_data (Gemini special format)
    - Put image base64 into contents.parts.inline_data
    """
    
    name: str = "Analyze Image [Gemini]"
    description: str = """Analyze and describe images using Google Gemini Vision.
    
    Accepts: Image URLs, local file paths, or base64 encoded images.
    Use for: menu translation, sign reading, image description, visual content analysis.
    
    """
    
    args_schema: Type[BaseModel] = VisionToolInput
    
    def _run(
        self,
        image_source: str,
        question: str = "Describe the content of this image in detail."
    ) -> str:
        # Check API key
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            return "Error: GEMINI_API_KEY not found in environment variables."
        
        # Convert to base64
        try:
            image_b64, mime_type = self._get_image_base64(image_source)
        except Exception as e:
            return f"Error processing image: {str(e)}"
        
        # Call Gemini API
        try:
            result = self._call_gemini_vision(api_key, image_b64, mime_type, question)
            return result
        except Exception as e:
            return f"Error calling Gemini Vision API: {str(e)}"
    
    def _get_image_base64(self, image_source: str) -> Tuple[str, str]:
        """
        Convert to base64 + MIME type

        Unified processing for all input formats:
        1. data:image/jpeg;base64,xxx → Extract base64 and MIME
        2. Very long string → Assume it's raw base64
        3. https://... → Download and convert
        4. Local path → Read and convert

        Returns:
            Tuple of (base64_string, mime_type)
        """
        image_source = image_source.strip()
        
        # Case 1: If it is data URI format already
        # For example: data:image/jpeg;base64,/9j/4AAQ...
        if image_source.startswith("data:"):
            match = re.match(r"data:([^;]+);base64,(.+)", image_source)
            if match:
                mime_type = match.group(1)  # 1st group: image/jpeg
                b64_data = match.group(2)   # 2nd group: /9j/4AAQ...
                return b64_data, mime_type
            else:
                raise ValueError("Invalid data URI format")
        
        # Case 2: Raw base64
        if len(image_source) > 500 and "/" not in image_source[:50] and "\\" not in image_source[:50]:
            return image_source, "image/jpeg"  # Assume is JPEG
        
        # Case 3: URL
        if image_source.startswith(("http://", "https://")):
            return self._download_image_to_base64(image_source)
        
        # Case 4: Local image path
        return self._read_local_file_to_base64(image_source)
    
    def _download_image_to_base64(self, url: str) -> Tuple[str, str]:
        """
        Download image from URL and convert to base64
        """
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        # Get MIME type (from response header or guess)
        content_type = response.headers.get("Content-Type", "")
        if "image/" in content_type:
            # "image/jpeg; charset=utf-8" → "image/jpeg"
            mime_type = content_type.split(";")[0].strip()
        else:
            # Guess from URL extension (.jpg → image/jpeg)
            mime_type = mimetypes.guess_type(url)[0] or "image/jpeg"

        # base64.b64encode() returns bytes, need to decode to string
        b64_data = base64.b64encode(response.content).decode("utf-8")
        return b64_data, mime_type
    
    def _read_local_file_to_base64(self, file_path: str) -> Tuple[str, str]:
        """
        Read local file and convert to base64
        """
        path = Path(file_path)
        
        if not path.exists():
            raise FileNotFoundError(f"Image file not found: {file_path}")
        
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        # Get MIME type from extension
        mime_type = mimetypes.guess_type(str(path))[0] or "image/jpeg"
        
        # "rb" = read binary（Image is binary）
        with open(path, "rb") as f:
            b64_data = base64.b64encode(f.read()).decode("utf-8")
        
        return b64_data, mime_type
    
    def _call_gemini_vision(
        self,
        api_key: str,
        image_b64: str,
        mime_type: str,
        question: str
    ) -> str:
        """
        Call Gemini Vision API with inline_data format.
        This is a Gemini-specific format, different from OpenAI
        """
        # Gemini API endpoint
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        # Payload
        payload = {
            "contents": [{
                "parts": [
                    {"text": question},
                    {
                        "inline_data": {
                            "mime_type": mime_type,
                            "data": image_b64
                        }
                    }
                ]
            }],
            "generationConfig": {
                "temperature": 0.4,
                "maxOutputTokens": 2048,
            }
        }
        
        # POST
        response = requests.post(url, json=payload, timeout=60)
        
        if response.status_code != 200:
            error_msg = response.json().get("error", {}).get("message", response.text)
            raise Exception(f"Gemini API error ({response.status_code}): {error_msg}")
        
        data = response.json()
        
        try:
            content = data["candidates"][0]["content"]["parts"][0]["text"]
            return content
        except (KeyError, IndexError) as e:
            raise Exception(f"Unexpected API response format: {str(e)}")

gemini_vision = GeminiVisionTool()


# Provider 2: Hugging Face Vision
# =============================================================================

class HuggingFaceVisionTool(BaseTool):
    """
    Uses Hugging Face to call Qwen Vision model 
    
    OpenAI-compatible
    - Hugging Face compatible with OpenAI API format
    - Reusable OpenAI sdk, no need to manually write HTTP requests
    """
    
    name: str = "Analyze Image (Hugging Face)"
    description: str = """Analyze and describe the images using Hugging Face open source vision model.

    Accepts: Image URLs, local file paths, or base64 encoded images.
    """
    
    args_schema: Type[BaseModel] = VisionToolInput
    
    def _run(
        self,
        image_source: str,
        question: str = "Describe the content of this image in detail."
    ) -> str:
        
        hf_token = os.getenv("HF_TOKEN")
        if not hf_token:
            return "Error: HF_TOKEN not found in environment variables."

        image_source = image_source.strip()
        
        if image_source.startswith(("http://", "https://")):
            image_url = image_source
        elif image_source.startswith("data:"):
            image_url = image_source
        elif len(image_source) > 500:
            # Raw base64，add data URI prefix
            image_url = f"data:image/jpeg;base64,{image_source}"
        else:
            # If local file path, convert to data URI
            try:
                path = Path(image_source)
                mime_type = mimetypes.guess_type(str(path))[0] or "image/jpeg"
                with open(path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                image_url = f"data:{mime_type};base64,{b64_data}"
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        try:
            # Uses OpenAI SDK，but direct to Hugging Face Router
            client = OpenAI(
                base_url="https://router.huggingface.co/v1",
                api_key=hf_token,
            )
            
            # messages.content is list，including text & image_url
            completion = client.chat.completions.create(
                model="Qwen/Qwen3-VL-8B-Instruct:novita",
                messages=[{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }],
                max_tokens=2048
            )
            
            return completion.choices[0].message.content
            
        except Exception as e:
            return f"Error calling Hugging Face API: {str(e)}"

huggingface_vision = HuggingFaceVisionTool()


# Provider 3: OpenRouter Vision
# =============================================================================

class OpenRouterVisionTool(BaseTool):
    """
    Call NVIDIA Nemotron Vision model via OpenRouter platform.
    """
    
    name: str = "Analyze Image (OpenRouter)"
    description: str = """Analyze and describe images via OpenRouter Vision Model.
    
    Accepts: Image URLs, local file paths, or base64 encoded images.
    """
    
    args_schema: Type[BaseModel] = VisionToolInput
    
    def _run(
        self,
        image_source: str,
        question: str = "Describe the content of this image in detail."
    ) -> str:
        
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            return "Error: OPENROUTER_API_KEY not found in environment variables."
        
        image_source = image_source.strip()
        
        if image_source.startswith(("http://", "https://")):
            # URL needs to convert to base64
            # OpenRouter seems not directly support URL
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(image_source, headers=headers, timeout=30)
                response.raise_for_status()
                
                content_type = response.headers.get("Content-Type", "")
                if "image/" in content_type:
                    mime_type = content_type.split(";")[0].strip()
                else:
                    mime_type = mimetypes.guess_type(image_source)[0] or "image/jpeg"
                
                b64_data = base64.b64encode(response.content).decode("utf-8")
                image_url = f"data:{mime_type};base64,{b64_data}"
            except Exception as e:
                return f"Error downloading image: {str(e)}"
            
        elif image_source.startswith("data:"):
            image_url = image_source
        elif len(image_source) > 500:
            image_url = f"data:image/jpeg;base64,{image_source}"
        else:
            # For local file path
            try:
                path = Path(image_source)
                mime_type = mimetypes.guess_type(str(path))[0] or "image/jpeg"
                with open(path, "rb") as f:
                    b64_data = base64.b64encode(f.read()).decode("utf-8")
                image_url = f"data:{mime_type};base64,{b64_data}"
            except Exception as e:
                return f"Error reading file: {str(e)}"
        
        try:
            # Headers
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            # POST Payload
            payload = {
                "model": "nvidia/nemotron-nano-12b-v2-vl:free",
                "messages": [{
                    "role": "user",
                    "content": [
                        {"type": "text", "text": question},
                        {"type": "image_url", "image_url": {"url": image_url}}
                    ]
                }],
                "max_tokens": 2048
            }
            
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=90
            )
            
            if response.status_code != 200:
                error = response.json().get("error", {}).get("message", response.text)
                raise Exception(f"OpenRouter API error ({response.status_code}): {error}")
            
            data = response.json()
            return data["choices"][0]["message"]["content"]
            
        except Exception as e:
            return f"Error calling OpenRouter API: {str(e)}"

openrouter_vision = OpenRouterVisionTool()
