from huggingface_hub import snapshot_download, list_repo_files
import os
import shutil

# Required model files for SadTalker
REQUIRED_MODELS = [
    'auido2exp_00300-model.pth',
    'auido2pose_00140-model.pth',
    'epoch_20.pth',
    'wav2lip.pth',
    'facevid2vid_00189-model.pth.tar',
    'mapping_00109-model.pth.tar',
    'mapping_00229-model.pth.tar',
]

def check_models_exist(models_dir):
    """
    Check if all required SadTalker models exist in the checkpoints directory.
    
    Args:
        models_dir: Path to the checkpoints directory
        
    Returns:
        tuple: (all_exist: bool, missing_models: list)
    """
    if not os.path.exists(models_dir):
        return False, REQUIRED_MODELS
    
    missing = []
    for model_file in REQUIRED_MODELS:
        model_path = os.path.join(models_dir, model_file)
        if not os.path.exists(model_path):
            missing.append(model_file)
    
    return len(missing) == 0, missing

def download_sadtalker_models(force=False):
    """
    Download SadTalker models from HuggingFace.
    
    Args:
        force: If True, download even if models exist
    """
    print("Checking SadTalker models...")
    
    # Destination directory for the models (app/SadTalker/checkpoints)
    models_dir = os.path.join(os.getcwd(), "app", "SadTalker", "checkpoints")
    
    # Check if models already exist
    all_exist, missing = check_models_exist(models_dir)
    
    if all_exist and not force:
        print(f"✓ All required SadTalker models found in: {models_dir}")
        print("  No download needed.")
        return True
    
    if not all_exist:
        print(f"✗ Missing {len(missing)} model file(s):")
        for model in missing:
            print(f"  - {model}")
    
    os.makedirs(models_dir, exist_ok=True)
    
    repo_id = "vinthony/SadTalker"

    try:
        print(f"\nDownloading from: {repo_id}")
        files = list_repo_files(repo_id=repo_id)
        print(f"Found {len(files)} files in repository.")
        
        print(f"Downloading to: {models_dir}")
        print("Note: This requires approximately 4GB of free disk space.")
        print("This may take several minutes depending on your internet speed...\n")
        
        path = snapshot_download(
            repo_id=repo_id,
            local_dir=models_dir,
            local_dir_use_symlinks=False
        )
        
        # Verify download
        all_exist, still_missing = check_models_exist(models_dir)
        if all_exist:
            print(f"\n✓ Successfully downloaded all SadTalker models to: {path}")
            return True
        else:
            print(f"\n⚠ Download completed but some files are still missing:")
            for model in still_missing:
                print(f"  - {model}")
            return False

    except Exception as e:
        print(f"\n✗ Download Error: {e}")
        print("\n[!] Download failed. Please check:")
        print("  - Internet connection")
        print(f"  - Available disk space (need ~4-5GB on {os.path.splitdrive(os.getcwd())[0]})")
        print("  - HuggingFace Hub access")
        return False

def ensure_models():
    """
    Ensure all required models are available. Download if necessary.
    This function can be called from other modules.
    
    Returns:
        bool: True if all models are available, False otherwise
    """
    models_dir = os.path.join(os.getcwd(), "app", "SadTalker", "checkpoints")
    all_exist, missing = check_models_exist(models_dir)
    
    if all_exist:
        return True
    
    print("\n" + "="*60)
    print("SadTalker models are required but not found.")
    print("="*60)
    return download_sadtalker_models()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download SadTalker models')
    parser.add_argument('--force', action='store_true', 
                        help='Force download even if models exist')
    args = parser.parse_args()
    
    success = download_sadtalker_models(force=args.force)
    exit(0 if success else 1)
