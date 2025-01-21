import os
import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class OCRAPI:
    def __init__(self):
        self.api_key = os.getenv('OCR_SPACE_API_KEY')
        if not self.api_key:
            raise ValueError("OCR_SPACE_API_KEY not found in environment variables")
        self.base_url = "https://api.ocr.space/parse/image"

    def image_to_text(self, image_path):
        # Check if the image size is greater than 1024KB (1MB)
        if os.path.getsize(image_path) > 1024 * 1024:
            print(f"Skipping image {image_path} as it exceeds 1MB size limit.")
            return "Image size exceeds limit"
        """
        Convert an image to text using OCR.space API.

        :param image_path: Path to the image file
        :return: Extracted text from the image
        """
        payload = {
            'apikey': self.api_key,
            'language': 'eng',  # You can change this to other languages if needed
            'isOverlayRequired': False
        }

        with open(image_path, 'rb') as image_file:
            files = {'image': image_file}
            response = requests.post(self.base_url, files=files, data=payload)

        response.raise_for_status()
        result = response.json()

        if result['IsErroredOnProcessing']:
            raise Exception(f"Error processing image: {result['ErrorMessage']}")

        extracted_text = ""
        for page in result['ParsedResults']:
            extracted_text += page['ParsedText']

        return extracted_text.strip()

# Usage example:
# ocr_api = OCRAPI()
# text = ocr_api.image_to_text('path/to/your/image.jpg')
# print(text)
