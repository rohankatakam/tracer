"""
Clean Database Script

This script methodically cleans the database by handling each table individually,
with separate transactions to ensure maximum reliability.
"""
import os
import sys
import logging
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add project root to path to import project modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import database configuration
from config.database import DATABASE_URL

def execute_safely(session, statement):
    """Execute a SQL statement safely, with its own transaction."""
    try:
        session.execute(text(statement))
        session.commit()
        logger.info(f"Successfully executed: {statement}")
        return True
    except Exception as e:
        session.rollback()
        logger.warning(f"Error executing {statement}: {e}")
        return False

def clean_database():
    """Clean database tables individually for maximum reliability."""
    # Connect to the database
    engine = create_engine(DATABASE_URL)
    inspector = inspect(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get list of existing tables
    existing_tables = inspector.get_table_names()
    logger.info(f"Found tables: {existing_tables}")
    print(f"Found {len(existing_tables)} tables in the database")
    
    # First handle many-to-many association tables
    association_tables = [
        "comment_attachment_association",
        "pdf_page_image_association",
        "pdf_page_text_association", 
        "attachment_text_association",
        "attachment_image_association",
        "attachment_video_association"  # Include it even if it might not exist
    ]
    
    # Break foreign key dependencies
    fk_updates = [
        "UPDATE image_contents SET ocr_text_id = NULL WHERE ocr_text_id IS NOT NULL",
        "UPDATE attachments SET pdf_content_id = NULL WHERE pdf_content_id IS NOT NULL"
    ]
    
    # List all tables to delete from
    tables_to_clean = (
        association_tables + 
        ["video_frames", "pdf_pages", "comments", "attachments"] +
        ["image_contents", "text_contents", "pdf_contents", "video_contents"] +
        ["bugs"]
    )
    
    success_count = 0
    fail_count = 0
    
    # Update foreign keys first
    for update in fk_updates:
        if execute_safely(session, update):
            success_count += 1
        else:
            fail_count += 1
    
    # Then delete from each table individually
    for table in tables_to_clean:
        if table in existing_tables:
            if execute_safely(session, f"DELETE FROM {table}"):
                success_count += 1
            else:
                fail_count += 1
        else:
            logger.info(f"Table {table} does not exist, skipping")
    
    # Summary
    logger.info(f"Clean database operations completed: {success_count} successful, {fail_count} failed")
    print(f"\nClean database operations completed: {success_count} successful, {fail_count} failed")
    
    # Clear attachment files
    clear_attachment_files()

def clear_attachment_files():
    """Remove physical attachment files from the filesystem."""
    try:
        # Define attachment directories
        attachment_dirs = [
            "data/attachments",
            "data/processed_attachments/images",
            "data/processed_attachments/texts",
            "data/processed_attachments/pdfs",
            "data/processed_attachments/videos"
        ]
        
        # Create base directories if they don't exist (to avoid errors)
        for dir_path in attachment_dirs:
            os.makedirs(dir_path, exist_ok=True)
        
        file_count = 0
        # Delete all files but keep directories
        for dir_path in attachment_dirs:
            for file_name in os.listdir(dir_path):
                file_path = os.path.join(dir_path, file_name)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    file_count += 1
        
        logger.info(f"Deleted {file_count} attachment files")
        print(f"Deleted {file_count} attachment files from the filesystem.")
    except Exception as e:
        logger.error(f"Error clearing attachment files: {str(e)}")
        print(f"Warning: Could not delete some attachment files: {str(e)}")

if __name__ == "__main__":
    clean_database()
