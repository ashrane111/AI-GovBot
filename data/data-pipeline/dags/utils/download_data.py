import os
import requests
import zipfile
import io

# Define the function to download the zip file
def download_and_unzip_data_file(download_url, output_dir_name):
    # Ensure the directory exists
    output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
    os.makedirs(output_dir, exist_ok=True)
    
    response = requests.get(download_url, stream=True)
    if response.status_code == 200:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), output_dir_name)
        os.makedirs(output_dir, exist_ok=True)

        zip_file_bytes = io.BytesIO(response.content)

        with zipfile.ZipFile(zip_file_bytes, 'r') as zip_ref:
            zip_ref.extractall(output_dir)
        print(f"File extracted successfully to {output_dir}")
        return output_dir
    else:
        raise Exception(f"Failed to download file, status code: {response.status_code}")
        return


# Main function for standalone testing
def main():
    
    test_url = 'https://zenodo.org/records/14877811/files/agora.zip'  # Replace with a valid URL
    test_path = 'merged_input'  # Replace with a valid path
    download_and_unzip_data_file(test_url, test_path)

if __name__ == "__main__":
    main()
