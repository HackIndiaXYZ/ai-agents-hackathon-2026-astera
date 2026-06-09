import os
import json
import subprocess

def push_to_kaggle(username, key):
    dataset_dir = os.path.join(os.path.dirname(__file__), "..", "dataset")
    
    # Create dataset-metadata.json
    metadata = {
        "title": "Asteria Bhojpuri and Assamese Civic QA",
        "id": f"{username}/asteria-civic-qa",
        "licenses": [
            {
                "name": "CC0-1.0"
            }
        ]
    }
    
    with open(os.path.join(dataset_dir, "dataset-metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
        
    # Set env vars for Kaggle
    os.environ["KAGGLE_USERNAME"] = username
    os.environ["KAGGLE_KEY"] = key
    
    print(f"Pushing dataset to Kaggle as {username}/asteria-civic-qa...")
    
    # Run Kaggle command
    try:
        result = subprocess.run(
            ["kaggle", "datasets", "create", "-p", dataset_dir],
            capture_output=True,
            text=True,
            check=True,
            shell=True
        )
        print("✅ Kaggle Push Success!")
        print(result.stdout)
    except subprocess.CalledProcessError as e:
        if "already exists" in e.stdout or "already exists" in e.stderr:
            print("Dataset already exists, creating new version...")
            subprocess.run(
                ["kaggle", "datasets", "version", "-p", dataset_dir, "-m", "Updated dataset"],
                check=True,
                shell=True
            )
            print("✅ Kaggle Version Update Success!")
        else:
            print("❌ Kaggle Push Failed!")
            print("STDOUT:", e.stdout)
            print("STDERR:", e.stderr)

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 3:
        print("Usage: python push_to_kaggle.py <username> <key>")
        sys.exit(1)
    push_to_kaggle(sys.argv[1], sys.argv[2])
