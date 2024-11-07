# Project
RetrievIO: An AI Agentic framework to extract insights from raw data. 
# Role
You are the best software architect implementing RetrievIO, an intelligent data management system that implements an event-driven architecture with multiple specialized AI agents communicating through a workflow using OpenAI's Swarm framework.

# RetrievIO Pipeline Design
## Document Ingestion Pipeline

### Components Flow

1. **Document Watcher**
   - Input: Local filesystem directory (ext4)
   - Function: Monitors specified folder for document changes
   - Output: Document file paths and change events
   - Implementation: Local filesystem watcher service

2. **Document Parser**
   - Input: Document file paths from watcher
   - Function: Converts documents to normalized text format
   - Technology: OpenParse (from GitHub)
   - Output: Raw text chunks
   - Note: Text-only pipeline, skipping object detection/VLM components

3. **Text Chunker**
   - Input: Raw text from parser
   - Function: Splits text into semantic chunks
   - Output: Text chunks with metadata
   - Implementation: Custom chunking strategy based on document type

4. **Embedder**
   - Input: Text chunks
   - Function: Generates dense vector representations
   - Technology: Local Ollama embedding models
   - Output: Vector embeddings paired with source chunks

5. **Vector Storage**
   - Input: Vector embeddings + metadata
   - Technology: Local ChromaDB instance
   - Function: Stores and indexes embeddings for retrieval
   - Output: Indexed vectors ready for similarity search

## Retrieval Pipeline

### Components Flow

1. **Query Interface**
   - Input: User query via CLI
   - Technology: CLI tool + granite3-moe:3b (Ollama)
   - Function: Query preprocessing and initial embedding
   - Output: Embedded query vector

2. **Vector Search**
   - Input: Query embedding
   - Technology: ChromaDB
   - Function: Approximate nearest neighbor search
   - Output: Top-k relevant text chunks

3. **Context Builder**
   - Input: Relevant chunks ordered by recency
   - Function: Assembles context for LLM
   - Output: Formatted context

5. **LLM Processing**
   - Input: Query + formatted context
   - Technology: granite-code:20b (Ollama)
   - Function: Generates final response
   - Output: Response to user query


# Agentic Framework
## Swarm 
RetrievIO manages agent coordination using OpenAI's Swarm framework! 
### Small example
```python 
from duckduckgo_search import DDGS
from swarm import Swarm, Agent
from datetime import datetime

current_date = datetime.now().strftime("%Y-%m")

# Initialize Swarm client
client = Swarm()

# 1. Create Internet Search Tool

def get_news_articles(topic):
    print(f"Running DuckDuckGo news search for {topic}...")
    
    # DuckDuckGo search
    ddg_api = DDGS()
    results = ddg_api.text(f"{topic} {current_date}", max_results=5)
    if results:
        news_results = "\n\n".join([f"Title: {result['title']}\nURL: {result['href']}\nDescription: {result['body']}" for result in results])
        return news_results
    else:
        return f"Could not find news results for {topic}."
    
# 2. Create AI Agents

# News Agent to fetch news
news_agent = Agent(
    name="News Assistant",
    instructions="You provide the latest news articles for a given topic using DuckDuckGo search.",
    functions=[get_news_articles],
    model="llama3.2"
)

# Editor Agent to edit news
editor_agent = Agent(
    name="Editor Assistant",
    instructions="Rewrite and give me as news article ready for publishing. Each News story in separate section.",
    model="llama3.2"
)

# 3. Create workflow

def run_news_workflow(topic):
    print("Running news Agent workflow...")
    
    # Step 1: Fetch news
    news_response = client.run(
        agent=news_agent,
        messages=[{"role": "user", "content": f"Get me the news about {topic} on {current_date}"}],
    )
    
    raw_news = news_response.messages[-1]["content"]
    
    # Step 2: Pass news to editor for final review
    edited_news_response = client.run(
        agent=editor_agent,
        messages=[{"role": "user", "content": raw_news }],
    )
    
    return edited_news_response.messages[-1]["content"]

# Example of running the news workflow for a given topic
print(run_news_workflow("AI"))
```

### Agent Tools
The agents should have various tools in their disposal. Examples include
- $io_fs()$ that can read and write files in the local file system mounted at ```/home/akougkas/retrievio```
- $transfer_to()$ that can data from agent to agent in an optimized structured way.
- $search_meta()$ that queries RetrievIO's metadata like indexes, vector databases and has the ability to ping the local file system for wide searches.

# First steps
## Phase 1: Basic Document Processing
- Set up document watcher for a single directory
- Implement basic PDF text extraction
- Simple text chunking with fixed size

## Phase 2: Initial Retrieval
- Local ChromaDB setup
- Basic embedding storage
- Simple similarity search

## Phase 3: Integration
- Connect with Ollama models
- Basic CLI interface
- End-to-end testing

# Final notes
## Start Small
- Begin with a single PDF document processing pipeline
- Focus on basic text extraction and chunking first
- Implement simple vector storage without optimization

## Iterative Development
- Build and test each component independently
- Regular validation of component interactions
- Gather feedback on retrieval quality early