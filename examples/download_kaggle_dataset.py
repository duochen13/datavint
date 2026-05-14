"""
Download and explore Kaggle Book Recommendation Dataset
"""
import kagglehub
import pandas as pd
import os

# Download latest version
print("📥 Downloading book recommendation dataset from Kaggle...")
path = kagglehub.dataset_download("arashnic/book-recommendation-dataset")

print(f"✅ Path to dataset files: {path}")
print(f"\n📁 Files in dataset:")
for file in os.listdir(path):
    file_path = os.path.join(path, file)
    size_mb = os.path.getsize(file_path) / (1024 * 1024)
    print(f"  - {file} ({size_mb:.2f} MB)")

# Explore the dataset
print("\n📊 Exploring dataset structure...")

# Load ratings (likely the main file for recommendations)
ratings_file = os.path.join(path, "Ratings.csv")
if os.path.exists(ratings_file):
    print(f"\n=== Ratings.csv ===")
    df_ratings = pd.read_csv(ratings_file, nrows=10000)  # Sample for quick exploration
    print(f"Shape: {df_ratings.shape}")
    print(f"Columns: {df_ratings.columns.tolist()}")
    print(f"\nFirst 5 rows:")
    print(df_ratings.head())
    print(f"\nData types:")
    print(df_ratings.dtypes)
    print(f"\nMissing values:")
    print(df_ratings.isna().sum())

# Load books
books_file = os.path.join(path, "Books.csv")
if os.path.exists(books_file):
    print(f"\n=== Books.csv ===")
    df_books = pd.read_csv(books_file, nrows=1000)
    print(f"Shape: {df_books.shape}")
    print(f"Columns: {df_books.columns.tolist()}")
    print(f"\nFirst 5 rows:")
    print(df_books.head())

# Load users
users_file = os.path.join(path, "Users.csv")
if os.path.exists(users_file):
    print(f"\n=== Users.csv ===")
    df_users = pd.read_csv(users_file, nrows=1000)
    print(f"Shape: {df_users.shape}")
    print(f"Columns: {df_users.columns.tolist()}")
    print(f"\nFirst 5 rows:")
    print(df_users.head())

print(f"\n✅ Dataset exploration complete!")
print(f"\n💡 Use this path in your experiment:")
print(f"   {path}")
