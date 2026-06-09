import os
from dotenv import load_dotenv
from huggingface_hub import HfApi

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"), override=True)
token = os.getenv("HF_TOKEN")
repo_id = "Afuu-coder/asteria-bhojpuri-assamese-civic-qa"
readme_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "README.md")

api = HfApi(token=token)
print(f"Uploading README.md to {repo_id}...")
api.upload_file(
    path_or_fileobj=readme_path,
    path_in_repo="README.md",
    repo_id=repo_id,
    repo_type="dataset"
)
print("✅ README successfully updated on Hugging Face!")
