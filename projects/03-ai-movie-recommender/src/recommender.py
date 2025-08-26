import logging
import os
import sys
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from datetime import datetime

# LangChain imports
from langchain.chains import RetrievalQA
from langchain.prompts import PromptTemplate
from langchain_community.llms import OpenAI
from langchain_openai import ChatOpenAI
from langchain.schema import Document
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import LLMChainExtractor
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain.chains import create_retrieval_chain

# Vector store
from .vector_store import AnimeVectorStore

# Configuration
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.config import OPENAI_API_KEY

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AnimeRecommender:
    """
    Advanced anime recommendation system using RAG (Retrieval-Augmented Generation).
    Combines vector similarity search with LLM-based reasoning for personalized recommendations.
    """
    
    def __init__(self, 
                 vector_store_path: str = "../data/chroma_db",
                 csv_path: str = "../data/combined_info.csv",
                 model_name: str = "gpt-3.5-turbo",
                 temperature: float = 0.7,
                 max_tokens: int = 1000):
        """
        Initialize the anime recommender.
        
        Args:
            vector_store_path (str): Path to the vector store
            csv_path (str): Path to the anime data CSV
            model_name (str): LLM model to use
            temperature (float): Model temperature for creativity
            max_tokens (int): Maximum tokens for response
        """
        self.vector_store_path = vector_store_path
        self.csv_path = csv_path
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Initialize components
        self.vector_store_manager = None
        self.vector_store = None
        self.llm = None
        self.retrieval_chain = None
        self.movie_data = None
        
        logger.info(f"AnimeRecommender initialized with model: {model_name}")
    
    def initialize_components(self):
        """Initialize all components of the recommender system."""
        try:
            logger.info("Initializing recommender components...")
            
            # Initialize vector store
            self._initialize_vector_store()
            
            # Initialize LLM
            self._initialize_llm()
            
            # Load movie data
            self._load_movie_data()
            
            # Create retrieval chain
            self._create_retrieval_chain()
            
            logger.info("All components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing components: {str(e)}")
            raise
    
    def _initialize_vector_store(self):
        """Initialize the vector store manager and load vector store."""
        try:
            logger.info("Initializing vector store...")
            
            self.vector_store_manager = AnimeVectorStore(
                persist_directory=self.vector_store_path,
                csv_path=self.csv_path
            )
            
            # Build or load vector store
            self.vector_store = self.vector_store_manager.build_vector_store()
            
            logger.info("Vector store initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing vector store: {str(e)}")
            raise
    
    def _initialize_llm(self):
        """Initialize the language model."""
        try:
            logger.info(f"Initializing LLM: {self.model_name}")
            
            if not OPENAI_API_KEY:
                logger.warning("OpenAI API key not found. Using fallback model.")
                # You can add fallback models here
                raise ValueError("OpenAI API key required for LLM functionality")
            
            self.llm = ChatOpenAI(
                model_name=self.model_name,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                openai_api_key=OPENAI_API_KEY
            )
            
            logger.info("LLM initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LLM: {str(e)}")
            raise
    
    def _load_movie_data(self):
        """Load the movie dataset for additional context."""
        try:
            logger.info("Loading movie dataset...")
            
            self.movie_data = pd.read_csv(self.csv_path, encoding='utf-8')
            
            logger.info(f"Movie dataset loaded: {len(self.movie_data)} entries")
            
        except Exception as e:
            logger.error(f"Error loading movie data: {str(e)}")
            raise
    
    def _create_retrieval_chain(self):
        """Create the retrieval chain for RAG pipeline."""
        try:
            logger.info("Creating retrieval chain...")
            
            # Create prompt template for recommendations
            prompt_template = self._create_recommendation_prompt()
            
            # Create document chain
            document_chain = create_stuff_documents_chain(
                llm=self.llm,
                prompt=prompt_template
            )
            
            # Create retrieval chain with proper input/output structure
            self.retrieval_chain = create_retrieval_chain(
                retriever=self.vector_store.as_retriever(
                    search_type="similarity",
                    search_kwargs={"k": 10}
                ),
                combine_docs_chain=document_chain
            )
            
            logger.info("Retrieval chain created successfully")
            
        except Exception as e:
            logger.error(f"Error creating retrieval chain: {str(e)}")
            raise
    
    def _create_recommendation_prompt(self) -> PromptTemplate:
        """Create the prompt template for movie recommendations."""
        
        prompt_text = """You are an expert movie recommendation system. Based on the user's query and the provided movie information, provide personalized recommendations.

Context Information:
{context}

User Query: {input}

Please provide recommendations following these guidelines:
1. Analyze the user's preferences and query intent
2. Consider genre, rating, year, runtime, and other relevant factors
3. Provide 3-5 specific movie recommendations
4. For each recommendation, include:
   - Title
   - Brief reason why it matches their preferences
   - Key features (genre, rating, year, runtime, certificate)
5. If the query is vague, ask for clarification
6. Be enthusiastic but honest about recommendations

Format your response as:
🎬 **Movie Recommendations**

**1. [Movie Title]**
- Why: [Brief explanation]
- Genre: [Genres] | Rating: [X.X/10] | Runtime: [X min] | Certificate: [PG/R/etc]

**2. [Movie Title]**
- Why: [Brief explanation]
- Genre: [Genres] | Rating: [X.X/10] | Runtime: [X min] | Certificate: [PG/R/etc]

[Continue for 3-5 recommendations]

💡 **Additional Suggestions**: [Any additional tips or categories to explore]

Response:"""

        return PromptTemplate(
            template=prompt_text,
            input_variables=["context", "input"]
        )
    
    def get_similar_movies(self, query: str, k: int = 5) -> List[Document]:
        """
        Get similar movies based on user query using vector similarity search.
        
        Args:
            query (str): User query
            k (int): Number of results to return
            
        Returns:
            List[Document]: Similar movie documents
        """
        try:
            logger.info(f"Searching for similar movies: '{query}'")
            
            if self.vector_store is None:
                raise ValueError("Vector store not initialized")
            
            # Perform similarity search
            similar_docs = self.vector_store.similarity_search(
                query=query,
                k=k
            )
            
            logger.info(f"Found {len(similar_docs)} similar movies")
            return similar_docs
            
        except Exception as e:
            logger.error(f"Error in similarity search: {str(e)}")
            raise
    
    def get_recommendations(self, user_query: str) -> Dict[str, Any]:
        """
        Get personalized anime recommendations using RAG pipeline.
        
        Args:
            user_query (str): User's recommendation request
            
        Returns:
            Dict[str, Any]: Recommendation results with explanation
        """
        try:
            logger.info(f"Generating recommendations for: '{user_query}'")
            
            if self.retrieval_chain is None:
                raise ValueError("Retrieval chain not initialized")
            
            # Get recommendations using RAG
            response = self.retrieval_chain.invoke({
                "input": user_query
            })
            
            # Extract similar movies for additional context
            similar_movies = self.get_similar_movies(user_query, k=5)
            
            # Debug: Print response keys to understand structure
            logger.info(f"Response keys: {list(response.keys())}")
            
            # Format results - try different possible keys
            recommendations = response.get("output", response.get("answer", response.get("result", "No recommendations generated")))
            
            # Format the final answer with decorators
            formatted_answer = f"""
=============
{recommendations}
=============
"""
            
            results = {
                "query": user_query,
                "recommendations": formatted_answer,
                "similar_movies": [
                    {
                        "content": doc.page_content[:200] + "...",
                        "metadata": doc.metadata
                    }
                    for doc in similar_movies
                ],
                "timestamp": datetime.now().isoformat(),
                "model_used": self.model_name
            }
            
            logger.info("Recommendations generated successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error generating recommendations: {str(e)}")
            raise
    
    def get_recommendations_by_genre(self, genre: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get movie recommendations by specific genre.
        
        Args:
            genre (str): Genre to search for
            limit (int): Number of recommendations
            
        Returns:
            List[Dict[str, Any]]: Genre-based recommendations
        """
        try:
            logger.info(f"Getting recommendations for genre: {genre}")
            
            # Search for movies in the specified genre
            query = f"movies in {genre} genre with high rating"
            similar_docs = self.get_similar_movies(query, k=limit)
            
            recommendations = []
            for doc in similar_docs:
                # Parse the combined_info to extract details
                info = self._parse_movie_info(doc.page_content)
                recommendations.append({
                    "title": info.get("title", "Unknown"),
                    "genre": info.get("genre", "Unknown"),
                    "rating": info.get("rating", "Unknown"),
                    "runtime": info.get("runtime", "Unknown"),
                    "certificate": info.get("certificate", "Unknown"),
                    "similarity_score": doc.metadata.get("score", 0.0)
                })
            
            logger.info(f"Found {len(recommendations)} {genre} movies")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting genre recommendations: {str(e)}")
            raise
    
    def get_recommendations_by_rating(self, min_rating: float = 8.0, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get high-rated movie recommendations.
        
        Args:
            min_rating (float): Minimum rating threshold
            limit (int): Number of recommendations
            
        Returns:
            List[Dict[str, Any]]: High-rated movie recommendations
        """
        try:
            logger.info(f"Getting recommendations with rating >= {min_rating}")
            
            query = f"movies with rating {min_rating} or higher"
            similar_docs = self.get_similar_movies(query, k=limit)
            
            recommendations = []
            for doc in similar_docs:
                info = self._parse_movie_info(doc.page_content)
                rating = float(info.get("rating", 0))
                if rating >= min_rating:
                    recommendations.append({
                        "title": info.get("title", "Unknown"),
                        "genre": info.get("genre", "Unknown"),
                        "rating": rating,
                        "runtime": info.get("runtime", "Unknown"),
                        "certificate": info.get("certificate", "Unknown")
                    })
            
            logger.info(f"Found {len(recommendations)} high-rated movies")
            return recommendations
            
        except Exception as e:
            logger.error(f"Error getting rating recommendations: {str(e)}")
            raise
    
    def _parse_movie_info(self, combined_info: str) -> Dict[str, str]:
        """
        Parse combined_info string to extract individual fields.
        
        Args:
            combined_info (str): Combined movie information string
            
        Returns:
            Dict[str, str]: Parsed movie information
        """
        try:
            info = {}
            parts = combined_info.split()
            
            current_key = None
            current_value = []
            
            for part in parts:
                if part.endswith(':'):
                    # Save previous key-value pair
                    if current_key and current_value:
                        info[current_key] = ' '.join(current_value)
                    
                    # Start new key
                    current_key = part[:-1]  # Remove colon
                    current_value = []
                else:
                    # Add to current value
                    if current_key:
                        current_value.append(part)
            
            # Save last key-value pair
            if current_key and current_value:
                info[current_key] = ' '.join(current_value)
            
            return info
            
        except Exception as e:
            logger.warning(f"Error parsing movie info: {str(e)}")
            return {}
    
    def get_recommendation_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the recommendation system.
        
        Returns:
            Dict[str, Any]: System statistics
        """
        try:
            if self.vector_store_manager is None:
                raise ValueError("Vector store not initialized")
            
            # Get collection info
            collection_info = self.vector_store_manager.get_collection_info()
            
            # Get movie data stats
            movie_stats = {
                "total_movies": len(self.movie_data) if self.movie_data is not None else 0,
                "columns": list(self.movie_data.columns) if self.movie_data is not None else [],
                "data_shape": self.movie_data.shape if self.movie_data is not None else (0, 0)
            }
            
            stats = {
                "vector_store": collection_info,
                "movie_data": movie_stats,
                "model_info": {
                    "model_name": self.model_name,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens
                },
                "system_status": "operational"
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error getting recommendation stats: {str(e)}")
            raise

def main():
    """Main function to demonstrate the recommender system."""
    try:
        # Initialize recommender
        recommender = AnimeRecommender()
        recommender.initialize_components()
        
        # Get system stats
        stats = recommender.get_recommendation_stats()
        print("🎬 Movie Recommender System")
        print(f"Total movies in database: {stats['movie_data']['total_movies']}")
        print(f"Vector store documents: {stats['vector_store']['document_count']}")
        
        # Test different recommendation types
        test_queries = [
            "I like action and adventure movies with great cinematography",
            "Show me some romantic comedy movies",
            "I want to watch something similar to Christopher Nolan films",
            "Recommend me some recent sci-fi movies"
        ]
        
        for query in test_queries:
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")
            
            # Get RAG-based recommendations
            results = recommender.get_recommendations(query)
            print(results['recommendations'])
            
            # Get similar movies
            similar = recommender.get_similar_movies(query, k=3)
            print(f"\nSimilar movies found: {len(similar)}")
        
        # Test genre-based recommendations
        print(f"\n{'='*60}")
        print("Genre-based recommendations (Action):")
        print(f"{'='*60}")
        action_recs = recommender.get_recommendations_by_genre("action", limit=3)
        for rec in action_recs:
            print(f"- {rec['title']} - Rating: {rec['rating']} - Runtime: {rec['runtime']} - Certificate: {rec['certificate']}")
        
        print("\n✅ Recommender system test completed successfully!")
        
    except Exception as e:
        logger.error(f"Error in main function: {str(e)}")
        raise

if __name__ == "__main__":
    main()
