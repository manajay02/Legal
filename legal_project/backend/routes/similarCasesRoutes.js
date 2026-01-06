const express = require('express');
const router = express.Router();
const Case = require('../models/Case');

// Calculate Jaccard similarity between two texts
function calculateSimilarity(text1, text2) {
  const getWords = (text) => {
    return new Set(
      text.toLowerCase()
        .replace(/[^\w\s]/g, '')
        .split(/\s+/)
        .filter(word => word.length > 2)
    );
  };
  
  const words1 = getWords(text1);
  const words2 = getWords(text2);
  
  const intersection = new Set([...words1].filter(x => words2.has(x)));
  const union = new Set([...words1, ...words2]);
  
  return union.size > 0 ? intersection.size / union.size : 0;
}

// POST /api/similar - Find similar cases
router.post('/', async (req, res) => {
  try {
    const { text, category, limit = 10, page = 1 } = req.body;
    
    if (!text) {
      return res.status(400).json({ error: 'Text is required' });
    }
    
    // Get cases to compare against
    let query = {};
    if (category && category !== 'all') {
      query.category = category;
    }
    
    const allCases = await Case.find(query);
    
    // Calculate similarity for each case
    const casesWithSimilarity = allCases.map(caseDoc => ({
      _id: caseDoc._id,
      title: caseDoc.title,
      caseNumber: caseDoc.caseNumber,
      category: caseDoc.category,
      content: caseDoc.content,
      summary: caseDoc.summary,
      similarity: calculateSimilarity(text, caseDoc.content)
    }));
    
    // Sort by similarity (highest first)
    casesWithSimilarity.sort((a, b) => b.similarity - a.similarity);
    
    // Pagination
    const startIndex = (parseInt(page) - 1) * parseInt(limit);
    const paginatedCases = casesWithSimilarity.slice(startIndex, startIndex + parseInt(limit));
    
    // Get category statistics
    const categoryStats = {};
    casesWithSimilarity.forEach(c => {
      if (!categoryStats[c.category]) {
        categoryStats[c.category] = 0;
      }
      categoryStats[c.category]++;
    });
    
    res.json({
      similarCases: paginatedCases,
      total: casesWithSimilarity.length,
      page: parseInt(page),
      totalPages: Math.ceil(casesWithSimilarity.length / parseInt(limit)),
      categoryStats
    });
  } catch (error) {
    console.error('Error finding similar cases:', error);
    res.status(500).json({ error: 'Failed to find similar cases' });
  }
});

module.exports = router;
