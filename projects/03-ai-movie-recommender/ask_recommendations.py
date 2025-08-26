#!/usr/bin/env python3
"""
Simple script to ask for movie recommendations after pipeline ingestion is complete.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from pipeline.pipeline import AnimeIngestionPipeline
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function to run recommendation queries."""
    try:
        # Define paths relative to project root
        data_path = project_root / "data" / "IMDB_10000.csv"
        output_dir = project_root / "data" / "processed_data"
        vector_store_path = project_root / "data" / "chroma_db"
        combined_info_path = project_root / "data" / "combined_info.csv"
        
        # Initialize pipeline (this will load existing data if available)
        print("🎬 Loading Movie Recommendation System...")
        pipeline = AnimeIngestionPipeline(
            data_path=str(data_path),
            output_dir=str(output_dir),
            vector_store_path=str(vector_store_path),
            combined_info_path=str(combined_info_path)
        )
        
        # Check if pipeline is ready
        status = pipeline.get_pipeline_status()
        if not status["components_initialized"]["recommender"]:
            print("❌ Pipeline not ready. Running complete pipeline first...")
            results = pipeline.run_complete_pipeline(force_rebuild=False)
            if results["pipeline_status"] != "completed":
                print("❌ Pipeline failed to complete. Please check the logs.")
                return 1
        
        print("✅ Pipeline ready! You can now ask for recommendations.")
        
        # Start interactive mode
        pipeline.interactive_mode()
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\n❌ Fatal error: {str(e)}")
        return 1
    
    return 0


def quick_test():
    """Quick test function for specific queries."""
    try:
        # Define paths relative to project root
        data_path = project_root / "data" / "IMDB_10000.csv"
        output_dir = project_root / "data" / "processed_data"
        vector_store_path = project_root / "data" / "chroma_db"
        combined_info_path = project_root / "data" / "combined_info.csv"
        
        print("🎬 Loading Anime Recommendation System...")
        pipeline = AnimeIngestionPipeline(
            data_path=str(data_path),
            output_dir=str(output_dir),
            vector_store_path=str(vector_store_path),
            combined_info_path=str(combined_info_path)
        )
        
        # Check if pipeline is ready
        status = pipeline.get_pipeline_status()
        if not status["components_initialized"]["recommender"]:
            print("❌ Pipeline not ready. Running complete pipeline first...")
            results = pipeline.run_complete_pipeline(force_rebuild=False)
            if results["pipeline_status"] != "completed":
                print("❌ Pipeline failed to complete.")
                return 1
        
        # Test specific queries
        test_queries = [
            "Movies similar to Forest Gump",
            "I like action movies with great cinematography",
            "Show me some romantic comedy movies",
            "Recommend me sci-fi movies with high ratings"
        ]
        
        print("\n🧪 Testing specific queries...")
        results = pipeline.quick_recommendations(test_queries)
        
        # Display results
        for query, result in results.items():
            print(f"\n{'='*60}")
            print(f"Query: {query}")
            print(f"{'='*60}")
            if "error" in result:
                print(f"❌ Error: {result['error']}")
            else:
                print(result.get("recommendations", "No recommendations"))
        
        return 0
        
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"\n❌ Fatal error: {str(e)}")
        return 1


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Ask for movie recommendations")
    parser.add_argument("--test", action="store_true", help="Run quick test with predefined queries")
    parser.add_argument("--query", type=str, help="Ask a specific question")
    
    args = parser.parse_args()
    
    if args.test:
        exit_code = quick_test()
    elif args.query:
        # Handle single query
        try:
            # Define paths relative to project root
            data_path = project_root / "data" / "IMDB_10000.csv"
            output_dir = project_root / "data" / "processed_data"
            vector_store_path = project_root / "data" / "chroma_db"
            combined_info_path = project_root / "data" / "combined_info.csv"
            
            pipeline = AnimeIngestionPipeline(
                data_path=str(data_path),
                output_dir=str(output_dir),
                vector_store_path=str(vector_store_path),
                combined_info_path=str(combined_info_path)
            )
            status = pipeline.get_pipeline_status()
            if not status["components_initialized"]["recommender"]:
                print("❌ Pipeline not ready. Running complete pipeline first...")
                results = pipeline.run_complete_pipeline(force_rebuild=False)
                if results["pipeline_status"] != "completed":
                    print("❌ Pipeline failed to complete.")
                    sys.exit(1)
            
            print(f"🔍 Getting recommendations for: {args.query}")
            response = pipeline.ask_question(args.query)
            print(f"\n📝 Recommendations:\n{response}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            sys.exit(1)
    else:
        exit_code = main()
        sys.exit(exit_code)
