const express = require('express');
const router = express.Router();

// @route   GET /api/cases
// @desc    Get all cases
// @access  Public
router.get('/', (req, res) => {
  res.json({ message: 'Get all cases' });
});

// @route   POST /api/cases/upload
// @desc    Upload PDF and extract text
// @access  Public
router.post('/upload', (req, res) => {
  try {
    res.status(200).json({
      message: 'Case uploaded successfully',
      caseId: `case_${Date.now()}`
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// @route   POST /api/cases/classify
// @desc    Classify case using ML model
// @access  Public
router.post('/classify', (req, res) => {
  try {
    const { caseText } = req.body;
    
    if (!caseText) {
      return res.status(400).json({ error: 'Case text is required' });
    }

    // Mock classification - replace with actual ML model
    const classification = {
      caseType: 'Civil',
      confidence: 0.92,
      tags: ['contract', 'dispute', 'damages']
    };

    res.json(classification);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
