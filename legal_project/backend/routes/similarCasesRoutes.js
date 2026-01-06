const express = require('express');
const router = express.Router();
const Case = require('../models/Case');
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const { processFile, validateFile, detectCaseType } = require('../utils/fileProcessor');

// Configure multer for file uploads
const uploadDir = path.join(__dirname, '../uploads');
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir, { recursive: true });
}

const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, uploadDir);
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, uniqueSuffix + path.extname(file.originalname));
  }
});

const upload = multer({
  storage: storage,
  limits: { fileSize: 25 * 1024 * 1024 }, // 25MB
  fileFilter: function (req, file, cb) {
    const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.odt'];
    const ext = path.extname(file.originalname).toLowerCase();
    
    if (!allowedExtensions.includes(ext)) {
      cb(new Error(`File format not supported. Allowed: ${allowedExtensions.join(', ')}`));
    } else {
      cb(null, true);
    }
  }
});

// Helper function to calculate text similarity using Jaccard index
const calculateSimilarity = (text1, text2) => {
  const set1 = new Set(text1.toLowerCase().split(/\s+/));
  const set2 = new Set(text2.toLowerCase().split(/\s+/));
  
  const intersection = new Set([...set1].filter(x => set2.has(x)));
  const union = new Set([...set1, ...set2]);
  
  return intersection.size / union.size * 100;
};

// @route   POST /api/similar-cases/find
// @desc    Find similar cases using AI model with auto-classification
// @access  Public
router.post('/find', async (req, res) => {
  try {
    const { caseText, caseType, limit = 5, offset = 0 } = req.body;

    if (!caseText) {
      return res.status(400).json({ error: 'Case text is required' });
    }

    // Auto-detect case type if needed
    const detectedType = caseType || detectCaseType(caseText);

    // Search for similar cases - first from same type, then from all types
    let allCases = await Case.find({
      caseType: detectedType
    })
      .limit(100)
      .lean();

    // If not enough cases of same type, also search all cases
    if (allCases.length < 20) {
      const otherCases = await Case.find({
        caseType: { $ne: detectedType }
      })
        .limit(50)
        .lean();
      allCases = [...allCases, ...otherCases];
    }

    // Calculate similarity scores for each case using full text
    const casesWithScores = allCases.map(caseItem => ({
      ...caseItem,
      similarityScore: calculateSimilarity(caseText, caseItem.title + ' ' + caseItem.summary + ' ' + (caseItem.fullText || '').substring(0, 1000))
    }));

    // Sort by similarity score
    const sortedCases = casesWithScores.sort((a, b) => b.similarityScore - a.similarityScore);
    
    // Get total count for pagination
    const totalCount = sortedCases.length;
    
    // Apply pagination
    const paginatedCases = sortedCases
      .slice(offset, offset + limit)
      .map((caseItem, index) => ({
        ...caseItem,
        relevantPoints: caseItem.keyPoints ? caseItem.keyPoints.slice(0, 3) : [],
        matchType: caseItem.similarityScore > 70 ? 'Exact Match' : caseItem.similarityScore > 50 ? 'Strong Match' : 'Relevant Case'
      }));

    const response = {
      found: paginatedCases.length,
      totalFound: totalCount,
      detectedType: detectedType,
      highestMatch: sortedCases[0]?.similarityScore || 0,
      averageMatch: paginatedCases.length > 0
        ? Math.round(paginatedCases.reduce((a, b) => a + b.similarityScore, 0) / paginatedCases.length * 100) / 100
        : 0,
      hasMore: (offset + limit) < totalCount,
      results: paginatedCases
    };

    res.json(response);
  } catch (error) {
    console.error('Error finding similar cases:', error);
    res.status(500).json({ error: 'Error finding similar cases: ' + error.message });
  }
});

// @route   POST /api/similar-cases/auto-analyze
// @desc    Auto-analyze case and return similar cases instantly
// @access  Public
router.post('/auto-analyze', async (req, res) => {
  try {
    const { caseText } = req.body;

    if (!caseText || caseText.trim().length < 20) {
      return res.status(400).json({ error: 'Minimum 20 characters required for auto-analysis' });
    }

    // Detect case type
    const detectedType = detectCaseType(caseText);

    // Find all cases of this type
    const allCases = await Case.find({ caseType: detectedType }).lean();

    // Calculate and rank by similarity
    const casesWithScores = allCases
      .map(caseItem => ({
        ...caseItem,
        similarityScore: calculateSimilarity(caseText, caseItem.title + ' ' + caseItem.summary)
      }))
      .sort((a, b) => b.similarityScore - a.similarityScore)
      .slice(0, 5);

    res.json({
      detectedType,
      autoDetected: true,
      totalFound: casesWithScores.length,
      results: casesWithScores
    });
  } catch (error) {
    console.error('Error in auto-analysis:', error);
    res.status(500).json({ error: 'Error in auto-analysis: ' + error.message });
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

// @route   POST /api/similar-cases/add-case
// @desc    Manually add a case to the database
// @access  Public
router.post('/add-case', async (req, res) => {
  try {
    const { title, summary, caseType, court, year, keyPoints, outcome, fullText } = req.body;

    // Validation
    if (!title || !summary || !caseType) {
      return res.status(400).json({ 
        error: 'Title, summary, and case type are required' 
      });
    }

    // Create new case
    const newCase = new Case({
      caseId: `case_${Date.now()}`,
      title,
      summary,
      caseType,
      court: court || 'Court of Law',
      year: year || new Date().getFullYear(),
      keyPoints: keyPoints || [],
      outcome: outcome || 'Pending',
      fullText: fullText || summary,
      dateAdded: new Date()
    });

    const savedCase = await newCase.save();

    res.status(201).json({
      success: true,
      message: 'Case added to database successfully',
      case: {
        _id: savedCase._id,
        caseId: savedCase.caseId,
        title: savedCase.title,
        summary: savedCase.summary,
        caseType: savedCase.caseType,
        court: savedCase.court,
        year: savedCase.year,
        keyPoints: savedCase.keyPoints,
        outcome: savedCase.outcome,
        dateAdded: savedCase.dateAdded
      }
    });
  } catch (error) {
    console.error('Error adding case:', error);
    res.status(500).json({ error: 'Error adding case: ' + error.message });
  }
});

// @route   GET /api/similar-cases/stored-cases
// @desc    Get all stored cases with analytics
// @access  Public
router.get('/stored-cases', async (req, res) => {
  try {
    const { caseType, page = 1, limit = 10 } = req.query;
    const skip = (page - 1) * limit;

    // Build query
    let query = {};
    if (caseType) {
      query.caseType = caseType;
    }

    // Get cases with pagination
    const cases = await Case.find(query)
      .skip(skip)
      .limit(parseInt(limit))
      .sort({ dateAdded: -1 })
      .lean();

    // Get total count
    const total = await Case.countDocuments(query);

    // Add analytics to each case
    const casesWithAnalytics = cases.map(caseItem => ({
      ...caseItem,
      id: caseItem._id,
      analytics: {
        keyPointsCount: (caseItem.keyPoints || []).length,
        summaryLength: (caseItem.summary || '').length,
        yearsOld: new Date().getFullYear() - (caseItem.year || new Date().getFullYear()),
        contentLength: (caseItem.fullText || '').length
      }
    }));

    res.json({
      success: true,
      total,
      page: parseInt(page),
      pages: Math.ceil(total / limit),
      caseType: caseType || 'All Types',
      cases: casesWithAnalytics
    });
  } catch (error) {
    console.error('Error retrieving cases:', error);
    res.status(500).json({ error: 'Error retrieving cases: ' + error.message });
  }
});

// @route   GET /api/similar-cases/stored-cases/stats
// @desc    Get database statistics
// @access  Public
router.get('/stored-cases/stats', async (req, res) => {
  try {
    const totalCases = await Case.countDocuments();
    
    // Count by case type
    const casesByType = await Case.aggregate([
      {
        $group: {
          _id: '$caseType',
          count: { $sum: 1 }
        }
      },
      { $sort: { count: -1 } }
    ]);

    // Average year
    const stats = await Case.aggregate([
      {
        $group: {
          _id: null,
          avgYear: { $avg: '$year' },
          minYear: { $min: '$year' },
          maxYear: { $max: '$year' }
        }
      }
    ]);

    res.json({
      success: true,
      totalCases,
      casesByType,
      yearStats: stats[0] || { avgYear: 0, minYear: 0, maxYear: 0 }
    });
  } catch (error) {
    console.error('Error getting stats:', error);
    res.status(500).json({ error: 'Error getting statistics: ' + error.message });
  }
});

// @route   DELETE /api/similar-cases/:id
// @desc    Delete a case from database
// @access  Public
router.delete('/:id', async (req, res) => {
  try {
    const { id } = req.params;

    const result = await Case.findByIdAndDelete(id);

    if (!result) {
      return res.status(404).json({ error: 'Case not found' });
    }

    res.json({
      success: true,
      message: 'Case deleted successfully',
      deletedCase: result._id
    });
  } catch (error) {
    console.error('Error deleting case:', error);
    res.status(500).json({ error: 'Error deleting case: ' + error.message });
  }
});

// @route   POST /api/similar-cases/upload-file
// @desc    Upload and convert file to text, detect case type
// @access  Public
router.post('/upload-file', upload.single('file'), async (req, res) => {
  try {
    if (!req.file) {
      return res.status(400).json({ error: 'No file provided' });
    }

    // Validate file
    validateFile(req.file);

    // Process the uploaded file
    const fileProcessingResult = await processFile(req.file.path);

    // Clean up uploaded file after processing
    fs.unlink(req.file.path, (err) => {
      if (err) console.log('File cleanup warning:', err.message);
    });

    // Return results
    res.json({
      success: true,
      extractedText: fileProcessingResult.extractedText,
      detectedType: fileProcessingResult.detectedType,
      fileName: req.file.originalname,
      fileSize: req.file.size,
      characterCount: fileProcessingResult.characterCount,
      format: fileProcessingResult.format,
      message: `Successfully extracted text from ${req.file.originalname}. Detected case type: ${fileProcessingResult.detectedType}`
    });

  } catch (error) {
    // Clean up file if it exists
    if (req.file && req.file.path) {
      fs.unlink(req.file.path, (err) => {
        if (err) console.log('File cleanup error:', err.message);
      });
    }

    console.error('File upload error:', error);
    res.status(400).json({ 
      error: error.message || 'Error processing file. Supported formats: PDF, DOCX, DOC, TXT, RTF, ODT' 
    });
  }
});

module.exports = router;
