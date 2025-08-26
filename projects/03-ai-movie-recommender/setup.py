from setuptools import setup, find_packages

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setup(
    name="movie-recommender",
    version="0.1.0",
    description="AI-powered Movie Recommendation System using RAG and Vector Search",
    author="Ashwjosh",
    author_email="your.email@example.com",
    packages=find_packages(),
    install_requires=requirements,
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="movie recommendation ai rag vector-search streamlit",
    project_urls={
        "Source": "https://github.com/yourusername/movie-recommender",
        "Documentation": "https://github.com/yourusername/movie-recommender#readme",
    },
)
