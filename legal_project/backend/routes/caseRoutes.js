const express = require('express');
const router = express.Router();
const Case = require('../models/Case');

// GET /api/cases - Get all cases with optional filtering
router.get('/', async (req, res) => {
  try {
    const { category, search, page = 1, limit = 20 } = req.query;
    
    let query = {};
    
    if (category && category !== 'all') {
      query.category = category;
    }
    
    if (search) {
      query.$text = { $search: search };
    }
    
    const skip = (parseInt(page) - 1) * parseInt(limit);
    
    const cases = await Case.find(query)
      .sort({ dateAdded: -1 })
      .skip(skip)
      .limit(parseInt(limit));
    
    const total = await Case.countDocuments(query);
    
    res.json({
      cases,
      total,
      page: parseInt(page),
      totalPages: Math.ceil(total / parseInt(limit))
    });
  } catch (error) {
    console.error('Error fetching cases:', error);
    res.status(500).json({ error: 'Failed to fetch cases' });
  }
});

// GET /api/cases/stats - Get statistics
router.get('/stats', async (req, res) => {
  try {
    const totalCases = await Case.countDocuments();
    const categories = await Case.aggregate([
      { $group: { _id: '$category', count: { $sum: 1 } } },
      { $sort: { count: -1 } }
    ]);
    
    res.json({
      totalCases,
      categories: categories.map(c => ({ name: c._id, count: c.count }))
    });
  } catch (error) {
    console.error('Error fetching stats:', error);
    res.status(500).json({ error: 'Failed to fetch statistics' });
  }
});

// GET /api/cases/check - Check if case exists
router.get('/check', async (req, res) => {
  try {
    const { title, content } = req.query;
    
    let query = {};
    if (title) {
      query.title = title;
    }
    if (content) {
      // Check by content similarity (first 500 chars)
      const contentPrefix = content.substring(0, 500);
      query.content = { $regex: contentPrefix.substring(0, 100), $options: 'i' };
    }
    
    const existingCase = await Case.findOne(query);
    
    res.json({
      exists: !!existingCase,
      case: existingCase ? { _id: existingCase._id, title: existingCase.title } : null
    });
  } catch (error) {
    console.error('Error checking case:', error);
    res.status(500).json({ error: 'Failed to check case' });
  }
});

// GET /api/cases/:id - Get single case
router.get('/:id', async (req, res) => {
  try {
    const caseDoc = await Case.findById(req.params.id);
    if (!caseDoc) {
      return res.status(404).json({ error: 'Case not found' });
    }
    res.json(caseDoc);
  } catch (error) {
    console.error('Error fetching case:', error);
    res.status(500).json({ error: 'Failed to fetch case' });
  }
});

// POST /api/cases - Add new case
router.post('/', async (req, res) => {
  try {
    const { title, caseNumber, category, content, summary, keywords } = req.body;
    
    if (!title || !category || !content) {
      return res.status(400).json({ error: 'Title, category, and content are required' });
    }
    
    const newCase = new Case({
      title,
      caseNumber: caseNumber || '',
      category,
      content,
      summary: summary || '',
      keywords: keywords || [],
      source: 'user-upload'
    });
    
    await newCase.save();
    
    res.status(201).json({
      success: true,
      message: 'Case added successfully',
      case: newCase
    });
  } catch (error) {
    console.error('Error adding case:', error);
    res.status(500).json({ error: 'Failed to add case' });
  }
});

// DELETE /api/cases/:id - Delete case
router.delete('/:id', async (req, res) => {
  try {
    const result = await Case.findByIdAndDelete(req.params.id);
    if (!result) {
      return res.status(404).json({ error: 'Case not found' });
    }
    res.json({ success: true, message: 'Case deleted successfully' });
  } catch (error) {
    console.error('Error deleting case:', error);
    res.status(500).json({ error: 'Failed to delete case' });
  }
});

module.exports = router;
