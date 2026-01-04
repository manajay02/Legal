const mongoose = require('mongoose');

const CaseSchema = new mongoose.Schema(
  {
    caseId: {
      type: String,
      required: true,
      unique: true,
      index: true
    },
    title: {
      type: String,
      required: true,
      index: true
    },
    caseType: {
      type: String,
      enum: ['Civil', 'Criminal', 'Labour', 'Family', 'Financial', 'Drug', 'Environmental', 'Asset', 'Contempt of Court', 'Sexual Cases', 'Sports', 'Tax', 'Terrorism'],
      required: true,
      index: true
    },
    court: {
      type: String,
      required: true
    },
    year: {
      type: Number,
      required: true
    },
    outcome: {
      type: String,
      enum: ['Won', 'Lost', 'Settled', 'Dismissed', 'Pending'],
      default: 'Pending'
    },
    summary: {
      type: String,
      required: true
    },
    fullText: {
      type: String,
      required: true
    },
    relevantLaws: [
      {
        type: String
      }
    ],
    citedCases: [
      {
        type: String
      }
    ],
    keyPoints: [
      {
        type: String
      }
    ],
    judge: String,
    advocates: [String],
    parties: {
      plaintiff: String,
      defendant: String
    },
    location: String,
    fileUrl: String,
    tags: [String],
    embeddings: {
      type: [Number],
      index: '2dsphere'
    },
    textEmbedding: [Number],
    uploadedAt: {
      type: Date,
      default: Date.now,
      index: true
    },
    updatedAt: {
      type: Date,
      default: Date.now
    }
  },
  { timestamps: true }
);

// Index for text search
CaseSchema.index({ title: 'text', summary: 'text', fullText: 'text' });

// Index for case type and year search
CaseSchema.index({ caseType: 1, year: -1 });

module.exports = mongoose.model('Case', CaseSchema);
