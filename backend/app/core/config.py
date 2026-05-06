import os
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR")
OUTPUT_DIR = os.getenv("OUTPUT_DIR")
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE"))

ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
