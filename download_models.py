from huggingface_hub import snapshot_download, list_repo_files
import os
import shutil

def download_sadtalker_models():
    print("Preparing to download SadTalker models...")
    
    # Destination directory for the models
    models_dir = os.path.join(os.getcwd(), "SadTalker", "checkpoints")
    os.makedirs(models_dir, exist_ok=True)
    
    repo_id = "vinthony/SadTalker"

    try:
        print(f"Checking repo: {repo_id}")
        files = list_repo_files(repo_id=repo_id)
        print(f"Found {len(files)} files in repository.")
        
        print(f"Downloading to {models_dir} ...")
        print("Note: This requires approximately 4GB of free disk space.")
        
        path = snapshot_download(
            repo_id=repo_id,
            local_dir=models_dir,
            local_dir_use_symlinks=False
        )
        print(f"Successfully downloaded SadTalker models to: {path}")

    except Exception as e:
        print(f"\nExample Error: {e}")
        print("\n[!] Download failed. Please check your internet connection or disk space.")
        print(f"Ensure you have at least 4-5GB free on {os.path.splitdrive(os.getcwd())[0]}")

if __name__ == "__main__":
    download_sadtalker_models()
