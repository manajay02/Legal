"""
db_setup.py
-----------
Reads legal_cases.csv and loads all case documents into MongoDB.

MongoDB structure:
  Database   : legal_cases_db
  Collection : cases
  Document   : { filename, category, subcategory, text, text_hash }
"""

import os
import hashlib
import pandas as pd
from pymongo import MongoClient, ASCENDING
from tqdm import tqdm

# ── Configuration ────────────────────────────────────────────────────────────
MONGO_URI  = "mongodb+srv://maneth:pathana123@cluster0.thqkj39.mongodb.net/?appName=Cluster0"
DB_NAME    = "legal_cases_db"
COLLECTION = "cases"
CSV_PATH   = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "legal_cases.csv")


def get_db():
    """Return the MongoDB database handle."""
    client = MongoClient(MONGO_URI)
    return client[DB_NAME]


def setup_database():
    print("Connecting to MongoDB...")
    client = MongoClient(MONGO_URI)
    db     = client[DB_NAME]
    col    = db[COLLECTION]

    # Drop existing data so re-runs are idempotent
    col.drop()
    print(f"  Collection '{COLLECTION}' cleared.")

    # Create indexes
    col.create_index([('category',    ASCENDING)])
    col.create_index([('subcategory', ASCENDING)])
    col.create_index([('filename',    ASCENDING)], unique=True)
    col.create_index([('text_hash',   ASCENDING)], unique=True)
    print('  Indexes created.')

    # Load CSV
    print(f"\nLoading CSV: {CSV_PATH}")
    df = pd.read_csv(CSV_PATH, dtype=str)
    df["text"] = df["text"].fillna("")
    df["text_hash"] = df["text"].apply(lambda t: hashlib.sha256(t.encode("utf-8")).hexdigest())
    total = len(df)
    print(f"  {total} records found.")

    # Deduplicate by text_hash (keep first occurrence)
    df = df.drop_duplicates(subset="text_hash", keep="first")
    total = len(df)
    print(f"  {total} unique records after deduplication.")

    # Bulk insert in batches of 500
    BATCH = 500
    inserted = 0
    for start in tqdm(range(0, total, BATCH), desc="Inserting", unit="batch"):
        batch = df.iloc[start:start + BATCH].to_dict(orient="records")
        col.insert_many(batch)
        inserted += len(batch)

    print(f"\nDone! {inserted} documents inserted into '{DB_NAME}.{COLLECTION}'.")

    # Summary per subcategory
    print("\nDocument count by subcategory:")
    pipeline = [
        {"$group": {"_id": {"category": "$category", "subcategory": "$subcategory"},
                    "count": {"$sum": 1}}},
        {"$sort": {"_id.category": 1, "_id.subcategory": 1}}
    ]
    for doc in col.aggregate(pipeline):
        g = doc["_id"]
        print(f"  [{g['category']}] {g['subcategory']}: {doc['count']}")

    client.close()


if __name__ == "__main__":
    setup_database()
