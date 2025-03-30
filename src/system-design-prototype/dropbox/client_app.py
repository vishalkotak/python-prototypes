import requests
import os
from datetime import datetime, timedelta, timezone
import logging

logging.basicConfig(level=logging.INFO)

FILE_SERVICE_URL = "http://localhost:8000" 
SYNC_SERVICE_URL = "http://localhost:8001"

DUMMY_FILE_NAME = "test_upload_fastapi.txt"
DUMMY_FILE_CONTENT = "This is the content for the FastAPI test file.\n" * 15


def create_dummy_file():
    try:
        with open(DUMMY_FILE_NAME, "w") as f:
            f.write(DUMMY_FILE_CONTENT)
        logging.info(f"Created dummy file: {DUMMY_FILE_NAME}")
    except Exception as e:
        logging.error(f"Failed to create dummy file: {e}")
        raise


def upload_file(file_path):
    upload_url = f"{FILE_SERVICE_URL}/upload"
    try:
        with open(file_path, 'rb') as f:
            files = {'file': (os.path.basename(file_path), f, 'text/plain')}
            response = requests.post(upload_url, files=files, timeout=60)
            response.raise_for_status()
            logging.info(f"Upload Response: {response.status_code}")
            result = response.json()
            logging.info(f"Server response: {result}")
            return result.get('file_id')
    except Exception as e:
        logging.error(f"An error occurred during upload: {e}")
        return None
    

def check_changes(since_timestamp=None):
    sync_url = f"{SYNC_SERVICE_URL}/changes"
    params = {}
    if since_timestamp:
        params['timestamp'] = since_timestamp.isoformat(timespec='seconds').replace('+00:00', 'Z')
    try:
        response = requests.get(sync_url, params=params, timeout=30)
        response.raise_for_status()
        logging.info(f"Check Changes Response: {response.status_code}")
        result = response.json()
        logging.info(f"Found changes raw data: {result}")
        return result.get('changes', [])
    except Exception as e:
        logging.error(f"An error occurred during check changes: {e}")
        return []
    

def download_file(file_id, output_filename):
    download_url = f"{FILE_SERVICE_URL}/get_file/{file_id}"
    try:
        with requests.get(download_url, stream=True, timeout=60) as response:
            response.raise_for_status()
            with open(output_filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            logging.info(f"Successfully downloaded file {file_id} to {output_filename}")
            return True   
    except requests.exceptions.RequestException as e:
        logging.error(f"Download failed for file {file_id}: {e}")
        if e.response is not None:
             try:
                 logging.error(f"Server error detail: {e.response.json()}")
             except ValueError:
                 logging.error(f"Server error detail: {e.response.text}")
        return False
    except Exception as e:
        logging.error(f"An error occurred during download: {e}")
        return False
    

def cleanup_dummy_file():
    if os.path.exists(DUMMY_FILE_NAME):
        try:
            os.remove(DUMMY_FILE_NAME)
            logging.info(f"Removed dummy file: {DUMMY_FILE_NAME}")
        except Exception as e:
            logging.error(f"Failed to remove dummy file: {e}")


if __name__ == "__main__":
    try:
        create_dummy_file()
        time_before_upload = datetime.now(timezone.utc) - timedelta(seconds=5) 
        logging.info("\n--- Attempting Upload ---")
        uploaded_file_id = upload_file(DUMMY_FILE_NAME)

        if uploaded_file_id:
            logging.info(f"File uploaded successfully with ID: {uploaded_file_id}")
            import time
            time.sleep(2)
            logging.info(f"\n--- Checking Changes since {time_before_upload.isoformat()} ---")
            changes = check_changes(since_timestamp=time_before_upload)
            download_target_id = None
            if changes:
                logging.info("Found recent changes:")
                for change in changes:
                    print(f"  - ID: {change.get('file_id')}, Name: {change.get('file_name')}, Modified: {change.get('last_modified')}")
                    if change.get('file_id') == uploaded_file_id:
                        download_target_id = uploaded_file_id
            else:
                logging.warning("No changes detected shortly after upload (check timestamp logic/DB timezones).")
                download_target_id = uploaded_file_id

            if download_target_id:
                logging.info(f"\n--- Attempting Download of file ID: {download_target_id} ---")
                download_path = f"downloaded_{DUMMY_FILE_NAME}"
                download_file(download_target_id, download_path)
                if os.path.exists(download_path):
                    logging.info(f"Downloaded file '{download_path}' exists.")
                else:
                    logging.warning("Cannot attempt download as file ID was not confirmed.")
            else:
                logging.error("Upload failed, skipping subsequent steps.")
    finally:
        cleanup_dummy_file()
