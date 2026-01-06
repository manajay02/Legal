const express = require('express');
const router = express.Router();
const Case = require('../models/Case');

// Helper function to detect case type from text
const detectCaseType = (text) => {
  const keywords = {
    'Civil': ['civil', 'contract', 'property', 'dispute', 'plaintiff', 'defendant', 'damages', 'breach', 'agreement', 'negligence', 'tort', 'liability', 'claim'],
    'Criminal': ['criminal', 'crime', 'offence', 'accused', 'prosecution', 'conviction', 'sentence', 'jail', 'punishment', 'penal', 'guilty', 'defence'],
    'Labour': ['labour', 'labor', 'employment', 'worker', 'wage', 'dismissal', 'termination', 'strike', 'union', 'workman', 'compensation', 'industrial'],
    'Family': ['family', 'divorce', 'marriage', 'custody', 'child', 'alimony', 'succession', 'inheritance', 'guardian', 'adoption', 'will'],
    'Financial': ['financial', 'banking', 'loan', 'debt', 'interest', 'mortgage', 'investment', 'fraud', 'insolvency', 'bankruptcy', 'credit'],
    'Drug': ['drug', 'narcotic', 'cannabis', 'heroin', 'cocaine', 'mdma', 'substance', 'possession', 'trafficking', 'smuggle', 'illegal'],
    'Environmental': ['environmental', 'pollution', 'waste', 'emission', 'water', 'forest', 'species', 'green', 'ecology', 'climate', 'conservation'],
    'Tax': ['tax', 'income', 'revenue', 'assessment', 'deduction', 'exemption', 'duty', 'tariff', 'customs', 'gst', 'tds'],
    'Terrorism': ['terrorism', 'terror', 'terrorist', 'pota', 'national security', 'threat', 'extremist', 'bomb', 'attack'],
    'Sexual Cases': ['sexual', 'rape', 'assault', 'harassment', 'abuse', 'minor', 'child', 'molestation', 'pornography'],
    'Sports': ['sports', 'athletics', 'match', 'doping', 'player', 'contract', 'tournament', 'federation'],
    'Asset': ['asset', 'property', 'possession', 'recovery', 'fraud', 'forfeiture', 'claim', 'stolen'],
    'Contempt of Court': ['contempt', 'court', 'disobey', 'judge', 'disrespect', 'violation', 'order']
  };

  const lowerText = text.toLowerCase();
  let detectedType = 'Civil'; // default
  let maxMatches = 0;

  for (const [type, words] of Object.entries(keywords)) {
    const matches = words.filter(word => lowerText.includes(word)).length;
    if (matches > maxMatches) {
      maxMatches = matches;
      detectedType = type;
    }
  }

  // Calculate confidence based on keyword matches
  const confidence = Math.min(100, (maxMatches / 5) * 100) / 100;

  return { type: detectedType, confidence, matches: maxMatches };
};

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
// @desc    Classify case using intelligent detection
// @access  Public
router.post('/classify', (req, res) => {
  try {
    const { caseText } = req.body;
    
    if (!caseText) {
      return res.status(400).json({ error: 'Case text is required' });
    }

    // Intelligent case type detection
    const { type, confidence, matches } = detectCaseType(caseText);
    
    // Validation: Reject files that are not legal cases
    const CONFIDENCE_THRESHOLD = 0.2; // 20% confidence minimum
    if (confidence < CONFIDENCE_THRESHOLD || matches < 2) {
      return res.status(400).json({ 
        error: 'not a legal case',
        message: 'The uploaded document does not appear to be a legal case. Please upload a valid legal document.',
        confidence: confidence,
        matches: matches
      });
    }
    
    // Extract keywords for tags
    const keywords = caseText
      .toLowerCase()
      .split(/[,.\s]+/)
      .filter(word => word.length > 4)
      .slice(0, 5);

    res.json({
      predictedType: type,
      caseType: type,
      confidence: confidence,
      keywordMatches: matches,
      tags: keywords,
      message: `Case auto-detected as ${type} case with ${Math.round(confidence * 100)}% confidence`
    });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// @route   GET /api/cases/check/:id
// @desc    Check if a case exists in database
// @access  Public
router.get('/check/:id', async (req, res) => {
  try {
    const caseExists = await Case.findById(req.params.id);
    res.json({ exists: !!caseExists });
  } catch (error) {
    // If ID format is invalid, check by title
    res.json({ exists: false });
  }
});

// @route   POST /api/cases
// @desc    Add a new case to the database
// @access  Public
router.post('/', async (req, res) => {
  try {
    const { title, caseType, court, year, outcome, content, relevantPoints } = req.body;
    
    // Check if case with same title already exists
    const existingCase = await Case.findOne({ title: title });
    if (existingCase) {
      return res.status(400).json({ error: 'Case already exists in library', exists: true });
    }
    
    const newCase = new Case({
      title,
      caseType,
      court,
      year,
      outcome,
      content,
      relevantPoints: relevantPoints || []
    });
    
    await newCase.save();
    res.status(201).json({ message: 'Case added to library', case: newCase });
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

// @route   GET /api/cases/library
// @desc    Get all cases in library
// @access  Public
router.get('/library', async (req, res) => {
  try {
    const cases = await Case.find().sort({ createdAt: -1 });
    res.json(cases);
  } catch (error) {
    res.status(500).json({ error: error.message });
  }
});

module.exports = router;
