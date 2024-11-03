import os
import time
import requests
import pyperclip
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from dotenv import load_dotenv

load_dotenv()
IMGUR_CLIENT_ID = os.getenv("IMGUR_CLIENT_ID")
SCREENSHOT_FOLDER = os.path.expanduser("~/Pictures/Screenshots")
SAVE_LINKS = True  # Set to False to disable saving links
DELAY = 0.1 # Ensure the file is fully written before uploading (Adjust if needed)
RETRY_COUNT = 5 # Number of times to retry uploading a file

class ScreenshotHandler(FileSystemEventHandler):
    def __init__(self):
        self.last_processed_time = time.time()

    def on_created(self, event):
        if event.is_directory or not event.src_path.endswith('.png'):
            return
        
        if os.path.getctime(event.src_path) > self.last_processed_time:
            time.sleep(DELAY)
            link = self.upload_image(event.src_path)
            if link:
                print(f"Uploaded: {link}")
                pyperclip.copy(link)
                if SAVE_LINKS:
                    self.save_link_to_file(link)
            
            self.last_processed_time = time.time()

    def upload_image(self, image_path):
        headers = {'Authorization': f'Client-ID {IMGUR_CLIENT_ID}'}

        for _ in range(RETRY_COUNT):
            try:
                with open(image_path, 'rb') as img:
                    response = requests.post('https://api.imgur.com/3/image', headers=headers, files={'image': img})
                    if response.status_code == 200:
                        return response.json()['data']['link']
                    else:
                        print("Failed to upload image.")
                        return None
            except PermissionError:
                print(f"Permission denied for {image_path}. Retrying...")
                time.sleep(1)
        print(f"Could not access {image_path} after multiple attempts.")
        return None

    def save_link_to_file(self, link):
        with open("screenshot_links.txt", "a") as f:
            f.write(link + "\n")

def start_watching():
    event_handler = ScreenshotHandler()
    observer = Observer()
    observer.schedule(event_handler, SCREENSHOT_FOLDER, recursive=False)
    observer.start()
    print("Monitoring for new screenshots...")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()

if __name__ == "__main__":
    start_watching()