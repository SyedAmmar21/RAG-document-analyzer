"""
Centralized path management for the application.

This module provides consistent, relative-path-based file management
that works across development, testing, and Docker environments.
"""

from pathlib import Path
from typing import Union

# ===== DIRECTORY STRUCTURE =====

# Root of the entire backend directory (where main.py is)
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Storage root directory
STORAGE_DIR = BASE_DIR / "storage"

# Subdirectories
UPLOAD_DIR = STORAGE_DIR / "uploads"
OUTPUT_DIR = STORAGE_DIR / "outputs"
NEWS_ARTICLES_DIR = STORAGE_DIR / "news_articles"

# Database location
DB_DIR = BASE_DIR / "app" / "db"
DB_PATH = DB_DIR / "documents.db"


def ensure_directories_exist() -> None:
    """Create all required storage directories if they don't exist."""
    for directory in [STORAGE_DIR, UPLOAD_DIR, OUTPUT_DIR, NEWS_ARTICLES_DIR, DB_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


# ===== PATH HELPER FUNCTIONS =====

def resolve_storage_path(stored_path: Union[str, Path]) -> Path:
    """
    Resolve a stored path (absolute or relative) to an absolute Path object.
    
    This function provides backwards compatibility with existing absolute paths
    while also supporting new relative paths.
    
    Args:
        stored_path: Either a relative path (e.g., "uploads/file.pdf") or 
                    an absolute path (from old database records)
    
    Returns:
        An absolute Path object pointing to the file
    
    Raises:
        ValueError: If the path is relative and goes outside STORAGE_DIR
    """
    path = Path(stored_path)
    
    # If already absolute, use it directly (backwards compatibility)
    if path.is_absolute():
        return path
    
    # Otherwise, reconstruct relative to STORAGE_DIR
    absolute_path = STORAGE_DIR / path
    
    # Security check: ensure the resolved path is within STORAGE_DIR
    try:
        absolute_path.relative_to(STORAGE_DIR)
    except ValueError:
        raise ValueError(
            f"Path traversal attempt detected: {stored_path} resolves outside STORAGE_DIR"
        )
    
    return absolute_path


def to_relative_storage_path(absolute_path: Union[str, Path]) -> str:
    """
    Convert an absolute path to a relative path for storage in the database.
    
    Args:
        absolute_path: An absolute Path or string
    
    Returns:
        A relative path string (e.g., "uploads/file.pdf") suitable for database storage
    
    Raises:
        ValueError: If the path is not within STORAGE_DIR
    """
    path = Path(absolute_path).resolve()
    storage_dir = STORAGE_DIR.resolve()
    
    try:
        relative = path.relative_to(storage_dir)
        # Use forward slashes for cross-platform compatibility
        return str(relative).replace("\\", "/")
    except ValueError:
        raise ValueError(
            f"Path {absolute_path} is not within STORAGE_DIR {storage_dir}"
        )


def get_upload_path(filename: str) -> Path:
    """
    Get the absolute path where an uploaded file should be stored.
    
    Args:
        filename: The filename (can include subdirectories)
    
    Returns:
        An absolute Path in UPLOAD_DIR
    """
    upload_path = UPLOAD_DIR / filename
    
    # Security check
    try:
        upload_path.relative_to(UPLOAD_DIR)
    except ValueError:
        raise ValueError(f"Invalid upload path: {filename}")
    
    return upload_path


def get_news_article_path(filename: str) -> Path:
    """
    Get the absolute path where a news article should be stored.
    
    Args:
        filename: The filename for the news article
    
    Returns:
        An absolute Path in NEWS_ARTICLES_DIR
    """
    article_path = NEWS_ARTICLES_DIR / filename
    
    # Security check
    try:
        article_path.relative_to(NEWS_ARTICLES_DIR)
    except ValueError:
        raise ValueError(f"Invalid news article path: {filename}")
    
    return article_path


# Initialize directories on import
ensure_directories_exist()
