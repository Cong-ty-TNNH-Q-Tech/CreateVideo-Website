try:
    from moviepy.editor import concatenate_audioclips, AudioFileClip
    print("MoviePy imported successfully")
except Exception as e:
    print(f"Error importing moviepy: {e}")
