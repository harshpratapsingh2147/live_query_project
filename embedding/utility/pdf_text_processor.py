from google.cloud import vision
from pdf2image import convert_from_path
from PIL import Image
from decouple import config
from pathlib import Path

import io
import re
import os
import glob

POPPLER_PATH = config("POPPLER_PATH")
GOOGLE_APPLICATION_CREDENTIALS = config("GOOGLE_APPLICATION_CREDENTIALS_PATH")

# OUTPUT_IMAGE_BASE_FOLDER = config("OUTPUT_IMAGE_FOLDER")
# INPUT_FOLDER_PATH = config("INPUT_FOLDER_PATH")
# OUTPUT_TEXT_FOLDER = config("OUTPUT_TEXT_FOLDER")

class PDFtoImage:
    """
    Converts PDF files to images for further processing.

    Attributes:
        pdf_filepath (str): The path to the input PDF file.
        poppler_path (str): The path to the Poppler utility for PDF conversion.
        output_image_folder (str): The folder to save the output images.
        input_pdf_folder (str): The folder containing the input PDF file.
        input_pdf_path (str): The full path to the input PDF file.
    """
    
    def __init__(self, pdf_filepath) -> None:
        self.poppler_path = POPPLER_PATH
        self.input_pdf_path = pdf_filepath
        self.file_name = pdf_filepath.split("/")[-1]
        self.input_pdf_folder = "/".join(pdf_filepath.split("/")[:-1])
        section_name = self.file_name.split("_")[0]
        self.output_image_folder = os.path.join(self.input_pdf_folder, section_name)
        self.create_output_image_path()
        
        
    def create_output_image_path(self):
        """
        Creates the output directory if it doesn't exist.
        """
        
        # Make sure the output folder exists
        if not os.path.exists(self.output_image_folder):
            os.makedirs(self.output_image_folder)
            
            
    def resize_image(self, image, width):
        """
        Resizes an image while maintaining its aspect ratio.

        Args:
            image (PIL.Image.Image): The image to resize.
            width (int): The desired width of the resized image.

        Returns:
            PIL.Image.Image: The resized image.
        """
        
        original_width, original_height = image.size

        # Calculate the new height based on the aspect ratio
        aspect_ratio = original_height / original_width
        new_height = int(width * aspect_ratio)

        # Resize the image using the LANCZOS filter
        resized_image = image.resize((width, new_height), Image.LANCZOS)
        return resized_image

    
    def pdf_to_images(self):
        """
        Converts the PDF into a series of images.

        Returns:
            list: A list of paths to the saved images.
        """

        # Convert PDF to list of images
        images = convert_from_path(self.input_pdf_path, poppler_path=self.poppler_path)

        image_paths = []
        for i, image in enumerate(images):
            
            # Resize the image before saving
            resized_image = self.resize_image(image, 1024)
            image_path = os.path.join(self.output_image_folder, f"{self.file_name.replace('.pdf','')}_page_{i + 1}.png")
            resized_image.save(image_path, 'PNG')
            image_paths.append(image_path)
            
            # Free up memory by deleting the resized image object
            del resized_image

        return image_paths


class ImagetoText:
    """
    Extracts text from images using Google Cloud Vision API.

    Attributes:
        input_filename (str): The name of the input PDF file.
        client (google.cloud.vision.ImageAnnotatorClient): Google Vision API client.
        image_base_folder (str): The folder containing the images generated from the PDF.
        image_file_list (list): List of image file paths.
        output_text_folder (str): The folder to save the extracted text.
        output_text_file (str): The file path to save the extracted text.
    """
    
    def __init__(self, pdf_filepath) -> None:
        self.client = vision.ImageAnnotatorClient.from_service_account_json(GOOGLE_APPLICATION_CREDENTIALS)
        self.input_pdf_path = pdf_filepath
        self.input_pdf_folder = "/".join(pdf_filepath.split("/")[:-1])
        filename = pdf_filepath.split("/")[-1]
        section_name = filename.split("_")[0]
        self.image_base_folder = os.path.join(self.input_pdf_folder, section_name)
        
        self.image_file_list = self.get_image_files()
        self.output_text_folder = f"{self.input_pdf_folder}/text_files"
        self.output_text_file = os.path.join(self.output_text_folder, filename.replace(".pdf", ".txt"))
        self.create_output_folder()
        
            

    def get_image_files(self):
        """
        Retrieves the list of image files generated from the PDF.

        Returns:
            list: List of image file paths.
        """
        # Ensure the image base folder path ends with a slash
        if '/' != self.image_base_folder[-1]:
            self.image_base_folder += '/'
        return [files for files in glob.glob(self.image_base_folder + '**')]
    
    
    def create_output_folder(self):
        """
        Creates the output folder for the extracted text if it doesn't exist.
        """
        os.makedirs(self.output_text_folder,exist_ok=True)
        
        
    def clean_text(self, text):
        """
        Cleans the extracted text by removing unwanted characters.

        Args:
            text (str): The text to clean.

        Returns:
            str: The cleaned text.
        """
        return re.sub(r'[^a-zA-Z0-9\s\u0900-\u097F]', '', text)


    def extract_text(self):
        """
        Extracts text from the images and saves it to a text file.

        Returns:
            str: The path to the output text file.
        """
        
        # Extract and clean text from images
        
        for image_path in self.image_file_list:
            print("image path to extract text:", image_path)
            with io.open(image_path, 'rb') as image_file:
                content = image_file.read()

            image = vision.Image(content=content)
            response = self.client.text_detection(image=image)
            texts = response.text_annotations

            if texts:
                # Extract and clean the text
                raw_text = texts[0].description
                cleaned_text = self.clean_text(raw_text)
                
                # Append the cleaned text to the output file
                with open(self.output_text_file, "a", encoding="utf-8") as file:
                    file.write(cleaned_text + "\n")

            if response.error.message:
                raise Exception(f'{response.error.message}')
        return self.output_text_file

        
class OCRDataExtract:
    """
    Manages the OCR process from PDF to text extraction.

    Methods:
        process(input_file_name): Converts a PDF to images and extracts text from those images.
    """

    def process(self, input_file_path):
        """
        Converts a PDF file to images and then extracts text from those images.

        Args:
            input_file_name (str): The name of the input PDF file.

        Returns:
            str: The path to the text file containing the extracted text.
        """
        
        # Convert PDF to images
        PDFtoImage(input_file_path).pdf_to_images()
        # Extract text from images
        text_file_path = ImagetoText(input_file_path).extract_text()
        return text_file_path