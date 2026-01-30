import json
import os
import time
import uuid

class PresentationModel:
    def __init__(self, data_folder):
        self.data_folder = data_folder
        self.json_path = os.path.join(data_folder, 'presentations.json')
        self.presentations = {}
        self.load()

    def load(self):
        """Load presentations from JSON file"""
        if os.path.exists(self.json_path):
            try:
                with open(self.json_path, 'r', encoding='utf-8') as f:
                    self.presentations = json.load(f)
                print(f"DEBUG: Loaded {len(self.presentations)} presentations from {self.json_path}", flush=True)
            except Exception as e:
                print(f"ERROR: Failed to load presentations from {self.json_path}: {e}", flush=True)
                # Do NOT overwrite with empty dict if load fails, keep existing memory or init empty if first load
                if not hasattr(self, 'presentations'): 
                    self.presentations = {}
        else:
            print(f"DEBUG: Data file {self.json_path} does not exist, initializing empty.", flush=True)
            self.presentations = {}

    def save(self):
        """Save presentations to JSON file"""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.json_path), exist_ok=True)
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.presentations, f, ensure_ascii=False, indent=2)
            print(f"DEBUG: Saved {len(self.presentations)} presentations to {self.json_path}", flush=True)
        except Exception as e:
            print(f"ERROR: Error saving presentations: {e}", flush=True)

    def get_all(self):
        return self.presentations

    def get_by_id(self, pres_id):
        # First check memory
        if pres_id in self.presentations:
            return self.presentations[pres_id]
        
        # If not found, try reloading from disk (in case another worker updated it)
        print(f"DEBUG: ID {pres_id} not found in memory, reloading from disk...", flush=True)
        self.load()
        
        # Check again
        if pres_id in self.presentations:
             print(f"DEBUG: ID {pres_id} found after reload.", flush=True)
             return self.presentations[pres_id]
        
        print(f"DEBUG: ID {pres_id} still not found after reload.", flush=True)
        return None

    def add(self, filename, file_path, file_type, slides, pres_id=None):
        if not pres_id:
            pres_id = str(uuid.uuid4())
            
        presentation_data = {
            'id': pres_id,
            'filename': filename,
            'file_path': file_path,
            'type': file_type,
            'slides': slides,
            'created_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'avatar_path': None,
            'final_video_path': None
        }
        
        # Initialize slide data
        for slide in presentation_data['slides']:
            slide['generated_text'] = ''
            slide['edited_text'] = ''
            slide['audio_path'] = None
            slide['video_path'] = None
            slide['status'] = 'pending'
            
        self.presentations[pres_id] = presentation_data
        self.save()
        return presentation_data

    def update(self, pres_id, data):
        if pres_id in self.presentations:
            self.presentations[pres_id].update(data)
            self.save()
            return True
        return False
        
    def get_slide(self, pres_id, slide_num):
        presentation = self.get_by_id(pres_id)
        if not presentation:
            return None
        return next((s for s in presentation['slides'] if s['slide_num'] == slide_num), None)

    def update_slide(self, pres_id, slide_num, data):
        slide = self.get_slide(pres_id, slide_num)
        if slide:
            slide.update(data)
            self.save()
            return True
        return False
