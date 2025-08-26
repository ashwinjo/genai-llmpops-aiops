import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.recommender import AnimeRecommender
from src.vector_store import AnimeVectorStore
from data.data_loader import AnimeDataLoader
from config.config import GROQ_API_KEY, OPENAI_API_KEY, HF_TOKEN

import logging
import os
import sys
from typing import Dict, Any, Optional, List
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AnimeIngestionPipeline:
    """
    Complete ingestion pipeline for the Anime Recommendation System.
    Sequentially runs: Data Loader -> Vector Store -> Recommender
    """
    
    def __init__(self, 
                 data_path: str = "IMDB_10000.csv",
                 output_dir: str = "processed_data",
                 vector_store_path: str = "data/chroma_db",
                 combined_info_path: str = "data/combined_info.csv"):
        """
        Initialize the ingestion pipeline.
        
        Args:
            data_path (str): Path to the raw CSV data file
            output_dir (str): Directory for processed data
            vector_store_path (str): Path for vector store persistence
            combined_info_path (str): Path for combined info CSV
        """
        self.data_path = data_path
        self.output_dir = output_dir
        self.vector_store_path = vector_store_path
        self.combined_info_path = combined_info_path
        
        # Initialize components
        self.data_loader = None
        self.vector_store = None
        self.recommender = None
        
        # Pipeline status
        self.pipeline_status = {
            "data_loading": False,
            "vector_store_creation": False,
            "recommender_initialization": False,
            "overall_status": "not_started"
        }
        
        logger.info("AnimeIngestionPipeline initialized")
        logger.info(f"Data path: {data_path}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Vector store path: {vector_store_path}")
    
    def run_complete_pipeline(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Run the complete ingestion pipeline sequentially.
        
        Args:
            force_rebuild (bool): Force rebuild of vector store
            
        Returns:
            Dict[str, Any]: Pipeline execution results and status
        """
        try:
            logger.info("🚀 Starting complete ingestion pipeline...")
            
            results = {
                "pipeline_status": "running",
                "steps_completed": [],
                "errors": [],
                "statistics": {}
            }
            
            # Step 1: Data Loading and Processing
            logger.info("=" * 60)
            logger.info("STEP 1: DATA LOADING AND PROCESSING")
            logger.info("=" * 60)
            
            data_results = self._run_data_loading_step()
            results["steps_completed"].append("data_loading")
            results["statistics"]["data_loading"] = data_results
            
            # Step 2: Vector Store Creation
            logger.info("=" * 60)
            logger.info("STEP 2: VECTOR STORE CREATION")
            logger.info("=" * 60)
            
            vector_results = self._run_vector_store_step(force_rebuild)
            results["steps_completed"].append("vector_store_creation")
            results["statistics"]["vector_store"] = vector_results
            
            # Step 3: Recommender Initialization
            logger.info("=" * 60)
            logger.info("STEP 3: RECOMMENDER INITIALIZATION")
            logger.info("=" * 60)
            
            recommender_results = self._run_recommender_step()
            results["steps_completed"].append("recommender_initialization")
            results["statistics"]["recommender"] = recommender_results
            
            # Update pipeline status
            self.pipeline_status["overall_status"] = "completed"
            results["pipeline_status"] = "completed"
            
            logger.info("=" * 60)
            logger.info("✅ PIPELINE COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ Pipeline failed: {str(e)}")
            results["pipeline_status"] = "failed"
            results["errors"].append(str(e))
            self.pipeline_status["overall_status"] = "failed"
            return results
    
    def _run_data_loading_step(self) -> Dict[str, Any]:
        """
        Run the data loading and processing step.
        
        Returns:
            Dict[str, Any]: Data loading results
        """
        try:
            logger.info("📊 Initializing data loader...")
            
            # Initialize data loader
            self.data_loader = AnimeDataLoader(data_path=self.data_path)
            
            # Load and clean data
            logger.info("🔄 Loading and cleaning data...")
            cleaned_data = self.data_loader.clean_data()
            
            # Save processed data
            logger.info("💾 Saving processed data...")
            self.data_loader.save_processed_data(self.output_dir)
            
            # Save combined info CSV
            logger.info("📝 Creating combined info CSV...")
            self.data_loader.save_combined_info_csv(self.combined_info_path)
            
            # Update status
            self.pipeline_status["data_loading"] = True
            
            results = {
                "status": "success",
                "data_shape": cleaned_data.shape,
                "output_files": [
                    f"{self.output_dir}/cleaned_anime_data.csv",
                    f"{self.output_dir}/tfidf_vectorizer.pkl",
                    f"{self.output_dir}/scaler.pkl",
                    f"{self.output_dir}/label_encoders.pkl",
                    self.combined_info_path
                ],
                "message": f"Data loaded and processed successfully. Shape: {cleaned_data.shape}"
            }
            
            logger.info(f"✅ Data loading completed. Shape: {cleaned_data.shape}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Data loading failed: {str(e)}")
            self.pipeline_status["data_loading"] = False
            raise
    
    def _run_vector_store_step(self, force_rebuild: bool = False) -> Dict[str, Any]:
        """
        Run the vector store creation step.
        
        Args:
            force_rebuild (bool): Force rebuild of vector store
            
        Returns:
            Dict[str, Any]: Vector store creation results
        """
        try:
            logger.info("🔍 Initializing vector store...")
            
            # Initialize vector store
            self.vector_store = AnimeVectorStore(
                csv_path=self.combined_info_path,
                persist_directory=self.vector_store_path
            )
            
            # Build vector store
            logger.info("🏗️ Building vector store...")
            vector_store = self.vector_store.build_vector_store(force_rebuild=force_rebuild)
            
            # Get collection info
            collection_info = self.vector_store.get_collection_info()
            
            # Update status
            self.pipeline_status["vector_store_creation"] = True
            
            results = {
                "status": "success",
                "collection_info": collection_info,
                "persist_directory": self.vector_store_path,
                "message": f"Vector store created successfully. Documents: {collection_info['document_count']}"
            }
            
            logger.info(f"✅ Vector store created. Documents: {collection_info['document_count']}")
            return results
            
        except Exception as e:
            logger.error(f"❌ Vector store creation failed: {str(e)}")
            self.pipeline_status["vector_store_creation"] = False
            raise
    
    def _run_recommender_step(self) -> Dict[str, Any]:
        """
        Run the recommender initialization step.
        
        Returns:
            Dict[str, Any]: Recommender initialization results
        """
        try:
            logger.info("🤖 Initializing recommender system...")
            
            # Initialize recommender
            self.recommender = AnimeRecommender(
                vector_store_path=self.vector_store_path,
                csv_path=self.combined_info_path
            )
            
            # Initialize all components
            logger.info("🔧 Initializing recommender components...")
            self.recommender.initialize_components()
            
            # Get system statistics
            stats = self.recommender.get_recommendation_stats()
            
            # Test the system with a simple query
            logger.info("🧪 Testing recommender system...")
            test_query = "action adventure movies"
            test_results = self.recommender.get_recommendations(test_query)
            
            # Update status
            self.pipeline_status["recommender_initialization"] = True
            
            results = {
                "status": "success",
                "system_stats": stats,
                "test_query": test_query,
                "test_results_available": len(test_results.get("similar_movies", [])) > 0,
                "message": "Recommender system initialized and tested successfully"
            }
            
            logger.info("✅ Recommender system initialized and tested successfully")
            return results
            
        except Exception as e:
            logger.error(f"❌ Recommender initialization failed: {str(e)}")
            self.pipeline_status["recommender_initialization"] = False
            raise
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """
        Get the current status of the pipeline.
        
        Returns:
            Dict[str, Any]: Pipeline status information
        """
        return {
            "pipeline_status": self.pipeline_status,
            "components_initialized": {
                "data_loader": self.data_loader is not None,
                "vector_store": self.vector_store is not None,
                "recommender": self.recommender is not None
            }
        }
    
    def test_recommendation_system(self, test_queries: list = None) -> Dict[str, Any]:
        """
        Test the recommendation system with sample queries.
        
        Args:
            test_queries (list): List of test queries
            
        Returns:
            Dict[str, Any]: Test results
        """
        if self.recommender is None:
            raise ValueError("Recommender not initialized. Run pipeline first.")
        
        if test_queries is None:
            test_queries = [
                "I like action and adventure movies",
                "Show me some romantic comedy movies",
                "Recommend me sci-fi movies with high ratings",
                "I want to watch something similar to Christopher Nolan films"
            ]
        
        results = {
            "test_queries": test_queries,
            "responses": []
        }
        
        for query in test_queries:
            try:
                response = self.recommender.get_recommendations(query)
                results["responses"].append({
                    "query": query,
                    "status": "success",
                    "recommendations": response["recommendations"],
                    "similar_movies_count": len(response.get("similar_movies", []))
                })
            except Exception as e:
                results["responses"].append({
                    "query": query,
                    "status": "error",
                    "error": str(e)
                })
        
        return results

    def get_recommendations(self, query: str) -> Dict[str, Any]:
        """
        Get recommendations for a specific query after pipeline is complete.
        
        Args:
            query (str): User's recommendation request
            
        Returns:
            Dict[str, Any]: Recommendation results
        """
        if self.recommender is None:
            raise ValueError("Recommender not initialized. Run pipeline first.")
        
        try:
            logger.info(f"Getting recommendations for: '{query}'")
            results = self.recommender.get_recommendations(query)
            return results
        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            raise
    
    def ask_question(self, question: str) -> str:
        """
        Simple interface to ask a question and get recommendations.
        
        Args:
            question (str): User's question/request
            
        Returns:
            str: Formatted recommendation response
        """
        try:
            results = self.get_recommendations(question)
            return results.get("recommendations", "No recommendations available")
        except Exception as e:
            return f"Error: {str(e)}"
    
    def interactive_mode(self):
        """
        Start an interactive mode for asking questions.
        """
        if self.recommender is None:
            print("❌ Pipeline not initialized. Please run the pipeline first.")
            return
        
        print("\n🎬 Anime Recommendation System - Interactive Mode")
        print("=" * 60)
        print("Type your questions about movies (e.g., 'I like action movies')")
        print("Type 'quit' or 'exit' to stop")
        print("=" * 60)
        
        while True:
            try:
                question = input("\n🤔 Your question: ").strip()
                
                if question.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                
                if not question:
                    continue
                
                print("\n🔍 Searching for recommendations...")
                response = self.ask_question(question)
                print(f"\n📝 Recommendations:\n{response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
    
    def quick_recommendations(self, queries: List[str] = None) -> Dict[str, Any]:
        """
        Get quick recommendations for common queries.
        
        Args:
            queries (List[str]): List of queries to process
            
        Returns:
            Dict[str, Any]: Results for all queries
        """
        if queries is None:
            queries = [
                "I like action and adventure movies",
                "Show me some romantic comedy movies", 
                "Recommend me sci-fi movies with high ratings",
                "I want to watch something similar to Christopher Nolan films"
            ]
        
        results = {}
        for query in queries:
            try:
                print(f"\n🔍 Processing: {query}")
                response = self.get_recommendations(query)
                results[query] = response
                print(f"✅ Completed: {query}")
            except Exception as e:
                results[query] = {"error": str(e)}
                print(f"❌ Error: {str(e)}")
        
        return results


def main():
    """Main function to run the complete ingestion pipeline."""
    try:
        # Initialize pipeline
        pipeline = AnimeIngestionPipeline()
        
        # Run complete pipeline
        results = pipeline.run_complete_pipeline(force_rebuild=False)
        
        # Print results summary
        print("\n" + "="*80)
        print("🎬 ANIME RECOMMENDATION SYSTEM - PIPELINE RESULTS")
        print("="*80)
        
        print(f"Pipeline Status: {results['pipeline_status']}")
        print(f"Steps Completed: {len(results['steps_completed'])}/3")
        
        for step in results['steps_completed']:
            if step in results['statistics']:
                stats = results['statistics'][step]
                print(f"\n✅ {step.upper().replace('_', ' ')}:")
                print(f"   Status: {stats['status']}")
                print(f"   Message: {stats['message']}")
        
        if results['errors']:
            print(f"\n❌ Errors: {results['errors']}")
        
        # Test the system
        print("\n" + "="*80)
        print("🧪 TESTING RECOMMENDATION SYSTEM")
        print("="*80)
        
        test_results = pipeline.test_recommendation_system()
        
        for response in test_results['responses']:
            print(f"\nQuery: {response['query']}")
            print(f"Status: {response['status']}")
            if response['status'] == 'success':
                print(f"Similar movies found: {response['similar_movies_count']}")
                print("Recommendations:")
                print(response['recommendations'][:500] + "..." if len(response['recommendations']) > 500 else response['recommendations'])
            else:
                print(f"Error: {response['error']}")
        
        print("\n🎉 Pipeline execution completed successfully!")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        raise


if __name__ == "__main__":
    main()

