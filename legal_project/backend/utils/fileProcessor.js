const fs = require('fs');
const path = require('path');

// Import file processing libraries
let pdfParse;
let mammoth;

try {
  pdfParse = require('pdf-parse');
} catch (err) {
  console.log('pdf-parse not installed');
}

try {
  mammoth = require('mammoth');
} catch (err) {
  console.log('mammoth not installed');
}

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

  return detectedType;
};

/**
 * Process PDF file and extract text
 */
const processPDF = async (filePath) => {
  try {
    if (!pdfParse) {
      throw new Error('pdf-parse library not available');
    }

    const fileBuffer = fs.readFileSync(filePath);
    const data = await pdfParse(fileBuffer);
    
    // Extract text from PDF
    let text = data.text || '';
    
    // Clean up text
    text = text
      .replace(/\s+/g, ' ') // Replace multiple spaces with single space
      .replace(/\n+/g, '\n') // Replace multiple newlines with single newline
      .trim();

    return text;
  } catch (error) {
    throw new Error(`PDF processing error: ${error.message}`);
  }
};

/**
 * Process DOCX file and extract text
 */
const processDOCX = async (filePath) => {
  try {
    if (!mammoth) {
      throw new Error('mammoth library not available');
    }

    const result = await mammoth.extractRawText({ path: filePath });
    let text = result.value || '';
    
    // Clean up text
    text = text
      .replace(/\s+/g, ' ')
      .replace(/\n+/g, '\n')
      .trim();

    return text;
  } catch (error) {
    throw new Error(`DOCX processing error: ${error.message}`);
  }
};

/**
 * Process TXT file and extract text
 */
const processTXT = async (filePath) => {
  try {
    const text = fs.readFileSync(filePath, 'utf8');
    return text
      .replace(/\s+/g, ' ')
      .replace(/\n+/g, '\n')
      .trim();
  } catch (error) {
    throw new Error(`TXT processing error: ${error.message}`);
  }
};

/**
 * Process RTF file and extract text (simplified)
 */
const processRTF = async (filePath) => {
  try {
    let text = fs.readFileSync(filePath, 'utf8');
    
    // Remove RTF control sequences
    text = text
      .replace(/\\[a-z0-9]+\s*/gi, ' ')
      .replace(/[{}]/g, '')
      .replace(/\s+/g, ' ')
      .trim();

    return text;
  } catch (error) {
    throw new Error(`RTF processing error: ${error.message}`);
  }
};

/**
 * Process ODT file (basic text extraction)
 */
const processODT = async (filePath) => {
  try {
    // ODT is a ZIP file, for now use basic extraction
    let text = fs.readFileSync(filePath, 'utf8');
    
    // Extract text content between specific patterns
    text = text
      .replace(/<[^>]*>/g, ' ') // Remove XML tags
      .replace(/\s+/g, ' ')
      .trim();

    return text;
  } catch (error) {
    throw new Error(`ODT processing error: ${error.message}`);
  }
};

/**
 * Main function to process files based on extension
 */
const processFile = async (filePath) => {
  try {
    const ext = path.extname(filePath).toLowerCase();
    let extractedText = '';

    switch (ext) {
      case '.pdf':
        extractedText = await processPDF(filePath);
        break;
      case '.docx':
        extractedText = await processDOCX(filePath);
        break;
      case '.doc':
        // Try DOCX processor for older Word format
        extractedText = await processDOCX(filePath);
        break;
      case '.txt':
        extractedText = await processTXT(filePath);
        break;
      case '.rtf':
        extractedText = await processRTF(filePath);
        break;
      case '.odt':
        extractedText = await processODT(filePath);
        break;
      default:
        throw new Error(`Unsupported file format: ${ext}`);
    }

    if (!extractedText || extractedText.length === 0) {
      throw new Error('No text could be extracted from the file');
    }

    // Detect case type from extracted text
    const detectedType = detectCaseType(extractedText);

    return {
      success: true,
      extractedText,
      detectedType,
      characterCount: extractedText.length,
      format: ext
    };
  } catch (error) {
    throw new Error(`File processing failed: ${error.message}`);
  }
};

/**
 * Validate file before processing
 */
const validateFile = (file, maxSizeInMB = 25) => {
  const allowedExtensions = ['.pdf', '.docx', '.doc', '.txt', '.rtf', '.odt'];
  const maxSizeInBytes = maxSizeInMB * 1024 * 1024;

  if (!file) {
    throw new Error('No file provided');
  }

  const ext = path.extname(file.originalname).toLowerCase();
  if (!allowedExtensions.includes(ext)) {
    throw new Error(`File format not supported. Allowed: ${allowedExtensions.join(', ')}`);
  }

  if (file.size > maxSizeInBytes) {
    throw new Error(`File size exceeds ${maxSizeInMB}MB limit`);
  }

  return true;
};

module.exports = {
  processFile,
  validateFile,
  detectCaseType,
  processPDF,
  processDOCX,
  processTXT,
  processRTF,
  processODT
};
