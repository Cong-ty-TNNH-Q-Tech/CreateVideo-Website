import os
import shutil
import traceback
from PIL import Image, ImageFilter, ImageOps
from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
from moviepy.video.fx.all import fadein, fadeout

# Handle Pillow version differences for resampling
if hasattr(Image, 'Resampling'):
    RESAMPLE_METHOD = Image.Resampling.LANCZOS
else:
    RESAMPLE_METHOD = Image.ANTIALIAS

class PresentationVideoExporter:
    """Export presentation slides + audio as video with transitions and layout styling"""
    
    def __init__(self):
        self.transition_duration = 0.5  # 0.5 second fade transition
        self.slide_buffer = 5  # Extra 5 seconds after audio
        self.target_size = (1920, 1080)
        
    def _create_styled_slide(self, image_path, temp_dir, index):
        """
        Create a styled 16:9 slide with blurred background if needed
        """
        try:
            output_path = os.path.join(temp_dir, f"styled_slide_{index}.png")
            
            with Image.open(image_path) as img:
                img = img.convert('RGBA')
                w, h = img.size
                
                # Check aspect ratio
                target_w, target_h = self.target_size
                target_ratio = target_w / target_h
                img_ratio = w / h
                
                # If ratio is close (within 10%), use original (resized)
                if abs(img_ratio - target_ratio) < 0.1:
                    img_resized = img.resize(self.target_size, RESAMPLE_METHOD)
                    img_resized.save(output_path, "PNG")
                    return output_path
                
                # Otherwise, create styled layout
                # 1. Background: Resize to cover target (crop excess)
                bg_scale = max(target_w / w, target_h / h)
                bg_w = int(w * bg_scale)
                bg_h = int(h * bg_scale)
                bg = img.resize((bg_w, bg_h), RESAMPLE_METHOD)
                
                # Center crop background
                left = (bg_w - target_w) // 2
                top = (bg_h - target_h) // 2
                bg = bg.crop((left, top, left + target_w, top + target_h))
                
                # Blur background
                bg = bg.filter(ImageFilter.GaussianBlur(radius=20))
                
                # 2. Foreground: Resize to fit within target with padding
                # Use 90% of available space to leave nice margin
                fg_scale = min(target_w / w, target_h / h) * 0.90 
                fg_w = int(w * fg_scale)
                fg_h = int(h * fg_scale)
                fg = img.resize((fg_w, fg_h), RESAMPLE_METHOD)
                
                # Add white border for card look
                fg = ImageOps.expand(fg, border=4, fill='white')
                fg_w, fg_h = fg.size
                
                # 3. Composite
                final_img = Image.new('RGBA', self.target_size, (0, 0, 0, 255))
                final_img.paste(bg, (0, 0))
                
                # Center foreground
                fg_x = (target_w - fg_w) // 2
                fg_y = (target_h - fg_h) // 2
                final_img.paste(fg, (fg_x, fg_y), fg)
                
                final_img.save(output_path, "PNG")
                return output_path
                
        except Exception as e:
            print(f"Warning: Failed to style slide {image_path}: {e}")
            return image_path  # Fallback to original

    def create_presentation_video(self, slides, output_path, fps=24):
        """
        Create video from slides with audio sync
        """
        temp_dir = None
        try:
            if not slides or len(slides) == 0:
                return {'success': False, 'error': 'No slides provided'}
            
            # Create temp directory for styled slides
            temp_dir = os.path.join(os.path.dirname(output_path), 'processed_slides')
            os.makedirs(temp_dir, exist_ok=True)
            
            clips = []
            audio_clips = []  # Keep track of audio clips to close later
            
            print(f"🎨 Styling {len(slides)} slides...")
            
            for i, slide in enumerate(slides):
                image_path = slide.get('image_path')
                audio_path = slide.get('audio_path')
                
                if not image_path or not os.path.exists(image_path):
                    print(f"Warning: Slide {i+1} image not found: {image_path}")
                    continue
                    
                if not audio_path or not os.path.exists(audio_path):
                    print(f"Warning: Slide {i+1} audio not found: {audio_path}")
                    continue
                
                # Style the slide image (add background/blur if needed)
                styled_image_path = self._create_styled_slide(image_path, temp_dir, i)
                
                # Get audio duration
                audio_clip = AudioFileClip(audio_path)
                audio_clips.append(audio_clip)  # Store for later cleanup
                audio_duration = audio_clip.duration
                
                # Slide duration = audio + buffer
                slide_duration = audio_duration + self.slide_buffer
                
                # Create image clip from styled image
                img_clip = ImageClip(styled_image_path).set_duration(slide_duration)
                
                # Set audio (only for the audio duration, not including buffer)
                img_clip = img_clip.set_audio(audio_clip)
                
                # Add fade transitions (except first slide fadein and last slide fadeout done separately)
                if i > 0:  # Fade in for all slides except first
                    img_clip = fadein(img_clip, self.transition_duration)
                if i < len(slides) - 1:  # Fade out for all slides except last
                    img_clip = fadeout(img_clip, self.transition_duration)
                
                clips.append(img_clip)
            
            if len(clips) == 0:
                return {'success': False, 'error': 'No valid slides to create video'}
            
            # Concatenate all clips
            print(f"Concatenating {len(clips)} slides...")
            final_video = concatenate_videoclips(clips, method="compose")
            
            # Write video
            print(f"Writing video to {output_path}...")
            final_video.write_videofile(
                output_path,
                fps=fps,
                codec='libx264',
                audio_codec='aac',
                temp_audiofile='temp-audio.m4a',
                remove_temp=True,
                preset='ultrafast',  # Much faster encoding
                threads=4,           # Use multi-threading
                logger=None  # Suppress moviepy logs
            )
            
            # Clean up - close all clips AFTER video is written
            final_video.close()
            for clip in clips:
                clip.close()
            for audio_clip in audio_clips:
                audio_clip.close()
            
            print(f"✅ Presentation video created: {output_path}")
            
            return {
                'success': True,
                'video_path': output_path
            }
            
        except Exception as e:
            print(f"❌ Error creating presentation video: {str(e)}")
            traceback.print_exc()
            return {
                'success': False,
                'error': f"Lỗi tạo video: {str(e)}"
            }
        finally:
            # Clean up temp files
            if temp_dir and os.path.exists(temp_dir):
                try:
                    shutil.rmtree(temp_dir)
                    print("🧹 Cleaned up temp slides")
                except Exception as e:
                    print(f"Warning: Could not clean up temp dir: {e}")
