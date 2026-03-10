/* ============================================
   Legal Research Platform - Unified JavaScript
   ============================================ */

// API Endpoints Configuration
// Port 5000: Flask (Similarity + Auth)
// Port 8000: Argument Scorer (backend-nawanjana)
// Port 8001: Document Extractor (backend-paramitha)
// Port 8002: Compliance Auditor
const API = {
    similarity: 'http://localhost:5000',
    argument: 'http://localhost:8000',
    compliance: 'http://localhost:8002',
    extractor: 'http://localhost:8001'
};

// ============================================
// Utility Functions
// ============================================

function showLoading(text = 'Processing...') {
    document.getElementById('loading-text').textContent = text;
    document.getElementById('loading-overlay').style.display = 'flex';
}

function hideLoading() {
    document.getElementById('loading-overlay').style.display = 'none';
}

function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icons = {
        success: 'fa-check-circle',
        error: 'fa-times-circle',
        warning: 'fa-exclamation-circle'
    };
    
    toast.innerHTML = `
        <i class="fas ${icons[type]}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// ============================================
// Navigation
// ============================================

document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        const component = item.dataset.component;
        
        // Update nav
        document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
        item.classList.add('active');
        
        // Update sections
        document.querySelectorAll('.component-section').forEach(s => s.classList.remove('active'));
        document.getElementById(component).classList.add('active');
    });
});

// Dashboard card navigation
document.querySelectorAll('.dashboard-card').forEach(card => {
    card.addEventListener('click', () => {
        const target = card.dataset.goto;
        document.querySelector(`.nav-item[data-component="${target}"]`).click();
    });
});

// ============================================
// Service Status Check
// ============================================

async function checkServiceStatus() {
    const services = [
        { port: 5000, id: 'status-5000', name: 'Similarity' },
        { port: 8000, id: 'status-8000', name: 'Argument' },
        { port: 8002, id: 'status-8002', name: 'Compliance' },
        { port: 8001, id: 'status-8001', name: 'Extractor' }
    ];
    
    for (const service of services) {
        const statusEl = document.getElementById(service.id);
        statusEl.textContent = 'Checking...';
        statusEl.className = 'card-status';
        
        try {
            const response = await fetch(`http://localhost:${service.port}/`, {
                method: 'GET',
                mode: 'cors',
                signal: AbortSignal.timeout(3000)
            });
            
            if (response.ok) {
                statusEl.textContent = 'Online';
                statusEl.classList.add('online');
            } else {
                statusEl.textContent = 'Error';
                statusEl.classList.add('offline');
            }
        } catch (e) {
            statusEl.textContent = 'Offline';
            statusEl.classList.add('offline');
        }
    }
}

document.getElementById('statusBtn').addEventListener('click', checkServiceStatus);

// Check status on load
window.addEventListener('load', checkServiceStatus);

// ============================================
// Component 1: Case Similarity Search
// ============================================

// Load categories on init
async function loadCategories() {
    try {
        const res = await fetch(`${API.similarity}/api/categories`);
        if (res.ok) {
            const data = await res.json();
            const catSelect = document.getElementById('sim-category');
            catSelect.innerHTML = '<option value="">All Categories</option>';
            
            if (data.categories) {
                Object.keys(data.categories).forEach(cat => {
                    catSelect.innerHTML += `<option value="${cat}">${cat}</option>`;
                });
            }
        }
    } catch (e) {
        console.log('Categories not available');
    }
}

document.getElementById('sim-category').addEventListener('change', async (e) => {
    const category = e.target.value;
    const subSelect = document.getElementById('sim-subcategory');
    subSelect.innerHTML = '<option value="">All Subcategories</option>';
    
    if (!category) return;
    
    try {
        const res = await fetch(`${API.similarity}/api/categories`);
        if (res.ok) {
            const data = await res.json();
            if (data.categories && data.categories[category]) {
                data.categories[category].forEach(sub => {
                    subSelect.innerHTML += `<option value="${sub}">${sub}</option>`;
                });
            }
        }
    } catch (e) {
        console.log('Subcategories not available');
    }
});

document.getElementById('sim-search-btn').addEventListener('click', async () => {
    const query = document.getElementById('sim-query').value;
    const file = document.getElementById('sim-file').files[0];
    const category = document.getElementById('sim-category').value;
    const subcategory = document.getElementById('sim-subcategory').value;
    const topK = document.getElementById('sim-topk').value || 5;
    
    if (!query && !file) {
        showToast('Please enter a query or upload a PDF', 'warning');
        return;
    }
    
    showLoading('Searching similar cases...');
    
    try {
        const formData = new FormData();
        if (file) formData.append('file', file);
        formData.append('query', query || '');
        formData.append('category', category);
        formData.append('subcategory', subcategory);
        formData.append('top_k', topK);
        
        const res = await fetch(`${API.similarity}/api/search`, {
            method: 'POST',
            body: formData
        });
        
        if (!res.ok) throw new Error('Search failed');
        
        const data = await res.json();
        displaySimilarityResults(data);
        showToast('Search completed!', 'success');
    } catch (e) {
        showToast('Search failed: ' + e.message, 'error');
        document.getElementById('sim-results').innerHTML = `
            <p class="placeholder-text">Search failed. Make sure the backend is running on port 5000.</p>
        `;
    } finally {
        hideLoading();
    }
});

function displaySimilarityResults(data) {
    const container = document.getElementById('sim-results');
    
    if (!data.results || data.results.length === 0) {
        container.innerHTML = '<p class="placeholder-text">No similar cases found.</p>';
        return;
    }
    
    let html = '';
    data.results.forEach((result, i) => {
        html += `
            <div class="result-card">
                <h4>#${i + 1} ${result.filename || result.title || 'Case'}</h4>
                <p>${result.snippet || result.text?.substring(0, 200) + '...' || 'No preview available'}</p>
                <div class="meta">
                    <span><i class="fas fa-folder"></i> ${result.category || 'N/A'}</span>
                    <span><i class="fas fa-tag"></i> ${result.subcategory || 'N/A'}</span>
                    <span><i class="fas fa-chart-line"></i> ${(result.similarity * 100).toFixed(1)}% match</span>
                </div>
            </div>
        `;
    });
    
    container.innerHTML = html;
}

// ============================================
// Component 2: Legal Argument Critic
// ============================================

document.getElementById('arg-analyze-btn').addEventListener('click', async () => {
    const text = document.getElementById('arg-text').value;
    const file = document.getElementById('arg-file').files[0];
    const jurisdiction = document.getElementById('arg-jurisdiction').value;
    const caseType = document.getElementById('arg-casetype').value;
    
    if (!text && !file) {
        showToast('Please enter text or upload a document', 'warning');
        return;
    }
    
    if (text && text.length < 50) {
        showToast('Text must be at least 50 characters', 'warning');
        return;
    }
    
    showLoading('Analyzing legal argument...');
    
    try {
        let response;
        
        if (file) {
            const formData = new FormData();
            formData.append('file', file);
            formData.append('jurisdiction', jurisdiction);
            formData.append('case_type', caseType);
            
            response = await fetch(`${API.argument}/api/v1/upload`, {
                method: 'POST',
                body: formData
            });
        } else {
            response = await fetch(`${API.argument}/api/v1/analyze`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    text: text,
                    jurisdiction: jurisdiction,
                    case_type: caseType
                })
            });
        }
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Analysis failed');
        }
        
        const data = await response.json();
        displayArgumentResults(data);
        showToast('Analysis completed!', 'success');
    } catch (e) {
        showToast('Analysis failed: ' + e.message, 'error');
        document.getElementById('arg-results').innerHTML = `
            <p class="placeholder-text">Analysis failed. Make sure the backend is running on port 8001.</p>
        `;
    } finally {
        hideLoading();
    }
});

function displayArgumentResults(data) {
    const container = document.getElementById('arg-results');
    
    const totalScore = data.total_score || data.score || 0;
    const maxScore = data.max_score || 100;
    const categories = data.category_breakdown || data.categories || [];
    
    let categoryHTML = '';
    categories.forEach(cat => {
        const percent = (cat.rubric_score / 5) * 100;
        categoryHTML += `
            <div class="category-item">
                <div class="header">
                    <span class="name">${cat.category}</span>
                    <span class="score">${cat.points?.toFixed(1) || cat.rubric_score}/5</span>
                </div>
                <div class="progress-bar">
                    <div class="fill" style="width: ${percent}%"></div>
                </div>
                <p style="font-size: 13px; color: #64748b; margin-top: 8px;">${cat.rationale || ''}</p>
            </div>
        `;
    });
    
    container.innerHTML = `
        <div class="score-display">
            <div class="score">${totalScore.toFixed(1)}</div>
            <div class="label">out of ${maxScore} points</div>
        </div>
        <div class="category-scores">
            ${categoryHTML}
        </div>
        ${data.overall_feedback ? `
            <div class="data-section" style="margin-top: 16px;">
                <h4>Overall Feedback</h4>
                <p class="value">${data.overall_feedback}</p>
            </div>
        ` : ''}
    `;
}

// ============================================
// Component 3: Case Structure Extractor
// ============================================

const extUploadZone = document.getElementById('ext-upload-zone');
const extFileInput = document.getElementById('ext-file');
const extFileInfo = document.getElementById('ext-file-info');
const extFilename = document.getElementById('ext-filename');
const extProcessBtn = document.getElementById('ext-process-btn');

extUploadZone.addEventListener('click', () => extFileInput.click());
extUploadZone.addEventListener('dragover', e => {
    e.preventDefault();
    extUploadZone.style.borderColor = '#2563eb';
});
extUploadZone.addEventListener('dragleave', () => {
    extUploadZone.style.borderColor = '#e2e8f0';
});
extUploadZone.addEventListener('drop', e => {
    e.preventDefault();
    extUploadZone.style.borderColor = '#e2e8f0';
    if (e.dataTransfer.files[0]) {
        extFileInput.files = e.dataTransfer.files;
        handleExtFileSelect();
    }
});

extFileInput.addEventListener('change', handleExtFileSelect);

function handleExtFileSelect() {
    const file = extFileInput.files[0];
    if (file) {
        extFilename.textContent = file.name;
        extFileInfo.style.display = 'flex';
        extUploadZone.style.display = 'none';
        extProcessBtn.disabled = false;
    }
}

document.getElementById('ext-remove-file').addEventListener('click', () => {
    extFileInput.value = '';
    extFileInfo.style.display = 'none';
    extUploadZone.style.display = 'block';
    extProcessBtn.disabled = true;
});

extProcessBtn.addEventListener('click', async () => {
    const file = extFileInput.files[0];
    if (!file) return;
    
    showLoading('Extracting case structure...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        
        const response = await fetch(`${API.extractor}/api/v1/upload`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Extraction failed');
        }
        
        const data = await response.json();
        displayExtractorResults(data);
        showToast('Extraction completed!', 'success');
    } catch (e) {
        showToast('Extraction failed: ' + e.message, 'error');
        document.getElementById('ext-results').innerHTML = `
            <p class="placeholder-text">Extraction failed. Make sure the backend is running on port 8003.</p>
        `;
    } finally {
        hideLoading();
    }
});

function displayExtractorResults(data) {
    const container = document.getElementById('ext-results');
    const result = data.result || data;
    
    let html = '<div class="extracted-data">';
    
    if (result.case_number) {
        html += `
            <div class="data-section">
                <h4>Case Number</h4>
                <div class="value">${result.case_number}</div>
            </div>
        `;
    }
    
    if (result.parties) {
        html += `
            <div class="data-section">
                <h4>Parties</h4>
                <div class="value">${JSON.stringify(result.parties, null, 2)}</div>
            </div>
        `;
    }
    
    if (result.judges || result.judge) {
        html += `
            <div class="data-section">
                <h4>Judges</h4>
                <div class="tag-list">
                    ${(result.judges || [result.judge]).map(j => `<span class="tag">${j}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    if (result.date || result.decision_date) {
        html += `
            <div class="data-section">
                <h4>Decision Date</h4>
                <div class="value">${result.date || result.decision_date}</div>
            </div>
        `;
    }
    
    if (result.summary || result.headnotes) {
        html += `
            <div class="data-section">
                <h4>Summary</h4>
                <div class="value">${result.summary || result.headnotes}</div>
            </div>
        `;
    }
    
    if (result.legal_issues) {
        html += `
            <div class="data-section">
                <h4>Legal Issues</h4>
                <div class="tag-list">
                    ${result.legal_issues.map(i => `<span class="tag">${i}</span>`).join('')}
                </div>
            </div>
        `;
    }
    
    // Show raw JSON for any other fields
    const displayedKeys = ['case_number', 'parties', 'judges', 'judge', 'date', 'decision_date', 'summary', 'headnotes', 'legal_issues'];
    const otherFields = Object.entries(result).filter(([k]) => !displayedKeys.includes(k));
    
    if (otherFields.length > 0) {
        html += `
            <div class="data-section">
                <h4>Additional Data</h4>
                <pre class="value" style="font-size: 12px; overflow-x: auto;">${JSON.stringify(Object.fromEntries(otherFields), null, 2)}</pre>
            </div>
        `;
    }
    
    html += '</div>';
    container.innerHTML = html;
}

// ============================================
// Component 4: Contract Compliance Auditor
// ============================================

const compUploadZone = document.getElementById('comp-upload-zone');
const compFileInput = document.getElementById('comp-file');
const compFileInfo = document.getElementById('comp-file-info');
const compFilename = document.getElementById('comp-filename');
const compCheckBtn = document.getElementById('comp-check-btn');

compUploadZone.addEventListener('click', () => compFileInput.click());
compUploadZone.addEventListener('dragover', e => {
    e.preventDefault();
    compUploadZone.style.borderColor = '#2563eb';
});
compUploadZone.addEventListener('dragleave', () => {
    compUploadZone.style.borderColor = '#e2e8f0';
});
compUploadZone.addEventListener('drop', e => {
    e.preventDefault();
    compUploadZone.style.borderColor = '#e2e8f0';
    if (e.dataTransfer.files[0]) {
        compFileInput.files = e.dataTransfer.files;
        handleCompFileSelect();
    }
});

compFileInput.addEventListener('change', handleCompFileSelect);

function handleCompFileSelect() {
    const file = compFileInput.files[0];
    if (file) {
        compFilename.textContent = file.name;
        compFileInfo.style.display = 'flex';
        compUploadZone.style.display = 'none';
        compCheckBtn.disabled = false;
    }
}

document.getElementById('comp-remove-file').addEventListener('click', () => {
    compFileInput.value = '';
    compFileInfo.style.display = 'none';
    compUploadZone.style.display = 'block';
    compCheckBtn.disabled = true;
});

compCheckBtn.addEventListener('click', async () => {
    const file = compFileInput.files[0];
    const contractType = document.getElementById('comp-type').value;
    
    if (!file) return;
    
    showLoading('Checking compliance...');
    
    try {
        const formData = new FormData();
        formData.append('file', file);
        formData.append('contract_type', contractType);
        
        const response = await fetch(`${API.compliance}/check-compliance`, {
            method: 'POST',
            body: formData
        });
        
        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Compliance check failed');
        }
        
        const data = await response.json();
        displayComplianceResults(data);
        showToast('Compliance check completed!', 'success');
    } catch (e) {
        showToast('Compliance check failed: ' + e.message, 'error');
        document.getElementById('comp-results').innerHTML = `
            <p class="placeholder-text">Compliance check failed. Make sure the backend is running on port 8002.</p>
        `;
    } finally {
        hideLoading();
    }
});

function displayComplianceResults(data) {
    const container = document.getElementById('comp-results');
    
    const results = data.compliance_results || data.results || data;
    const issues = results.issues || results.violations || [];
    
    let passCount = 0, warnCount = 0, failCount = 0;
    issues.forEach(issue => {
        if (issue.severity === 'critical' || issue.severity === 'high') failCount++;
        else if (issue.severity === 'warning' || issue.severity === 'medium') warnCount++;
        else passCount++;
    });
    
    const overallScore = results.compliance_score || results.score || 
        (issues.length === 0 ? 100 : Math.max(0, 100 - (failCount * 20 + warnCount * 10)));
    
    let issuesHTML = '';
    issues.forEach(issue => {
        const severity = issue.severity === 'critical' || issue.severity === 'high' ? 'critical' :
                        issue.severity === 'warning' || issue.severity === 'medium' ? 'warning' : 'info';
        const icon = severity === 'critical' ? 'fa-times-circle' :
                    severity === 'warning' ? 'fa-exclamation-triangle' : 'fa-info-circle';
        
        issuesHTML += `
            <li class="issue-item ${severity}">
                <i class="fas ${icon}"></i>
                <div>
                    <strong>${issue.clause || issue.rule || 'Issue'}</strong>
                    <p style="margin: 4px 0 0; font-size: 13px;">${issue.description || issue.message || ''}</p>
                </div>
            </li>
        `;
    });
    
    container.innerHTML = `
        <div class="score-display" style="background: ${overallScore >= 80 ? 'linear-gradient(135deg, #10b981, #059669)' : overallScore >= 50 ? 'linear-gradient(135deg, #f59e0b, #d97706)' : 'linear-gradient(135deg, #ef4444, #dc2626)'}">
            <div class="score">${overallScore}%</div>
            <div class="label">Compliance Score</div>
        </div>
        
        <div class="compliance-summary">
            <div class="compliance-stat pass">
                <div class="value">${passCount}</div>
                <div class="label">Compliant</div>
            </div>
            <div class="compliance-stat warning">
                <div class="value">${warnCount}</div>
                <div class="label">Warnings</div>
            </div>
            <div class="compliance-stat fail">
                <div class="value">${failCount}</div>
                <div class="label">Critical</div>
            </div>
        </div>
        
        ${issues.length > 0 ? `
            <h4 style="margin-bottom: 12px;">Issues Found</h4>
            <ul class="issue-list">${issuesHTML}</ul>
        ` : '<p style="text-align: center; color: #10b981;"><i class="fas fa-check-circle"></i> No compliance issues found!</p>'}
    `;
}

// ============================================
// Initialize
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    loadCategories();
});
