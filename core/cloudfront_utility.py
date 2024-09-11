import requests

class FileDownloader:
    def __init__(self, url, download_file_path):
        self.url = url
        self.file_path = download_file_path

    def download_file(self):
        # Send a GET request to the URL
        response = requests.get(self.url, stream=True)

        # Check if the request was successful
        if response.status_code == 200:
            # Open a local file with write-binary mode to save the downloaded PDF
            with open(self.file_path, "wb") as file:
                for chunk in response.iter_content(chunk_size=8192):
                    file.write(chunk)
            print("File downloaded successfully!")
        else:
            print(f"Failed to download the file. Status code: {response.status_code}")


