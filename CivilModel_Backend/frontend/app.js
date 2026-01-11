/**
 * Civil Case Extractor Frontend Application
 * Connects to the FastAPI backend for document processing
 */

const API_BASE_URL = 'http://localhost:8000';
const API_V1_URL = `${API_BASE_URL}/api/v1`;

// State
let currentDocId = null;
let currentOutputDoc = null;
let allDocuments = [];

// DOM Elements
const pages = document.querySelectorAll('.page');
const navItems = document.querySelectorAll('.nav-item');
const apiStatusEl = document.getElementById('api-status');
const modal = document.getElementById('document-modal');

// ============================================
// Navigation
// ============================================
function navigateTo(pageName) {
    pages.forEach(page => page.classList.remove('active'));
    navItems.forEach(item => item.classList.remove('active'));
    
    const targetPage = document.getElementById(`${pageName}-page`);
    const targetNav = document.querySelector(`[data-page="${pageName}"]`);
    
    if (targetPage) targetPage.classList.add('active');
    if (targetNav) targetNav.classList.add('active');
    
    // Load page-specific data
    if (pageName === 'dashboard') loadDashboard();
    if (pageName === 'documents') loadDocuments();
    if (pageName === 'output') loadOutputPage();
}

navItems.forEach(item => {
    item.addEventListener('click', (e) => {
        e.preventDefault();
        const pageName = item.dataset.page;
        navigateTo(pageName);
    });
});

// ============================================
// API Functions
// ============================================
async function checkApiStatus() {
    const statusDot = apiStatusEl.querySelector('.status-dot');
    const statusText = apiStatusEl.querySelector('span');
    
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        const data = await response.json();
        
        statusDot.classList.remove('offline');
        statusDot.classList.add('online');
        statusText.textContent = 'API Online';
        
        return data;
    } catch (error) {
        statusDot.classList.remove('online');
        statusDot.classList.add('offline');
        statusText.textContent = 'API Offline';
        return null;
    }
}

async function fetchDocuments() {
    try {
        const response = await fetch(`${API_V1_URL}/documents`);
        if (!response.ok) throw new Error('Failed to fetch documents');
        const data = await response.json();
        allDocuments = data.documents || [];
        return data;
    } catch (error) {
        console.error('Error fetching documents:', error);
        return { documents: [], total: 0 };
    }
}

async function fetchDocument(docId) {
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}`);
        if (!response.ok) throw new Error('Document not found');
        return await response.json();
    } catch (error) {
        console.error('Error fetching document:', error);
        return null;
    }
}

async function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_V1_URL}/upload`, {
        method: 'POST',
        body: formData
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Upload failed');
    }
    
    return await response.json();
}

async function processDocument(docId) {
    const response = await fetch(`${API_V1_URL}/process/${docId}`, {
        method: 'POST'
    });
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Processing failed');
    }
    
    return await response.json();
}

// ============================================
// Dashboard
// ============================================
async function loadDashboard() {
    const data = await fetchDocuments();
    const documents = data.documents || [];
    
    // Calculate stats
    const stats = {
        total: documents.length,
        processing: documents.filter(d => d.status === 'processing').length,
        completed: documents.filter(d => d.status === 'completed').length,
        failed: documents.filter(d => d.status === 'failed').length
    };
    
    document.getElementById('total-docs').textContent = stats.total;
    document.getElementById('processing-docs').textContent = stats.processing;
    document.getElementById('completed-docs').textContent = stats.completed;
    document.getElementById('failed-docs').textContent = stats.failed;
    
    // Recent documents
    const recentList = document.getElementById('recent-docs-list');
    
    if (documents.length === 0) {
        recentList.innerHTML = '<p class="empty-state">No documents yet. Upload a PDF to get started!</p>';
        return;
    }
    
    const recentDocs = documents.slice(0, 5);
    recentList.innerHTML = recentDocs.map(doc => createDocumentCard(doc)).join('');
    
    // Add click handlers
    recentList.querySelectorAll('.document-card').forEach(card => {
        card.addEventListener('click', () => openDocumentModal(card.dataset.docId));
    });
}

// ============================================
// Documents Page
// ============================================
async function loadDocuments() {
    const grid = document.getElementById('documents-grid');
    grid.innerHTML = '<p class="empty-state">Loading documents...</p>';
    
    const data = await fetchDocuments();
    const documents = data.documents || [];
    
    if (documents.length === 0) {
        grid.innerHTML = '<p class="empty-state">No documents found. Upload a PDF to get started!</p>';
        return;
    }
    
    grid.innerHTML = documents.map(doc => createDocumentCard(doc)).join('');
    
    // Add click handlers
    grid.querySelectorAll('.document-card').forEach(card => {
        card.addEventListener('click', () => openDocumentModal(card.dataset.docId));
    });
}

function createDocumentCard(doc) {
    const statusClass = doc.status?.toLowerCase() || 'uploaded';
    const caseNumber = doc.metadata?.case_number || 'N/A';
    const court = doc.metadata?.court || 'N/A';
    
    return `
        <div class="document-card" data-doc-id="${doc.id}">
            <div class="document-card-header">
                <h3>${doc.filename || 'Unknown'}</h3>
                <span class="status-badge ${statusClass}">${doc.status || 'Unknown'}</span>
            </div>
            <div class="document-card-meta">
                <span><i class="fas fa-gavel"></i> ${caseNumber}</span>
                <span><i class="fas fa-landmark"></i> ${court}</span>
            </div>
            <div class="document-card-id">
                <i class="fas fa-fingerprint"></i> ${doc.id}
            </div>
        </div>
    `;
}

// ============================================
// Document Modal
// ============================================
async function openDocumentModal(docId) {
    currentDocId = docId;
    modal.classList.remove('hidden');
    
    const modalBody = document.getElementById('modal-body');
    const modalTitle = document.getElementById('modal-title');
    const modalStatus = document.getElementById('modal-status');
    
    modalBody.innerHTML = '<p style="text-align:center;">Loading...</p>';
    
    const doc = await fetchDocument(docId);
    
    if (!doc) {
        modalBody.innerHTML = '<p class="empty-state">Document not found</p>';
        return;
    }
    
    modalTitle.textContent = doc.filename || 'Document Details';
    modalStatus.textContent = doc.status || 'Unknown';
    modalStatus.className = `status-badge ${(doc.status || '').toLowerCase()}`;
    
    const metadata = doc.metadata || {};
    const sections = doc.sections || [];
    
    let html = `
        <div class="detail-section">
            <h4><i class="fas fa-info-circle"></i> Basic Information</h4>
            <div class="detail-grid">
                <div class="detail-item">
                    <label>Document ID</label>
                    <span>${doc.id}</span>
                </div>
                <div class="detail-item">
                    <label>File Size</label>
                    <span>${formatFileSize(doc.file_size)}</span>
                </div>
                <div class="detail-item">
                    <label>Page Count</label>
                    <span>${doc.page_count || 'N/A'}</span>
                </div>
                <div class="detail-item">
                    <label>Status</label>
                    <span>${doc.status || 'Unknown'}</span>
                </div>
            </div>
        </div>
    `;
    
    if (Object.keys(metadata).length > 0) {
        html += `
            <div class="detail-section">
                <h4><i class="fas fa-gavel"></i> Case Metadata</h4>
                <div class="detail-grid">
                    <div class="detail-item">
                        <label>Case Number</label>
                        <span>${metadata.case_number || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Court</label>
                        <span>${metadata.court || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Date</label>
                        <span>${metadata.date || 'N/A'}</span>
                    </div>
                    <div class="detail-item">
                        <label>Case Type</label>
                        <span>${metadata.case_type || 'N/A'}</span>
                    </div>
                </div>
            </div>
        `;
    }
    
    if (sections.length > 0) {
        html += `
            <div class="detail-section">
                <h4><i class="fas fa-list"></i> Sections (${sections.length})</h4>
                <div class="section-list">
                    ${sections.slice(0, 3).map(section => `
                        <div class="section-item">
                            <h5>${section.title || 'Untitled Section'}</h5>
                            <p>${truncateText(section.content, 200)}</p>
                        </div>
                    `).join('')}
                    ${sections.length > 3 ? `<p style="text-align:center;color:var(--text-secondary);">+ ${sections.length - 3} more sections</p>` : ''}
                </div>
            </div>
        `;
    }
    
    // Add action buttons
    if (doc.status === 'uploaded') {
        html += `
            <div class="detail-section">
                <button class="btn btn-primary" onclick="processDocumentFromModal('${doc.id}')">
                    <i class="fas fa-cog"></i> Process Document
                </button>
            </div>
        `;
    } else if (doc.status === 'completed') {
        html += `
            <div class="detail-section">
                <button class="btn btn-primary" onclick="viewOutputFromModal('${doc.id}')">
                    <i class="fas fa-eye"></i> View Full Output
                </button>
            </div>
        `;
    }
    
    if (doc.error_message) {
        html += `
            <div class="detail-section">
                <h4><i class="fas fa-exclamation-triangle"></i> Error</h4>
                <div class="detail-item" style="background: rgba(239, 68, 68, 0.1); color: var(--error);">
                    <span>${doc.error_message}</span>
                </div>
            </div>
        `;
    }
    
    modalBody.innerHTML = html;
}

async function processDocumentFromModal(docId) {
    try {
        await processDocument(docId);
        alert('Document processing started! It will continue in the background.');
        closeModal();
        loadDocuments();
    } catch (error) {
        alert('Error: ' + error.message);
    }
}

function viewOutputFromModal(docId) {
    closeModal();
    navigateTo('output');
    setTimeout(() => {
        document.getElementById('output-doc-select').value = docId;
        loadDocumentOutput(docId);
    }, 100);
}

function closeModal() {
    modal.classList.add('hidden');
    currentDocId = null;
}

document.getElementById('modal-close').addEventListener('click', closeModal);
document.querySelector('.modal-overlay').addEventListener('click', closeModal);

// ============================================
// Upload
// ============================================
const uploadZone = document.getElementById('upload-zone');
const fileInput = document.getElementById('file-input');
const uploadProgress = document.getElementById('upload-progress');
const uploadResult = document.getElementById('upload-result');

uploadZone.addEventListener('click', () => fileInput.click());

uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileUpload(files[0]);
    }
});

fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
        handleFileUpload(fileInput.files[0]);
    }
});

async function handleFileUpload(file) {
    if (!file.name.toLowerCase().endsWith('.pdf')) {
        alert('Please upload a PDF file');
        return;
    }
    
    uploadZone.classList.add('hidden');
    uploadProgress.classList.remove('hidden');
    uploadResult.classList.add('hidden');
    
    document.getElementById('upload-filename').textContent = file.name;
    document.getElementById('upload-status').textContent = 'Uploading...';
    document.getElementById('progress-fill').style.width = '0%';
    
    // Simulate progress
    let progress = 0;
    const progressInterval = setInterval(() => {
        progress += 10;
        document.getElementById('progress-fill').style.width = `${Math.min(progress, 90)}%`;
    }, 200);
    
    try {
        const result = await uploadFile(file);
        
        clearInterval(progressInterval);
        document.getElementById('progress-fill').style.width = '100%';
        document.getElementById('upload-status').textContent = 'Complete!';
        
        setTimeout(() => {
            uploadProgress.classList.add('hidden');
            uploadResult.classList.remove('hidden');
            // API returns document_id, not id
            const docId = result.document_id || result.id;
            document.getElementById('result-doc-id').textContent = docId;
            currentDocId = docId;
            console.log('Upload complete. Document ID:', currentDocId);
        }, 500);
        
    } catch (error) {
        clearInterval(progressInterval);
        document.getElementById('upload-status').textContent = 'Failed: ' + error.message;
        document.getElementById('progress-fill').style.width = '0%';
        document.getElementById('progress-fill').style.background = 'var(--error)';
    }
}

document.getElementById('process-btn').addEventListener('click', async () => {
    console.log('Process button clicked. currentDocId:', currentDocId);
    if (!currentDocId) {
        console.log('No document ID available');
        alert('Please wait for upload to complete');
        return;
    }
    
    const btn = document.getElementById('process-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    
    try {
        console.log('Calling processDocument with ID:', currentDocId);
        await processDocument(currentDocId);
        btn.innerHTML = '<i class="fas fa-check"></i> Processing Started!';
        setTimeout(() => {
            navigateTo('documents');
        }, 1500);
    } catch (error) {
        console.error('Process error:', error);
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-cog"></i> Process Document';
        alert('Error: ' + error.message);
    }
});

document.getElementById('upload-another-btn').addEventListener('click', () => {
    uploadZone.classList.remove('hidden');
    uploadProgress.classList.add('hidden');
    uploadResult.classList.add('hidden');
    fileInput.value = '';
    currentDocId = null;
});

// ============================================
// Output Page
// ============================================
async function loadOutputPage() {
    const select = document.getElementById('output-doc-select');
    await fetchDocuments();
    
    // Populate dropdown with completed documents
    const completedDocs = allDocuments.filter(d => d.status === 'completed');
    
    select.innerHTML = '<option value="">-- Choose a document --</option>';
    completedDocs.forEach(doc => {
        const option = document.createElement('option');
        option.value = doc.id;
        option.textContent = `${doc.filename} (${doc.metadata?.case_number || doc.id})`;
        select.appendChild(option);
    });
    
    // Show empty state if no completed docs
    if (completedDocs.length === 0) {
        document.getElementById('output-empty').innerHTML = `
            <i class="fas fa-hourglass-half"></i>
            <h3>No Completed Documents</h3>
            <p>Upload and process a document first to see output here.</p>
            <button class="btn btn-primary" onclick="navigateTo('upload')" style="margin-top:1rem;">
                <i class="fas fa-upload"></i> Upload Document
            </button>
        `;
    }
}

document.getElementById('load-output-btn').addEventListener('click', () => {
    const docId = document.getElementById('output-doc-select').value;
    if (docId) {
        loadDocumentOutput(docId);
    } else {
        alert('Please select a document first');
    }
});

async function loadDocumentOutput(docId) {
    const doc = await fetchDocument(docId);
    if (!doc) {
        alert('Document not found');
        return;
    }
    
    currentOutputDoc = doc;
    
    // Hide empty, show content
    document.getElementById('output-empty').classList.add('hidden');
    document.getElementById('output-content').classList.remove('hidden');
    
    // Populate metadata
    const metadata = doc.metadata || {};
    const caseMetadataEl = document.getElementById('case-metadata');
    caseMetadataEl.innerHTML = `
        <div class="metadata-item">
            <label>Case Number</label>
            <div class="value">${metadata.case_number || 'N/A'}</div>
        </div>
        <div class="metadata-item">
            <label>Court</label>
            <div class="value">${metadata.court || 'N/A'}</div>
        </div>
        <div class="metadata-item">
            <label>Date</label>
            <div class="value">${metadata.date || 'N/A'}</div>
        </div>
        <div class="metadata-item">
            <label>Case Type</label>
            <div class="value">${metadata.case_type || 'N/A'}</div>
        </div>
        <div class="metadata-item">
            <label>Page Count</label>
            <div class="value">${doc.page_count || 'N/A'}</div>
        </div>
        <div class="metadata-item">
            <label>File Size</label>
            <div class="value">${formatFileSize(doc.file_size)}</div>
        </div>
    `;
    
    const partiesMetadataEl = document.getElementById('parties-metadata');
    const parties = metadata.parties || [];
    const judges = metadata.judges || [];
    
    partiesMetadataEl.innerHTML = `
        <div class="metadata-item" style="grid-column: span 2;">
            <label>Parties</label>
            <div class="value list">
                ${parties.length > 0 ? parties.map(p => `<span class="tag">${p}</span>`).join('') : '<span style="color:var(--text-secondary)">No parties found</span>'}
            </div>
        </div>
        <div class="metadata-item" style="grid-column: span 2;">
            <label>Judges</label>
            <div class="value list">
                ${judges.length > 0 ? judges.map(j => `<span class="tag">${j}</span>`).join('') : '<span style="color:var(--text-secondary)">No judges found</span>'}
            </div>
        </div>
    `;
    
    // Populate sections
    const sections = doc.sections || [];
    const sectionsListEl = document.getElementById('sections-list');
    
    if (sections.length === 0) {
        sectionsListEl.innerHTML = '<p class="empty-state">No sections extracted</p>';
    } else {
        sectionsListEl.innerHTML = sections.map((section, index) => `
            <div class="section-card" onclick="toggleSection(this)">
                <div class="section-card-header">
                    <h4><i class="fas fa-bookmark"></i> ${section.title || `Section ${index + 1}`}</h4>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="section-card-content">
                    <p>${section.content || 'No content'}</p>
                </div>
            </div>
        `).join('');
    }
    
    // Populate raw text
    document.getElementById('raw-text-content').textContent = doc.raw_text || 'No raw text available';
    
    // Populate JSON
    const jsonExport = {
        id: doc.id,
        filename: doc.filename,
        status: doc.status,
        metadata: doc.metadata,
        sections: doc.sections,
        page_count: doc.page_count,
        file_size: doc.file_size
    };
    document.getElementById('json-content').textContent = JSON.stringify(jsonExport, null, 2);
}

function toggleSection(el) {
    el.classList.toggle('expanded');
}

// Tab switching
document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const tabName = btn.dataset.tab;
        
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update active tab content
        document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));
        document.getElementById(`${tabName}-tab`).classList.add('active');
    });
});

// Copy and Download functions
document.getElementById('copy-raw-btn').addEventListener('click', () => {
    const text = document.getElementById('raw-text-content').textContent;
    navigator.clipboard.writeText(text);
    alert('Raw text copied to clipboard!');
});

document.getElementById('download-raw-btn').addEventListener('click', () => {
    if (!currentOutputDoc) return;
    const text = currentOutputDoc.raw_text || '';
    downloadFile(text, `${currentOutputDoc.filename || 'document'}_raw.txt`, 'text/plain');
});

document.getElementById('copy-json-btn').addEventListener('click', () => {
    const text = document.getElementById('json-content').textContent;
    navigator.clipboard.writeText(text);
    alert('JSON copied to clipboard!');
});

document.getElementById('download-json-btn').addEventListener('click', () => {
    if (!currentOutputDoc) return;
    const json = document.getElementById('json-content').textContent;
    downloadFile(json, `${currentOutputDoc.filename || 'document'}_output.json`, 'application/json');
});

function downloadFile(content, filename, contentType) {
    const blob = new Blob([content], { type: contentType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Refresh button
document.getElementById('refresh-docs-btn').addEventListener('click', loadDocuments);

// ============================================
// Utilities
// ============================================
function formatFileSize(bytes) {
    if (!bytes) return 'N/A';
    const units = ['B', 'KB', 'MB', 'GB'];
    let unitIndex = 0;
    let size = bytes;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
}

function truncateText(text, maxLength) {
    if (!text) return '';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

// ============================================
// Initialization
// ============================================
async function init() {
    await checkApiStatus();
    loadDashboard();
    
    // Periodic status check
    setInterval(checkApiStatus, 30000);
}

init();
