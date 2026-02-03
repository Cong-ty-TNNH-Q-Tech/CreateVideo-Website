"""
Module để đọc nội dung từ file PowerPoint và PDF
"""
from pptx import Presentation
from pypdf import PdfReader
import fitz  # pymupdf
from PIL import Image
import os
from typing import List, Dict

class PresentationReader:
    """Đọc nội dung từ file PPT và PDF"""
    
    @staticmethod
    def read_pptx(file_path: str) -> List[Dict]:
        """
        Đọc file PowerPoint và trả về danh sách slides
        """
        try:
            prs = Presentation(file_path)
            slides_data = []
            
            for idx, slide in enumerate(prs.slides, 1):
                content_parts = []
                for shape in slide.shapes:
                    if hasattr(shape, "text") and shape.text.strip():
                        content_parts.append(shape.text.strip())
                
                notes = ""
                if slide.has_notes_slide:
                    notes_slide = slide.notes_slide
                    if notes_slide.notes_text_frame:
                        notes = notes_slide.notes_text_frame.text
                
                content = "\n".join(content_parts)
                slides_data.append({
                    'slide_num': idx,
                    'content': content,
                    'notes': notes,
                    'total_slides': len(prs.slides)
                })
            return slides_data
        except Exception as e:
            raise Exception(f"Error reading PPTX: {str(e)}")
    
    @staticmethod
    def read_pdf(file_path: str) -> List[Dict]:
        """
        Đọc file PDF và trả về danh sách pages
        """
        try:
            reader = PdfReader(file_path)
            pages_data = []
            for idx, page in enumerate(reader.pages, 1):
                content = page.extract_text()
                pages_data.append({
                    'slide_num': idx,
                    'content': content.strip(),
                    'notes': "",
                    'total_slides': len(reader.pages)
                })
            return pages_data
        except Exception as e:
            raise Exception(f"Error reading PDF: {str(e)}")
    
    @staticmethod
    def extract_text_from_file(file_path: str) -> List[Dict]:
        """
        Tự động detect loại file và đọc
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        
        if ext in ['.pptx', '.ppt']:
            return PresentationReader.read_pptx(file_path)
        elif ext == '.pdf':
            return PresentationReader.read_pdf(file_path)
        else:
            raise ValueError(f"Unsupported file type: {ext}. Supported: .pptx, .ppt, .pdf")
    
    @staticmethod
    def _convert_ppt_to_pdf(ppt_path: str, pdf_path: str):
        """Convert PPT/PPTX to PDF using COM Automation (Thread-Safe)"""
        # Imports here to avoid global dependencies and ensure visibility
        import pythoncom
        import comtypes.client
        
        ppt_path = os.path.abspath(ppt_path)
        pdf_path = os.path.abspath(pdf_path)
        
        print(f"🔄 Converting PPT to PDF: {ppt_path} -> {pdf_path}")
        
        # Initialize COM for this thread
        pythoncom.CoInitialize()
        
        try:
            powerpoint = comtypes.client.CreateObject("Powerpoint.Application")
            # powerpoint.Visible = 1
            
            presentation = powerpoint.Presentations.Open(ppt_path, WithWindow=False)
            presentation.SaveAs(pdf_path, 32) # 32 = ppSaveAsPDF
            presentation.Close()
            
        except Exception as e:
            print(f"❌ PPT Conversion Error: {e}")
            raise Exception(f"PPT Conversion failed: {e}. Ensure Microsoft PowerPoint is installed.")
        finally:
            # Clean up COM
            pythoncom.CoUninitialize()

    @staticmethod
    def extract_slide_images(file_path: str, output_dir: str) -> List[str]:
        """
        Extract slides/pages as PNG images using pymupdf
        Handles PPT files by auto-converting to PDF first.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        os.makedirs(output_dir, exist_ok=True)
        
        ext = os.path.splitext(file_path)[1].lower()
        
        pdf_path = file_path
        
        # Handle PPT files
        if ext in ['.pptx', '.ppt']:
            pdf_path = os.path.splitext(file_path)[0] + ".pdf"
            
            should_convert = False
            if not os.path.exists(pdf_path):
                should_convert = True
            elif os.path.getmtime(file_path) > os.path.getmtime(pdf_path):
                should_convert = True
                
            if should_convert:
                PresentationReader._convert_ppt_to_pdf(file_path, pdf_path)
        
        # Extract slides from PDF using pymupdf
        try:
            doc = fitz.open(pdf_path)
            image_paths = []
            
            for page_num in range(len(doc)):
                page = doc[page_num]
                
                # Render page to image at high resolution
                zoom = 2
                mat = fitz.Matrix(zoom, zoom)
                pix = page.get_pixmap(matrix=mat)
                
                image_path = os.path.join(output_dir, f'slide_{page_num + 1}.png')
                pix.save(image_path)
                image_paths.append(image_path)
            
            doc.close()
            print(f"✅ Successfully extracted {len(image_paths)} slides from {pdf_path}")
            return image_paths
            
        except Exception as e:
            raise Exception(f"Error extracting slides: {str(e)}")
