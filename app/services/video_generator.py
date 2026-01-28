import os
import subprocess
import sys
import glob

class VideoGenerationService:
    def __init__(self, app_root):
        """
        Initialize VideoGenerationService
        args:
            app_root: Root path of the application (where SadTalker folder is located)
        """
        # SadTalker is now inside app/SadTalker
        self.sadtalker_dir = os.path.join(app_root, 'SadTalker')
        
    def generate_video(self, source_image_path, driven_audio_path, result_dir, use_cpu=False):
        """
        Generate talking head video using SadTalker
        """
        # Ensure absolute paths
        source_image_abs = os.path.abspath(source_image_path)
        driven_audio_abs = os.path.abspath(driven_audio_path)
        result_dir_abs = os.path.abspath(result_dir)
        
        # Determine python executable
        # Try to find venv python from the project root (parent of app_root)
        project_root = os.path.dirname(app_root)
        venv_python = os.path.join(project_root, 'venv', 'Scripts', 'python.exe')
        
        if os.path.exists(venv_python):
            python_exec = venv_python
        else:
            python_exec = sys.executable

        # Construct command
        command = [
            python_exec, 'inference.py',
            '--driven_audio', driven_audio_abs,
            '--source_image', source_image_abs,
            '--result_dir', result_dir_abs,
            '--still', 
            '--preprocess', 'resize',
            '--checkpoint_dir', 'checkpoints',
            '--batch_size', '1'
        ]
        
        if use_cpu:
            command.append('--cpu')
            print("Force CPU mode enabled.")
        
        print(f"Running command: {' '.join(command)}")
        print(f"CWD: {self.sadtalker_dir}")

        try:
            # Run inference
            process = subprocess.run(
                command, 
                cwd=self.sadtalker_dir, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True
            )
            
            if process.returncode != 0:
                print(f"Error Output: {process.stderr}")
                return {
                    'success': False, 
                    'error': f"SadTalker Error: {process.stderr}"
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
            
            list_of_files = glob.glob(os.path.join(result_dir_abs, '*.mp4'))
            # Check for files in subfolders too just in case
            list_of_files += glob.glob(os.path.join(result_dir_abs, '*', '*.mp4'))
            
            if not list_of_files:
                 return {'success': False, 'error': "No video generated."}
                 
            latest_file = max(list_of_files, key=os.path.getctime)
            
            # If the file is in a subfolder, we need to handle the relative path for URL
            # result_dir_abs is static/results
            # latest_file is static/results/timestamp/vid.mp4
            
            rel_path = os.path.relpath(latest_file, result_dir_abs)
            
            # If rel_path has backslashes (Windows), replace with forward slashes for URL
            rel_path_url = rel_path.replace('\\', '/')
            
            return {
                'success': True,
                'video_url': f'/static/results/{rel_path_url}'
            }

        except Exception as e:
            print(f"Exception: {str(e)}")
            return {'success': False, 'error': str(e)}
