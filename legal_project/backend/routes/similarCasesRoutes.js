const express = require('express');
const router = express.Router();
const Case = require('../models/Case');

// @route   POST /api/similar-cases/find
// @desc    Find similar cases using AI model
// @access  Public
router.post('/find', async (req, res) => {
  try {
    const { caseText, caseType, limit = 5 } = req.body;

    if (!caseText) {
      return res.status(400).json({ error: 'Case text is required' });
    }

    // Simple text search - in production, use ML embeddings
    const searchResults = await Case.find({
      $or: [
        { title: { $regex: caseText, $options: 'i' } },
        { summary: { $regex: caseText, $options: 'i' } },
        { keyPoints: { $in: [new RegExp(caseText, 'i')] } }
      ],
      ...(caseType && { caseType })
    })
      .limit(limit + 5)
      .sort({ year: -1 })
      .lean();

    // Calculate similarity scores (mock implementation)
    const similarCases = searchResults.slice(0, limit).map((caseItem, index) => ({
      ...caseItem,
      similarityScore: Math.round((85 - index * 5) * 100) / 100,
      relevantPoints: caseItem.keyPoints ? caseItem.keyPoints.slice(0, 3) : [],
      matchType: index === 0 ? 'Exact Match' : 'Relevant Case'
    }));

    res.json({
      found: similarCases.length,
      highestMatch: similarCases[0]?.similarityScore || 0,
      averageMatch: similarCases.length > 0
        ? Math.round(similarCases.reduce((a, b) => a + b.similarityScore, 0) / similarCases.length * 100) / 100
        : 0,
      results: similarCases
    });
  } catch (error) {
    console.error('Error finding similar cases:', error);
    res.status(500).json({ error: 'Error finding similar cases: ' + error.message });
  }
});

// @route   GET /api/similar-cases
// @desc    Get all cases
// @access  Public
router.get('/', async (req, res) => {
  try {
    const { caseType, page = 1, limit = 10 } = req.query;
    const skip = (page - 1) * limit;

    let query = {};
    if (caseType) {
      query.caseType = caseType;
    }

    const cases = await Case.find(query)
      .skip(skip)
      .limit(parseInt(limit))
      .sort({ year: -1 });

    const total = await Case.countDocuments(query);

    res.json({
      total,
      page: parseInt(page),
      pages: Math.ceil(total / limit),
      results: cases
    });
  } catch (error) {
    res.status(500).json({ error: 'Error retrieving cases: ' + error.message });
  }
});

// @route   GET /api/similar-cases/:id
// @desc    Get case by ID
// @access  Public
router.get('/:id', async (req, res) => {
  try {
    const caseItem = await Case.findById(req.params.id);
    if (!caseItem) {
      return res.status(404).json({ error: 'Case not found' });
    }
    res.json(caseItem);
  } catch (error) {
    res.status(500).json({ error: 'Error retrieving case: ' + error.message });
  }
});

// @route   POST /api/similar-cases/upload
// @desc    Upload and classify a new case
// @access  Public
router.post('/upload', async (req, res) => {
  try {
    const { caseText, title, caseType, court, year } = req.body;

    if (!caseText || !title) {
      return res.status(400).json({ error: 'Case text and title are required' });
    }

    const newCase = new Case({
      caseId: `case_${Date.now()}`,
      title,
      caseType: caseType || 'Civil',
      court: court || 'Court of Law',
      year: year || new Date().getFullYear(),
      summary: caseText.substring(0, 500),
      fullText: caseText
    });

    const savedCase = await newCase.save();

    res.status(201).json({
      message: 'Case uploaded successfully',
      caseId: savedCase._id,
      case: savedCase
    });
  } catch (error) {
    res.status(500).json({ error: 'Error uploading case: ' + error.message });
  }
});

module.exports = router;
