from decouple import config
import json
import boto3
import os
import requests


AWS_ACCESS_KEY_ID = config('AWS_ACCESS_KEY_ID')
AWS_SECRET_KEY_ID = config('AWS_SECRET_KEY_ID')


class S3Utility:
    def __init__(self) -> None:
        self.s3_client = boto3.client('s3',
                             aws_access_key_id=AWS_ACCESS_KEY_ID,
                             aws_secret_access_key=AWS_SECRET_KEY_ID
                            )
        
        
    def upload_files(self, local_file_path, s3_bucket, s3_file_path):
        try:
            self.s3_client.upload_file(local_file_path, s3_bucket, s3_file_path)
            return True
        except Exception as err:
            print(err)
            return False
        
        

    def download_files(self, s3_bucket, s3_filepath, local_filepath):
        """
        Function to download a file to an S3 bucket
        -----------------------------------
        :param
        * s3_location: S3 object name. 
        * local_filepath: local file path where the file will get downloaded.

        :return: True if file was uploaded, else False 
        """
        try:
            self.s3_client.download_file(s3_bucket, s3_filepath, local_filepath)
            return True
        except Exception as err:
            print(str(err))
            return False

    
        
        
        
class CloudFrontDownloadUtility:


    def download_files(self, cloudfront_link, local_filepath):
        """
        Function to download a file from cloudfront link
        -----------------------------------
        :param
        * cloudfront_link: S3 object name. 
        * local_filepath: local file path where the file will get downloaded.

        :return: True if file was uploaded, else False 
        """
        try:

            # Send a GET request to the URL
            response = requests.get(cloudfront_link, stream=True)

            # Check if the request was successful
            if response.status_code == 200:
                # Open a local file with write-binary mode to save the downloaded PDF
                with open(local_filepath, "wb") as file:
                    for chunk in response.iter_content(chunk_size=8192):
                        file.write(chunk)
                print("File downloaded successfully!")
                return True
            
            print(f"Failed to download the file. Status code: {response.status_code}")
            return False

        except Exception as err:
            print(str(err))
            return False

    
        