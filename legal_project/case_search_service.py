#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class CaseDatabase:
    def __init__(self):
        self.cases = []
        self.tfidf_vectorizer = None
        self.case_vectors = None
        self.load_cases()
        self.build_vectorizer()

    def load_cases(self):
        """Load all cases from extracted_text directory"""
        extracted_text_dir = Path(__file__).parent / 'extracted_text'
        
        if not extracted_text_dir.exists():
            return

        for case_file in sorted(extracted_text_dir.glob('*.txt')):
            try:
                with open(case_file, 'r', encoding='utf-8', errors='ignore') as f:
                    text = f.read().strip()
                    if len(text) > 100:
                        case_name = case_file.stem.replace('.txt', '')
                        case_type = self.classify_case_type(text)
                        self.cases.append({
                            'name': case_name,
                            'type': case_type,
                            'text': text[:5000],
                            'preview': text[:200]
                        })
            except Exception:
                continue

    def classify_case_type(self, text):
        """Classify case type based on keywords"""
        text_lower = text.lower()
        
        case_type_keywords = {
            'criminal': ['criminal', 'crime', 'theft', 'assault', 'murder', 'conviction', 'prosecution', 'police', 'arrest'],
            'drug': ['drug', 'narcotics', 'possession', 'trafficking', 'cocaine', 'heroin'],
            'civil': ['civil', 'contract', 'property', 'tort', 'plaintiff', 'defendant', 'suit'],
            'family': ['family', 'marriage', 'divorce', 'custody', 'child', 'alimony'],
            'labour': ['labour', 'employment', 'worker', 'wage', 'termination', 'discrimination'],
            'tax': ['tax', 'revenue', 'income', 'assessment', 'tariff'],
            'environmental': ['environmental', 'pollution', 'conservation', 'wildlife', 'forest'],
            'financial': ['financial', 'fraud', 'investment', 'securities', 'bank'],
            'terrorism': ['terrorism', 'terrorist', 'extremism', 'sedition'],
            'sports': ['sports', 'athlete', 'competition', 'doping'],
            'contemptofcourt': ['contempt', 'defiance', 'wilful', 'disobey'],
            'asset': ['asset', 'property', 'ownership', 'title', 'real estate'],
            'sexualcases': ['sexual', 'assault', 'harassment', 'rape', 'abuse']
        }
        
        best_type = 'general'
        best_score = 0
        
        for case_type, keywords in case_type_keywords.items():
            score = sum(text_lower.count(kw) for kw in keywords)
            if score > best_score:
                best_score = score
                best_type = case_type
        
        return best_type

    def build_vectorizer(self):
        """Build TF-IDF vectorizer from all cases"""
        if not self.cases:
            return
        
        texts = [case['text'] for case in self.cases]
        self.tfidf_vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.case_vectors = self.tfidf_vectorizer.fit_transform(texts)

    def find_similar(self, query_text, case_type='', top_n=10):
        """Find similar cases using TF-IDF"""
        if not self.cases or self.tfidf_vectorizer is None:
            return []

        try:
            query_vector = self.tfidf_vectorizer.transform([query_text])
            similarities = cosine_similarity(query_vector, self.case_vectors)[0]
            
            results = []
            for idx, similarity in enumerate(similarities):
                case = self.cases[idx]
                score = float(similarity) * 100
                
                # Filter by case type if specified
                if case_type and case['type'] != case_type:
                    continue
                
                if score > 0:
                    results.append({
                        'case_name': case['name'],
                        'case_type': case['type'],
                        'similarity_score': round(score, 2),
                        'preview': case['preview'][:150]
                    })
            
            # Sort by similarity score descending
            results.sort(key=lambda x: x['similarity_score'], reverse=True)
            return results[:top_n]
        except Exception:
            return []


def main():
    try:
        # Read input from stdin
        input_data = json.load(sys.stdin)
        query_text = input_data.get('query_text', '')
        case_type = input_data.get('case_type', '')
        
        # Load database and find similar cases
        db = CaseDatabase()
        similar_cases = db.find_similar(query_text, case_type)
        
        # Output results as JSON
        print(json.dumps(similar_cases))
        
    except Exception:
        print(json.dumps([]))


if __name__ == '__main__':
    main()

    if len(sys.argv) > 1:
        query = sys.argv[1]
        case_type = sys.argv[2] if len(sys.argv) > 2 else None
        
        results = search_similar_cases(query, case_type, top_n=10)
        
        output = []
        for case in results:
            output.append({
                'case_name': case['name'],
                'case_type': case['type'],
                'similarity_score': case['similarity_score'],
                'preview': case['text'][:200]
            })
        
        print(json.dumps(output))
    else:
        # Test mode
        db = get_database()
        print(f"\n📊 Database contains {len(db.cases)} cases")
        print(f"Case type distribution:")
        type_dist = {}
        for case in db.cases:
            type_dist[case['type']] = type_dist.get(case['type'], 0) + 1
        for ctype, count in sorted(type_dist.items()):
            print(f"  {ctype}: {count}")
