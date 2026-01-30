"""
Service to interact with Google Gemini API for generating presentation scripts.
"""
import os
import google.generativeai as genai
from typing import Optional

class GeminiService:
    """Service to interact with Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service
        
        Args:
            api_key: Gemini API key (if None, loads from GEMINI_API_KEY env var)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            # We don't raise error here to allow app to start, 
            # but methods will fail if key is missing.
            print("Warning: GEMINI_API_KEY not found.")
        else:
            genai.configure(api_key=self.api_key)
        
        # Configure generation config for TTS-friendly output
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.95,
            "top_k": 40,
            "max_output_tokens": 8192,
        }
        
        # Use gemini-2.5-flash as requested by user and verified in available models
        self.model_name = 'gemini-2.5-flash'
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            generation_config=self.generation_config
        )
    
    def generate_script(self, slide_text: str, language: str = 'vi') -> str:
        """
        Generate a speech script from slide text.
        
        Args:
            slide_text: The text content extracted from the slide.
            language: The target language for the script (default: 'vi' for Vietnamese).
            
        Returns:
            str: The generated speech script (plain text).
        """
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")
            
        if not slide_text or not slide_text.strip():
            return "Slide này không có nội dung, vui lòng nhập nội dung để tạo kịch bản."
            
        # Prompt Engineering for TTS
        prompt = f"""
        Act as a professional presenter and speaker.
        Rewrite the following slide content into a natural, engaging speech script suitable for Text-to-Speech (TTS).
        
        Input Text:
        "{slide_text}"
        
        Requirements:
        1. Language: {language} (Vietnamese).
        2. Tone: Professional, engaging, and clear.
        3. Format: PLAIN TEXT ONLY. Do NOT use Markdown, lists, bullet points, asterisks (*), hashtags (#), or emojis. TTS engines do not read these well.
        4. Structure: Write in full sentences/paragraphs as if you are speaking to an audience.
        5. Content: Do not just read the text. Explain and expand on the points naturally.
        6. Length: Keep it concise and appropriate for the amount of content (approx. 1-2 minutes max).
        
        Generated Script:
        """
        
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Error generating script with Gemini: {e}")
            # Fallback handling or re-raise
            raise Exception(f"Gemini API Error: {str(e)}")

    def enhance_text(self, current_text: str, instruction: str) -> str:
        """
        Enhance the existing script based on user instruction.
        """
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")
            
        prompt = f"""
        Act as a professional editor.
        Update the following speech script based on the instruction.
        
        Current Script:
        "{current_text}"
        
        Instruction:
        "{instruction}"
        
        Requirements:
        1. Keep it as PLAIN TEXT (no markdown/emojis).
        2. Maintain a professional speech tone.
        3. Make it suitable for TTS.
        
        Updated Script:
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini enhancement error: {str(e)}")

    def regenerate_text(self, slide_content: str, current_text: str, feedback: str) -> str:
        """
        Regenerate the script with feedback.
        """
        if not self.api_key:
            raise ValueError("Gemini API key is not configured.")
            
        prompt = f"""
        Act as a professional presenter.
        Regenerate the speech script for the slide content, taking into account the user's feedback.
        
        Slide Content:
        "{slide_content}"
        
        Current Script:
        "{current_text}"
        
        User Feedback:
        "{feedback}"
        
        Requirements:
        1. Address the feedback specifically.
        2. Format: PLAIN TEXT ONLY (no markdown/emojis).
        3. Tone: Professional and natural for speech.
        
        New Script:
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini regeneration error: {str(e)}")
