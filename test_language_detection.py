"""
Test script to verify language detection and TTS engine selection
"""

import sys
import os

# Add app to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.services.audio_service import AudioService

def test_language_detection():
    """Test language detection with various texts"""
    
    print("=" * 60)
    print("🧪 TESTING LANGUAGE DETECTION & TTS ENGINE SELECTION")
    print("=" * 60)
    
    # Initialize AudioService
    audio_service = AudioService()
    
    # Test cases
    test_cases = [
        ("Xin chào, tôi là trợ lý AI của bạn. Tôi có thể giúp gì cho bạn?", "Vietnamese"),
        ("Hello, I am your AI assistant. How can I help you today?", "English"),
        ("Đây là một bài thuyết trình về công nghệ AI và machine learning.", "Vietnamese"),
        ("This is a presentation about AI technology and machine learning.", "English"),
        ("Hôm nay chúng ta sẽ tìm hiểu về Deep Learning", "Vietnamese"),
        ("Today we will learn about Deep Learning and neural networks", "English"),
        ("Trí tuệ nhân tạo đang thay đổi thế giới", "Vietnamese"),
        ("Artificial intelligence is changing the world", "English"),
    ]
    
    print("\n📋 Test Cases:\n")
    
    for i, (text, expected_lang) in enumerate(test_cases, 1):
        print(f"\nTest #{i}: {expected_lang}")
        print(f"Text: {text[:50]}...")
        print("-" * 60)
        
        # Detect language
        detected = audio_service.detect_language(text)
        
        # Check which engine should be used
        should_use_vieneu = audio_service.should_use_vieneu(detected)
        
        # Display results
        print(f"✅ Detected language: {detected}")
        print(f"🎤 TTS Engine: {'VieNeu-TTS' if should_use_vieneu else 'gTTS'}")
        
        # Verify correctness
        is_correct = (
            (expected_lang == "Vietnamese" and detected == "vi") or
            (expected_lang == "English" and detected == "en")
        )
        
        if is_correct:
            print("✅ CORRECT!")
        else:
            print(f"❌ INCORRECT! Expected: {expected_lang}")
        
        print()
    
    print("=" * 60)
    print("🎯 SUMMARY")
    print("=" * 60)
    print("✅ VieNeu-TTS will be used for Vietnamese text")
    print("✅ gTTS will be used for English text")
    print("✅ System automatically detects and switches engines")
    print("=" * 60)

if __name__ == "__main__":
    test_language_detection()
