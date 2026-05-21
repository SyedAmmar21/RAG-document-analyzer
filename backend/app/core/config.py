import os
from dotenv import load_dotenv

load_dotenv()

# File storage limits
MAX_FILE_SIZE = int(os.getenv("MAX_FILE_SIZE", 5242880))  # Default 5MB

# API Keys
ELASTICSEARCH_HOST = os.getenv("ELASTICSEARCH_HOST")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")