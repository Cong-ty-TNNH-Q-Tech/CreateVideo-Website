import os
import subprocess
import sys
import glob
import platform
import uuid

class VideoGenerationService:
    def __init__(self, app_root):
        """
        Initialize VideoGenerationService
        args:
            app_root: Root path of the application (where SadTalker folder is located)
        """
        # SadTalker is now inside app/SadTalker
        self.app_root = app_root
        self.sadtalker_dir = os.path.join(app_root, 'SadTalker')
        
    def generate_video(self, source_image_path, driven_audio_path, result_dir, use_cpu=False):
        """
        Generate talking head video using SadTalker
        """
        # Ensure absolute paths
        source_image_abs = os.path.abspath(source_image_path)
        driven_audio_abs = os.path.abspath(driven_audio_path)
        result_dir_abs = os.path.abspath(result_dir)
        
        # Create a unique sub-directory to isolate outputs and prevent race conditions
        unique_id = uuid.uuid4().hex
        unique_result_dir = os.path.join(result_dir_abs, unique_id)
        os.makedirs(unique_result_dir, exist_ok=True)
        
        # Determine python executable based on OS
        project_root = os.path.dirname(self.app_root)
        
        # Check for both .venv and venv directories
        venv_dirs = ['.venv', 'venv']
        python_exec = sys.executable  # Default to current python
        
        for venv_name in venv_dirs:
            if platform.system() == 'Windows':
                venv_python = os.path.join(project_root, venv_name, 'Scripts', 'python.exe')
            else:  # Linux, macOS, etc.
                venv_python = os.path.join(project_root, venv_name, 'bin', 'python')
            
            if os.path.exists(venv_python):
                python_exec = venv_python
                break

        # Construct command
        command = [
            python_exec, 'inference.py',
            '--driven_audio', driven_audio_abs,
            '--source_image', source_image_abs,
            '--result_dir', unique_result_dir,
            '--still', 
            '--preprocess', 'full',  # 'full' for better quality, 'crop' for cropped face
            '--size', '256',  # 256 is the minimum supported size for SadTalker mapping models
            '--checkpoint_dir', 'checkpoints',
            '--batch_size', '1',  # Reduce batch_size to 1 to prevent VRAM overflow instead of reducing size
            '--enhancer', 'gfpgan',  # Enabled GFPGAN for face enhancement
            '--expression_scale', '1.0',  # Expression intensity
            '--gpu_id', '0'  # Fallback to GPU 0 since GPU 1 doesn't exist
        ]
        
        if use_cpu:
            command.append('--cpu')
            print("Force CPU mode enabled.")
        
        # Ensure checkpoints directory exists (weights dir is now handled inside SadTalker with fallback)
        os.makedirs(os.path.join(self.sadtalker_dir, 'checkpoints'), exist_ok=True)

        print(f"Running command: {' '.join(command)}")
        print(f"CWD: {self.sadtalker_dir}")

        try:
            # Run inference — cap at 45 minutes to prevent silent hangs
            VIDEO_TIMEOUT = 2700  # 45 minutes
            process = subprocess.run(
                command,
                cwd=self.sadtalker_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=VIDEO_TIMEOUT,
            )
            
            if process.returncode != 0:
                stderr = process.stderr
                print(f"Error Output: {stderr}")
                
                # Provide user-friendly error messages
                if "No face detected" in stderr or "index 0 is out of bounds" in stderr:
                    return {
                        'success': False, 
                        'error': "Không phát hiện được khuôn mặt trong ảnh. Vui lòng sử dụng ảnh chân dung rõ nét với khuôn mặt hiện diện rõ ràng."
                    }
                elif "CUDA out of memory" in stderr:
                    return {
                        'success': False,
                        'error': "Hết bộ nhớ GPU. Vui lòng thử lại hoặc sử dụng ảnh có kích thước nhỏ hơn."
                    }
                else:
                    return {
                        'success': False, 
                        'error': f"Lỗi khi tạo video: {stderr}"
                    }
                
            print(f"Output: {process.stdout}")

            # Find the latest generated MP4 file in the result directory
            # Note: SadTalker usually creates a subdirectory named with timestamp
            # But the 'still' mode might output directly or in a folder.
            # Let's check all mp4s in result_dir_abs recursively or just flat?
            # Original code used glob.glob(os.path.join(result_dir_abs, '*.mp4'))
            # Let's stick to that logic but be careful about concurrency. 
            # Ideally SadTalker should return the specific filename.
            # Since we can't easily change SadTalker return, we scan.
            
            list_of_files = glob.glob(os.path.join(unique_result_dir, '*.mp4'))
            # Check for files in subfolders too just in case
            list_of_files += glob.glob(os.path.join(unique_result_dir, '*', '*.mp4'))
            
            if not list_of_files:
                 return {'success': False, 'error': "No video generated."}
                 
            latest_file = max(list_of_files, key=os.path.getctime)
            
            # Build URL by finding the 'static' directory in the absolute path
            parts = latest_file.replace('\\', '/').split('/')
            try:
                static_idx = next(i for i in range(len(parts) - 1, -1, -1) if parts[i] == 'static')
                video_url = '/' + '/'.join(parts[static_idx:])
            except StopIteration:
                # Fallback if 'static' not found in path
                rel = os.path.relpath(latest_file, result_dir_abs).replace('\\', '/')
                video_url = f'/static/results/{rel}'

            return {
                'success': True,
                'video_url': video_url,
                'video_path': latest_file
            }

        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'error': "Video generation timed out (45 min limit). Try a shorter audio or smaller image."
            }
        except ValueError as e:
            # Handle face detection errors
            error_msg = str(e)
            if "No face detected" in error_msg:
                return {
                    'success': False,
                    'error': "Không phát hiện được khuôn mặt trong ảnh. Vui lòng sử dụng ảnh chân dung rõ nét với khuôn mặt hiện diện rõ ràng."
                }
            else:
                return {'success': False, 'error': error_msg}
        except Exception as e:
            print(f"Exception: {str(e)}")
            return {'success': False, 'error': f"Lỗi không mong đợi: {str(e)}"}
