import pytest
from pathlib import Path
import shutil
import time
from src.pipeline import DocumentPipeline
from src.config import WATCH_DIR, PROCESSED_DIR
import json

@pytest.fixture
def setup_test_env():
    """Set up test environment"""
    # Create test directories
    test_watch = Path("test_watch")
    test_processed = Path("test_processed")
    
    test_watch.mkdir(exist_ok=True)
    test_processed.mkdir(exist_ok=True)
    
    # Create test PDF
    test_pdf = test_watch / "test.pdf"
    with open(test_pdf, "wb") as f:
        f.write(b"%PDF-1.4\nTest content")
    
    yield {
        "watch_dir": test_watch,
        "processed_dir": test_processed,
        "test_pdf": test_pdf
    }
    
    # Cleanup
    shutil.rmtree(test_watch)
    shutil.rmtree(test_processed)

def test_mvp_flow(setup_test_env):
    """Test the complete MVP flow"""
    pipeline = DocumentPipeline()
    
    # Start pipeline
    pipeline.start()
    
    try:
        # Process test document
        success = pipeline.process_document(str(setup_test_env["test_pdf"]))
        assert success, "Document processing failed"
        
        # Wait for processing
        time.sleep(2)
        
        # Check if file was moved to processed
        processed_file = PROCESSED_DIR / setup_test_env["test_pdf"].name
        assert processed_file.exists(), "File not moved to processed directory"
        
        # Check if chunks were created
        chunk_dir = PROCESSED_DIR / setup_test_env["test_pdf"].stem / "chunks"
        assert chunk_dir.exists(), "Chunks directory not created"
        assert list(chunk_dir.glob("*.json")), "No chunks generated"
        
        # Check vector store
        # TODO: Add vector store checks
        
        # Check engagement content
        engagement_file = PROCESSED_DIR / setup_test_env["test_pdf"].stem / "engagement.json"
        assert engagement_file.exists(), "Engagement content not generated"
        
        # Verify engagement content structure
        with open(engagement_file) as f:
            engagement = json.load(f)
            analysis = json.loads(engagement["analysis"])
            
            assert "topic" in analysis
            assert "overview" in analysis
            assert "key_concepts" in analysis
            assert "questions" in analysis
            assert all(k in analysis["questions"] for k in ["basic", "detailed", "practical"])
        
    finally:
        pipeline.stop() 