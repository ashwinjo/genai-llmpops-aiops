#!/usr/bin/env python3
"""
Streamlit interface for the Anime Recommendation System.
Provides pipeline management and recommendation functionality.
"""

import streamlit as st
import pandas as pd
import os
import sys
from pathlib import Path
import time
import logging

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.append(str(project_root))

from pipeline.pipeline import AnimeIngestionPipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="Movie Recommendation System",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        color: #1f77b4;
        margin-bottom: 2rem;
    }
    .sub-header {
        font-size: 1.5rem;
        font-weight: bold;
        color: #2c3e50;
        margin-bottom: 1rem;
    }
    .success-box {
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .info-box {
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        border: 1px solid #ffeaa7;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
    .recommendation-box {
        background-color: #f8f9fa;
        border: 1px solid #dee2e6;
        border-radius: 5px;
        padding: 1rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def initialize_session_state():
    """Initialize session state variables."""
    if 'pipeline' not in st.session_state:
        st.session_state.pipeline = None
    if 'pipeline_ready' not in st.session_state:
        st.session_state.pipeline_ready = False
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'recommendation_history' not in st.session_state:
        st.session_state.recommendation_history = []

def create_pipeline():
    """Create and initialize the pipeline."""
    try:
        # Define paths
        data_path = project_root / "data" / "IMDB_10000.csv"
        output_dir = project_root / "data" / "processed_data"
        vector_store_path = project_root / "data" / "chroma_db"
        combined_info_path = project_root / "data" / "combined_info.csv"
        
        # Create directories if they don't exist
        output_dir.mkdir(parents=True, exist_ok=True)
        vector_store_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize pipeline
        pipeline = AnimeIngestionPipeline(
            data_path=str(data_path),
            output_dir=str(output_dir),
            vector_store_path=str(vector_store_path),
            combined_info_path=str(combined_info_path)
        )
        
        return pipeline
    except Exception as e:
        st.error(f"Error creating pipeline: {str(e)}")
        return None

def quick_connect_to_existing():
    """Quickly connect to existing ChromaDB without running full pipeline."""
    try:
        # Define paths
        vector_store_path = project_root / "data" / "chroma_db"
        combined_info_path = project_root / "data" / "combined_info.csv"
        
        # Check if ChromaDB exists
        if not vector_store_path.exists() or not any(vector_store_path.iterdir()):
            return None, "No existing ChromaDB found. Please run the pipeline first."
        
        # Check if combined_info.csv exists
        if not combined_info_path.exists():
            return None, "Combined info CSV not found. Please run the pipeline first."
        
        # Create a minimal pipeline that only initializes the recommender
        from src.recommender import AnimeRecommender
        
        recommender = AnimeRecommender(
            vector_store_path=str(vector_store_path),
            csv_path=str(combined_info_path)
        )
        
        # Initialize components (this will load existing ChromaDB)
        recommender.initialize_components()
        
        # Create a minimal pipeline object for compatibility
        class QuickPipeline:
            def __init__(self, recommender):
                self.recommender = recommender
                self.pipeline_status = {
                    "data_loading": True,
                    "vector_store_creation": True,
                    "recommender_initialization": True,
                    "overall_status": "completed"
                }
            
            def get_recommendations(self, query):
                return self.recommender.get_recommendations(query)
            
            def get_pipeline_status(self):
                return {
                    "pipeline_status": self.pipeline_status,
                    "components_initialized": {
                        "data_loader": True,
                        "vector_store": True,
                        "recommender": True
                    }
                }
        
        pipeline = QuickPipeline(recommender)
        return pipeline, "Successfully connected to existing ChromaDB!"
        
    except Exception as e:
        return None, f"Error connecting to existing data: {str(e)}"

def run_pipeline_with_progress(pipeline, force_rebuild=False):
    """Run the pipeline with progress indicators."""
    try:
        with st.spinner("🚀 Starting pipeline..."):
            # Step 1: Data Loading
            st.info("📊 Step 1: Loading and processing data...")
            data_results = pipeline._run_data_loading_step()
            st.success(f"✅ Data loaded successfully! Shape: {data_results['data_shape']}")
            
            # Step 2: Vector Store Creation
            st.info("🔍 Step 2: Creating vector store...")
            vector_results = pipeline._run_vector_store_step(force_rebuild)
            st.success(f"✅ Vector store created! Documents: {vector_results['collection_info']['document_count']}")
            
            # Step 3: Recommender Initialization
            st.info("🤖 Step 3: Initializing recommender system...")
            recommender_results = pipeline._run_recommender_step()
            st.success("✅ Recommender system ready!")
            
            return True
            
    except Exception as e:
        st.error(f"❌ Pipeline failed: {str(e)}")
        return False

def upload_and_process_csv():
    """Handle CSV upload and processing."""
    st.subheader("📁 Upload Custom Dataset")
    
    uploaded_file = st.file_uploader(
        "Choose a CSV file",
        type=['csv'],
        help="Upload your own movie dataset in CSV format"
    )
    
    if uploaded_file is not None:
        try:
            # Save uploaded file
            data_path = project_root / "data" / "uploaded_data.csv"
            with open(data_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            st.session_state.uploaded_file = str(data_path)
            st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
            
            # Show preview
            df = pd.read_csv(data_path)
            st.write("**Data Preview:**")
            st.dataframe(df.head(), use_container_width=True)
            st.write(f"**Dataset Info:** {df.shape[0]} rows, {df.shape[1]} columns")
            
            return str(data_path)
            
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            return None
    
    return None

def pipeline_management_section():
    """Pipeline management section."""
    st.markdown('<div class="sub-header">🔧 Pipeline Management</div>', unsafe_allow_html=True)
    
    # Create tabs for different pipeline options
    tab1, tab2, tab3, tab4 = st.tabs(["🚀 Quick Connect", "📊 Use Default Dataset", "📁 Upload Custom Dataset", "⚙️ Pipeline Status"])
    
    with tab1:
        st.write("**Quick Connect to Existing ChromaDB**")
        st.info("This option connects directly to existing ChromaDB without running the full pipeline. Use this for faster startup if you've already processed data.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🔗 Quick Connect", type="primary", use_container_width=True):
                with st.spinner("Connecting to existing ChromaDB..."):
                    pipeline, message = quick_connect_to_existing()
                    if pipeline:
                        st.session_state.pipeline = pipeline
                        st.session_state.pipeline_ready = True
                        st.success(message)
                    else:
                        st.error(message)
        
        with col2:
            if st.button("📊 Check Data Status", use_container_width=True):
                vector_store_path = project_root / "data" / "chroma_db"
                combined_info_path = project_root / "data" / "combined_info.csv"
                
                col_a, col_b = st.columns(2)
                with col_a:
                    if vector_store_path.exists() and any(vector_store_path.iterdir()):
                        st.success("✅ ChromaDB exists")
                    else:
                        st.error("❌ ChromaDB not found")
                
                with col_b:
                    if combined_info_path.exists():
                        st.success("✅ Combined CSV exists")
                    else:
                        st.error("❌ Combined CSV not found")
    
    with tab2:
        st.write("Use the default IMDB dataset for the recommendation system.")
        
        col1, col2 = st.columns([1, 1])
        
        with col1:
            if st.button("🚀 Run Pipeline", type="primary", use_container_width=True):
                with st.spinner("Initializing pipeline..."):
                    pipeline = create_pipeline()
                    if pipeline:
                        st.session_state.pipeline = pipeline
                        
                        # Run pipeline
                        if run_pipeline_with_progress(pipeline, force_rebuild=False):
                            st.session_state.pipeline_ready = True
                            st.success("🎉 Pipeline completed successfully!")
                        else:
                            st.session_state.pipeline_ready = False
        
        with col2:
            if st.button("🔄 Force Rebuild", use_container_width=True):
                with st.spinner("Force rebuilding pipeline..."):
                    pipeline = create_pipeline()
                    if pipeline:
                        st.session_state.pipeline = pipeline
                        
                        # Run pipeline with force rebuild
                        if run_pipeline_with_progress(pipeline, force_rebuild=True):
                            st.session_state.pipeline_ready = True
                            st.success("🎉 Pipeline rebuilt successfully!")
                        else:
                            st.session_state.pipeline_ready = False
    
    with tab3:
        uploaded_data_path = upload_and_process_csv()
        
        if uploaded_data_path and st.button("🚀 Run Pipeline with Uploaded Data", type="primary"):
            with st.spinner("Initializing pipeline with uploaded data..."):
                # Create pipeline with uploaded data
                try:
                    output_dir = project_root / "data" / "processed_data"
                    vector_store_path = project_root / "data" / "chroma_db"
                    combined_info_path = project_root / "data" / "combined_info.csv"
                    
                    pipeline = AnimeIngestionPipeline(
                        data_path=uploaded_data_path,
                        output_dir=str(output_dir),
                        vector_store_path=str(vector_store_path),
                        combined_info_path=str(combined_info_path)
                    )
                    
                    st.session_state.pipeline = pipeline
                    
                    # Run pipeline
                    if run_pipeline_with_progress(pipeline, force_rebuild=True):
                        st.session_state.pipeline_ready = True
                        st.success("🎉 Pipeline completed with uploaded data!")
                    else:
                        st.session_state.pipeline_ready = False
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
    
    with tab4:
        st.write("**Current Pipeline Status:**")
        
        if st.session_state.pipeline:
            status = st.session_state.pipeline.get_pipeline_status()
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Components:**")
                for component, initialized in status["components_initialized"].items():
                    status_icon = "✅" if initialized else "❌"
                    st.write(f"{status_icon} {component.replace('_', ' ').title()}")
            
            with col2:
                st.write("**Pipeline Status:**")
                pipeline_status = status["pipeline_status"]
                for step, completed in pipeline_status.items():
                    if step != "overall_status":
                        status_icon = "✅" if completed else "❌"
                        st.write(f"{status_icon} {step.replace('_', ' ').title()}")
            
            if st.session_state.pipeline_ready:
                st.success("🎉 Pipeline is ready for recommendations!")
            else:
                st.warning("⚠️ Pipeline needs to be initialized.")
        else:
            st.info("ℹ️ No pipeline initialized yet.")

def recommendation_section():
    """Recommendation section."""
    st.markdown('<div class="sub-header">🎬 Movie Recommendations</div>', unsafe_allow_html=True)
    
    if not st.session_state.pipeline_ready:
        st.warning("⚠️ Please initialize the pipeline first before getting recommendations.")
        return
    
    # Query input
    st.write("**Ask for movie recommendations:**")
    
    # Example queries
    example_queries = [
        "I like action movies",
        "Movies similar to Forest Gump",
        "Show me some romantic comedy movies",
        "Recommend me sci-fi movies with high ratings",
        "I want to watch something similar to Christopher Nolan films"
    ]
    
    # Query input with examples
    query = st.text_input(
        "Enter your question:",
        placeholder="e.g., I like action movies with great cinematography",
        help="Ask about movies you'd like to watch"
    )
    
    # Quick query buttons
    st.write("**Quick queries:**")
    cols = st.columns(len(example_queries))
    for i, example in enumerate(example_queries):
        with cols[i]:
            if st.button(example, key=f"example_{i}"):
                query = example
                st.session_state.current_query = query
    
    # Process query
    if query and st.button("🔍 Get Recommendations", type="primary"):
        with st.spinner("🔍 Searching for recommendations..."):
            try:
                # Get recommendations
                results = st.session_state.pipeline.get_recommendations(query)
                
                # Display results
                st.markdown('<div class="recommendation-box">', unsafe_allow_html=True)
                st.markdown("### 🎬 Recommendations")
                st.markdown(results.get("recommendations", "No recommendations available"))
                st.markdown('</div>', unsafe_allow_html=True)
                
                # Show metadata
                with st.expander("📊 Query Details"):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**Query:** {results.get('query', 'N/A')}")
                    with col2:
                        st.write(f"**Similar Movies:** {len(results.get('similar_movies', []))}")
                    with col3:
                        st.write(f"**Model:** {results.get('model_used', 'N/A')}")
                
                # Add to history
                st.session_state.recommendation_history.append({
                    'query': query,
                    'response': results.get("recommendations", ""),
                    'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                })
                
            except Exception as e:
                st.error(f"❌ Error getting recommendations: {str(e)}")

def history_section():
    """Recommendation history section."""
    if st.session_state.recommendation_history:
        st.markdown('<div class="sub-header">📚 Recommendation History</div>', unsafe_allow_html=True)
        
        # Show recent queries
        for i, entry in enumerate(reversed(st.session_state.recommendation_history[-5:])):
            with st.expander(f"Query {len(st.session_state.recommendation_history) - i}: {entry['query']} ({entry['timestamp']})"):
                st.write(entry['response'])
        
        # Clear history button
        if st.button("🗑️ Clear History"):
            st.session_state.recommendation_history = []
            st.rerun()

def sidebar_info():
    """Sidebar information and controls."""
    st.sidebar.title("🎬 Movie Recommender")
    
    st.sidebar.markdown("### About")
    st.sidebar.info("""
    This is an AI-powered movie recommendation system that uses:
    - **RAG (Retrieval-Augmented Generation)**
    - **Vector similarity search**
    - **OpenAI GPT models**
    """)
    
    st.sidebar.markdown("### Quick Start")
    st.sidebar.write("1. **Quick Connect** (if data exists)")
    st.sidebar.write("2. Or run full pipeline")
    st.sidebar.write("3. Ask for recommendations")
    st.sidebar.write("4. Explore different queries")
    
    st.sidebar.markdown("### Example Queries")
    st.sidebar.write("• I like action movies")
    st.sidebar.write("• Movies similar to Forest Gump")
    st.sidebar.write("• Show me romantic comedies")
    st.sidebar.write("• Sci-fi movies with high ratings")
    
    # System status
    st.sidebar.markdown("### System Status")
    if st.session_state.pipeline_ready:
        st.sidebar.success("✅ Ready")
    else:
        st.sidebar.warning("⚠️ Not Ready")
    
    # Clear all button
    if st.sidebar.button("🔄 Reset All"):
        st.session_state.clear()
        st.rerun()

def main():
    """Main application function."""
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<div class="main-header">🎬 Movie Recommendation System</div>', unsafe_allow_html=True)
    
    # Sidebar
    sidebar_info()
    
    # Main content
    if st.session_state.pipeline_ready:
        # Show success message
        st.markdown('<div class="success-box">🎉 Pipeline is ready! You can now ask for movie recommendations.</div>', unsafe_allow_html=True)
    
    # Pipeline management
    pipeline_management_section()
    
    # Recommendations
    recommendation_section()
    
    # History
    history_section()
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style='text-align: center; color: #666;'>
        Built with ❤️ using Streamlit, LangChain, and OpenAI
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()
