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
let currentUploadMode = 'single';
let batchFiles = [];

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
    if (pageName === 'batches') loadBatchesPage();
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

async function uploadBatch(files) {
    const formData = new FormData();
    files.forEach(f => formData.append('files', f));
    const response = await fetch(`${API_V1_URL}/upload/batch`, {
        method: 'POST',
        body: formData
    });
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Batch upload failed');
    }
    return await response.json();
}

async function fetchBatches() {
    try {
        const response = await fetch(`${API_V1_URL}/batches`);
        if (!response.ok) throw new Error('Failed to fetch batches');
        return await response.json();
    } catch (e) {
        console.error('Error fetching batches:', e);
        return { batches: [], total: 0 };
    }
}

async function fetchBatch(batchId) {
    try {
        const response = await fetch(`${API_V1_URL}/batches/${batchId}`);
        if (!response.ok) throw new Error('Batch not found');
        return await response.json();
    } catch (e) {
        console.error('Error fetching batch:', e);
        return null;
    }
}

async function processAllInBatch(batchId) {
    const batch = await fetchBatch(batchId);
    if (!batch) return;
    const promises = batch.documents
        .filter(d => d.status === 'uploaded')
        .map(d => processDocument(d.id || d.document_id).catch(() => {}));
    await Promise.all(promises);
}

// ============================================
// Dashboard
// ============================================
async function loadDashboard() {
    const data = await fetchDocuments();
    const documents = data.documents || [];
    const batchData = await fetchBatches();
    
    const stats = {
        total: documents.length,
        batches: batchData.total || 0,
        processing: documents.filter(d => d.status === 'processing').length,
        completed: documents.filter(d => d.status === 'completed').length,
        failed: documents.filter(d => d.status === 'failed').length
    };
    
    document.getElementById('total-docs').textContent = stats.total;
    document.getElementById('total-batches').textContent = stats.batches;
    document.getElementById('processing-docs').textContent = stats.processing;
    document.getElementById('completed-docs').textContent = stats.completed;
    document.getElementById('failed-docs').textContent = stats.failed;
    
    const recentList = document.getElementById('recent-docs-list');
    if (documents.length === 0) {
        recentList.innerHTML = '<p class="empty-state">No documents yet. Upload a PDF to get started!</p>';
        return;
    }
    const recentDocs = documents.slice(0, 5);
    recentList.innerHTML = recentDocs.map(doc => createDocumentCard(doc)).join('');
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
    const meta = doc.metadata || {};
    const caseNumber = meta.case_number || 'N/A';
    const court = meta.court || 'N/A';
    const outcome = doc.outcome;
    const outcomeHtml = outcome && outcome.classification
        ? `<span class="outcome-badge outcome-${outcome.classification.toLowerCase().replace(' ', '-')}">
               <i class="fas fa-gavel"></i> ${outcome.classification}
           </span>`
        : '';
    const batchHtml = doc.batch_id
        ? `<span><i class="fas fa-layer-group"></i> ${doc.batch_id}</span>`
        : '';
    return `
        <div class="document-card" data-doc-id="${doc.id || doc.document_id}">
            <div class="document-card-header">
                <h3>${doc.filename || 'Unknown'}</h3>
                <span class="status-badge ${statusClass}">${doc.status || 'Unknown'}</span>
            </div>
            <div class="document-card-meta">
                <span><i class="fas fa-hashtag"></i> ${caseNumber}</span>
                <span><i class="fas fa-landmark"></i> ${court}</span>
                ${batchHtml}
            </div>
            ${outcomeHtml ? `<div style="margin-top:.5rem;">${outcomeHtml}</div>` : ''}
            <div class="document-card-id">
                <i class="fas fa-fingerprint"></i> ${doc.id || doc.document_id}
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
    const outcome = doc.outcome || {};
    const timeline = doc.timeline || [];
    const citations = doc.citations || [];
    
    let html = `
        <div class="detail-section">
            <h4><i class="fas fa-info-circle"></i> Basic Information</h4>
            <div class="detail-grid">
                <div class="detail-item"><label>Document ID</label><span>${doc.id || doc.document_id}</span></div>
                <div class="detail-item"><label>Batch ID</label><span>${doc.batch_id || '—'}</span></div>
                <div class="detail-item"><label>Page Count</label><span>${doc.page_count || 'N/A'}</span></div>
                <div class="detail-item"><label>Status</label><span>${doc.status || 'Unknown'}</span></div>
            </div>
        </div>
    `;
    
    if (Object.keys(metadata).length > 0) {
        html += `
            <div class="detail-section">
                <h4><i class="fas fa-gavel"></i> Case Metadata</h4>
                <div class="detail-grid">
                    <div class="detail-item"><label>Case Number</label><span>${metadata.case_number || 'N/A'}</span></div>
                    <div class="detail-item"><label>Court</label><span>${metadata.court || 'N/A'}</span></div>
                    <div class="detail-item"><label>Year</label><span>${metadata.year || metadata.date || 'N/A'}</span></div>
                    <div class="detail-item"><label>Case Type</label><span>${metadata.case_type || 'N/A'}</span></div>
                </div>
            </div>
        `;
    }
    
    if (outcome.classification) {
        const cls = outcome.classification;
        html += `
            <div class="detail-section">
                <h4><i class="fas fa-gavel"></i> Outcome</h4>
                <div class="outcome-display outcome-${cls.toLowerCase().replace(' ', '-')}">
                    <span class="outcome-label">${cls}</span>
                    <span class="outcome-conf">${outcome.confidence != null ? outcome.confidence + '%' : ''}</span>
                    <p class="outcome-expl">${outcome.explanation || ''}</p>
                </div>
            </div>
        `;
    }
    
    if (timeline.length > 0) {
        html += `
            <div class="detail-section">
                <h4><i class="fas fa-stream"></i> Timeline (${timeline.length} events)</h4>
                <div class="timeline-mini">
                    ${timeline.slice(0, 3).map(e => `<div class="timeline-mini-item"><span class="tl-date">${e.date || '?'}</span><span>${e.event_name || ''}</span></div>`).join('')}
                    ${timeline.length > 3 ? `<p style="color:var(--text-secondary);font-size:.8rem;margin-top:.5rem;">+ ${timeline.length - 3} more events</p>` : ''}
                </div>
            </div>
        `;
    }
    
    if (citations.length > 0) {
        html += `
            <div class="detail-section">
                <h4><i class="fas fa-quote-left"></i> Citations (${citations.length})</h4>
                <div class="section-list">
                    ${citations.slice(0, 3).map(c => `<div class="section-item"><h5>${c.case_name || 'Unknown'} ${c.year ? '('+c.year+')' : ''}</h5><p>${c.usage || ''} — ${c.source || ''}</p></div>`).join('')}
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
                            <p>${truncateText(section.text || section.content, 200)}</p>
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
// Upload Mode Toggle
// ============================================
function setUploadMode(mode) {
    currentUploadMode = mode;
    document.getElementById('single-upload-section').classList.toggle('hidden', mode !== 'single');
    document.getElementById('batch-upload-section').classList.toggle('hidden', mode !== 'batch');
    document.getElementById('mode-single').classList.toggle('active', mode === 'single');
    document.getElementById('mode-batch').classList.toggle('active', mode === 'batch');
}

// Batch upload zone
const batchUploadZone = document.getElementById('batch-upload-zone');
const batchFileInput = document.getElementById('batch-file-input');

batchUploadZone.addEventListener('click', () => batchFileInput.click());
batchUploadZone.addEventListener('dragover', (e) => { e.preventDefault(); batchUploadZone.classList.add('dragover'); });
batchUploadZone.addEventListener('dragleave', () => batchUploadZone.classList.remove('dragover'));
batchUploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    batchUploadZone.classList.remove('dragover');
    addBatchFiles(Array.from(e.dataTransfer.files));
});
batchFileInput.addEventListener('change', () => {
    addBatchFiles(Array.from(batchFileInput.files));
    batchFileInput.value = '';
});

function addBatchFiles(files) {
    const pdfs = files.filter(f => f.name.toLowerCase().endsWith('.pdf'));
    if (pdfs.length < files.length) alert(`${files.length - pdfs.length} non-PDF file(s) skipped.`);
    batchFiles.push(...pdfs);
    renderBatchFileList();
}

function renderBatchFileList() {
    const listEl = document.getElementById('batch-file-list');
    const actionsEl = document.getElementById('batch-upload-actions');
    if (batchFiles.length === 0) {
        listEl.classList.add('hidden');
        actionsEl.classList.add('hidden');
        return;
    }
    listEl.classList.remove('hidden');
    actionsEl.classList.remove('hidden');
    listEl.innerHTML = batchFiles.map((f, i) => `
        <div class="batch-file-item">
            <i class="fas fa-file-pdf"></i>
            <span class="batch-file-name">${f.name}</span>
            <span class="batch-file-size">${formatFileSize(f.size)}</span>
            <button class="btn-icon" onclick="removeBatchFile(${i})" title="Remove"><i class="fas fa-times"></i></button>
        </div>
    `).join('');
}

function removeBatchFile(index) {
    batchFiles.splice(index, 1);
    renderBatchFileList();
}

function resetBatchUpload() {
    batchFiles = [];
    document.getElementById('batch-file-list').classList.add('hidden');
    document.getElementById('batch-upload-actions').classList.add('hidden');
    document.getElementById('batch-result').classList.add('hidden');
    document.getElementById('batch-upload-zone').classList.remove('hidden');
}

document.getElementById('clear-batch-btn').addEventListener('click', resetBatchUpload);

document.getElementById('start-batch-btn').addEventListener('click', async () => {
    if (batchFiles.length === 0) { alert('Please add at least one PDF file.'); return; }
    const btn = document.getElementById('start-batch-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Uploading...';
    try {
        const result = await uploadBatch(batchFiles);
        document.getElementById('batch-upload-zone').classList.add('hidden');
        document.getElementById('batch-file-list').classList.add('hidden');
        document.getElementById('batch-upload-actions').classList.add('hidden');
        const resultEl = document.getElementById('batch-result');
        resultEl.classList.remove('hidden');
        document.getElementById('batch-result-id').textContent = result.batch_id;
        const itemsEl = document.getElementById('batch-result-items');
        itemsEl.innerHTML = (result.documents || []).map(d => `
            <div class="batch-result-item ${d.status === 'uploaded' ? 'ok' : 'fail'}">
                <i class="fas ${d.status === 'uploaded' ? 'fa-check-circle' : 'fa-times-circle'}"></i>
                <span>${d.filename}</span>
                <code>${d.document_id || ''}</code>
            </div>
        `).join('');
    } catch (e) {
        alert('Batch upload failed: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-upload"></i> Upload All Files';
    }
});

// ============================================
// Batches Page
// ============================================
async function loadBatchesPage() {
    const container = document.getElementById('batches-container');
    container.innerHTML = '<p class="empty-state">Loading batches...</p>';
    const data = await fetchBatches();
    const batches = data.batches || [];
    if (batches.length === 0) {
        container.innerHTML = '<p class="empty-state">No batches found. Use Batch Upload to group documents.</p>';
        return;
    }
    container.innerHTML = batches.map(b => `
        <div class="batch-card" onclick="expandBatch('${b.batch_id}', this)">
            <div class="batch-card-header">
                <div>
                    <h3><i class="fas fa-layer-group"></i> ${b.batch_id}</h3>
                    <span>${b.document_count} document${b.document_count !== 1 ? 's' : ''}</span>
                </div>
                <div class="batch-card-actions">
                    <button class="btn btn-primary btn-sm" onclick="event.stopPropagation(); processBatch('${b.batch_id}', this)">
                        <i class="fas fa-cog"></i> Process All
                    </button>
                    <i class="fas fa-chevron-down"></i>
                </div>
            </div>
            <div class="batch-card-docs hidden"></div>
        </div>
    `).join('');
}

async function expandBatch(batchId, cardEl) {
    const docsEl = cardEl.querySelector('.batch-card-docs');
    const chevron = cardEl.querySelector('.fa-chevron-down');
    if (!docsEl.classList.contains('hidden')) {
        docsEl.classList.add('hidden');
        chevron.style.transform = '';
        return;
    }
    docsEl.innerHTML = '<p style="padding:1rem;color:var(--text-secondary);">Loading...</p>';
    docsEl.classList.remove('hidden');
    chevron.style.transform = 'rotate(180deg)';
    const batch = await fetchBatch(batchId);
    if (!batch || batch.documents.length === 0) {
        docsEl.innerHTML = '<p style="padding:1rem;color:var(--text-secondary);">No documents found.</p>';
        return;
    }
    docsEl.innerHTML = batch.documents.map(doc => createDocumentCard(doc)).join('');
    docsEl.querySelectorAll('.document-card').forEach(card => {
        card.addEventListener('click', () => openDocumentModal(card.dataset.docId));
    });
}

async function processBatch(batchId, btn) {
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Starting...';
    await processAllInBatch(batchId);
    btn.innerHTML = '<i class="fas fa-check"></i> Started!';
    setTimeout(() => { btn.disabled = false; btn.innerHTML = '<i class="fas fa-cog"></i> Process All'; }, 2000);
}

document.getElementById('refresh-batches-btn').addEventListener('click', loadBatchesPage);

// ============================================
// Output Page
// ============================================
async function loadOutputPage() {
    const select = document.getElementById('output-doc-select');
    await fetchDocuments();

    // Show all docs; completed ones labelled clearly
    select.innerHTML = '<option value="">-- Choose a document --</option>';
    allDocuments.forEach(doc => {
        const docId = doc.id || doc.document_id;
        const option = document.createElement('option');
        option.value = docId;
        const statusLabel = doc.status === 'completed' ? '' : ` [${doc.status}]`;
        option.textContent = `${doc.filename} (${doc.metadata?.case_number || docId})${statusLabel}`;
        if (doc.status !== 'completed') option.style.color = '#888';
        select.appendChild(option);
    });

    // Show empty state if no docs
    if (allDocuments.length === 0) {
        document.getElementById('output-empty').innerHTML = `
            <i class="fas fa-hourglass-half"></i>
            <h3>No Documents Yet</h3>
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
    if (!doc) { alert('Document not found'); return; }
    currentOutputDoc = doc;

    // DEBUG: log to console so we can verify what the API returned
    console.log('=== DOCUMENT DATA FROM API ===', {
        id: doc.id,
        status: doc.status,
        outcome: doc.outcome,
        timeline: (doc.timeline || []).length + ' events',
        citations: (doc.citations || []).length + ' items',
        insights: !!doc.insights,
        sections: (doc.sections || []).map(s => ({title: s.title, textLen: (s.text||s.content||'').length})),
    });

    document.getElementById('output-empty').classList.add('hidden');
    document.getElementById('output-content').classList.remove('hidden');

    // Status banner
    let statusBanner = document.getElementById('output-status-banner');
    if (!statusBanner) {
        statusBanner = document.createElement('div');
        statusBanner.id = 'output-status-banner';
        document.getElementById('output-content').prepend(statusBanner);
    }

    if (doc.status === 'completed') {
        const hasOutcome = !!(doc.outcome && doc.outcome.classification);
        const tlCount = (doc.timeline || []).length;
        const ciCount = (doc.citations || []).length;
        const hasInsights = !!doc.insights;
        const secCount = (doc.sections || []).length;

        const badge = (ok, label, extra) =>
            `<span style="display:inline-flex;align-items:center;gap:.3rem;padding:.2rem .6rem;border-radius:.5rem;font-size:.8rem;font-weight:600;margin:.2rem;
             background:${ok ? 'rgba(16,185,129,.15)' : 'rgba(239,68,68,.15)'};
             color:${ok ? 'var(--success)' : 'var(--error)'}">
             <i class="fas ${ok ? 'fa-check-circle' : 'fa-times-circle'}"></i> ${label}${extra ? ' ('+extra+')' : ''}
            </span>`;

        const allGood = hasOutcome && tlCount > 0 && ciCount > 0 && hasInsights && secCount > 0;

        statusBanner.style.cssText = `padding:.75rem 1.25rem;border-radius:.75rem;margin-bottom:1rem;
            background:${allGood ? 'rgba(16,185,129,.08)' : 'rgba(245,158,11,.1)'};
            border:1px solid ${allGood ? 'rgba(16,185,129,.3)' : 'rgba(245,158,11,.3)'};display:block;`;
        statusBanner.innerHTML = `
            <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:.5rem;">
              <span style="font-weight:600;color:${allGood ? 'var(--success)' : 'var(--warning)'}">
                <i class="fas ${allGood ? 'fa-check-circle' : 'fa-exclamation-triangle'}"></i>
                ${allGood ? 'All fields extracted' : 'Partial extraction — click Reprocess to retry'}
              </span>
              <div>
                ${badge(hasOutcome, 'Outcome')}
                ${badge(tlCount > 0, 'Timeline', tlCount + ' events')}
                ${badge(ciCount > 0, 'Citations', ciCount)}
                ${badge(hasInsights, 'Insights')}
                ${badge(secCount > 0, 'Sections', secCount)}
                ${!allGood ? `<button class="btn btn-primary btn-sm" style="margin-left:.5rem;" onclick="reprocessOutputDoc('${doc.id || doc.document_id}')"><i class="fas fa-redo"></i> Reprocess</button>` : ''}
              </div>
            </div>`;
    } else if (doc.status === 'processing') {
        statusBanner.style.cssText = 'padding:.75rem 1.25rem;border-radius:.75rem;margin-bottom:1rem;background:rgba(245,158,11,.12);color:var(--warning);display:block;';
        statusBanner.innerHTML = '<i class="fas fa-spinner fa-spin"></i> This document is currently being processed. Refresh to see results.';
    } else if (doc.status === 'failed') {
        statusBanner.style.cssText = 'padding:.75rem 1.25rem;border-radius:.75rem;margin-bottom:1rem;background:rgba(239,68,68,.12);color:var(--error);display:block;';
        statusBanner.innerHTML = `<i class="fas fa-exclamation-circle"></i> Processing failed: ${doc.error_message || 'Unknown error'}. <button class="btn btn-primary btn-sm" style="margin-left:.5rem;" onclick="reprocessOutputDoc('${doc.id || doc.document_id}')"><i class="fas fa-redo"></i> Reprocess</button>`;
    } else {
        statusBanner.style.cssText = 'padding:.75rem 1.25rem;border-radius:.75rem;margin-bottom:1rem;background:rgba(79,70,229,.1);color:var(--primary-light);display:block;';
        statusBanner.innerHTML = '<i class="fas fa-info-circle"></i> Document uploaded but not yet processed. Select it in the Documents page and click Process.';
    }

    // Helper: safely convert any value to an array of strings
    const toArr = (v, splitOn = /[;|]+/) => {
        if (!v) return [];
        if (Array.isArray(v)) return v.map(String).filter(Boolean);
        if (typeof v === 'string') return v.split(splitOn).map(s => s.trim()).filter(Boolean);
        return [String(v)];
    };

    const metadata = doc.metadata || {};

    // ---- METADATA TAB ----
    document.getElementById('case-metadata').innerHTML = [
        ['Case Number', metadata.case_number],
        ['Court', metadata.court],
        ['Date', metadata.date],
        ['Year', metadata.year],
        ['Case Type', metadata.case_type],
        ['Page Count', doc.page_count],
        ['Batch ID', doc.batch_id]
    ].map(([label, val]) => `
        <div class="metadata-item">
            <label>${label}</label>
            <div class="value">${val || '<span style="color:var(--text-secondary)">N/A</span>'}</div>
        </div>`).join('');

    const petitioners = toArr(metadata.petitioners, /[,;|]+/);
    const respondents = toArr(metadata.respondents, /[,;|]+/);
    const judges      = toArr(metadata.judges, /,\s*/);
    const parties     = toArr(metadata.parties, /[,;|]+/);
    document.getElementById('parties-metadata').innerHTML = [
        ['Petitioners', petitioners.length ? petitioners : null],
        ['Respondents', respondents.length ? respondents : null],
        ['All Parties', !petitioners.length && parties.length ? parties : null],
        ['Judges', judges.length ? judges : null]
    ].filter(([, v]) => v).map(([label, arr]) => `
        <div class="metadata-item" style="grid-column:span 2;">
            <label>${label}</label>
            <div class="value list">${arr.map(p => `<span class="tag">${p}</span>`).join('')}</div>
        </div>`).join('');

    const provisions = toArr(metadata.legal_provisions);
    document.getElementById('legal-provisions-metadata').innerHTML = provisions.length
        ? `<div class="provision-list">${provisions.map(p => `<span class="provision-tag">${p.trim()}</span>`).join('')}</div>`
        : '<p style="color:var(--text-secondary);padding:.5rem;">No legal provisions extracted</p>';

    // ---- OUTCOME TAB ----
    const outcome = doc.outcome;
    const outEl = document.getElementById('outcome-content');
    if (outcome && outcome.classification) {
        const cls = outcome.classification;
        const conf = outcome.confidence != null ? outcome.confidence : null;
        outEl.innerHTML = `
            <div class="outcome-card outcome-${cls.toLowerCase().replace(' ', '-')}">
                <div class="outcome-header">
                    <span class="outcome-type">${cls}</span>
                    ${conf !== null ? `<span class="outcome-pct">${conf}% confidence</span>` : ''}
                </div>
                ${conf !== null ? `<div class="confidence-bar-wrap"><div class="confidence-bar-fill" style="width:${conf}%"></div></div>` : ''}
                <p class="outcome-explanation">${outcome.explanation || 'No explanation provided.'}</p>
            </div>`;
    } else if (doc.status === 'completed') {
        outEl.innerHTML = '<p class="empty-state">Outcome could not be extracted from this document. Try reprocessing.</p>';
    } else {
        outEl.innerHTML = '<p class="empty-state">Outcome not yet extracted. Process the document first.</p>';
    }

    // ---- SECTIONS TAB ----
    const sections = doc.sections || [];
    const sectionsListEl = document.getElementById('sections-list');
    if (sections.length === 0) {
        sectionsListEl.innerHTML = '<p class="empty-state">No sections extracted</p>';
    } else {
        const sorted = [...sections].sort((a, b) => (a.order_index || 0) - (b.order_index || 0));
        sectionsListEl.innerHTML = sorted.map((section, i) => `
            <div class="section-card expanded" onclick="toggleSection(this)">
                <div class="section-card-header">
                    <h4><i class="fas fa-bookmark"></i> ${section.order_index ? section.order_index + '. ' : ''}${section.title || 'Section ' + (i+1)}</h4>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="section-card-content">
                    <p>${section.text || section.content || '<em style="color:var(--text-secondary)">No content extracted for this section.</em>'}</p>
                </div>
            </div>`).join('');
    }

    // ---- TIMELINE TAB ----
    const timeline = doc.timeline || [];
    const tlEl = document.getElementById('timeline-content');
    if (timeline.length === 0) {
        tlEl.innerHTML = '<p class="empty-state">No timeline extracted</p>';
    } else {
        tlEl.innerHTML = `<div class="timeline">${timeline.map(e => `
            <div class="timeline-event">
                <div class="timeline-dot"></div>
                <div class="timeline-body">
                    <div class="timeline-event-header">
                        <span class="timeline-event-name">${e.event_name || 'Event'}</span>
                        <span class="timeline-event-type">${e.event_type || ''}</span>
                        <span class="timeline-date">${e.date || '—'}</span>
                    </div>
                    <p>${e.description || ''}</p>
                </div>
            </div>`).join('')}</div>`;
    }

    // ---- CITATIONS TAB ----
    const citations = doc.citations || [];
    const citEl = document.getElementById('citations-content');
    if (citations.length === 0) {
        citEl.innerHTML = '<p class="empty-state">No citations extracted</p>';
    } else {
        const usageColors = { Precedent: 'var(--primary-light)', Principle: 'var(--success)', Reference: 'var(--warning)' };
        citEl.innerHTML = `<div class="citations-grid">${citations.map(c => `
            <div class="citation-card">
                <div class="citation-header">
                    <h4>${c.case_name || 'Unknown Case'}</h4>
                    <span class="citation-year">${c.year || ''}</span>
                </div>
                <div class="citation-source">${c.source || '—'}</div>
                <span class="citation-usage" style="background:${usageColors[c.usage] || 'var(--secondary)'}20;color:${usageColors[c.usage] || 'var(--secondary)'}">${c.usage || 'Reference'}</span>
            </div>`).join('')}</div>`;
    }

    // ---- INSIGHTS TAB ----
    const insights = doc.insights;
    const insEl = document.getElementById('insights-content');
    if (!insights) {
        insEl.innerHTML = '<p class="empty-state">No insights extracted</p>';
    } else {
        const riskColors = { High: 'var(--error)', Medium: 'var(--warning)', Low: 'var(--success)' };
        const riskColor = riskColors[insights.risk_level] || 'var(--secondary)';
        insEl.innerHTML = `
            <div class="insights-grid">
                <div class="insight-card full">
                    <h4><i class="fas fa-exclamation-circle"></i> Key Legal Issues</h4>
                    <div class="tag-list">${toArr(insights.key_legal_issues, /[.;|]+/).map(i => `<span class="insight-tag">${i}</span>`).join('') || '<span style="color:var(--text-secondary)">None extracted</span>'}</div>
                </div>
                <div class="insight-card">
                    <h4><i class="fas fa-hand-paper"></i> Reliefs Requested</h4>
                    <p>${insights.reliefs_requested || '—'}</p>
                </div>
                <div class="insight-card">
                    <h4><i class="fas fa-check-circle"></i> Reliefs Granted</h4>
                    <p>${insights.reliefs_granted || '—'}</p>
                </div>
                <div class="insight-card">
                    <h4><i class="fas fa-building"></i> State Involvement</h4>
                    <p>${insights.state_involvement ? 'Yes &mdash; ' + (insights.state_involvement_level || '') : 'No'}</p>
                </div>
                <div class="insight-card">
                    <h4><i class="fas fa-balance-scale"></i> Doctrines &amp; Principles</h4>
                    <div class="tag-list">${toArr(insights.doctrines, /[.;|]+/).map(d => `<span class="insight-tag">${d}</span>`).join('') || '<span style="color:var(--text-secondary)">None</span>'}</div>
                </div>
                <div class="insight-card">
                    <h4><i class="fas fa-thermometer-half"></i> Risk / Importance</h4>
                    <span class="risk-badge" style="background:${riskColor}20;color:${riskColor}">${insights.risk_level || 'Unknown'}</span>
                </div>
            </div>`;
    }

    // ---- CONFIDENCE TAB ----
    const conf = doc.confidence_scores;
    const confEl = document.getElementById('confidence-content');
    if (!conf || Object.keys(conf).length === 0) {
        confEl.innerHTML = '<p class="empty-state">No confidence scores available</p>';
    } else {
        const scores = [
            ['Outcome Classification', conf.outcome, 'fa-gavel'],
            ['Section Segmentation', conf.sections, 'fa-list'],
            ['Citation Extraction', conf.citations, 'fa-quote-left'],
            ['Insights Generation', conf.insights, 'fa-lightbulb']
        ];
        confEl.innerHTML = `<div class="confidence-cards">${scores.map(([label, val, icon]) => {
            const pct = val != null ? Math.round(val) : null;
            const color = pct >= 80 ? 'var(--success)' : pct >= 60 ? 'var(--warning)' : 'var(--error)';
            return `
                <div class="conf-card">
                    <div class="conf-header">
                        <span><i class="fas ${icon}"></i> ${label}</span>
                        <span class="conf-pct" style="color:${color}">${pct !== null ? pct + '%' : 'N/A'}</span>
                    </div>
                    <div class="confidence-bar-wrap">
                        <div class="confidence-bar-fill" style="width:${pct || 0}%;background:${color};"></div>
                    </div>
                </div>`;
        }).join('')}</div>`;
    }

    // ---- RAW TEXT ----
    document.getElementById('raw-text-content').textContent = doc.raw_text || 'No raw text available';

    // ---- JSON EXPORT ----
    const jsonExport = {
        id: doc.id, document_id: doc.document_id, batch_id: doc.batch_id,
        filename: doc.filename, status: doc.status,
        metadata: doc.metadata, outcome: doc.outcome,
        sections: doc.sections, timeline: doc.timeline,
        citations: doc.citations, insights: doc.insights,
        confidence_scores: doc.confidence_scores,
        page_count: doc.page_count, file_size: doc.file_size
    };
    document.getElementById('json-content').textContent = JSON.stringify(jsonExport, null, 2);
}

function toggleSection(el) {
    el.classList.toggle('expanded');
}

async function reprocessOutputDoc(docId) {
    if (!confirm('Reprocess this document? The existing data will be replaced.')) return;
    try {
        const response = await fetch(`${API_V1_URL}/process/${docId}?force=true`, { method: 'POST' });
        if (!response.ok) { const err = await response.json(); throw new Error(err.detail || 'Failed'); }
        alert('Reprocessing started! Refresh the output page in ~1-2 minutes to see updated results.');
    } catch (e) {
        alert('Error starting reprocess: ' + e.message);
    }
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
