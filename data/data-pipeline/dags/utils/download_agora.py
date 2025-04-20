import requests
import json
import os

def get_latest_agora_release():
    doi_url = "https://doi.org/10.5281/zenodo.13883066"

    try:
        response = requests.get(doi_url, allow_redirects=True, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f'Failed to resolve DOI: {e}')

    final_url = response.url
    if 'zenodo.org/records/' not in final_url:
        raise Exception(f'Unexpected final URL: {final_url}')
    
    record_id = final_url.split('zenodo.org/records/')[-1].strip('/')

    try:
        api_url = f'https://zenodo.org/api/records/{record_id}'
        api_response = requests.get(api_url, timeout=10)
        api_response.raise_for_status()
    except requests.RequestException as e:
        raise Exception(f'Failed to fetch record metadata: {e}')

    data = api_response.json()
    version = data.get('metadata', {}).get('version', 'N/A')
    publication_date = data.get('metadata', {}).get('publication_date', 'N/A')
    files = data.get('files', [])
    download_url = next((file['links']['self'] for file in files if file['key'] == 'agora.zip'), None)

    return {
        'version': version,
        'publication_date': publication_date,
        'download_url': download_url,
        'record_id': record_id,
        'final_url': final_url
    }

def update_config_with_download_url(config_path="config.json"):
    try:
        latest_info = get_latest_agora_release()
        download_url = latest_info.get('download_url')
        if not download_url:
            raise ValueError('No download URL found in latest AGORA release.')

        if not os.path.isfile(config_path):
            raise FileNotFoundError(f'Config file not found at {config_path}')

        with open(config_path, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        config_data['download_url'] = download_url

        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, indent=4)

        return True

    except (IOError, ValueError, json.JSONDecodeError, Exception) as e:
        print(f'Error updating config: {e}')
        return False

if __name__ == '__main__':
    # Resolve config.json path relative to script location
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Get parent of script directory
    parent_dir = os.path.dirname(script_dir)
    # Get grandparent of script directory
    grandparent_dir = os.path.dirname(parent_dir)
    # Config path
    config_file_path = os.path.join(grandparent_dir, "config", "config.json")
    
    
    success = update_config_with_download_url(config_file_path)
    print('Update successful.' if success else 'Update failed.')