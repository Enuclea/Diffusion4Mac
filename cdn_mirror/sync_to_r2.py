import os
import json
import hashlib
import requests
import boto3
from botocore.config import Config

bucket_name = "diffusion4mac-storage"

def get_r2_client():
    r2_access_key_id = os.environ.get("r2_access_key_id")
    r2_secret_access_key = os.environ.get("r2_secret_access_key")
    cloudflare_id = os.environ.get("cloudflare_id")

    if not r2_access_key_id or not r2_secret_access_key:
        print("[Error] S3 credentials 'r2_access_key_id' and 'r2_secret_access_key' are required in .env for S3-compatible multipart uploads.")
        return None

    endpoint = f"https://{cloudflare_id}.r2.cloudflarestorage.com"
    session = boto3.Session()
    client = session.client(
        service_name="s3",
        endpoint_url=endpoint,
        aws_access_key_id=r2_access_key_id,
        aws_secret_access_key=r2_secret_access_key,
        config=Config(signature_version="s3v4")
    )
    return client

def calculate_md5(filepath):
    hash_md5 = hashlib.md5()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()

def check_file_exists_in_r2(client, key):
    try:
        client.head_object(Bucket=bucket_name, Key=key)
        return True
    except Exception:
        return False

def upload_to_r2(client, filepath, key):
    print(f"Uploading {filepath} to R2 bucket '{bucket_name}' key '{key}'...")
    # boto3 automatically handles multipart uploads for files > 8MB
    client.upload_file(filepath, bucket_name, key)
    print("Upload complete!")

def download_file(url, dest_path):
    hf_token = os.environ.get("HF_TOKEN")
    print(f"Downloading from {url}...")
    headers = {}
    if hf_token:
        headers["Authorization"] = f"Bearer {hf_token}"
        
    # Handle redirects manually to prevent authorization forwarding
    current_url = url
    response = None
    for _ in range(10):
        r = requests.get(current_url, headers=headers, stream=True, allow_redirects=False)
        if r.status_code in (301, 302, 303, 307, 308):
            location = r.headers.get("Location")
            if not location:
                response = r
                break
            from urllib.parse import urljoin, urlparse
            next_url = urljoin(current_url, location)
            if urlparse(next_url).netloc != urlparse(current_url).netloc:
                headers = {k: v for k, v in headers.items() if k.lower() != "authorization"}
            current_url = next_url
        else:
            response = r
            break
            
    response.raise_for_status()
    
    os.makedirs(os.path.dirname(dest_path), exist_ok=True)
    with open(dest_path, "wb") as f:
        for chunk in response.iter_content(chunk_size=1024 * 1024):
            if chunk:
                f.write(chunk)

def main():
    cloudflare_id = os.environ.get("cloudflare_id")
    if not cloudflare_id:
        print("[Error] 'cloudflare_id' is missing in .env.")
        return

    client = get_r2_client()
    if not client:
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))
    registry_path = os.path.join(script_dir, "registry.json")
    if not os.path.exists(registry_path):
        print(f"[Error] Manifest {registry_path} not found.")
        return

    with open(registry_path, "r") as f:
        registry = json.load(f)

    # Sync LoRAs
    loras = registry.get("loras", {})
    temp_dir = os.path.join(script_dir, "temp_sync")
    os.makedirs(temp_dir, exist_ok=True)

    updated_registry = False

    for lora_id, lora_info in loras.items():
        r2_key = lora_info["r2_key"]
        
        # Check if already in R2
        if check_file_exists_in_r2(client, r2_key):
            print(f"[Skip] LoRA {lora_id} already exists in R2.")
            continue

        url = lora_info["url"]
        filename = lora_info["filename"]
        local_path = os.path.join(temp_dir, filename)

        try:
            download_file(url, local_path)
            md5_hash = calculate_md5(local_path)
            upload_to_r2(client, local_path, r2_key)
            
            # Update manifest metadata
            lora_info["md5"] = md5_hash
            lora_info["size_bytes"] = os.path.getsize(local_path)
            updated_registry = True
            
            # Cleanup local temp file
            os.remove(local_path)
        except Exception as e:
            print(f"[Error] Failed to sync LoRA {lora_id}: {e}")

    # Sync base models
    models = registry.get("models", {})
    for model_id, model_info in models.items():
        r2_key = model_info["r2_key"] + ".zip"  # stored as zip in R2
        if check_file_exists_in_r2(client, r2_key):
            print(f"[Skip] Model {model_id} already exists in R2 as {r2_key}.")
            continue

        repo = model_info.get("huggingface_repo")
        if not repo:
            print(f"[Error] No huggingface_repo for model {model_id}, skipping.")
            continue

        print(f"[Sync] Downloading repo {repo} for model {model_id}...")
        try:
            from huggingface_hub import snapshot_download
            import zipfile
            import shutil

            hf_token = os.environ.get("HF_TOKEN")
            # Download the full repo to a temp directory
            repo_dir = snapshot_download(
                repo_id=repo,
                token=hf_token,
                local_dir=os.path.join(temp_dir, model_id),
            )
            print(f"[Sync] Repo downloaded to {repo_dir}")

            # Zip the repo
            zip_path = os.path.join(temp_dir, f"{model_id}.zip")
            print(f"[Sync] Creating zip archive {zip_path}...")
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:
                for root, dirs, files in os.walk(repo_dir):
                    # Skip .git and .cache dirs
                    dirs[:] = [d for d in dirs if d not in ('.git', '.cache')]
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, repo_dir)
                        print(f"  Adding {arc_name} ({os.path.getsize(file_path) / (1024*1024):.1f} MB)")
                        zf.write(file_path, arc_name)

            zip_size = os.path.getsize(zip_path) / (1024*1024*1024)
            print(f"[Sync] Zip created: {zip_size:.2f} GB. Uploading to R2 as {r2_key}...")
            upload_to_r2(client, zip_path, r2_key)
            print(f"[Sync] Model {model_id} uploaded successfully!")

            # Cleanup
            os.remove(zip_path)
            shutil.rmtree(repo_dir, ignore_errors=True)
        except Exception as e:
            print(f"[Error] Failed to sync model {model_id}: {e}")
            import traceback
            traceback.print_exc()

    # Upload updated registry.json to R2 publicly
    if updated_registry:
        with open(registry_path, "w") as f:
            json.dump(registry, f, indent=2)
            
    upload_to_r2(client, registry_path, "registry.json")
    print("Registry manifest successfully synced to R2!")

if __name__ == "__main__":
    # Load .env file from CWD, script directory, or parent directories
    script_dir = os.path.dirname(os.path.abspath(__file__))
    env_paths = [
        ".env",
        "../.env",
        os.path.join(script_dir, ".env"),
        os.path.join(script_dir, "../.env"),
        os.path.join(script_dir, "../../.env")
    ]
    for env_path in env_paths:
        if os.path.exists(env_path):
            with open(env_path) as f:
                for line in f:
                    if "=" in line and not line.startswith("#"):
                        k, v = line.strip().split("=", 1)
                        os.environ[k.strip()] = v.strip()
            break
    main()
