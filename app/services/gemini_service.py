"""
Service để gọi Gemini API
"""
import os
from google import genai
from google.genai import types
from typing import Optional

class GeminiService:
    """Service để gọi Gemini API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Gemini service
        
        Args:
            api_key: Gemini API key (nếu None thì lấy từ env GEMINI_API_KEY)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found. Please set it in environment variables or pass as parameter.")
        
        # Initialize client with new google.genai package
        self.client = genai.Client(api_key=self.api_key)
        
        # Sử dụng model mới nhất - gemini-2.5-flash (latest & recommended)
        # gemini-2.5-flash: Model mới nhất, nhanh, miễn phí, chất lượng tốt
        # gemini-1.5-flash: Fallback nếu 2.5 không có
        # gemini-1.5-pro: Fallback cho chất lượng cao hơn
        try:
            # Sử dụng gemini-2.5-flash (model mới nhất, nhanh và miễn phí)
            self.model_name = 'gemini-2.5-flash'
            # Test model by attempting to use it
            _ = self.client.models.get(model=self.model_name)
        except Exception as e:
            # Fallback về gemini-1.5-flash nếu 2.5 không có
            try:
                self.model_name = 'gemini-1.5-flash'
                _ = self.client.models.get(model=self.model_name)
            except Exception:
                # Fallback về gemini-1.5-pro nếu flash không có
                try:
                    self.model_name = 'gemini-1.5-pro'
                    _ = self.client.models.get(model=self.model_name)
                except Exception:
                    # Nếu tất cả đều không được, raise error với message rõ ràng
                    raise ValueError(
                        f"Không thể khởi tạo Gemini model. "
                        f"Đã thử: gemini-2.5-flash, gemini-1.5-flash, gemini-1.5-pro. "
                        f"Vui lòng kiểm tra API key và model availability. "
                        f"Error: {str(e)}"
                    )
    
    def generate_presentation_text(self, slide_content: str, language: str = 'vi') -> str:
        """
        Tạo text thuyết trình từ nội dung slide
        
        Args:
            slide_content: Nội dung raw từ slide
            language: Ngôn ngữ output (vi, en, ...)
        
        Returns:
            str: Text thuyết trình đã được generate
        """
        if not slide_content or not slide_content.strip():
            return "Nội dung slide trống, không thể tạo text thuyết trình."
        
        prompt = f"""
Bạn là một chuyên gia tạo nội dung thuyết trình. 
Dựa vào nội dung slide sau, hãy tạo ra một đoạn text thuyết trình tự nhiên, 
dễ hiểu, phù hợp để nói trước đám đông.

Nội dung slide:
{slide_content}

Yêu cầu:
- Text phải tự nhiên, như đang nói chuyện
- Độ dài phù hợp (khoảng 1-2 phút khi nói)
- Sử dụng ngôn ngữ {language}
- Không cần lặp lại tiêu đề slide
- Tập trung vào giải thích và mở rộng nội dung
- Giọng điệu chuyên nghiệp nhưng thân thiện

Text thuyết trình:
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def enhance_text(self, user_text: str, instruction: str = "") -> str:
        """
        Cải thiện text dựa trên instruction của user
        
        Args:
            user_text: Text hiện tại
            instruction: Hướng dẫn cải thiện (vd: "làm ngắn gọn hơn", "thêm ví dụ")
        
        Returns:
            str: Text đã được cải thiện
        """
        if not user_text or not user_text.strip():
            return user_text
        
        if not instruction:
            instruction = "Cải thiện text này để tự nhiên và dễ hiểu hơn"
        
        prompt = f"""
{instruction}

Text hiện tại:
{user_text}

Yêu cầu:
- Giữ nguyên ý nghĩa chính
- Làm cho text tự nhiên hơn
- Dễ hiểu và phù hợp để nói

Text cải thiện:
"""
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")
    
    def regenerate_text(self, slide_content: str, current_text: str, feedback: str = "") -> str:
        """
        Tạo lại text với feedback từ user
        
        Args:
            slide_content: Nội dung slide gốc
            current_text: Text hiện tại
            feedback: Feedback từ user (vd: "ngắn gọn hơn", "thêm ví dụ")
        
        Returns:
            str: Text mới được generate
        """
        if feedback:
            prompt = f"""
Dựa vào nội dung slide và feedback, tạo lại text thuyết trình.

Nội dung slide:
{slide_content}

Text hiện tại:
{current_text}

Feedback: {feedback}

Yêu cầu:
- Áp dụng feedback: {feedback}
- Giữ nguyên chất lượng và tự nhiên
- Phù hợp để nói trước đám đông

Text thuyết trình mới:
"""
        else:
            # Nếu không có feedback, generate lại từ đầu
            return self.generate_presentation_text(slide_content)
        
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt
            )
            return response.text.strip()
        except Exception as e:
            raise Exception(f"Gemini API error: {str(e)}")

