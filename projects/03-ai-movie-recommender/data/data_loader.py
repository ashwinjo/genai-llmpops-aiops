import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
import re
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AnimeDataLoader:
    """
    Data loader for anime recommendation system.
    Handles loading, cleaning, and preprocessing of IMDB anime dataset.
    """
    
    def __init__(self, data_path: str = "IMDB_10000.csv"):
        """
        Initialize the data loader.
        
        Args:
            data_path (str): Path to the CSV file
        """
        self.data_path = data_path
        self.df = None
        self.cleaned_df = None
        self.vectorizer = None
        self.scaler = StandardScaler()
        self.label_encoders = {}
        
    def load_data(self) -> pd.DataFrame:
        """
        Load the CSV data file.
        
        Returns:
            pd.DataFrame: Raw dataset
        """
        try:
            logger.info(f"Loading data from {self.data_path}")
            self.df = pd.read_csv(self.data_path)
            logger.info(f"Data loaded successfully. Shape: {self.df.shape}")
            return self.df
        except FileNotFoundError:
            logger.error(f"File not found: {self.data_path}")
            raise
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            raise
    
    def clean_data(self) -> pd.DataFrame:
        """
        Clean and preprocess the dataset.
        
        Returns:
            pd.DataFrame: Cleaned dataset
        """
        if self.df is None:
            self.load_data()
        
        logger.info("Starting data cleaning process...")
        
        # Create a copy for cleaning
        self.cleaned_df = self.df.copy()
        
        # 1. Handle missing values
        self._handle_missing_values()
        
        # 2. Clean text columns
        self._clean_text_columns()
        
        # 3. Extract and clean numerical features
        self._extract_numerical_features()
        
        # 4. Handle categorical variables
        self._encode_categorical_variables()
        
        # 5. Create feature combinations
        self._create_feature_combinations()
        
        # 6. Remove duplicates
        self._remove_duplicates()
        
        logger.info(f"Data cleaning completed. Final shape: {self.cleaned_df.shape}")
        return self.cleaned_df
    
    def _handle_missing_values(self):
        """Handle missing values in the dataset."""
        logger.info("Handling missing values...")
        
        # Fill missing values based on column type
        text_columns = self.cleaned_df.select_dtypes(include=['object']).columns
        numeric_columns = self.cleaned_df.select_dtypes(include=[np.number]).columns
        
        # Fill text columns with 'Unknown'
        for col in text_columns:
            self.cleaned_df[col] = self.cleaned_df[col].fillna('Unknown')
        
        # Fill numeric columns with median
        for col in numeric_columns:
            self.cleaned_df[col] = self.cleaned_df[col].fillna(self.cleaned_df[col].median())
    
    def _clean_text_columns(self):
        """Clean text columns by removing special characters and normalizing."""
        logger.info("Cleaning text columns...")
        
        text_columns = ['title', 'genre', 'description', 'director', 'cast']
        
        for col in text_columns:
            if col in self.cleaned_df.columns:
                # Convert to string and clean
                self.cleaned_df[col] = self.cleaned_df[col].astype(str)
                self.cleaned_df[col] = self.cleaned_df[col].apply(self._clean_text)
    
    def _clean_text(self, text: str) -> str:
        """Clean individual text entries."""
        if pd.isna(text) or text == 'nan':
            return 'Unknown'
        
        # Remove special characters but keep spaces and basic punctuation
        text = re.sub(r'[^\w\s\-.,!?]', '', str(text))
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        # Convert to lowercase
        text = text.lower()
        
        return text if text else 'Unknown'
    
    def _extract_numerical_features(self):
        """Extract and clean numerical features."""
        logger.info("Extracting numerical features...")
        
        # Extract year from title if available
        if 'title' in self.cleaned_df.columns:
            self.cleaned_df['year'] = self.cleaned_df['title'].str.extract(r'\((\d{4})\)')
            self.cleaned_df['year'] = pd.to_numeric(self.cleaned_df['year'], errors='coerce')
            self.cleaned_df['year'] = self.cleaned_df['year'].fillna(self.cleaned_df['year'].median())
        
        # Clean rating column
        if 'rating' in self.cleaned_df.columns:
            self.cleaned_df['rating'] = pd.to_numeric(self.cleaned_df['rating'], errors='coerce')
            self.cleaned_df['rating'] = self.cleaned_df['rating'].fillna(self.cleaned_df['rating'].median())
        
        # Clean votes column
        if 'votes' in self.cleaned_df.columns:
            self.cleaned_df['votes'] = pd.to_numeric(self.cleaned_df['votes'], errors='coerce')
            self.cleaned_df['votes'] = self.cleaned_df['votes'].fillna(self.cleaned_df['votes'].median())
    
    def _encode_categorical_variables(self):
        """Encode categorical variables using Label Encoding."""
        logger.info("Encoding categorical variables...")
        
        categorical_columns = ['genre', 'director']
        
        for col in categorical_columns:
            if col in self.cleaned_df.columns:
                le = LabelEncoder()
                self.cleaned_df[f'{col}_encoded'] = le.fit_transform(self.cleaned_df[col])
                self.label_encoders[col] = le
    
    def _create_feature_combinations(self):
        """Create feature combinations for better recommendations."""
        logger.info("Creating feature combinations...")
        
        # Create genre combinations
        if 'genre' in self.cleaned_df.columns:
            # Split genres and create genre list (convert to string to avoid unhashable type issues)
            self.cleaned_df['genre_list'] = self.cleaned_df['genre'].str.split(',').apply(lambda x: ','.join(x) if isinstance(x, list) else str(x))
            self.cleaned_df['genre_count'] = self.cleaned_df['genre'].str.count(',') + 1
        
        # Create decade feature
        if 'year' in self.cleaned_df.columns:
            self.cleaned_df['decade'] = (self.cleaned_df['year'] // 10) * 10
        
        # Create rating categories
        if 'rating' in self.cleaned_df.columns:
            self.cleaned_df['rating_category'] = pd.cut(
                self.cleaned_df['rating'], 
                bins=[0, 5, 6, 7, 8, 10], 
                labels=['Poor', 'Below Average', 'Average', 'Good', 'Excellent']
            )
        
        # Create combined_info column
        self._create_combined_info_column()
    
    def _remove_duplicates(self):
        """Remove duplicate entries."""
        logger.info("Removing duplicates...")
        initial_count = len(self.cleaned_df)
        
        # Remove duplicates based on key columns, excluding problematic ones
        key_columns = [col for col in self.cleaned_df.columns if col not in ['genre_list']]
        self.cleaned_df = self.cleaned_df.drop_duplicates(subset=key_columns)
        
        final_count = len(self.cleaned_df)
        logger.info(f"Removed {initial_count - final_count} duplicate entries")
    
    def _create_combined_info_column(self):
        """Create a combined_info column with all column names and values."""
        logger.info("Creating combined_info column...")
        
        # Get all columns except the combined_info column itself
        columns_to_combine = [col for col in self.cleaned_df.columns if col != 'combined_info']
        
        # Create the combined_info column
        self.cleaned_df['combined_info'] = self.cleaned_df.apply(
            lambda row: ' '.join([f"{col}: {row[col]}" for col in columns_to_combine if pd.notna(row[col]) and str(row[col]).strip() != '']),
            axis=1
        )
        
        logger.info("combined_info column created successfully")
    
    def save_combined_info_csv(self, output_path: str = "combined_info.csv"):
        """
        Save only the combined_info column to a new CSV file with UTF-8 encoding.
        
        Args:
            output_path (str): Path for the output CSV file
        """
        if self.cleaned_df is None:
            self.clean_data()
        
        if 'combined_info' not in self.cleaned_df.columns:
            logger.error("combined_info column not found. Please run clean_data() first.")
            return
        
        try:
            # Create DataFrame with only combined_info column
            combined_info_df = self.cleaned_df[['combined_info']].copy()
            
            # Save to CSV with UTF-8 encoding
            combined_info_df.to_csv(output_path, index=False, encoding='utf-8')
            
            logger.info(f"Combined info CSV saved successfully to {output_path}")
            logger.info(f"File contains {len(combined_info_df)} rows")
            
        except Exception as e:
            logger.error(f"Error saving combined info CSV: {str(e)}")
            raise
    
    def create_text_features(self, text_column: str = 'description') -> np.ndarray:
        """
        Create TF-IDF features from text column.
        
        Args:
            text_column (str): Column name for text features (default: 'description', can use 'combined_info')
            
        Returns:
            np.ndarray: TF-IDF features
        """
        if self.cleaned_df is None:
            self.clean_data()
        
        logger.info(f"Creating TF-IDF features from {text_column}")
        
        # Initialize TF-IDF vectorizer
        self.vectorizer = TfidfVectorizer(
            max_features=1000,
            stop_words='english',
            ngram_range=(1, 2),
            min_df=2,
            max_df=0.95
        )
        
        # Fit and transform the text data
        text_features = self.vectorizer.fit_transform(self.cleaned_df[text_column])
        
        logger.info(f"TF-IDF features created. Shape: {text_features.shape}")
        return text_features.toarray()
    
    def get_numerical_features(self) -> np.ndarray:
        """
        Get numerical features for the model.
        
        Returns:
            np.ndarray: Numerical features
        """
        if self.cleaned_df is None:
            self.clean_data()
        
        numerical_columns = [
            'year', 'rating', 'votes', 'genre_count', 'decade',
            'genre_encoded', 'director_encoded'
        ]
        
        # Filter columns that exist in the dataset
        available_columns = [col for col in numerical_columns if col in self.cleaned_df.columns]
        
        features = self.cleaned_df[available_columns].values
        
        # Scale the features
        features_scaled = self.scaler.fit_transform(features)
        
        logger.info(f"Numerical features prepared. Shape: {features_scaled.shape}")
        return features_scaled
    
    def save_processed_data(self, output_dir: str = "processed_data"):
        """
        Save processed data and models for production use.
        
        Args:
            output_dir (str): Directory to save processed data
        """
        if self.cleaned_df is None:
            self.clean_data()
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        logger.info(f"Saving processed data to {output_dir}")
        
        # Save cleaned dataset
        self.cleaned_df.to_csv(f"{output_dir}/cleaned_anime_data.csv", index=False)
        
        # Save vectorizer
        if self.vectorizer is not None:
            with open(f"{output_dir}/tfidf_vectorizer.pkl", 'wb') as f:
                pickle.dump(self.vectorizer, f)
        
        # Save scaler
        with open(f"{output_dir}/scaler.pkl", 'wb') as f:
            pickle.dump(self.scaler, f)
        
        # Save label encoders
        with open(f"{output_dir}/label_encoders.pkl", 'wb') as f:
            pickle.dump(self.label_encoders, f)
        
        logger.info("Processed data saved successfully")
    
    def get_recommendation_features(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get all features needed for recommendation system.
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: Text features and numerical features
        """
        if self.cleaned_df is None:
            self.clean_data()
        
        # Create text features
        text_features = self.create_text_features()
        
        # Get numerical features
        numerical_features = self.get_numerical_features()
        
        return text_features, numerical_features
    
    def get_anime_info(self, anime_id: int) -> Dict:
        """
        Get information about a specific anime.
        
        Args:
            anime_id (int): Index of the anime
            
        Returns:
            Dict: Anime information
        """
        if self.cleaned_df is None:
            self.clean_data()
        
        if anime_id >= len(self.cleaned_df):
            raise ValueError(f"Anime ID {anime_id} is out of range")
        
        anime = self.cleaned_df.iloc[anime_id]
        
        return {
            'title': anime.get('title', 'Unknown'),
            'genre': anime.get('genre', 'Unknown'),
            'rating': anime.get('rating', 0),
            'year': anime.get('year', 0),
            'description': anime.get('description', 'No description available'),
            'director': anime.get('director', 'Unknown'),
            'votes': anime.get('votes', 0)
        }

def main():
    """Main function to demonstrate data loading and processing."""
    # Initialize data loader
    loader = AnimeDataLoader()
    
    # Load and clean data
    cleaned_data = loader.clean_data()

    
    # Save processed data
    loader.save_processed_data()
    
    # Save combined_info CSV
    loader.save_combined_info_csv("combined_info.csv")
    
    print("Data processing completed successfully!")
    print(f"Dataset shape: {cleaned_data.shape}")
    print("Combined info CSV created: combined_info.csv")

if __name__ == "__main__":
    main()
