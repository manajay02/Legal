const mongoose = require('mongoose');
const fs = require('fs');
const path = require('path');
require('dotenv').config();

const Case = require('./models/Case');

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
  'Supreme Court',
  'High Court',
  'District Court',
  'Sessions Court',
  'Court of Appeal',
  'Magistrate Court'
];

const outcomes = ['Won', 'Lost', 'Settled', 'Dismissed', 'Pending'];

const relevantLawsTemplates = {
  'Civil': ['Section 12, Civil Procedure Code', 'Indian Contract Act, 1872', 'Law of Torts'],
  'Criminal': ['Indian Penal Code', 'Criminal Procedure Code, 1973', 'Evidence Act, 1872'],
  'Labour': ['Industrial Disputes Act, 1947', 'Labour Code', 'Workmen Compensation Act'],
  'Family': ['Hindu Marriage Act, 1955', 'Succession Act', 'Guardianship Act'],
  'Financial': ['Companies Act, 2013', 'Insolvency Code', 'Financial Act'],
  'Drug': ['NDPS Act, 1985', 'Drugs and Cosmetics Act'],
  'Environmental': ['Environmental Protection Act, 1986', 'Wildlife Protection Act'],
  'Asset': ['Property Law', 'Transfer of Property Act, 1882', 'Land Acquisition Act'],
  'Contempt of Court': ['Contempt of Courts Act, 1971', 'Constitution of India'],
  'Sexual Cases': ['Indian Penal Code', 'Protection of Women Act', 'Criminal Procedure Code'],
  'Sports': ['Sports Act', 'Code of Conduct', 'Competition Rules'],
  'Tax': ['Income Tax Act, 1961', 'Tax Code', 'GST Act'],
  'Terrorism': ['Prevention of Terrorism Act', 'National Security Act', 'Criminal Code']
};

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

    // Read from each category folder
    for (const [folderName, caseType] of Object.entries(typeMapping)) {
      const categoryPath = path.join(DATASET_DIR, folderName);
      
      if (!fs.existsSync(categoryPath)) {
        console.log(`⚠ Folder not found: ${folderName}`);
        continue;
      }

      const files = fs.readdirSync(categoryPath);
      console.log(`\n📂 Processing ${folderName} (${caseType}): ${files.length} files`);

      for (const file of files) {
        try {
          const filePath = path.join(categoryPath, file);
          const content = fs.readFileSync(filePath, 'utf-8');
          
          if (!content.trim()) continue;

          // Extract case ID from filename
          const caseId = file.replace('.txt.txt', '').replace('.txt', '');
          
          // Create a meaningful title from content
          const lines = content.split('\n').filter(l => l.trim());
          const title = lines[0] || `${caseType} Case ${caseCount + 1}`;
          const summary = lines.slice(0, 3).join(' ').substring(0, 500) || content.substring(0, 500);

          const caseData = {
            caseId: caseId,
            title: title.substring(0, 200),
            caseType: caseType,
            court: courts[Math.floor(Math.random() * courts.length)],
            year: 2015 + Math.floor(Math.random() * 10),
            outcome: outcomes[Math.floor(Math.random() * outcomes.length)],
            summary: summary,
            fullText: content,
            relevantLaws: relevantLawsTemplates[caseType] || [],
            citedCases: [],
            keyPoints: extractKeyPoints(content),
            judges: [`Judge ${String.fromCharCode(65 + Math.floor(Math.random() * 26))}`],
            dateOfDecision: new Date(2015 + Math.floor(Math.random() * 10), Math.floor(Math.random() * 12), Math.floor(Math.random() * 28))
          };

          casesToInsert.push(caseData);
          caseCount++;

          // Insert in batches of 20
          if (casesToInsert.length >= 20) {
            await Case.insertMany(casesToInsert, { ordered: false }).catch(err => {
              console.log(`⚠ Some cases had issues (likely duplicates): ${err.message.substring(0, 50)}`);
            });
            console.log(`  ✓ Inserted ${casesToInsert.length} cases`);
            casesToInsert.length = 0;
          }
        } catch (err) {
          console.error(`  ✗ Error processing file ${file}:`, err.message);
        }
      }
    }

    // Insert remaining cases
    if (casesToInsert.length > 0) {
      await Case.insertMany(casesToInsert, { ordered: false }).catch(err => {
        console.log(`⚠ Some cases had issues (likely duplicates): ${err.message.substring(0, 50)}`);
      });
      console.log(`  ✓ Inserted ${casesToInsert.length} cases`);
    }

    // Get final count
    const finalCount = await Case.countDocuments();
    console.log(`\n✓ Database seeding complete!`);
    console.log(`✓ Total cases in database: ${finalCount}`);

    await mongoose.connection.close();
    console.log('✓ Database connection closed');
    process.exit(0);
  } catch (err) {
    console.error('✗ Error seeding database:', err);
    process.exit(1);
  }
}

function extractKeyPoints(text) {
  const lines = text.split('\n').filter(l => l.trim().length > 20);
  return lines.slice(0, 3).map(l => l.substring(0, 100));
}

// Run the seeding script
seedDatabase();
