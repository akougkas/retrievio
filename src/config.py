from pathlib import Path
import logging
import chromadb
from chromadb.config import Settings

# Base configuration
BASE_DIR = Path("/home/akougkas/retrievio")
WATCH_DIR = BASE_DIR / "documents"
PROCESSED_DIR = BASE_DIR / "processed"
LOGS_DIR = BASE_DIR / "logs"

# Document processing settings
CHUNK_SIZE = 1000  # characters
CHUNK_OVERLAP = 200  # characters

# Logging configuration
LOG_FILE = LOGS_DIR / "retrievio.log"
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_LEVEL = logging.INFO

# Ensure required directories exist
for directory in [WATCH_DIR, PROCESSED_DIR, LOGS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Configure logging
logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

# Vector DB settings
VECTOR_DB_DIR = BASE_DIR / "vectordb"
VECTOR_DB_DIR.mkdir(parents=True, exist_ok=True)

# ChromaDB client configuration
CHROMA_SETTINGS = Settings(
    persist_directory=str(VECTOR_DB_DIR),
    anonymized_telemetry=False
)

# Initialize ChromaDB client
CHROMA_CLIENT = chromadb.PersistentClient(path=str(VECTOR_DB_DIR), settings=CHROMA_SETTINGS)

# Create default collection
DEFAULT_COLLECTION = CHROMA_CLIENT.get_or_create_collection(
    name="documents",
    metadata={"description": "Main document collection"}
) 