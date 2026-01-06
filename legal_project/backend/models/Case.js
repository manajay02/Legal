const mongoose = require('mongoose');

const caseSchema = new mongoose.Schema({
  title: {
    type: String,
    required: true
  },
  caseNumber: {
    type: String,
    default: ''
  },
  category: {
    type: String,
    required: true,
    enum: ['criminal', 'drug', 'labour', 'family', 'tax', 'environmental', 'financial', 'asset', 'civil', 'contemptofcourt', 'sexualcases', 'sports', 'terrorism']
  },
  content: {
    type: String,
    required: true
  },
  summary: {
    type: String,
    default: ''
  },
  keywords: [{
    type: String
  }],
  dateAdded: {
    type: Date,
    default: Date.now
  },
  source: {
    type: String,
    default: 'database'
  }
});

// Text index for search
caseSchema.index({ title: 'text', content: 'text', summary: 'text' });

module.exports = mongoose.model('Case', caseSchema);
