import pandas as pd
import logging
import os
from typing import List, Dict, Optional, Any
from pathlib import Path
import chromadb
from chromadb.config import Settings

# LangChain imports
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceEmbeddings

# Configuration
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import OPENAI_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AnimeVectorStore:
    """
    Vector store manager for anime recommendation system.
    Handles loading, chunking, embedding, and storing anime data in ChromaDB.
    """
    
    def __init__(self, 
                 csv_path: str = "/Users/ashwjosh/genai-llmpops-aiops/projects/03-ai-anime-recommender/data/combined_info.csv",
                 persist_directory: str = "/Users/ashwjosh/genai-llmpops-aiops/projects/03-ai-anime-recommender/data/chroma_db",
                 embedding_model: str = "openai",
                 chunk_size: int = 1000,
                 chunk_overlap: int = 200):
        """
        Initialize the vector store manager.
        
        Args:
            csv_path (str): Path to the combined_info.csv file
            persist_directory (str): Directory to persist ChromaDB
            embedding_model (str): Embedding model to use ('openai' or 'huggingface')
            chunk_size (int): Size of text chunks
            chunk_overlap (int): Overlap between chunks
        """
        self.csv_path = csv_path
        self.persist_directory = persist_directory
        self.embedding_model = embedding_model
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize components
        self.embeddings = None
        self.vector_store = None
        self.text_splitter = None
        
        # Create persist directory
        os.makedirs(persist_directory, exist_ok=True)
        
        logger.info(f"AnimeVectorStore initialized with CSV: {csv_path}")
        logger.info(f"Persist directory: {persist_directory}")
        logger.info(f"Embedding model: {embedding_model}")
    
    def load_csv_data(self) -> pd.DataFrame:
        """
        Load the combined_info.csv file.
        
        Returns:
            pd.DataFrame: Loaded CSV data
            
        Raises:
            FileNotFoundError: If CSV file doesn't exist
            Exception: For other loading errors
        """
        try:
            logger.info(f"Loading CSV data from {self.csv_path}")
            
            if not os.path.exists(self.csv_path):
                raise FileNotFoundError(f"CSV file not found: {self.csv_path}")
            
            # Load CSV with UTF-8 encoding
            df = pd.read_csv(self.csv_path, encoding='utf-8')
            
            logger.info(f"CSV loaded successfully. Shape: {df.shape}")
            logger.info(f"Columns: {list(df.columns)}")
            
            return df
            
        except FileNotFoundError as e:
            logger.error(f"File not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error loading CSV: {str(e)}")
            raise
    
    def initialize_embeddings(self):
        """
        Initialize the embedding model based on configuration.
        
        Raises:
            ValueError: If embedding model is not supported
            Exception: For API key or model loading errors
        """
        try:
            logger.info(f"Initializing {self.embedding_model} embeddings...")
            
            if self.embedding_model == "openai":
                if not OPENAI_API_KEY:
                    logger.warning("OpenAI API key not found. Falling back to HuggingFace embeddings.")
                    self.embedding_model = "huggingface"
                else:
                    self.embeddings = OpenAIEmbeddings(
                        openai_api_key=OPENAI_API_KEY,
                        model="text-embedding-ada-002"
                    )
                    logger.info("OpenAI embeddings initialized successfully")
            
            if self.embedding_model == "huggingface":
                self.embeddings = HuggingFaceEmbeddings(
                    model_name="sentence-transformers/all-MiniLM-L6-v2",
                    model_kwargs={'device': 'cpu'}
                )
                logger.info("HuggingFace embeddings initialized successfully")
            
            if self.embeddings is None:
                raise ValueError(f"Unsupported embedding model: {self.embedding_model}")
                
        except Exception as e:
            logger.error(f"Error initializing embeddings: {str(e)}")
            raise
    
    def create_text_splitter(self):
        """
        Create text splitter for chunking documents.
        """
        try:
            logger.info("Creating text splitter...")
            
            self.text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap,
                length_function=len,
                separators=["\n\n", "\n", " ", ""]
            )
            
            logger.info(f"Text splitter created with chunk_size={self.chunk_size}, overlap={self.chunk_overlap}")
            
        except Exception as e:
            logger.error(f"Error creating text splitter: {str(e)}")
            raise
    
    def create_documents(self, df: pd.DataFrame) -> List[Document]:
        """
        Create LangChain documents from DataFrame.
        
        Args:
            df (pd.DataFrame): DataFrame with combined_info column
            
        Returns:
            List[Document]: List of LangChain documents
        """
        try:
            logger.info("Creating LangChain documents...")
            
            documents = []
            
            for idx, row in df.iterrows():
                try:
                    # Create document with metadata
                    doc = Document(
                        page_content=row['combined_info'],
                        metadata={
                            'anime_id': idx,
                            'source': 'combined_info',
                            'chunk_type': 'anime_info'
                        }
                    )
                    documents.append(doc)
                    
                except Exception as e:
                    logger.warning(f"Error creating document for row {idx}: {str(e)}")
                    continue
            
            logger.info(f"Created {len(documents)} documents")
            return documents
            
        except Exception as e:
            logger.error(f"Error creating documents: {str(e)}")
            raise
    
    def chunk_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into chunks.
        
        Args:
            documents (List[Document]): Original documents
            
        Returns:
            List[Document]: Chunked documents
        """
        try:
            logger.info("Chunking documents...")
            
            if self.text_splitter is None:
                self.create_text_splitter()
            
            chunked_docs = self.text_splitter.split_documents(documents)
            
            logger.info(f"Documents chunked: {len(documents)} -> {len(chunked_docs)} chunks")
            return chunked_docs
            
        except Exception as e:
            logger.error(f"Error chunking documents: {str(e)}")
            raise
    
    def create_vector_store(self, documents: List[Document]) -> Chroma:
        """
        Create and populate the vector store.
        
        Args:
            documents (List[Document]): Documents to store
            
        Returns:
            Chroma: LangChain Chroma vector store
        """
        try:
            logger.info("Creating vector store...")
            
            if self.embeddings is None:
                self.initialize_embeddings()
            
            # Create Chroma vector store with simpler configuration
            self.vector_store = Chroma.from_documents(
                documents=documents,
                embedding=self.embeddings,
                persist_directory=self.persist_directory
            )
            
            # Persist the vector store (not needed in newer versions)
            # self.vector_store.persist()
            
            logger.info(f"Vector store created and persisted to {self.persist_directory}")
            
            return self.vector_store
            
        except Exception as e:
            logger.error(f"Error creating vector store: {str(e)}")
            raise
    
    def load_existing_vector_store(self) -> Optional[Chroma]:
        """
        Load existing vector store if it exists.
        
        Returns:
            Optional[Chroma]: Loaded vector store or None
        """
        try:
            logger.info("Checking for existing vector store...")
            
            if self.embeddings is None:
                self.initialize_embeddings()
            
            # Check if persist directory exists and has data
            if os.path.exists(self.persist_directory) and os.listdir(self.persist_directory):
                try:
                    self.vector_store = Chroma(
                        persist_directory=self.persist_directory,
                        embedding_function=self.embeddings
                    )
                    
                    logger.info("Existing vector store loaded successfully")
                    return self.vector_store
                except Exception as e:
                    logger.warning(f"Error loading existing vector store (schema mismatch): {str(e)}")
                    logger.info("Will rebuild vector store...")
                    return None
            else:
                logger.info("No existing vector store found")
                return None
                
        except Exception as e:
            logger.error(f"Error loading existing vector store: {str(e)}")
            return None
    
    def similarity_search(self, 
                         query: str, 
                         k: int = 5,
                         filter_dict: Optional[Dict] = None) -> List[Document]:
        """
        Perform similarity search in the vector store.
        
        Args:
            query (str): Search query
            k (int): Number of results to return
            filter_dict (Optional[Dict]): Filter criteria
            
        Returns:
            List[Document]: Similar documents
        """
        try:
            if self.vector_store is None:
                raise ValueError("Vector store not initialized. Run build_vector_store() first.")
            
            logger.info(f"Performing similarity search for query: '{query}'")
            
            results = self.vector_store.similarity_search(
                query=query,
                k=k,
                filter=filter_dict
            )
            
            logger.info(f"Found {len(results)} similar documents")
            return results
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise
    
    def build_vector_store(self, force_rebuild: bool = False, incremental_update: bool = False) -> Chroma:
        """
        Build the complete vector store pipeline.
        
        Args:
            force_rebuild (bool): Force rebuild even if existing store exists
            incremental_update (bool): Check for CSV changes and update incrementally
            
        Returns:
            Chroma: Built vector store
        """
        try:
            logger.info("Starting vector store build process...")
            
            # Check for existing vector store
            if not force_rebuild:
                existing_store = self.load_existing_vector_store()
                if existing_store is not None:
                    if incremental_update:
                        # Check if CSV has changed and update incrementally
                        updated_store = self._incremental_update(existing_store)
                        if updated_store is not None:
                            self.vector_store = updated_store
                            logger.info("Vector store updated incrementally")
                            return self.vector_store
                    
                    self.vector_store = existing_store
                    logger.info("Using existing vector store")
                    return self.vector_store
            
            # If we get here, we need to build a new vector store
            # Clean up any existing corrupted data
            if os.path.exists(self.persist_directory):
                logger.info("Cleaning up existing vector store directory...")
                import shutil
                shutil.rmtree(self.persist_directory)
                os.makedirs(self.persist_directory, exist_ok=True)
            
            # Load CSV data
            df = self.load_csv_data()
            
            # Create documents
            documents = self.create_documents(df)
            
            # Chunk documents
            chunked_docs = self.chunk_documents(documents)
            
            # Create vector store
            vector_store = self.create_vector_store(chunked_docs)
            
            logger.info("Vector store build completed successfully")
            return vector_store
            
        except Exception as e:
            logger.error(f"Error building vector store: {str(e)}")
            raise
    

    
    def _get_csv_hash(self, df: pd.DataFrame) -> str:
        """Generate hash for CSV content."""
        import hashlib
        content = df.to_string()
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_stored_hash(self) -> Optional[str]:
        """Get stored CSV hash."""
        hash_file = os.path.join(self.persist_directory, "csv_hash.txt")
        if os.path.exists(hash_file):
            with open(hash_file, 'r') as f:
                return f.read().strip()
        return None
    
    def _store_csv_hash(self, hash_value: str):
        """Store CSV hash."""
        hash_file = os.path.join(self.persist_directory, "csv_hash.txt")
        with open(hash_file, 'w') as f:
            f.write(hash_value)
    
    def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the vector store collection.
        
        Returns:
            Dict[str, Any]: Collection information
        """
        try:
            if self.vector_store is None:
                raise ValueError("Vector store not initialized")
            
            # Get collection info
            collection = self.vector_store._collection
            count = collection.count()
            
            # Safely get metadata with fallback
            metadata = collection.metadata if hasattr(collection, 'metadata') and collection.metadata is not None else {}
            embedding_dimension = metadata.get('hnsw:space', 'unknown') if metadata else 'unknown'
            
            info = {
                'collection_name': collection.name,
                'document_count': count,
                'embedding_dimension': embedding_dimension,
                'persist_directory': self.persist_directory
            }
            
            logger.info(f"Collection info: {info}")
            return info
            
        except Exception as e:
            logger.error(f"Error getting collection info: {str(e)}")
            raise
    
    def delete_vector_store(self):
        """
        Delete the vector store and its data.
        """
        try:
            logger.warning("Deleting vector store...")
            
            if os.path.exists(self.persist_directory):
                import shutil
                shutil.rmtree(self.persist_directory)
                logger.info("Vector store deleted successfully")
            else:
                logger.info("Vector store directory does not exist")
                
        except Exception as e:
            logger.error(f"Error deleting vector store: {str(e)}")
            raise

def main():
    """Main function to demonstrate vector store creation."""
    try:
        # Initialize vector store manager
        vector_store_manager = AnimeVectorStore()
        
        # Build vector store with incremental updates
        vector_store = vector_store_manager.build_vector_store()
        
        # Get collection info
        info = vector_store_manager.get_collection_info()
        
        # Test similarity search
        test_query = "action adventure movies with high rating"
        results = vector_store_manager.similarity_search(test_query, k=3)
        
        print("Vector store creation completed successfully!")
        print(f"Collection info: {info}")
        print(f"Test search results for '{test_query}':")
        for i, doc in enumerate(results, 1):
            print(f"{i}. {doc.page_content[:100]}...")
            
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise

if __name__ == "__main__":
    main()

"""
# Basic run
docker run -p 8501:8501 movie-recommender

# With environment variables
docker run -p 8501:8501 --env-file .env movie-recommender

# With data persistence
docker run -p 8501:8501 --env-file .env -v $(pwd)/data:/app/data movie-recommender
"""