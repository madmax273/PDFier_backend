# PDFier Backend

PDFier is a powerful document processing and management system that implements Retrieval-Augmented Generation (RAG) to provide AI-powered chat capabilities with your PDF documents. The backend is built with FastAPI and integrates with vector databases and LLMs to deliver accurate, context-aware responses based on your documents.

## Features

- **Document Processing**: Upload and process PDF documents with automatic text extraction and chunking
- **RAG-Powered Chat**: Interact with your documents using natural language with responses augmented by document context
- **Vector Embeddings**: Convert document content into vector representations using state-of-the-art embedding models
- **Semantic Search**: Advanced semantic search capabilities using Pinecone vector database
- **Context-Aware Responses**: Generate accurate answers by retrieving and synthesizing relevant document passages
- **User Authentication**: Secure user management with JWT
- **RESTful API**: Well-documented endpoints for easy integration

## RAG Implementation

PDFier implements a robust RAG (Retrieval-Augmented Generation) pipeline that combines the power of large language models with document retrieval:

1. **Document Processing**:
   - PDF text extraction and cleaning
   - Document chunking with overlap for context preservation
   - Metadata extraction and storage

2. **Vector Embeddings**:
   - Converts text chunks into high-dimensional vectors
   - Uses state-of-the-art embedding models for semantic understanding
   - Efficient storage and retrieval of vector representations

3. **Retrieval System**:
   - Semantic search using Pinecone vector database
   - Context-aware retrieval of relevant document chunks
   - Hybrid search combining semantic and keyword-based approaches

4. **Generation**:
   - Augments LLM prompts with retrieved context
   - Generates accurate, document-grounded responses
   - Maintains conversation context across interactions

## Tech Stack

- **Backend Framework**: FastAPI
- **Database**: MongoDB (with Supabase for authentication)
- **Vector Database**: Pinecone
- **AI/ML**: 
  - OpenAI GPT models for text generation
  - Google AI for embeddings
  - LangChain for RAG pipeline orchestration
- **Authentication**: JWT
- **API Documentation**: OpenAPI/Swagger
- **Containerization**: Docker

## Prerequisites

- Python 3.8+
- MongoDB
- Pinecone account and API key
- Supabase account
- OpenAI API key (optional, if using OpenAI models)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/PDFier_backend.git
   cd PDFier_backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   Create a `.env` file in the root directory with the following variables:
   ```
   MONGODB_URL=your_mongodb_connection_string
   PINECONE_API_KEY=your_pinecone_api_key
   PINECONE_ENVIRONMENT=your_pinecone_environment
   OPENAI_API_KEY=your_openai_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

## Running the Application

1. Start the FastAPI server:
   ```bash
   uvicorn main:app --reload
   ```

2. Access the API documentation:
   - Swagger UI: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

## API Endpoints

- `POST /api/v1/upload` - Upload and process PDF documents for RAG
- `POST /api/v1/chat` - Chat with your documents using RAG
- `GET /api/v1/conversations` - Get user's chat history
- `GET /api/v1/conversations/{conversation_id}` - Get specific conversation
- `POST /api/v1/ingest` - Programmatically ingest documents into the RAG system

## Deployment

The application can be deployed using Docker:

```bash
docker build -t pdfier-backend .
docker run -d -p 8000:8000 --env-file .env pdfier-backend
```

## Environment Variables

- `MONGODB_URL`: MongoDB connection string
- `PINECONE_API_KEY`: Pinecone API key
- `PINECONE_ENVIRONMENT`: Pinecone environment
- `OPENAI_API_KEY`: OpenAI API key
- `SUPABASE_URL`: Supabase project URL
- `SUPABASE_KEY`: Supabase anon/public key

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support, please open an issue in the GitHub repository or contact the maintainers.
