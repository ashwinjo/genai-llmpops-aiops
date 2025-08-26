# 🎬 Movie Recommendation System

An intelligent AI-powered movie recommendation system that combines **RAG (Retrieval-Augmented Generation)** with vector similarity search to provide personalized movie recommendations. Built with modern AI technologies including LangChain, ChromaDB, and OpenAI.

## 🌟 Features

- **🤖 AI-Powered Recommendations**: Uses GPT models for intelligent, contextual movie suggestions
- **🔍 Vector Similarity Search**: Fast semantic search through movie embeddings
- **📊 Multiple Data Sources**: Supports both default IMDB dataset and custom CSV uploads
- **🚀 Quick Connect Mode**: Instant connection to existing ChromaDB for faster startup
- **💬 Interactive Interface**: Streamlit web app with intuitive UI
- **🔄 Smart Caching**: Reuses existing embeddings to avoid reprocessing
- **📈 Real-time Processing**: Live pipeline status and progress tracking

## 🏗️ Architecture

The system follows a modular architecture with three main components:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Loader   │───▶│  Vector Store   │───▶│   Recommender   │
│                 │    │   (ChromaDB)    │    │   (RAG + LLM)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Core Components

- **`data_loader.py`**: Handles CSV processing, cleaning, and feature engineering
- **`vector_store.py`**: Manages ChromaDB operations and embeddings
- **`recommender.py`**: RAG system with LLM integration for recommendations
- **`pipeline.py`**: Orchestrates the complete ingestion pipeline

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- OpenAI API key (or GROQ API key)
- 2GB+ RAM for processing

### Installation

1. **Clone and navigate to the project:**
```bash
cd projects/03-ai-anime-recommender
```

2. **Install dependencies:**
```bash
pip install -r requirements.txt
```

3. **Set up environment variables:**
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_api_key_here
GROQ_API_KEY=your_groq_api_key_here  # Optional
HF_TOKEN=your_huggingface_token_here  # Optional
```

### Usage Options

#### Option 1: Streamlit Web App (Recommended)
```bash
streamlit run st_app.py
```
- **Quick Connect**: Instantly connect to existing ChromaDB
- **Upload Custom Data**: Process your own movie datasets
- **Interactive Recommendations**: Ask questions and get AI-powered suggestions

#### Option 2: Command Line Pipeline
```bash
# Run complete pipeline
python run_pipeline.py

# Interactive recommendations
python ask_recommendations.py

# Quick test with sample queries
python ask_recommendations.py --test
```

#### Option 3: Single Query
```bash
python ask_recommendations.py --query "I like action movies with great cinematography"
```

## 📁 Project Structure

```
03-ai-anime-recommender/
├── 📁 data/                    # Data storage
│   ├── IMDB_10000.csv         # Default movie dataset
│   ├── combined_info.csv      # Processed combined data
│   ├── chroma_db/             # Vector store database
│   ├── processed_data/        # Feature encoders and scalers
│   └── data_loader.py         # Data processing logic
├── 📁 src/                    # Core system components
│   ├── recommender.py         # RAG recommendation engine
│   ├── vector_store.py        # ChromaDB vector store manager
│   └── prompts.py             # LLM prompt templates
├── 📁 pipeline/               # Pipeline orchestration
│   └── pipeline.py            # Complete ingestion pipeline
├── 📁 config/                 # Configuration
│   └── config.py              # Environment variables
├── st_app.py                  # Streamlit web application
├── run_pipeline.py            # CLI pipeline runner
├── ask_recommendations.py     # CLI recommendation interface
└── requirements.txt           # Python dependencies
```

## 🔧 How It Works

### 1. Data Processing Pipeline
```python
# Load and clean movie data
data_loader = AnimeDataLoader("IMDB_10000.csv")
cleaned_data = data_loader.clean_data()

# Create embeddings and store in ChromaDB
vector_store = AnimeVectorStore(csv_path="combined_info.csv")
vector_store.build_vector_store()

# Initialize RAG recommender
recommender = AnimeRecommender()
recommender.initialize_components()
```

### 2. Recommendation Process
1. **Query Processing**: User question is analyzed
2. **Vector Search**: Similar movies found using embeddings
3. **Context Retrieval**: Relevant movie information gathered
4. **LLM Generation**: GPT model generates personalized recommendations
5. **Response Formatting**: Structured, engaging response delivered

### 3. Smart Caching
- **ChromaDB Persistence**: Embeddings stored locally
- **Quick Connect**: Skip pipeline for existing data
- **Incremental Updates**: Only reprocess when data changes

## 🎯 Example Queries

The system can handle various types of movie requests:

- **Genre-based**: "I like action movies with great cinematography"
- **Similarity-based**: "Movies similar to Forest Gump"
- **Mood-based**: "Show me some romantic comedy movies"
- **Quality-based**: "Recommend me sci-fi movies with high ratings"
- **Director-based**: "I want to watch something similar to Christopher Nolan films"

## 📊 Data Requirements

### Default Dataset (IMDB_10000.csv)
The system comes with a pre-processed IMDB dataset containing:
- Movie titles and years
- Genres and descriptions
- Ratings and vote counts
- Director and cast information

### Custom Dataset Format
For custom datasets, ensure your CSV includes:
```csv
title,year,genre,description,rating,votes,director,cast
Movie Title,2023,Action|Adventure,Plot description...,8.5,1000,Director Name,Cast Names
```

## 🔍 Advanced Features

### Quick Connect Mode
- **Instant Startup**: Connect to existing ChromaDB in seconds
- **Status Checking**: Verify data availability before connecting
- **Smart Detection**: Automatically detects existing processed data

### Custom Data Upload
- **CSV Support**: Upload your own movie datasets
- **Force Rebuild**: Process new data with fresh embeddings
- **Data Preview**: See uploaded data statistics and preview

### Pipeline Management
- **Progress Tracking**: Real-time pipeline status updates
- **Error Handling**: Detailed error messages and recovery
- **Force Rebuild**: Option to reprocess existing data

## 🛠️ Configuration

### Environment Variables
```env
# Required
OPENAI_API_KEY=sk-...

# Optional (for alternative models)
GROQ_API_KEY=gsk_...
HF_TOKEN=hf_...
```

### Model Configuration
The system supports multiple LLM providers:
- **OpenAI GPT**: Default, most capable
- **GROQ**: Fast inference, cost-effective
- **HuggingFace**: Local deployment option

## 📈 Performance

### Processing Times
- **Initial Pipeline**: 5-10 minutes (first run)
- **Quick Connect**: 10-30 seconds
- **Recommendation Generation**: 2-5 seconds

### Resource Requirements
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 500MB for processed data
- **CPU**: Multi-core recommended for faster processing

## 🐛 Troubleshooting

### Common Issues

**1. ModuleNotFoundError**
```bash
# Fix import issues
pip install -r requirements.txt
```

**2. API Key Errors**
```bash
# Check .env file
cat .env
# Ensure OPENAI_API_KEY is set
```

**3. ChromaDB Issues**
```bash
# Clear and rebuild vector store
rm -rf data/chroma_db/
python run_pipeline.py
```

**4. Memory Issues**
```bash
# Reduce chunk size in vector_store.py
chunk_size = 500  # Default: 1000
```

### Debug Mode
Enable detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- **IMDB Dataset**: Movie data source
- **LangChain**: RAG framework
- **ChromaDB**: Vector database
- **OpenAI**: LLM provider
- **Streamlit**: Web interface

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review the code comments
3. Open an issue on GitHub

---

**Built with ❤️ using modern AI technologies for intelligent movie discovery!**
