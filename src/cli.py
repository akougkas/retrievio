import click
import logging
from pathlib import Path
from .pipeline import DocumentPipeline
from .config import WATCH_DIR, PROCESSED_DIR
from .search import SearchManager
from .agents.vector_store import VectorStoreAgent
import json

logger = logging.getLogger(__name__)

@click.group()
def cli():
    """RetrievIO - Intelligent Document Processing System"""
    pass

@cli.command()
def start():
    """Start the document processing pipeline"""
    pipeline = DocumentPipeline()
    try:
        pipeline.start()
        click.echo(f"Watching directory: {WATCH_DIR}")
        click.echo("Press CTRL+C to stop...")
        # Keep the main thread alive
        while True:
            pass
    except KeyboardInterrupt:
        click.echo("\nStopping pipeline...")
        pipeline.stop()
    except Exception as e:
        logger.exception("Pipeline error")
        click.echo(f"Error: {str(e)}", err=True)

@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False))
def process_directory(directory):
    """Process all PDF files in a directory"""
    pipeline = DocumentPipeline()
    dir_path = Path(directory)
    
    pdf_files = list(dir_path.glob("*.pdf"))
    if not pdf_files:
        click.echo("No PDF files found in directory")
        return
        
    with click.progressbar(pdf_files, label='Processing documents') as files:
        for file_path in files:
            success = pipeline.process_document(str(file_path))
            if not success:
                click.echo(f"Failed to process {file_path.name}", err=True)

@cli.command()
def status():
    """Show pipeline status"""
    watch_files = list(WATCH_DIR.glob("*.pdf"))
    processed_files = list(PROCESSED_DIR.glob("*.pdf"))
    
    click.echo("RetrievIO Status")
    click.echo("-" * 20)
    click.echo(f"Watch directory: {WATCH_DIR}")
    click.echo(f"Files pending: {len(watch_files)}")
    click.echo(f"Files processed: {len(processed_files)}")

@cli.command()
@click.argument('query')
@click.option('--results', '-n', default=5, help='Number of results to return')
@click.option('--min-relevance', '-r', default=0.7, help='Minimum relevance score (0-1)')
@click.option('--file', '-f', help='Filter results to specific file')
@click.option('--json', 'json_output', is_flag=True, help='Output results as JSON')
def search(query: str, results: int, min_relevance: float, file: str, json_output: bool):
    """Search through processed documents"""
    search_manager = SearchManager()
    
    click.echo(f"Searching for: {query}")
    search_results = search_manager.search(
        query=query,
        n_results=results,
        min_relevance=min_relevance,
        file_filter=file
    )
    
    if not search_results:
        click.echo("No results found")
        return
        
    if json_output:
        click.echo(json.dumps(search_results, indent=2))
        return
        
    # Pretty print results
    click.echo("\nSearch Results:")
    click.echo("-" * 80)
    
    for result in search_results:
        click.echo(f"\n[{result['rank']}] Relevance: {result['relevance']}%")
        click.echo(f"File: {result['file']}")
        click.echo("-" * 40)
        click.echo(result['text'])
        click.echo("-" * 40)

@cli.command()
def list_documents():
    """List all processed documents"""
    vector_store = VectorStoreAgent()
    
    try:
        # Get unique file names from collection
        results = vector_store.collection.get(
            include=['metadatas']
        )
        
        if not results['metadatas']:
            click.echo("No documents found")
            return
            
        # Extract unique file names
        files = set(meta['file_name'] for meta in results['metadatas'])
        
        click.echo("\nProcessed Documents:")
        click.echo("-" * 20)
        for file in sorted(files):
            click.echo(file)
            
    except Exception as e:
        click.echo(f"Error listing documents: {str(e)}", err=True)

@cli.command()
@click.argument('file_name')
def document_info(file_name: str):
    """Show information about a processed document"""
    vector_store = VectorStoreAgent()
    
    try:
        # Get chunks for specific file
        results = vector_store.collection.get(
            where={"file_name": {"$eq": file_name}},
            include=['metadatas']
        )
        
        if not results['metadatas']:
            click.echo(f"Document not found: {file_name}")
            return
            
        # Calculate statistics
        chunk_count = len(results['metadatas'])
        
        click.echo(f"\nDocument: {file_name}")
        click.echo("-" * 20)
        click.echo(f"Number of chunks: {chunk_count}")
        click.echo(f"First chunk start: {results['metadatas'][0]['start_idx']}")
        click.echo(f"Last chunk end: {results['metadatas'][-1]['end_idx']}")
        
    except Exception as e:
        click.echo(f"Error getting document info: {str(e)}", err=True)

@cli.command()
@click.argument('question')
@click.option('--results', '-n', default=5, help='Number of context results to use')
@click.option('--min-relevance', '-r', default=0.7, help='Minimum relevance score (0-1)')
@click.option('--file', '-f', help='Filter context to specific file')
@click.option('--json', 'json_output', is_flag=True, help='Output response as JSON')
def ask(question: str, results: int, min_relevance: float, file: str, json_output: bool):
    """Ask a question about your documents"""
    search_manager = SearchManager()
    
    click.echo(f"Question: {question}")
    response = search_manager.ask(
        question=question,
        n_results=results,
        min_relevance=min_relevance,
        file_filter=file
    )
    
    if "error" in response:
        click.echo(f"Error: {response['error']}", err=True)
        return
        
    if json_output:
        click.echo(json.dumps(response, indent=2))
        return
    
    click.echo("\nAnswer:")
    click.echo("-" * 80)
    click.echo(response["answer"])
    click.echo("\nSources:")
    for source in response["sources"]:
        click.echo(f"- {source}")

@cli.command()
@click.argument('document_name')
@click.option('--json', 'json_output', is_flag=True, help='Output as JSON')
def engagement(document_name: str, json_output: bool):
    """Show document engagement suggestions"""
    doc_path = PROCESSED_DIR / document_name.replace('.pdf', '') / "engagement.json"
    
    if not doc_path.exists():
        click.echo(f"No engagement content found for: {document_name}")
        return
        
    try:
        with open(doc_path) as f:
            content = json.load(f)
            
        if json_output:
            click.echo(json.dumps(content, indent=2))
            return
            
        analysis = json.loads(content["analysis"])
        
        click.echo(f"\nDocument: {content['document']}")
        click.echo("=" * 50)
        click.echo(f"\nTopic: {analysis['topic']}")
        click.echo(f"Overview: {analysis['overview']}")
        
        click.echo("\nKey Concepts:")
        for concept in analysis['key_concepts']:
            click.echo(f"- {concept}")
        
        click.echo("\nSuggested Questions:")
        click.echo(f"Basic: {analysis['questions']['basic']}")
        click.echo(f"Detailed: {analysis['questions']['detailed']}")
        click.echo(f"Practical: {analysis['questions']['practical']}")
        
        click.echo("\nFollow-up Topics:")
        for topic in analysis['follow_up']:
            click.echo(f"- {topic}")
            
    except Exception as e:
        click.echo(f"Error reading engagement content: {str(e)}", err=True)