from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId
import os

# MongoDB Connection
MONGODB_URL = "mongodb+srv://chamathka:chamathka123@studentmanagementsystem.liuiv0a.mongodb.net/?appName=studentmanagementsystem"
DB_NAME = "civil_compliance_auditor"

# Initialize MongoDB client
client = MongoClient(MONGODB_URL)
db = client[DB_NAME]

# Collections
documents_collection = db["documents"]
analysis_results_collection = db["analysis_results"]


def save_document_analysis(file_name: str, file_type: str, extracted_text: str, 
                           analysis_result: dict, user_id: str = "default_user"):
    """
    Save document and its analysis result to MongoDB
    """
    # Create document record
    document_record = {
        "user_id": user_id,
        "file_name": file_name,
        "file_type": file_type,
        "extracted_text": extracted_text[:5000] if extracted_text else "",  # Store first 5000 chars
        "text_length": len(extracted_text) if extracted_text else 0,
        "uploaded_at": datetime.utcnow(),
        "analysis_result": {
            "domain": analysis_result.get("domain", "unknown"),
            "clauses": analysis_result.get("clauses", []),
            "missing_mandatory": analysis_result.get("missing_mandatory", []),
            "total_clauses": len(analysis_result.get("clauses", [])),
            "compliant_count": len([c for c in analysis_result.get("clauses", []) if c.get("status") == "🟢 Compliant"]),
            "violation_count": len([c for c in analysis_result.get("clauses", []) if c.get("status") == "🔴 Violation"]),
        },
        "compliance_percentage": calculate_compliance_percentage(analysis_result)
    }
    
    result = documents_collection.insert_one(document_record)
    return str(result.inserted_id)


def calculate_compliance_percentage(analysis_result: dict) -> float:
    """Calculate compliance percentage from analysis result"""
    clauses = analysis_result.get("clauses", [])
    if not clauses:
        return 0.0
    
    compliant = len([c for c in clauses if c.get("status") == "🟢 Compliant"])
    return round((compliant / len(clauses)) * 100, 2)


def get_user_history(user_id: str = "default_user", limit: int = 50):
    """
    Get user's document analysis history
    """
    cursor = documents_collection.find(
        {"user_id": user_id},
        {
            "_id": 1,
            "file_name": 1,
            "file_type": 1,
            "uploaded_at": 1,
            "analysis_result.domain": 1,
            "analysis_result.total_clauses": 1,
            "analysis_result.compliant_count": 1,
            "analysis_result.violation_count": 1,
            "compliance_percentage": 1,
            "text_length": 1
        }
    ).sort("uploaded_at", -1).limit(limit)
    
    history = []
    for doc in cursor:
        doc["_id"] = str(doc["_id"])
        doc["uploaded_at"] = doc["uploaded_at"].isoformat() if doc.get("uploaded_at") else None
        history.append(doc)
    
    return history


def get_document_by_id(document_id: str):
    """
    Get a specific document analysis by ID
    """
    try:
        doc = documents_collection.find_one({"_id": ObjectId(document_id)})
        if doc:
            doc["_id"] = str(doc["_id"])
            doc["uploaded_at"] = doc["uploaded_at"].isoformat() if doc.get("uploaded_at") else None
        return doc
    except Exception as e:
        print(f"Error fetching document: {e}")
        return None


def delete_document(document_id: str, user_id: str = "default_user"):
    """
    Delete a document from history
    """
    try:
        result = documents_collection.delete_one({
            "_id": ObjectId(document_id),
            "user_id": user_id
        })
        return result.deleted_count > 0
    except Exception as e:
        print(f"Error deleting document: {e}")
        return False


def get_user_statistics(user_id: str = "default_user"):
    """
    Get user's overall statistics
    """
    pipeline = [
        {"$match": {"user_id": user_id}},
        {"$group": {
            "_id": None,
            "total_documents": {"$sum": 1},
            "avg_compliance": {"$avg": "$compliance_percentage"},
            "total_clauses_analyzed": {"$sum": "$analysis_result.total_clauses"},
            "total_violations": {"$sum": "$analysis_result.violation_count"},
            "total_compliant": {"$sum": "$analysis_result.compliant_count"}
        }}
    ]
    
    result = list(documents_collection.aggregate(pipeline))
    if result:
        stats = result[0]
        stats.pop("_id", None)
        stats["avg_compliance"] = round(stats.get("avg_compliance", 0) or 0, 2)
        return stats
    
    return {
        "total_documents": 0,
        "avg_compliance": 0,
        "total_clauses_analyzed": 0,
        "total_violations": 0,
        "total_compliant": 0
    }
