#!/usr/bin/env python3
"""
Simple script to run the Anime Recommendation System ingestion pipeline.
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
    """Run the complete ingestion pipeline."""
    try:
        # Define paths relative to project root
        data_path = project_root / "data" / "IMDB_10000.csv"
        output_dir = project_root / "data" / "processed_data"
        vector_store_path = project_root / "data" / "chroma_db"
        combined_info_path = project_root / "data" / "combined_info.csv"
        
        # Check if data file exists
        if not data_path.exists():
            logger.error(f"Data file not found: {data_path}")
            logger.info("Please ensure the IMDB_10000.csv file is in the data/ directory")
            return
        
        # Create output directories
        output_dir.mkdir(parents=True, exist_ok=True)
        vector_store_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("🎬 Starting Anime Recommendation System Pipeline")
        logger.info(f"Data file: {data_path}")
        logger.info(f"Output directory: {output_dir}")
        logger.info(f"Vector store path: {vector_store_path}")
        
        # Initialize and run pipeline
        pipeline = AnimeIngestionPipeline(
            data_path=str(data_path),
            output_dir=str(output_dir),
            vector_store_path=str(vector_store_path),
            combined_info_path=str(combined_info_path)
        )
        
        # Run the complete pipeline
        results = pipeline.run_complete_pipeline(force_rebuild=False)
        
        # Print summary
        print("\n" + "="*80)
        print("🎬 PIPELINE EXECUTION SUMMARY")
        print("="*80)
        print(f"Status: {results['pipeline_status']}")
        print(f"Steps completed: {len(results['steps_completed'])}/3")
        
        if results['pipeline_status'] == 'completed':
            print("\n✅ All steps completed successfully!")
            
            # Show statistics
            for step, stats in results['statistics'].items():
                print(f"\n📊 {step.replace('_', ' ').title()}:")
                print(f"   {stats['message']}")
                
                if step == 'data_loading':
                    print(f"   Data shape: {stats['data_shape']}")
                elif step == 'vector_store':
                    print(f"   Documents: {stats['collection_info']['document_count']}")
                elif step == 'recommender':
                    print(f"   System tested: {stats['test_results_available']}")
            
            # Ask if user wants to start interactive mode
            print("\n" + "="*80)
            print("🎯 PIPELINE READY FOR RECOMMENDATIONS!")
            print("="*80)
            print("You can now:")
            print("1. Run 'python ask_recommendations.py' for interactive mode")
            print("2. Run 'python ask_recommendations.py --query \"your question\"' for a single query")
            print("3. Run 'python ask_recommendations.py --test' for quick test")
            print("4. Use the pipeline object directly in your code")
            
            # Start interactive mode if requested
            try:
                start_interactive = input("\n🤔 Start interactive mode now? (y/n): ").strip().lower()
                if start_interactive in ['y', 'yes']:
                    print("\n🎬 Starting interactive mode...")
                    pipeline.interactive_mode()
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
            
        else:
            print(f"\n❌ Pipeline failed with errors:")
            for error in results['errors']:
                print(f"   - {error}")
        
    except Exception as e:
        logger.error(f"Pipeline execution failed: {str(e)}")
        print(f"\n❌ Fatal error: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
