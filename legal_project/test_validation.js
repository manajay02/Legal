const http = require('http');

// Test 1: Non-legal content (should return "not a legal case" error)
const testNonLegal = {
  hostname: 'localhost',
  port: 5000,
  path: '/api/cases/classify',
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  }
};

const nonLegalPayload = JSON.stringify({
  caseText: 'The quick brown fox jumps over the lazy dog. This is just random content about animals and nature without any legal terminology.'
});

console.log('\n📋 Test 1: Non-Legal Content');
console.log('Sending: Random non-legal text\n');

const req1 = http.request(testNonLegal, (res) => {
  let data = '';
  res.on('data', (chunk) => { data += chunk; });
  res.on('end', () => {
    console.log(`Status: ${res.statusCode}`);
    console.log(`Response:`, JSON.parse(data));
    
    // Test 2: Valid legal content
    testLegalContent();
  });
});

req1.on('error', (e) => {
  console.error(`Problem with request: ${e.message}`);
});

req1.write(nonLegalPayload);
req1.end();

// Test 2: Legal content (should accept and classify)
function testLegalContent() {
  const testLegal = {
    hostname: 'localhost',
    port: 5000,
    path: '/api/cases/classify',
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    }
  };

  const legalPayload = JSON.stringify({
    caseText: 'This is a criminal case involving the accused prosecution conviction sentence jail punishment penal guilty defence. The defendant was charged with a crime and faced prosecution in criminal court.'
  });

  console.log('\n📋 Test 2: Valid Legal Content (Criminal Case)');
  console.log('Sending: Legal text with criminal case keywords\n');

  const req2 = http.request(testLegal, (res) => {
    let data = '';
    res.on('data', (chunk) => { data += chunk; });
    res.on('end', () => {
      console.log(`Status: ${res.statusCode}`);
      console.log(`Response:`, JSON.parse(data));
    });
  });

  req2.on('error', (e) => {
    console.error(`Problem with request: ${e.message}`);
  });

  req2.write(legalPayload);
  req2.end();
}
