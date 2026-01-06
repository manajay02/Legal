import React from 'react';

function CaseCard({ case_name, similarity_score, case_type }) {
  const similarityPercent = Math.round(similarity_score * 100);
  
  return (
    <div className="case-result">
      <div className="row align-items-center">
        <div className="col-md-8">
          <h5 className="mb-2">{case_name}</h5>
          <p className="mb-1 text-muted">
            <strong>Category:</strong> <span className="badge bg-info">{case_type}</span>
          </p>
        </div>
        <div className="col-md-4 text-end">
          <span className="similarity-badge">
            {similarityPercent}% Match
          </span>
        </div>
      </div>
    </div>
  );
}

export default CaseCard;
