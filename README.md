# RetrievIO

An AI Agentic framework to extract insights from raw data.

## Features

- Document processing pipeline with specialized AI agents
- Vector-based document storage and retrieval
- Integration with Ollama for LLM processing
- CLI interface for document management and querying
- Event-driven architecture for agent communication

## Installation

1. Clone the repository:
```bash
git clone https://github.com/YOUR_USERNAME/retrievio.git
cd retrievio
```
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Install Ollama and required models:
```bash
Follow Ollama installation instructions from: https://ollama.ai/
E.G., ollama pull llama2
```

## Usage

1. Start the document processing pipeline:
```bash
python -m retrievio start
```
2. Process a directory of documents:
```bash
python -m retrievio process-directory /path/to/documents
```
3. Search through processed documents:
```bash
python -m retrievio search "your query here"
```

## License

MIT License - see LICENSE file for details
