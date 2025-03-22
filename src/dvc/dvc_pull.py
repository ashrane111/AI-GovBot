import subprocess
import os
from pathlib import Path
import configparser

def restore_dvc_data(repo_path: str, gcp_bucket: str):
    """
    Restores DVC-tracked files from GCP in an existing repository
    
    Args:
        repo_path: Path to existing cloned repository
        gcp_bucket: GCP bucket path (gs://your-bucket/path)
    """
    original_dir = Path.cwd()
    try:
        repo_path = Path(repo_path).resolve()
        if not (repo_path / ".dvc").exists():
            raise ValueError("Not a DVC repository (missing .dvc directory)")

        os.chdir(repo_path)
        remote_name = "dvc-ai-govbot"
        creds_path = "data/data-pipeline/secrets/google_cloud_key.json"
        config_path = repo_path / ".dvc/config"

        # Check if config exists and is properly configured
        config_needs_update = True
        if config_path.exists():
            config = configparser.ConfigParser()
            config.read(config_path)
            if (config.has_section('core') and
                config.has_option('core', 'remote') and
                config.get('core', 'remote') == remote_name and
                config.has_section(f'remote "{remote_name}"') and
                config.has_option(f'remote "{remote_name}"', 'url') and
                config.get(f'remote "{remote_name}"', 'url') == gcp_bucket and
                config.has_option(f'remote "{remote_name}"', 'credentialpath') and
                config.get(f'remote "{remote_name}"', 'credentialpath') == creds_path):
                config_needs_update = False

        if config_needs_update:
            print("Configuring DVC remote...")
            subprocess.run(
                ["dvc", "remote", "add", "-f", "-d", remote_name, gcp_bucket],
                check=True
            )
            subprocess.run(
                ["dvc", "remote", "modify", remote_name, "credentialpath", creds_path],
                check=True
            )
        else:
            print("DVC remote already properly configured.")

        # Pull data and checkout
        print("Pulling data from remote storage...")
        subprocess.run(["dvc", "pull"], check=True)
        subprocess.run(["dvc", "checkout"], check=True)
        
        print("✅ DVC data restoration completed successfully!")

    except subprocess.CalledProcessError as e:
        print(f"🚨 DVC operation failed: {str(e)}")
        print("Verify that:")
        print(f"- Remote '{remote_name}' configuration in .dvc/config is correct")
        print("- GCP credentials have storage.objectAdmin permissions")
        print(f"- Credential file exists at {creds_path}")
    except Exception as e:
        print(f"🚨 Unexpected error: {str(e)}")
    finally:
        os.chdir(original_dir)


if __name__ == "__main__":
    restore_dvc_data(
        repo_path= os.getcwd(),
        gcp_bucket="gs://dvc-ai-govbot"
    )
