"""Parallel sync for FLUX.2 klein models only."""
import os, json, zipfile, shutil, sys

# Load env
script_dir = os.path.dirname(os.path.abspath(__file__))
for env_path in (".env", "../.env", os.path.join(script_dir, "../.env")):
    if os.path.exists(env_path):
        with open(env_path) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip()
        break

import boto3
from botocore.config import Config

bucket_name = "diffusion4mac-storage"

def get_r2_client():
    return boto3.Session().client('s3',
        endpoint_url=f"https://{os.environ['cloudflare_id']}.r2.cloudflarestorage.com",
        aws_access_key_id=os.environ['r2_access_key_id'],
        aws_secret_access_key=os.environ['r2_secret_access_key'],
        config=Config(signature_version='s3v4')
    )

def check_exists(client, key):
    try:
        client.head_object(Bucket=bucket_name, Key=key)
        return True
    except:
        return False

client = get_r2_client()

models = {
    "flux_klein_4b": {
        "repo": "black-forest-labs/FLUX.2-klein-4B",
        "r2_key": "models/FLUX.2-klein-4B.zip"
    },
    "flux_klein": {
        "repo": "black-forest-labs/FLUX.2-klein-9B",
        "r2_key": "models/FLUX.2-klein-9B.zip"
    }
}

temp_dir = os.path.join(script_dir, "temp_sync")
os.makedirs(temp_dir, exist_ok=True)
hf_token = os.environ.get("HF_TOKEN")

for model_id, info in models.items():
    r2_key = info["r2_key"]
    if check_exists(client, r2_key):
        print(f"[Skip] {model_id} already in R2 as {r2_key}")
        continue

    print(f"\n[Sync] Downloading {info['repo']} for {model_id}...")
    from huggingface_hub import snapshot_download

    local_dir = os.path.join(temp_dir, model_id)
    try:
        repo_dir = snapshot_download(
            repo_id=info["repo"],
            token=hf_token,
            local_dir=local_dir,
        )
        print(f"[Sync] Download complete: {repo_dir}")

        zip_path = os.path.join(temp_dir, f"{model_id}.zip")
        print(f"[Sync] Creating zip {zip_path}...")
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zf:
            for root, dirs, files in os.walk(repo_dir):
                dirs[:] = [d for d in dirs if d not in ('.git', '.cache')]
                for file in files:
                    fp = os.path.join(root, file)
                    arc = os.path.relpath(fp, repo_dir)
                    sz = os.path.getsize(fp) / (1024*1024)
                    print(f"  Adding {arc} ({sz:.1f} MB)")
                    zf.write(fp, arc)

        sz_gb = os.path.getsize(zip_path) / (1024**3)
        print(f"[Sync] Zip: {sz_gb:.2f} GB. Uploading to R2 as {r2_key}...")
        client.upload_file(zip_path, bucket_name, r2_key)
        print(f"[Sync] {model_id} uploaded successfully!")

        os.remove(zip_path)
        shutil.rmtree(repo_dir, ignore_errors=True)
    except Exception as e:
        print(f"[Error] {model_id}: {e}")
        import traceback
        traceback.print_exc()

print("\nDone! Klein models synced.")
