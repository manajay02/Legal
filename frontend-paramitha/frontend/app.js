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

// DOM Elements - will be initialized after DOM loads
let pages, navItems, apiStatusEl, modal;

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
    if (pageName === 'search') initSearchPage();
}

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

async function deleteDocument(docId) {
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }
        return await response.json();
    } catch (error) {
        console.error('Error deleting document:', error);
        throw error;
    }
}

async function deleteBatch(batchId) {
    try {
        const response = await fetch(`${API_V1_URL}/batches/${batchId}`, {
            method: 'DELETE'
        });
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Delete failed');
        }
        return await response.json();
    } catch (error) {
        console.error('Error deleting batch:', error);
        throw error;
    }
}

// Delete document with confirmation
async function deleteDocumentConfirm(docId, filename) {
    const confirmed = confirm(`Are you sure you want to delete "${filename}"?\n\nThis action cannot be undone and will permanently remove the document and all its data.`);
    
    if (!confirmed) return;
    
    try {
        await deleteDocument(docId);
        
        // Show success message
        alert(`Document "${filename}" deleted successfully!`);
        
        // Refresh the page content
        if (document.getElementById('documents-page').classList.contains('active')) {
            loadDocuments();
        }
        if (document.getElementById('dashboard-page').classList.contains('active')) {
            loadDashboard();
        }
        
        // Close modal if it was open for this document
        if (currentDocId === docId) {
            closeModal();
        }
        
    } catch (error) {
        alert(`Error deleting document: ${error.message}`);
    }
}

// Delete batch with confirmation
async function deleteBatchConfirm(batchId, documentCount) {
    const confirmed = confirm(`Are you sure you want to delete batch "${batchId}"?\n\nThis will permanently delete ${documentCount} document${documentCount !== 1 ? 's' : ''} and cannot be undone.`);
    
    if (!confirmed) return;
    
    try {
        await deleteBatch(batchId);
        
        // Show success message
        alert(`Batch "${batchId}" with ${documentCount} document${documentCount !== 1 ? 's' : ''} deleted successfully!`);
        
        // Refresh the page content
        if (document.getElementById('batches-page').classList.contains('active')) {
            loadBatchesPage();
        }
        if (document.getElementById('dashboard-page').classList.contains('active')) {
            loadDashboard();
        }
        if (document.getElementById('documents-page').classList.contains('active')) {
            loadDocuments();
        }
        
    } catch (error) {
        alert(`Error deleting batch: ${error.message}`);
    }
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
                <div class="card-header-actions">
                    <span class="status-badge ${statusClass}">${doc.status || 'Unknown'}</span>
                    <button class="btn-delete" onclick="event.stopPropagation(); deleteDocumentConfirm('${doc.id || doc.document_id}', '${(doc.filename || 'Unknown').replace("'", "\\'")}')"
                        title="Delete document" aria-label="Delete document">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
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
                            <h5>
                                ${section.title || 'Untitled Section'}
                                ${section.page_start ? `<span class="section-meta-badge" style="margin-left:.4rem;"><i class="fas fa-file"></i> p.${section.page_start}</span>` : ''}
                            </h5>
                            <p>${truncateText(section.text || section.content, 200)}</p>
                            ${(section.clauses||[]).length > 0 ? `<p style="font-size:.75rem;color:var(--primary-light);margin-top:.25rem;"><i class="fas fa-list-ol"></i> ${section.clauses.length} clause(s)</p>` : ''}
                        </div>
                    `).join('')}
                    ${sections.length > 3 ? `<p style="text-align:center;color:var(--text-secondary);">+ ${sections.length - 3} more sections</p>` : ''}
                </div>
            </div>
        `;
    }
    
    // Add action buttons
    let actionButtonsHtml = '';
    
    if (doc.status === 'uploaded') {
        actionButtonsHtml += `
            <button class="btn btn-primary" onclick="processDocumentFromModal('${doc.id}')">
                <i class="fas fa-cog"></i> Process Document
            </button>
        `;
    } else if (doc.status === 'completed') {
        actionButtonsHtml += `
            <button class="btn btn-primary" onclick="viewOutputFromModal('${doc.id}')">
                <i class="fas fa-eye"></i> View Full Output
            </button>
        `;
    }
    
    // Always add delete button
    actionButtonsHtml += `
        <button class="btn btn-danger" onclick="deleteDocumentFromModal('${doc.id}', '${(doc.filename || 'Unknown').replace("'", "\\'")}')">
            <i class="fas fa-trash"></i> Delete Document
        </button>
    `;

    if (actionButtonsHtml) {
        html += `
            <div class="detail-section">
                <div class="action-buttons">
                    ${actionButtonsHtml}
                </div>
            </div>
        `;
    }

    // Add Notes Section for Quick Implementation
    html += `
        <div class="detail-section">
            <h4><i class="fas fa-sticky-note"></i> Notes</h4>
            <div id="notes-section">
                <div class="notes-container" id="notes-container-${doc.id}">
                    <p style="color: #666;">Loading notes...</p>
                </div>
                <div class="add-note-form">
                    <div class="note-form-controls">
                        <div class="section-selector-container">
                            <label for="note-section-select">Add note to:</label>
                            <select id="note-section-select" class="section-select">
                                <option value="document">Entire Document</option>
                                ${(doc.sections || []).map((section, index) => 
                                    `<option value="${index}">Section ${index + 1}: ${section.title || 'Untitled'}</option>`
                                ).join('')}
                            </select>
                        </div>
                    </div>
                    <textarea id="new-note-content" placeholder="Add a note..." rows="3"></textarea>
                    <button class="btn btn-primary btn-sm" onclick="addUnifiedNote('${doc.id}')">
                        <i class="fas fa-plus"></i> Add Note
                    </button>
                </div>
            </div>
        </div>
    `;

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

async function deleteDocumentFromModal(docId, filename) {
    closeModal();
    // Use the existing delete confirmation function
    await deleteDocumentConfirm(docId, filename);
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
                    <button class="btn btn-danger btn-sm" onclick="event.stopPropagation(); deleteBatchConfirm('${b.batch_id}', ${b.document_count})" 
                        title="Delete entire batch">
                        <i class="fas fa-trash"></i>
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
        sectionsListEl.innerHTML = sorted.map((section, i) => {
            // Build meta badges (section number + page start)
            const metaBadges = [
                section.section_number ? `<span class="section-meta-badge"><i class="fas fa-hashtag"></i> § ${section.section_number}</span>` : '',
                section.page_start    ? `<span class="section-meta-badge"><i class="fas fa-file"></i> Page ${section.page_start}</span>` : ''
            ].filter(Boolean).join('');

            // Build clauses list
            const clauses = section.clauses || [];
            const clausesHtml = clauses.length > 0 ? `
                <div class="clauses-container">
                    <div class="clauses-header"><i class="fas fa-list-ol"></i> Clauses (${clauses.length})</div>
                    <div class="clauses-list">
                        ${clauses.map(cl => `
                            <div class="clause-item">
                                <div class="clause-item-meta">
                                    ${cl.clause_number ? `<span class="clause-num">${cl.clause_number}</span>` : ''}
                                    ${cl.page_number   ? `<span class="clause-page"><i class="fas fa-file"></i> p.${cl.page_number}</span>` : ''}
                                </div>
                                <p class="clause-text">${cl.text || ''}</p>
                            </div>`).join('')}
                    </div>
                </div>` : '';

            return `
            <div class="section-card expanded" onclick="toggleSection(this)">
                <div class="section-card-header">
                    <div style="display:flex;align-items:center;gap:.6rem;flex-wrap:wrap;">
                        <h4 style="margin:0;"><i class="fas fa-bookmark"></i> ${section.order_index ? section.order_index + '. ' : ''}${section.title || 'Section ' + (i+1)}</h4>
                        ${metaBadges}
                    </div>
                    <i class="fas fa-chevron-down"></i>
                </div>
                <div class="section-card-content">
                    <p>${section.text || section.content || '<em style="color:var(--text-secondary)">No content extracted for this section.</em>'}</p>
                    ${clausesHtml}
                    
                    <!-- Section Notes -->
                    <div class="section-notes" onclick="event.stopPropagation();">
                        <div class="section-notes-header">
                            <h5><i class="fas fa-sticky-note"></i> Section Notes</h5>
                        </div>
                        <div class="section-notes-container" id="section-notes-container-${i}">
                            <p style="color: #666; font-size: 12px;">Loading notes...</p>
                        </div>
                        <div class="section-note-form">
                            <textarea id="section-note-input-${i}" placeholder="Add a note about this section..." rows="2"></textarea>
                            <button class="btn btn-sm btn-primary" onclick="addSectionNote('${doc.id || doc.document_id}', ${i})">
                                <i class="fas fa-plus"></i> Add Note
                            </button>
                        </div>
                    </div>
                </div>
            </div>`;
        }).join('');
        
        // Load section notes for all sections
        if (doc.id || doc.document_id) {
            const documentId = doc.id || doc.document_id;
            for (let i = 0; i < sections.length; i++) {
                loadSectionNotes(documentId, i);
            }
        }
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
    // Initialize DOM elements
    pages = document.querySelectorAll('.page');
    navItems = document.querySelectorAll('.nav-item');
    apiStatusEl = document.getElementById('api-status');
    modal = document.getElementById('document-modal');
    
    // Setup navigation event listeners
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const pageName = item.dataset.page;
            navigateTo(pageName);
        });
    });
    
    await checkApiStatus();
    loadDashboard();
    
    // Periodic status check
    setInterval(checkApiStatus, 30000);
}

// Wait for DOM to be ready before initializing
document.addEventListener('DOMContentLoaded', init);


// ============================================================
// SEARCH PAGE
// ============================================================

let _searchResults = []; // current result set for re-sorting

async function initSearchPage() {
    await loadSearchPresets();
    await refreshIndexStatus();
}

// --------- index status ----------
async function refreshIndexStatus() {
    const bar = document.getElementById('index-status-bar');
    const txt = document.getElementById('index-status-text');
    if (!bar || !txt) return;
    try {
        const res = await fetch(`${API_V1_URL}/search/index/status`);
        if (res.ok) {
            const data = await res.json();
            txt.innerHTML = `<b>${data.index_size}</b> vectors in FAISS index &nbsp;|&nbsp; <b>${data.total}</b> total documents`;
            bar.classList.remove('index-warn');
            if (data.index_size === 0 && data.total > 0) {
                txt.innerHTML += ' &nbsp;<span style="color:var(--warning)">⚠ Index empty – click Rebuild Index</span>';
                bar.classList.add('index-warn');
            }
        }
    } catch (e) {
        txt.textContent = 'Could not fetch index status';
    }
}

// --------- presets ----------
async function loadSearchPresets() {
    const row = document.getElementById('presets-row');
    if (!row) return;
    try {
        const res = await fetch(`${API_V1_URL}/search/presets`);
        if (!res.ok) return;
        const data = await res.json();
        const presets = data.presets || {};
        // keep the label
        row.innerHTML = '<span class="presets-label">Quick filters:</span>';
        Object.entries(presets).forEach(([id, preset]) => {
            const chip = document.createElement('button');
            chip.className = 'preset-chip';
            chip.textContent = preset.label;
            chip.title = preset.description || '';
            chip.onclick = () => applyPreset(id, preset);
            row.appendChild(chip);
        });
    } catch (e) { /* ignore */ }
}

function applyPreset(id, preset) {
    // Set filter drawer fields from preset
    const f = preset.filters || {};
    _setFilterField('f-outcome',     f.outcome      || '');
    _setFilterField('f-risk-level',  f.risk_level   || '');
    _setFilterField('f-state',       f.state_involvement !== undefined ? String(f.state_involvement) : '');
    _setFilterField('f-case-type',   f.case_type    || '');
    _setFilterField('f-legal-prov',  f.legal_provision || '');
    _setFilterField('f-year-from',   f.year_from    || '');
    _setFilterField('f-year-to',     f.year_to      || '');
    // Mark chip active
    document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
    const chips = document.querySelectorAll('.preset-chip');
    chips.forEach(c => { if (c.textContent === preset.label) c.classList.add('active'); });
    // Run search with preset label as query
    document.getElementById('search-query').value = preset.label;
    updateFilterBadge();
    runSearch();
}

function _setFilterField(id, val) {
    const el = document.getElementById(id);
    if (el) el.value = String(val);
}

// --------- filter drawer ----------
function toggleFilterDrawer() {
    const drawer  = document.getElementById('filter-drawer');
    const overlay = document.getElementById('filter-overlay');
    if (!drawer) return;
    drawer.classList.toggle('hidden');
    overlay.classList.toggle('hidden');
}

function clearFilters() {
    ['f-outcome','f-court','f-year-from','f-year-to','f-case-type',
     'f-legal-prov','f-risk-level','f-state','f-confidence','f-batch-id']
        .forEach(id => { const el = document.getElementById(id); if (el) el.value = ''; });
    document.querySelectorAll('.preset-chip').forEach(c => c.classList.remove('active'));
    updateFilterBadge();
}

function updateFilterBadge() {
    const fields = ['f-outcome','f-court','f-year-from','f-year-to','f-case-type',
                    'f-legal-prov','f-risk-level','f-state','f-confidence','f-batch-id'];
    const count = fields.filter(id => { const el = document.getElementById(id); return el && el.value.trim() !== ''; }).length;
    const badge = document.getElementById('filter-count');
    if (!badge) return;
    badge.textContent = count;
    count > 0 ? badge.classList.remove('hidden') : badge.classList.add('hidden');
}

function applyFiltersAndSearch() {
    toggleFilterDrawer();
    updateFilterBadge();
    runSearch();
}

// --------- core search ----------
async function runSearch() {
    const query = (document.getElementById('search-query')?.value || '').trim();
    if (!query) return;
    const alpha = parseFloat(document.getElementById('alpha-slider')?.value ?? 0.4);

    // Collect explicit filters
    const filters = {};
    const outcome = document.getElementById('f-outcome')?.value;
    if (outcome) filters.outcome = outcome;
    const court = document.getElementById('f-court')?.value?.trim();
    if (court) filters.court = court;
    const yf = document.getElementById('f-year-from')?.value;
    if (yf) filters.year_from = parseInt(yf);
    const yt = document.getElementById('f-year-to')?.value;
    if (yt) filters.year_to = parseInt(yt);
    const ct = document.getElementById('f-case-type')?.value?.trim();
    if (ct) filters.case_type = ct;
    const lp = document.getElementById('f-legal-prov')?.value?.trim();
    if (lp) filters.legal_provision = lp;
    const rl = document.getElementById('f-risk-level')?.value;
    if (rl) filters.risk_level = rl;
    const si = document.getElementById('f-state')?.value;
    if (si === 'true')  filters.state_involvement = true;
    if (si === 'false') filters.state_involvement = false;
    const conf = document.getElementById('f-confidence')?.value;
    if (conf) filters.confidence_min = parseFloat(conf);
    const batchId = document.getElementById('f-batch-id')?.value?.trim();
    if (batchId) filters.batch_id = batchId;

    const body = { query, filters, alpha, k: 50 };

    // Show loading
    const list = document.getElementById('search-results-list');
    list.innerHTML = '<div class="search-loading"><i class="fas fa-spinner fa-spin"></i> Searching...</div>';
    document.getElementById('search-empty-state').style.display = 'none';
    document.getElementById('search-results-header').style.display = 'none';

    try {
        const res = await fetch(`${API_V1_URL}/search`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body),
        });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        const data = await res.json();
        _searchResults = data.results || [];
        renderSearchResults(_searchResults, data);
    } catch (e) {
        list.innerHTML = `<div class="error-msg"><i class="fas fa-exclamation-triangle"></i> Search failed: ${escapeHtml(e.message)}</div>`;
    }
}

function sortResults() {
    const key = document.getElementById('sort-select')?.value || 'final_score';
    const sorted = [..._searchResults].sort((a, b) => {
        if (key === 'year') return (b[key] || 0) - (a[key] || 0);
        return (b[key] || 0) - (a[key] || 0);
    });
    renderResultCards(sorted);
}

async function rebuildSearchIndex() {
    const btn = document.getElementById('rebuild-index-btn');
    if (btn) { btn.disabled = true; btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Rebuilding...'; }
    try {
        const res = await fetch(`${API_V1_URL}/search/index/rebuild`, { method: 'POST' });
        const data = await res.json();
        showToast(data.message || 'Index rebuild started', 'success');
    } catch (e) {
        showToast('Rebuild failed: ' + e.message, 'error');
    } finally {
        if (btn) { btn.disabled = false; btn.innerHTML = '<i class="fas fa-sync-alt"></i> Rebuild Index'; }
        setTimeout(refreshIndexStatus, 3000);
    }
}

// --------- render ----------
function renderSearchResults(results, data) {
    const header = document.getElementById('search-results-header');
    const empty  = document.getElementById('search-empty-state');
    const countEl = document.getElementById('search-results-count');
    if (results.length === 0) {
        document.getElementById('search-results-list').innerHTML = '';
        empty.style.display = 'flex';
        empty.innerHTML = '<i class="fas fa-search-minus"></i><h3>No results found</h3><p>Try adjusting your query or removing filters.</p>';
        header.style.display = 'none';
        return;
    }
    empty.style.display = 'none';
    header.style.display = 'flex';
    countEl.textContent = `${results.length} result${results.length !== 1 ? 's' : ''} found`;
    if (data?.parsed_filters && Object.keys(data.parsed_filters).length) {
        const f = JSON.stringify(data.parsed_filters, null, 0);
        countEl.textContent += ` · Filters: ${f}`;
    }
    renderResultCards(results);
}

function renderResultCards(results) {
    const list = document.getElementById('search-results-list');
    if (!list) return;
    list.innerHTML = '';
    results.forEach(r => list.appendChild(buildResultCard(r)));
}

function buildResultCard(r) {
    const card = document.createElement('div');
    card.className = 'search-result-card';

    // Score badge colour
    const score = r.final_score || 0;
    const scoreClass = score >= 70 ? 'score-high' : score >= 40 ? 'score-mid' : 'score-low';

    // Risk badge
    const riskBadge = r.risk_level
        ? `<span class="risk-badge risk-${(r.risk_level||'').toLowerCase()}">${escapeHtml(r.risk_level)}</span>`
        : '';

    // Outcome badge
    const outcomeBadge = r.outcome
        ? `<span class="outcome-badge outcome-${(r.outcome||'').toLowerCase().replace(' ','-')}">${escapeHtml(r.outcome)}</span>`
        : '';

    // State involvement
    const stateBadge = r.state_involvement === true
        ? '<span class="state-badge"><i class="fas fa-university"></i> State</span>'
        : '';

    // Confidence bar
    const conf = r.outcome_confidence != null
        ? `<div class="conf-bar-wrap" title="Extraction confidence"><div class="conf-bar" style="width:${r.outcome_confidence}%"></div><span>${r.outcome_confidence.toFixed(0)}%</span></div>`
        : '';

    // Legal issues chips
    const issueChips = (r.key_legal_issues || []).slice(0, 3)
        .map(i => `<span class="issue-chip">${escapeHtml(i)}</span>`).join('');

    card.innerHTML = `
        <div class="src-card-top">
            <div class="src-card-meta">
                <span class="src-case-num">${escapeHtml(r.case_number || r.filename || r.document_id)}</span>
                <span class="src-court">${escapeHtml(r.court || '—')}</span>
                <span class="src-year">${escapeHtml(String(r.year || '—'))}</span>
            </div>
            <div class="src-badges">${outcomeBadge}${riskBadge}${stateBadge}</div>
            <div class="src-score ${scoreClass}">
                <span class="score-num">${score.toFixed(0)}</span>
                <span class="score-lbl">/ 100</span>
            </div>
        </div>
        <div class="src-card-body">
            ${r.reasoning_summary ? `<p class="src-reasoning">${escapeHtml(r.reasoning_summary)}</p>` : ''}
            ${issueChips ? `<div class="src-issues">${issueChips}</div>` : ''}
        </div>
        <div class="src-card-footer">
            <div class="src-score-details">
                <span title="Semantic similarity"><i class="fas fa-brain"></i> ${r.semantic_score?.toFixed(1)}%</span>
                <span title="Filter match"><i class="fas fa-filter"></i> ${r.structured_score?.toFixed(1)}%</span>
                ${conf}
            </div>
            <button class="btn btn-sm" onclick="openDocumentModal('${escapeHtml(r.document_id)}')">
                <i class="fas fa-eye"></i> View
            </button>
        </div>
    `;
    return card;
}

// --------- toast ----------
function showToast(msg, type = 'info') {
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.style.cssText = 'position:fixed;bottom:1.5rem;right:1.5rem;z-index:9999;display:flex;flex-direction:column;gap:.5rem;';
        document.body.appendChild(container);
    }
    const toast = document.createElement('div');
    const colour = type === 'success' ? 'var(--success)' : type === 'error' ? 'var(--error)' : 'var(--primary)';
    toast.style.cssText = `background:${colour};color:#fff;padding:.75rem 1.25rem;border-radius:.5rem;font-size:.875rem;box-shadow:0 4px 12px rgba(0,0,0,.3);max-width:320px;`;
    toast.textContent = msg;
    container.appendChild(toast);
    setTimeout(() => toast.remove(), 4000);
}

// ============================================
// Notes Functions - Quick Implementation
// ============================================

// Unified Notes Loading Function - shows both document and section notes
async function loadNotesForDocument(docId) {
    // For compatibility with old calls, if no docId provided, use current document
    if (!docId && currentOutputDoc) {
        docId = currentOutputDoc.id;
    }
    
    // Update current document if different
    if (docId && (!currentOutputDoc || currentOutputDoc.id !== docId)) {
        const doc = allDocuments.find(d => d.id === docId);
        if (doc) {
            currentOutputDoc = doc;
        }
    }
    
    const container = document.getElementById(`notes-container-${docId}`);
    if (!container) {
        // If we're on the new notes page, use the new system
        if (document.getElementById('notes-display')) {
            await loadNotesForCurrentDocument();
        }
        return;
    }
    
    try {
        // Use the unified notes endpoint to get both document and section notes
        const response = await fetch(`${API_V1_URL}/documents/${docId}/all-notes`);
        if (!response.ok) throw new Error('Failed to load notes');
        
        const data = await response.json();
        const documentNotes = data.document_notes || [];
        const sectionNotes = data.section_notes || [];
        const totalNotes = data.total_notes || 0;
        
        if (totalNotes === 0) {
            container.innerHTML = '<p style="color: #666; font-style: italic;">No notes yet. Add your first note below!</p>';
            return;
        }
        
        // Render document notes section
        let notesHTML = '';
        if (documentNotes.length > 0) {
            notesHTML += `
                <div class="notes-section">
                    <h4 class="notes-section-title">
                        <i class="fas fa-file-text"></i> Document Notes
                        <span class="notes-count">(${documentNotes.length})</span>
                    </h4>
                    ${documentNotes.map(note => renderNoteItem(docId, note, 'document')).join('')}
                </div>
            `;
        }
        
        // Render section notes section
        if (sectionNotes.length > 0) {
            notesHTML += `
                <div class="notes-section">
                    <h4 class="notes-section-title">
                        <i class="fas fa-list"></i> Section Notes
                        <span class="notes-count">(${sectionNotes.length})</span>
                    </h4>
                    ${sectionNotes.map(note => renderNoteItem(docId, note, 'section')).join('')}
                </div>
            `;
        }
        
        container.innerHTML = notesHTML;
        
    } catch (error) {
        console.error('Error loading notes:', error);
        container.innerHTML = '<p style="color: #f56565;">Error loading notes</p>';
    }
}

// Helper function to render individual note items with type-specific styling
function renderNoteItem(docId, note, type) {
    const isSection = type === 'section';
    const sectionInfo = isSection ? `
        <div class="note-section-info">
            <i class="fas fa-link"></i> ${note.section_title || `Section ${note.section_index + 1}`}
        </div>
    ` : '';
    
    return `
        <div class="note-item ${type}-note" data-note-id="${note.id}" data-note-type="${type}" ${isSection ? `data-section-index="${note.section_index}"` : ''}>
            <div class="note-header">
                <div class="note-meta">
                    <span class="note-date">${new Date(note.created_at).toLocaleDateString()}</span>
                    <span class="note-type-badge ${type}">${isSection ? 'Section' : 'Document'}</span>
                </div>
                <div class="note-actions">
                    <button class="btn-icon" onclick="editUnifiedNote('${docId}', '${note.id}', '${type}', ${isSection ? note.section_index : 'null'})" title="Edit note">
                        <i class="fas fa-edit"></i>
                    </button>
                    <button class="btn-icon" onclick="deleteUnifiedNote('${docId}', '${note.id}', '${type}', ${isSection ? note.section_index : 'null'})" title="Delete note">
                        <i class="fas fa-trash"></i>
                    </button>
                    ${isSection ? `<button class="btn-icon" onclick="goToSection(${note.section_index})" title="Jump to section"><i class="fas fa-external-link-alt"></i></button>` : ''}
                </div>
            </div>
            ${sectionInfo}
            <div class="note-content" id="note-content-${note.id}">${escapeHtml(note.content)}</div>
            <div class="note-edit-form" id="note-edit-${note.id}" style="display:none;">
                <textarea id="edit-content-${note.id}" rows="3">${escapeHtml(note.content)}</textarea>
                <div class="edit-actions">
                    <button class="btn btn-sm btn-primary" onclick="saveUnifiedNoteEdit('${docId}', '${note.id}', '${type}', ${isSection ? note.section_index : 'null'})">Save</button>
                    <button class="btn btn-sm btn-secondary" onclick="cancelNoteEdit('${note.id}')">Cancel</button>
                </div>
            </div>
        </div>
    `;
}

async function addNote(docId) {
    const textarea = document.getElementById('new-note-content');
    const content = textarea.value.trim();
    
    if (!content) {
        showToast('Please enter a note', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content })
        });
        
        if (!response.ok) throw new Error('Failed to create note');
        
        textarea.value = ''; // Clear the textarea
        showToast('Note added successfully', 'success');
        loadNotesForDocument(docId); // Reload notes
        
    } catch (error) {
        console.error('Error adding note:', error);
        showToast('Error adding note', 'error');
    }
}

async function deleteNote(docId, noteId) {
    if (!confirm('Are you sure you want to delete this note?')) {
        return;
    }
    
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}/notes/${noteId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete note');
        
        showToast('Note deleted', 'success');
        loadNotesForDocument(docId); // Reload notes
        
    } catch (error) {
        console.error('Error deleting note:', error);
        showToast('Error deleting note', 'error');
    }
}

function editNote(docId, noteId, currentContent, buttonElement) {
    // Hide the note content and show edit form
    document.getElementById(`note-content-${noteId}`).style.display = 'none';
    document.getElementById(`note-edit-${noteId}`).style.display = 'block';
    
    // Hide edit button, show form
    buttonElement.style.display = 'none';
}

function cancelNoteEdit(noteId) {
    // Show the note content and hide edit form
    document.getElementById(`note-content-${noteId}`).style.display = 'block';
    document.getElementById(`note-edit-${noteId}`).style.display = 'none';
    
    // Show edit button again
    document.querySelector(`[onclick*="editNote"][onclick*="${noteId}"]`).style.display = 'inline-block';
}

async function saveNoteEdit(docId, noteId) {
    const textarea = document.getElementById(`edit-content-${noteId}`);
    const content = textarea.value.trim();
    
    if (!content) {
        showToast('Note cannot be empty', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}/notes/${noteId}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content })
        });
        
        if (!response.ok) throw new Error('Failed to update note');
        
        showToast('Note updated', 'success');
        loadNotesForDocument(docId); // Reload notes
        
    } catch (error) {
        console.error('Error updating note:', error);
        showToast('Error updating note', 'error');
    }
}

// Section Notes Functions
async function loadSectionNotes(docId, sectionIndex) {
    const container = document.getElementById(`section-notes-container-${sectionIndex}`);
    if (!container) return;
    
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}/sections/${sectionIndex}/notes`);
        if (!response.ok) throw new Error('Failed to load section notes');
        
        const data = await response.json();
        const notes = data.notes || [];
        
        if (notes.length === 0) {
            container.innerHTML = '<p style="color: #666; font-size: 12px; font-style: italic;">No notes for this section</p>';
        } else {
            container.innerHTML = notes.map(note => `
                <div class="section-note-item" data-note-id="${note.id}" style="position: relative;" onmouseover="this.querySelector('.section-note-actions').style.opacity='1'" onmouseout="this.querySelector('.section-note-actions').style.opacity='0'">
                    <div class="section-note-content" id="section-note-content-${note.id}">${escapeHtml(note.content)}</div>
                    <div class="section-note-edit-form" id="section-edit-form-${note.id}" style="display: none;">
                        <textarea id="section-edit-content-${note.id}" rows="3" style="width: 100%; padding: 8px; border: 1px solid #d1d5db; border-radius: 6px; font-family: inherit; resize: vertical; margin-bottom: 8px;">${escapeHtml(note.content)}</textarea>
                        <div style="display: flex; gap: 8px;">
                            <button onclick="saveSectionNoteEdit('${docId}', ${sectionIndex}, '${note.id}')" style="padding: 6px 12px; font-size: 12px; border: none; border-radius: 4px; cursor: pointer; background: #10b981; color: white;">
                                <i class="fas fa-check"></i> Save
                            </button>
                            <button onclick="cancelSectionNoteEdit('${note.id}')" style="padding: 6px 12px; font-size: 12px; border: none; border-radius: 4px; cursor: pointer; background: #6b7280; color: white;">
                                <i class="fas fa-times"></i> Cancel
                            </button>
                        </div>
                    </div>
                    <div class="section-note-actions" style="position: absolute; top: 8px; right: 8px; display: flex; gap: 4px; opacity: 0; transition: opacity 0.2s;">
                        <button onclick="editSectionNote('${note.id}')" style="background: none; border: none; color: #6b7280; font-size: 14px; cursor: pointer; padding: 4px; border-radius: 3px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;" title="Edit note" onmouseover="this.style.backgroundColor='#f3f4f6'; this.style.color='#374151';" onmouseout="this.style.backgroundColor=''; this.style.color='#6b7280';">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button onclick="deleteSectionNote('${docId}', ${sectionIndex}, '${note.id}')" style="background: none; border: none; color: #ef4444; font-size: 14px; cursor: pointer; padding: 4px; border-radius: 3px; width: 24px; height: 24px; display: flex; align-items: center; justify-content: center;" title="Delete note" onmouseover="this.style.backgroundColor='#f3f4f6';" onmouseout="this.style.backgroundColor='';">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                    <div class="section-note-meta" style="margin-top: 8px; font-size: 11px; color: #6b7280;">
                        Added ${new Date(note.created_at).toLocaleDateString()}
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error loading section notes:', error);
        container.innerHTML = '<p style="color: #f56565; font-size: 12px;">Error loading notes</p>';
    }
}

// Section Note Edit Functions
function editSectionNote(noteId) {
    const contentDiv = document.getElementById(`section-note-content-${noteId}`);
    const editForm = document.getElementById(`section-edit-form-${noteId}`);
    
    if (contentDiv && editForm) {
        contentDiv.style.display = 'none';
        editForm.style.display = 'block';
        
        const textarea = document.getElementById(`section-edit-content-${noteId}`);
        if (textarea) {
            textarea.focus();
        }
    }
}

function cancelSectionNoteEdit(noteId) {
    const contentDiv = document.getElementById(`section-note-content-${noteId}`);
    const editForm = document.getElementById(`section-edit-form-${noteId}`);
    
    if (contentDiv && editForm) {
        contentDiv.style.display = 'block';
        editForm.style.display = 'none';
    }
}

async function saveSectionNoteEdit(docId, sectionIndex, noteId) {
    const textarea = document.getElementById(`section-edit-content-${noteId}`);
    if (!textarea) return;
    
    const newContent = textarea.value.trim();
    if (!newContent) {
        alert('Note content cannot be empty');
        return;
    }
    
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}/sections/${sectionIndex}/notes/${noteId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent })
        });
        
        if (response.ok) {
            // Update the display
            const contentDiv = document.getElementById(`section-note-content-${noteId}`);
            const editForm = document.getElementById(`section-edit-form-${noteId}`);
            
            if (contentDiv && editForm) {
                contentDiv.innerHTML = escapeHtml(newContent);
                contentDiv.style.display = 'block';
                editForm.style.display = 'none';
            }
        } else {
            alert('Error updating note');
        }
    } catch (error) {
        console.error('Error updating section note:', error);
        alert('Error updating note');
    }
}

async function addSectionNote(docId, sectionIndex) {
    const textarea = document.getElementById(`section-note-input-${sectionIndex}`);
    const content = textarea.value.trim();
    
    if (!content) {
        showToast('Please enter a note', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}/sections/${sectionIndex}/notes`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content })
        });
        
        if (!response.ok) throw new Error('Failed to create section note');
        
        textarea.value = '';
        showToast('Section note added', 'success');
        loadSectionNotes(docId, sectionIndex);
        
        // Also refresh the unified notes view
        refreshAllNotes(docId);
        
    } catch (error) {
        console.error('Error adding section note:', error);
        showToast('Error adding section note', 'error');
    }
}

async function deleteSectionNote(docId, sectionIndex, noteId) {
    if (!confirm('Delete this section note?')) return;
    
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}/sections/${sectionIndex}/notes/${noteId}`, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete section note');
        
        showToast('Section note deleted', 'success');
        loadSectionNotes(docId, sectionIndex);
        
        // Also refresh the unified notes view
        refreshAllNotes(docId);
        
    } catch (error) {
        console.error('Error deleting section note:', error);
        showToast('Error deleting section note', 'error');
    }
}

// Edit section note
function editSectionNote(noteId) {
    const contentDiv = document.getElementById(`section-note-content-${noteId}`);
    const editForm = document.getElementById(`section-edit-form-${noteId}`);
    
    if (contentDiv && editForm) {
        contentDiv.style.display = 'none';
        editForm.style.display = 'block';
        
        const textarea = document.getElementById(`section-edit-content-${noteId}`);
        if (textarea) {
            textarea.focus();
        }
    }
}

// Cancel section note edit
function cancelSectionNoteEdit(noteId) {
    const contentDiv = document.getElementById(`section-note-content-${noteId}`);
    const editForm = document.getElementById(`section-edit-form-${noteId}`);
    
    if (contentDiv && editForm) {
        contentDiv.style.display = 'block';
        editForm.style.display = 'none';
    }
}

// Save section note edit  
async function saveSectionNoteEdit(docId, sectionIndex, noteId) {
    const textarea = document.getElementById(`section-edit-content-${noteId}`);
    if (!textarea) return;
    
    const newContent = textarea.value.trim();
    if (!newContent) {
        showToast('Note content cannot be empty', 'error');
        return;
    }
    
    try {
        const response = await fetch(`${API_V1_URL}/documents/${docId}/sections/${sectionIndex}/notes/${noteId}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content: newContent })
        });
        
        if (response.ok) {
            // Update the display
            const contentDiv = document.getElementById(`section-note-content-${noteId}`);
            const editForm = document.getElementById(`section-edit-form-${noteId}`);
            
            if (contentDiv && editForm) {
                contentDiv.innerHTML = escapeHtml(newContent);
                contentDiv.style.display = 'block';
                editForm.style.display = 'none';
            }
            showToast('Note updated successfully', 'success');
            
            // Also refresh the unified notes view
            refreshAllNotes(docId);
        } else {
            showToast('Error updating note', 'error');
        }
    } catch (error) {
        console.error('Error updating section note:', error);
        showToast('Error updating note', 'error');
    }
}

// ============================================
// Unified Notes Functions - Connects Document & Section Notes
// ============================================

// Edit unified note (works for both document and section notes)
function editUnifiedNote(docId, noteId, type, sectionIndex) {
    document.getElementById(`note-content-${noteId}`).style.display = 'none';
    document.getElementById(`note-edit-${noteId}`).style.display = 'block';
    
    const textarea = document.getElementById(`edit-content-${noteId}`);
    if (textarea) {
        textarea.focus();
    }
}

// Delete unified note (works for both document and section notes)
async function deleteUnifiedNote(docId, noteId, type, sectionIndex) {
    if (!confirm('Are you sure you want to delete this note?')) {
        return;
    }
    
    try {
        let endpoint;
        if (type === 'document') {
            endpoint = `${API_V1_URL}/documents/${docId}/notes/${noteId}`;
        } else {
            endpoint = `${API_V1_URL}/documents/${docId}/sections/${sectionIndex}/notes/${noteId}`;
        }
        
        const response = await fetch(endpoint, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error(`Failed to delete ${type} note`);
        
        showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} note deleted`, 'success');
        
        // Refresh both views
        loadNotesForDocument(docId);
        if (type === 'section') {
            loadSectionNotes(docId, sectionIndex);
        }
        
    } catch (error) {
        console.error(`Error deleting ${type} note:`, error);
        showToast(`Error deleting ${type} note`, 'error');
    }
}

// Save unified note edit (works for both document and section notes)
async function saveUnifiedNoteEdit(docId, noteId, type, sectionIndex) {
    const textarea = document.getElementById(`edit-content-${noteId}`);
    const content = textarea.value.trim();
    
    if (!content) {
        showToast('Note cannot be empty', 'error');
        return;
    }
    
    try {
        let endpoint;
        if (type === 'document') {
            endpoint = `${API_V1_URL}/documents/${docId}/notes/${noteId}`;
        } else {
            endpoint = `${API_V1_URL}/documents/${docId}/sections/${sectionIndex}/notes/${noteId}`;
        }
        
        const response = await fetch(endpoint, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ content })
        });
        
        if (!response.ok) throw new Error(`Failed to update ${type} note`);
        
        // Update the display
        document.getElementById(`note-content-${noteId}`).innerHTML = escapeHtml(content);
        document.getElementById(`note-content-${noteId}`).style.display = 'block';
        document.getElementById(`note-edit-${noteId}`).style.display = 'none';
        
        showToast(`${type.charAt(0).toUpperCase() + type.slice(1)} note updated`, 'success');
        
        // Refresh section view if it's a section note
        if (type === 'section') {
            loadSectionNotes(docId, sectionIndex);
        }
        
    } catch (error) {
        console.error(`Error updating ${type} note:`, error);
        showToast(`Error updating ${type} note`, 'error');
    }
}

// Navigate to a specific section from the notes view
function goToSection(sectionIndex) {
    // Switch to sections tab
    const sectionsTab = document.querySelector('[data-tab="sections"]');
    if (sectionsTab) {
        sectionsTab.click();
    }
    
    // Scroll to the section after a brief delay to ensure tab is loaded
    setTimeout(() => {
        const sectionElement = document.querySelector(`[data-section-index="${sectionIndex}"]`);
        if (sectionElement) {
            sectionElement.scrollIntoView({ 
                behavior: 'smooth', 
                block: 'start' 
            });
            
            // Add a highlight effect
            sectionElement.classList.add('highlighted-section');
            setTimeout(() => {
                sectionElement.classList.remove('highlighted-section');
            }, 3000);
        }
    }, 300);
}

// Enhanced add note function with section selection
async function addUnifiedNote(docId) {
    const textarea = document.getElementById('new-note-content');
    const sectionSelect = document.getElementById('note-section-select');
    const content = textarea.value.trim();
    
    if (!content) {
        showToast('Please enter a note', 'error');
        return;
    }
    
    const selectedSection = sectionSelect ? sectionSelect.value : '';
    
    try {
        let endpoint;
        let body;
        
        if (selectedSection === '' || selectedSection === 'document') {
            // Create document note
            endpoint = `${API_V1_URL}/documents/${docId}/notes`;
            body = JSON.stringify({ content });
        } else {
            // Create section note
            const sectionIndex = parseInt(selectedSection);
            endpoint = `${API_V1_URL}/documents/${docId}/sections/${sectionIndex}/notes`;
            body = JSON.stringify({ content });
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: body
        });
        
        if (!response.ok) throw new Error('Failed to create note');
        
        textarea.value = '';
        if (sectionSelect) sectionSelect.value = 'document';
        
        showToast('Note added successfully', 'success');
        
        // Refresh both views
        loadNotesForDocument(docId);
        if (selectedSection !== '' && selectedSection !== 'document') {
            loadSectionNotes(docId, parseInt(selectedSection));
        }
        
    } catch (error) {
        console.error('Error adding note:', error);
        showToast('Error adding note', 'error');
    }
}

// Function to refresh all notes when section notes are updated
function refreshAllNotes(docId) {
    loadNotesForDocument(docId);
}

// ============================================
// Enhanced Notes Page Implementation
// ============================================

let currentNotesDocument = null;
let allNotes = [];
let filteredNotes = [];

// Initialize Enhanced Notes System
function initializeNotesPage() {
    setupNotesEventListeners();
    loadNotesForCurrentDocument();
}

// Setup event listeners for notes page
function setupNotesEventListeners() {
    // Add note button
    const addNoteBtn = document.getElementById('add-note-btn');
    if (addNoteBtn) {
        addNoteBtn.addEventListener('click', addEnhancedNote);
    }
    
    // Clear note button
    const clearNoteBtn = document.getElementById('clear-note-btn');
    if (clearNoteBtn) {
        clearNoteBtn.addEventListener('click', clearNoteForm);
    }
    
    // Filter tabs (updated for new structure)
    const filterTabs = document.querySelectorAll('.filter-tab');
    filterTabs.forEach(tab => {
        tab.addEventListener('click', (e) => {
            // Remove active from all tabs
            filterTabs.forEach(t => t.classList.remove('active'));
            // Add active to clicked tab
            e.target.classList.add('active');
            // Apply filter
            applyNotesFilter(e.target.dataset.filter);
        });
    });
    
    // Category filter
    const categoryFilter = document.getElementById('category-filter');
    if (categoryFilter) {
        categoryFilter.addEventListener('change', (e) => {
            const activeFilter = document.querySelector('.filter-tab.active');
            applyNotesFilter(activeFilter ? activeFilter.dataset.filter : 'all', e.target.value);
        });
    }
    
    // Enter key in textarea
    const noteInput = document.getElementById('note-content-input');
    if (noteInput) {
        noteInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && e.ctrlKey) {
                addEnhancedNote();
            }
        });
    }
}

// Load notes for current document
async function loadNotesForCurrentDocument() {
    if (!currentOutputDoc) {
        showEmptyNotesState();
        return;
    }
    
    currentNotesDocument = currentOutputDoc;
    
    try {
        // Populate section selector
        populateSectionSelector(currentOutputDoc);
        
        // Load all notes
        const response = await fetch(`${API_V1_URL}/documents/${currentOutputDoc.id}/all-notes`);
        if (!response.ok) throw new Error('Failed to load notes');
        
        const data = await response.json();
        
        // Combine and process notes
        allNotes = [
            ...data.document_notes.map(note => ({...note, type: 'document'})),
            ...data.section_notes.map(note => ({...note, type: 'section'}))
        ];
        
        // Update stats
        updateNotesStats(data);
        
        // Display notes
        filteredNotes = [...allNotes];
        renderNotesList(filteredNotes);
        
    } catch (error) {
        console.error('Error loading notes:', error);
        showNotesError('Failed to load notes. Please try again.');
    }
}

// Populate section selector dropdown
function populateSectionSelector(doc) {
    const sectionSelect = document.getElementById('note-section-select');
    if (!sectionSelect) return;
    
    // Clear existing options except document option
    sectionSelect.innerHTML = '<option value="document">📄 Entire Document</option>';
    
    // Add section options
    if (doc.sections && doc.sections.length > 0) {
        doc.sections.forEach((section, index) => {
            const option = document.createElement('option');
            option.value = index;
            option.textContent = `📑 Section ${index + 1}: ${section.title || 'Untitled'}`;
            sectionSelect.appendChild(option);
        });
    }
}

// Update notes statistics
function updateNotesStats(data) {
    const totalCount = (data.document_notes.length + data.section_notes.length);
    
    document.getElementById('total-notes-count').textContent = totalCount;
    document.getElementById('doc-notes-count').textContent = data.document_notes.length;
    document.getElementById('section-notes-count').textContent = data.section_notes.length;
}

// Add enhanced note
async function addEnhancedNote() {
    const contentInput = document.getElementById('note-content-input');
    const sectionSelect = document.getElementById('note-section-select');
    const categorySelect = document.getElementById('note-category-select');
    
    const content = contentInput.value.trim();
    
    if (!content) {
        showToast('Please enter note content', 'error');
        return;
    }
    
    if (!currentNotesDocument) {
        showToast('No document selected', 'error');
        return;
    }
    
    try {
        const selectedSection = sectionSelect.value;
        const category = categorySelect.value;
        
        let endpoint, body;
        
        if (selectedSection === 'document') {
            // Create document note
            endpoint = `${API_V1_URL}/documents/${currentNotesDocument.id}/notes`;
            body = JSON.stringify({ content, category });
        } else {
            // Create section note
            const sectionIndex = parseInt(selectedSection);
            endpoint = `${API_V1_URL}/documents/${currentNotesDocument.id}/sections/${sectionIndex}/notes`;
            body = JSON.stringify({ content });
        }
        
        const response = await fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: body
        });
        
        if (!response.ok) throw new Error('Failed to create note');
        
        // Clear form
        clearNoteForm();
        
        // Show success message
        showToast('Note added successfully! 📝', 'success');
        
        // Reload notes
        await loadNotesForCurrentDocument();
        
    } catch (error) {
        console.error('Error adding note:', error);
        showToast('Error adding note', 'error');
    }
}

// Clear note form
function clearNoteForm() {
    document.getElementById('note-content-input').value = '';
    document.getElementById('note-section-select').value = 'document';
    document.getElementById('note-category-select').value = 'General';
}

// Apply notes filter
function applyNotesFilter(typeFilter = 'all', categoryFilter = 'all') {
    filteredNotes = allNotes.filter(note => {
        // Type filter
        if (typeFilter !== 'all' && note.type !== typeFilter) return false;
        
        // Category filter (only for document notes)
        if (categoryFilter !== 'all' && note.type === 'document' && note.category !== categoryFilter) return false;
        
        return true;
    });
    
    renderNotesList(filteredNotes);
}

// Render notes list
function renderNotesList(notes) {
    const container = document.getElementById('notes-display');
    
    if (notes.length === 0) {
        showEmptyNotesState();
        return;
    }
    
    const notesHTML = notes.map(note => createNoteCardHTML(note)).join('');
    container.innerHTML = notesHTML;
    
    // Attach event listeners
    attachNoteEventListeners();
}

// Create HTML for a note card
function createNoteCardHTML(note) {
    const isSection = note.type === 'section';
    const sectionInfo = isSection ? getSectionInfo(note.section_index) : null;
    
    return `
        <div class="note-card ${note.type}-note" data-note-id="${note.id}" data-note-type="${note.type}">
            <div class="note-header-enhanced">
                <div class="note-meta-enhanced">
                    <div class="note-badges">
                        <span class="note-badge type-${note.type}">
                            ${note.type === 'document' ? '📄 Document' : '📑 Section'}
                        </span>
                        ${note.category ? `<span class="note-badge category">${note.category}</span>` : ''}
                    </div>
                    ${isSection ? `
                        <div class="note-section-link">
                            <i class="fas fa-link"></i>
                            ${sectionInfo ? sectionInfo.title : `Section ${note.section_index + 1}`}
                        </div>
                    ` : ''}
                    <div class="note-date-enhanced">
                        📅 ${new Date(note.created_at).toLocaleDateString('en-US', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        })}
                    </div>
                </div>
                <div class="note-actions-enhanced">
                    <button class="note-action-btn edit" onclick="editEnhancedNote('${note.id}')">
                        <i class="fas fa-edit"></i> Edit
                    </button>
                    ${isSection ? `
                        <button class="note-action-btn go-to" onclick="goToNoteSection(${note.section_index})">
                            <i class="fas fa-external-link-alt"></i> Go to
                        </button>
                    ` : ''}
                    <button class="note-action-btn delete" onclick="deleteEnhancedNote('${note.id}', '${note.type}', ${note.section_index || 'null'})">
                        <i class="fas fa-trash"></i> Delete
                    </button>
                </div>
            </div>
            <div class="note-content-enhanced" id="note-content-${note.id}">
                ${escapeHtml(note.content)}
            </div>
        </div>
    `;
}

// Get section information
function getSectionInfo(sectionIndex) {
    if (!currentNotesDocument || !currentNotesDocument.sections) return null;
    const section = currentNotesDocument.sections[sectionIndex];
    return section ? {
        title: `Section ${sectionIndex + 1}: ${section.title || 'Untitled'}`,
        index: sectionIndex
    } : null;
}

// Edit enhanced note
function editEnhancedNote(noteId) {
    const note = allNotes.find(n => n.id === noteId);
    if (!note) return;
    
    // Fill form with note data
    document.getElementById('note-content-input').value = note.content;
    
    if (note.type === 'document') {
        document.getElementById('note-section-select').value = 'document';
        if (note.category) {
            document.getElementById('note-category-select').value = note.category;
        }
    } else {
        document.getElementById('note-section-select').value = note.section_index;
    }
    
    // Change button to update mode
    const addBtn = document.getElementById('add-note-btn');
    addBtn.innerHTML = '<i class="fas fa-save"></i> Update Note';
    addBtn.onclick = () => updateEnhancedNote(noteId);
    
    // Scroll to form
    document.querySelector('.add-note-card').scrollIntoView({ 
        behavior: 'smooth', 
        block: 'center' 
    });
}

// Update enhanced note
async function updateEnhancedNote(noteId) {
    const note = allNotes.find(n => n.id === noteId);
    if (!note) return;
    
    const content = document.getElementById('note-content-input').value.trim();
    
    if (!content) {
        showToast('Please enter note content', 'error');
        return;
    }
    
    try {
        let endpoint, body;
        
        if (note.type === 'document') {
            endpoint = `${API_V1_URL}/documents/${currentNotesDocument.id}/notes/${noteId}`;
            body = JSON.stringify({ 
                content, 
                category: document.getElementById('note-category-select').value 
            });
        } else {
            endpoint = `${API_V1_URL}/documents/${currentNotesDocument.id}/sections/${note.section_index}/notes/${noteId}`;
            body = JSON.stringify({ content });
        }
        
        const response = await fetch(endpoint, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: body
        });
        
        if (!response.ok) throw new Error('Failed to update note');
        
        // Reset form
        resetNoteForm();
        
        showToast('Note updated successfully! ✏️', 'success');
        
        // Reload notes
        await loadNotesForCurrentDocument();
        
    } catch (error) {
        console.error('Error updating note:', error);
        showToast('Error updating note', 'error');
    }
}

// Delete enhanced note
async function deleteEnhancedNote(noteId, noteType, sectionIndex) {
    if (!confirm('Are you sure you want to delete this note?')) return;
    
    try {
        let endpoint;
        
        if (noteType === 'document') {
            endpoint = `${API_V1_URL}/documents/${currentNotesDocument.id}/notes/${noteId}`;
        } else {
            endpoint = `${API_V1_URL}/documents/${currentNotesDocument.id}/sections/${sectionIndex}/notes/${noteId}`;
        }
        
        const response = await fetch(endpoint, {
            method: 'DELETE'
        });
        
        if (!response.ok) throw new Error('Failed to delete note');
        
        showToast('Note deleted! 🗑️', 'success');
        
        // Reload notes
        await loadNotesForCurrentDocument();
        
    } catch (error) {
        console.error('Error deleting note:', error);
        showToast('Error deleting note', 'error');
    }
}

// Go to note section
function goToNoteSection(sectionIndex) {
    // Switch to sections tab
    const sectionsTab = document.querySelector('[data-tab="sections"]');
    if (sectionsTab) {
        sectionsTab.click();
        
        // Wait for tab to load then scroll to section
        setTimeout(() => {
            const sectionElement = document.querySelector(`[data-section-index="${sectionIndex}"]`);
            if (sectionElement) {
                sectionElement.scrollIntoView({ behavior: 'smooth', block: 'start' });
                
                // Highlight effect
                sectionElement.classList.add('highlighted-section');
                setTimeout(() => {
                    sectionElement.classList.remove('highlighted-section');
                }, 3000);
            }
        }, 300);
    }
}

// Reset note form to add mode
function resetNoteForm() {
    clearNoteForm();
    const addBtn = document.getElementById('add-note-btn');
    addBtn.innerHTML = '<i class="fas fa-plus"></i> Add Note';
    addBtn.onclick = addEnhancedNote;
}

// Show empty notes state
function showEmptyNotesState() {
    const container = document.getElementById('notes-display');
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">
                <i class="fas fa-sticky-note"></i>
            </div>
            <h3 class="empty-title">No notes yet</h3>
            <p class="empty-description">Create your first note to get started organizing your thoughts and insights.</p>
        </div>
    `;
}

// Show notes error
function showNotesError(message) {
    const container = document.getElementById('notes-display');
    container.innerHTML = `
        <div class="empty-state">
            <div class="empty-icon">
                <i class="fas fa-exclamation-triangle"></i>
            </div>
            <h3 class="empty-title">Error Loading Notes</h3>
            <p class="empty-description">${message}</p>
        </div>
    `;
}
                <i class="fas fa-exclamation-triangle" style="color: var(--error)"></i>
            </div>
            <h3>Error Loading Notes</h3>
            <p>${message}</p>
            <button class="btn btn-primary" onclick="loadNotesForCurrentDocument()">
                <i class="fas fa-retry"></i> Try Again
            </button>
        </div>
    `;
}

// Attach event listeners to note elements
function attachNoteEventListeners() {
    // Any additional dynamic event listeners can be added here
}

// Initialize when tab is clicked
document.addEventListener('DOMContentLoaded', () => {
    // Setup tab click listener for notes
    const notesTab = document.querySelector('[data-tab="notes"]');
    if (notesTab) {
        notesTab.addEventListener('click', () => {
            setTimeout(initializeNotesPage, 100);
        });
    }
});

// ============================================
