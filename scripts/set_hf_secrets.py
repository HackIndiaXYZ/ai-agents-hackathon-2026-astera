import os
import json
from huggingface_hub import HfApi

# Configuration
REPO_ID = "Afuu-coder/asteria-civic-agent"
HF_TOKEN = os.getenv("HF_TOKEN")
ADAPTION_KEY = os.getenv("ADAPTION_API_KEY")

api = HfApi()

def set_secrets():
    print("Setting ADAPTION_API_KEY...")
    api.add_space_secret(
        repo_id=REPO_ID,
        key="ADAPTION_API_KEY",
        value=ADAPTION_KEY,
        token=HF_TOKEN
    )
    
    print("Reading service_account.json...")
    try:
        with open("e:/Dataset project/service_account.json", "r") as f:
            gcp_json = f.read()
            
        print("Setting GCP_CREDENTIALS_JSON...")
        api.add_space_secret(
            repo_id=REPO_ID,
            key="GCP_CREDENTIALS_JSON",
            value=gcp_json,
            token=HF_TOKEN
        )
        print("Secrets successfully added to Hugging Face Space!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    set_secrets()
