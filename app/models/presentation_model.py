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
            except:
                self.presentations = {}
        else:
            self.presentations = {}

    def save(self):
        """Save presentations to JSON file"""
        try:
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(self.presentations, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving presentations: {e}")

    def get_all(self):
        return self.presentations

    def get_by_id(self, pres_id):
        return self.presentations.get(pres_id)

    def add(self, filename, file_path, file_type, slides):
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
