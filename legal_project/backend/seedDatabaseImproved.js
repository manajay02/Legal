const mongoose = require('mongoose');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const Case = require('./models/Case');

// Directories
const EXTRACTED_TEXT_DIR = path.join(__dirname, '../extracted_text');
const DATASET_DIR = path.join(__dirname, '../dataset');

// Case type mapping
const typeMapping = {
  'civil': 'Civil',
  'criminal': 'Criminal',
  'labour': 'Labour',
  'family': 'Family',
  'financial': 'Financial',
  'drug': 'Drug',
  'environmental': 'Environmental',
  'asset': 'Asset',
  'contemptofcourt': 'Contempt of Court',
  'sexualcases': 'Sexual Cases',
  'sports': 'Sports',
  'tax': 'Tax',
  'terrorism': 'Terrorism'
};

const courts = [
  'Supreme Court of Sri Lanka',
  'Court of Appeal',
  'High Court',
  'District Court',
  'Magistrate Court'
];

const outcomes = ['Won', 'Lost', 'Settled', 'Dismissed', 'Pending', 'Appeal Allowed', 'Appeal Dismissed'];

const relevantLawsTemplates = {
  'Civil': ['Civil Procedure Code', 'Contract Law', 'Law of Torts', 'Property Law'],
  'Criminal': ['Penal Code of Sri Lanka', 'Criminal Procedure Code', 'Evidence Ordinance'],
  'Labour': ['Industrial Disputes Act', 'Shop and Office Employees Act', 'Termination of Employment Act'],
  'Family': ['Marriage Registration Ordinance', 'Maintenance Act', 'Adoption of Children Ordinance'],
  'Financial': ['Companies Act', 'Banking Act', 'Securities and Exchange Commission Act'],
  'Drug': ['Poisons, Opium and Dangerous Drugs Ordinance', 'National Dangerous Drugs Control Board Act'],
  'Environmental': ['National Environmental Act', 'Forest Conservation Ordinance', 'Fauna and Flora Protection Ordinance'],
  'Asset': ['Land Acquisition Act', 'Registration of Title Act', 'Partition Law'],
  'Contempt of Court': ['Contempt of Court Ordinance', 'Constitution of Sri Lanka'],
  'Sexual Cases': ['Penal Code', 'Prevention of Domestic Violence Act', 'Children and Young Persons Ordinance'],
  'Sports': ['Sports Law Act', 'National Sports Council Act'],
  'Tax': ['Inland Revenue Act', 'Value Added Tax Act', 'Customs Ordinance'],
  'Terrorism': ['Prevention of Terrorism Act', 'Public Security Ordinance']
};

// Function to extract case number from text
function extractCaseNumber(text) {
  const patterns = [
    /CA\s*(?:Bail|Appeal|Writ|Case)?\s*(?:No\.?)?\s*(\d+[-\/]\d+)/i,
    /SC\s*(?:Appeal|Case)?\s*(?:No\.?)?\s*(\d+[-\/]\d+)/i,
    /HC\s*(?:Case)?\s*(?:No\.?)?\s*(\d+[-\/]\d+)/i,
    /Case\s*No\.?\s*:?\s*([A-Z0-9\-\/]+)/i,
    /Application\s*No\.?\s*:?\s*([A-Z0-9\-\/]+)/i
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match) return match[1] || match[0];
  }
  return null;
}

// Function to extract court from text
function extractCourt(text) {
  const upperText = text.toUpperCase();
  if (upperText.includes('SUPREME COURT')) return 'Supreme Court of Sri Lanka';
  if (upperText.includes('COURT OF APPEAL')) return 'Court of Appeal';
  if (upperText.includes('HIGH COURT')) return 'High Court';
  if (upperText.includes('DISTRICT COURT')) return 'District Court';
  if (upperText.includes('MAGISTRATE')) return 'Magistrate Court';
  return courts[Math.floor(Math.random() * courts.length)];
}

// Function to extract year from text
function extractYear(text) {
  const patterns = [
    /(\d{4})[-\/]\d+/,
    /DECIDED\s*(?:ON)?\s*:?\s*\d+[-\/]\d+[-\/](\d{4})/i,
    /ARGUED\s*(?:ON)?\s*:?\s*\d+[-\/]\d+[-\/](\d{4})/i,
    /\b(20\d{2})\b/,
    /\b(19\d{2})\b/
  ];
  
  for (const pattern of patterns) {
    const match = text.match(pattern);
    if (match && match[1]) {
      const year = parseInt(match[1]);
      if (year >= 1950 && year <= 2026) return year;
    }
  }
  return 2020 + Math.floor(Math.random() * 6);
}

// Function to extract parties from text
function extractParties(text) {
  const vsPattern = /([A-Z][a-zA-Z\s]+)\s*(?:Vs\.?|vs\.?|V\.)\s*([A-Z][a-zA-Z\s]+)/;
  const match = text.match(vsPattern);
  if (match) {
    return {
      petitioner: match[1].trim().substring(0, 100),
      respondent: match[2].trim().substring(0, 100)
    };
  }
  return null;
}

// Function to create a proper title
function createTitle(text, caseNumber, caseType) {
  // Try to extract case number and parties
  const parties = extractParties(text);
  
  if (caseNumber && parties) {
    return `${caseNumber} - ${parties.petitioner} vs. ${parties.respondent}`.substring(0, 200);
  }
  
  if (caseNumber) {
    return `${caseType} Case ${caseNumber}`.substring(0, 200);
  }
  
  // Extract first meaningful line
  const lines = text.split('\n').filter(l => l.trim().length > 10);
  for (const line of lines.slice(0, 10)) {
    const clean = line.trim();
    if (clean.length > 20 && clean.length < 150 && !clean.match(/^\d+\s*\|\s*P/)) {
      return clean;
    }
  }
  
  return `${caseType} Legal Case`;
}

// Function to create summary
function createSummary(text) {
  const lines = text.split('\n').filter(l => l.trim().length > 30);
  let summary = '';
  
  for (const line of lines.slice(0, 10)) {
    const clean = line.trim();
    if (!clean.match(/^\d+\s*\|\s*P/) && !clean.match(/^[A-Z\s]+$/) && clean.length > 30) {
      summary += clean + ' ';
      if (summary.length > 400) break;
    }
  }
  
  return summary.trim().substring(0, 500) || 'Legal case document from Sri Lankan courts.';
}

// Function to extract key points
function extractKeyPoints(text) {
  const points = [];
  const lines = text.split('\n').filter(l => l.trim().length > 50);
  
  for (const line of lines.slice(0, 20)) {
    const clean = line.trim();
    if (clean.length > 50 && clean.length < 200 && !clean.match(/^\d+\s*\|\s*P/)) {
      points.push(clean.substring(0, 150));
      if (points.length >= 5) break;
    }
  }
  
  return points.length > 0 ? points : ['Key legal proceedings documented in this case'];
}

// Function to detect case type from content
function detectCaseType(text) {
  const upperText = text.toUpperCase();
  
  if (upperText.includes('DANGEROUS DRUGS') || upperText.includes('NARCOTIC') || upperText.includes('OPIUM')) return 'Drug';
  if (upperText.includes('MURDER') || upperText.includes('CRIMINAL') || upperText.includes('PENAL CODE')) return 'Criminal';
  if (upperText.includes('LABOUR') || upperText.includes('EMPLOYMENT') || upperText.includes('INDUSTRIAL DISPUTE')) return 'Labour';
  if (upperText.includes('MARRIAGE') || upperText.includes('DIVORCE') || upperText.includes('CUSTODY') || upperText.includes('MAINTENANCE')) return 'Family';
  if (upperText.includes('TAX') || upperText.includes('REVENUE') || upperText.includes('CUSTOMS')) return 'Tax';
  if (upperText.includes('ENVIRONMENT') || upperText.includes('POLLUTION') || upperText.includes('FOREST')) return 'Environmental';
  if (upperText.includes('COMPANY') || upperText.includes('BANKING') || upperText.includes('FINANCIAL')) return 'Financial';
  if (upperText.includes('LAND') || upperText.includes('PROPERTY') || upperText.includes('PARTITION')) return 'Asset';
  if (upperText.includes('CONTEMPT')) return 'Contempt of Court';
  if (upperText.includes('TERRORISM') || upperText.includes('SECURITY')) return 'Terrorism';
  if (upperText.includes('SEXUAL') || upperText.includes('RAPE')) return 'Sexual Cases';
  if (upperText.includes('SPORT')) return 'Sports';
  if (upperText.includes('CIVIL') || upperText.includes('CONTRACT') || upperText.includes('TORT')) return 'Civil';
  
  return 'Civil'; // Default
}

async function seedDatabase() {
  try {
    // Connect to MongoDB
    const mongoUri = process.env.MONGODB_URI || 'mongodb://localhost:27017/legal_db';
    await mongoose.connect(mongoUri);
    console.log('✓ Connected to MongoDB');

    // Clear existing cases
    await Case.deleteMany({});
    console.log('✓ Cleared existing cases');

    let caseCount = 0;
    const casesToInsert = [];
    const processedCaseIds = new Set();

    // FIRST: Process extracted_text folder (better quality)
    console.log('\n📂 Processing extracted_text folder...');
    if (fs.existsSync(EXTRACTED_TEXT_DIR)) {
      const files = fs.readdirSync(EXTRACTED_TEXT_DIR);
      console.log(`Found ${files.length} files`);

      for (const file of files) {
        try {
          const filePath = path.join(EXTRACTED_TEXT_DIR, file);
          const content = fs.readFileSync(filePath, 'utf-8');
          
          if (!content.trim() || content.length < 100) continue;

          const caseId = file.replace('.txt.txt', '').replace('.txt', '');
          if (processedCaseIds.has(caseId)) continue;
          processedCaseIds.add(caseId);

          const caseNumber = extractCaseNumber(content);
          const caseType = detectCaseType(content);
          const court = extractCourt(content);
          const year = extractYear(content);
          const title = createTitle(content, caseNumber, caseType);
          const summary = createSummary(content);

          const caseData = {
            caseId: caseNumber || caseId,
            title: title,
            caseType: caseType,
            court: court,
            year: year,
            outcome: outcomes[Math.floor(Math.random() * outcomes.length)],
            summary: summary,
            fullText: content,
            relevantLaws: relevantLawsTemplates[caseType] || [],
            citedCases: [],
            keyPoints: extractKeyPoints(content),
            judges: [],
            dateOfDecision: new Date(year, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1)
          };

          casesToInsert.push(caseData);
          caseCount++;
          console.log(`  ✓ Processed: ${caseId} -> ${caseType} (${title.substring(0, 50)}...)`);

        } catch (err) {
          console.error(`  ✗ Error processing ${file}:`, err.message);
        }
      }
    }

    // SECOND: Process dataset folders
    console.log('\n📂 Processing dataset folders...');
    for (const [folderName, caseType] of Object.entries(typeMapping)) {
      const categoryPath = path.join(DATASET_DIR, folderName);
      
      if (!fs.existsSync(categoryPath)) continue;

      const files = fs.readdirSync(categoryPath);
      console.log(`Processing ${folderName} (${caseType}): ${files.length} files`);

      for (const file of files) {
        try {
          const filePath = path.join(categoryPath, file);
          const content = fs.readFileSync(filePath, 'utf-8');
          
          if (!content.trim() || content.length < 100) continue;

          const caseId = `${folderName}_${file.replace('.txt.txt', '').replace('.txt', '')}`;
          if (processedCaseIds.has(caseId)) continue;
          processedCaseIds.add(caseId);

          const caseNumber = extractCaseNumber(content);
          const court = extractCourt(content);
          const year = extractYear(content);
          const title = createTitle(content, caseNumber, caseType);
          const summary = createSummary(content);

          const caseData = {
            caseId: caseNumber || caseId,
            title: title,
            caseType: caseType,
            court: court,
            year: year,
            outcome: outcomes[Math.floor(Math.random() * outcomes.length)],
            summary: summary,
            fullText: content,
            relevantLaws: relevantLawsTemplates[caseType] || [],
            citedCases: [],
            keyPoints: extractKeyPoints(content),
            judges: [],
            dateOfDecision: new Date(year, Math.floor(Math.random() * 12), Math.floor(Math.random() * 28) + 1)
          };

          casesToInsert.push(caseData);
          caseCount++;

        } catch (err) {
          console.error(`  ✗ Error processing ${file}:`, err.message);
        }
      }
    }

    // Insert all cases
    console.log(`\n📥 Inserting ${casesToInsert.length} cases into database...`);
    
    for (let i = 0; i < casesToInsert.length; i += 20) {
      const batch = casesToInsert.slice(i, i + 20);
      try {
        await Case.insertMany(batch, { ordered: false });
        console.log(`  ✓ Inserted batch ${Math.floor(i/20) + 1}`);
      } catch (err) {
        console.log(`  ⚠ Batch ${Math.floor(i/20) + 1} had some issues (likely duplicates)`);
      }
    }

    // Get final count
    const finalCount = await Case.countDocuments();
    console.log(`\n✅ Database seeding complete!`);
    console.log(`✅ Total cases in database: ${finalCount}`);

    // Show sample case
    const sampleCase = await Case.findOne();
    if (sampleCase) {
      console.log('\n📋 Sample case:');
      console.log(`   ID: ${sampleCase.caseId}`);
      console.log(`   Title: ${sampleCase.title.substring(0, 80)}...`);
      console.log(`   Type: ${sampleCase.caseType}`);
      console.log(`   Court: ${sampleCase.court}`);
      console.log(`   Year: ${sampleCase.year}`);
    }

    await mongoose.connection.close();
    console.log('\n✓ Database connection closed');
    process.exit(0);
  } catch (err) {
    console.error('✗ Error seeding database:', err);
    process.exit(1);
  }
}

// Run the seeding script
seedDatabase();
