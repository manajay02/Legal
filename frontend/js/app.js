// Main Application Logic
class LegalCriticApp {
    constructor() {
        this.pendingSupportFiles = [];
        this.uploadedSupportDocs = []; // { doc_id, filename, file_type, text_length }
        this.init();
    }

    /**
     * Initialize the application
     */
    async init() {
        this.setupEventListeners();
        await this.checkAPIStatus();
    }

    /**
     * Setup all event listeners
     */
    setupEventListeners() {
        // Text analysis
        const argumentText = document.getElementById('argumentText');
        argumentText.addEventListener('input', () => {
            UI.updateCharCount(argumentText.value.length);
        });

        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeText();
        });

        // Supporting documents upload
        const supportFileInput = document.getElementById('supportFileInput');
        const supportUploadArea = document.getElementById('supportUploadArea');
        const supportUploadBtn = document.getElementById('supportUploadBtn');

        supportUploadArea.addEventListener('click', () => {
            supportFileInput.click();
        });

        supportFileInput.addEventListener('change', (e) => {
            this.handleSupportFileSelection(Array.from(e.target.files || []));
            supportFileInput.value = '';
        });

        supportUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            supportUploadArea.classList.add('dragover');
        });

        supportUploadArea.addEventListener('dragleave', () => {
            supportUploadArea.classList.remove('dragover');
        });

        supportUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            supportUploadArea.classList.remove('dragover');
            const files = Array.from(e.dataTransfer.files || []);
            this.handleSupportFileSelection(files);
        });

        supportUploadBtn.addEventListener('click', () => {
            this.uploadSupportingDocuments();
        });
    }

    /**
     * Check API status on startup
     */
    async checkAPIStatus() {
        const health = await API.checkHealth();
        UI.updateAPIStatus(health !== null);
    }

    /**
     * Validate text input
     */
    validateText(text) {
        if (text.length < CONFIG.MIN_TEXT_LENGTH) {
            UI.showError('textResults', `Text must be at least ${CONFIG.MIN_TEXT_LENGTH} characters long`);
            return false;
        }
        if (text.length > CONFIG.MAX_TEXT_LENGTH) {
            UI.showError('textResults', `Text must not exceed ${CONFIG.MAX_TEXT_LENGTH} characters`);
            return false;
        }
        return true;
    }

    /**
     * Analyze text argument
     */
    async analyzeText() {
        const text = document.getElementById('argumentText').value;
        const analyzeBtn = document.getElementById('analyzeBtn');

        // Validation
        if (!this.validateText(text)) {
            return;
        }

        // Show loading state
        analyzeBtn.disabled = true;
        analyzeBtn.textContent = 'Analyzing...';
        UI.showLoading('textResults');

        try {
            const docIds = this.uploadedSupportDocs.map(d => d.doc_id);
            const data = await API.analyzeTextGrounded(text, docIds, true);
            UI.displayResults(data, 'textResults');
        } catch (error) {
            console.error('Analysis error:', error);
            UI.showError('textResults', error.message);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Argument';
        }
    }

    handleSupportFileSelection(files) {
        if (!files || files.length === 0) return;
        const validTypes = ['.pdf', '.txt'];
        const accepted = files.filter(f => {
            const ext = '.' + f.name.split('.').pop().toLowerCase();
            return validTypes.includes(ext) && f.size <= CONFIG.MAX_FILE_SIZE;
        });
        // Merge, avoid duplicates by name
        accepted.forEach(f => {
            if (!this.pendingSupportFiles.find(p => p.name === f.name))
                this.pendingSupportFiles.push(f);
        });
        document.getElementById('supportUploadBtn').disabled = (this.pendingSupportFiles.length === 0);
        this.renderSupportDocsList();
    }

    removePendingFile(index) {
        this.pendingSupportFiles.splice(index, 1);
        document.getElementById('supportUploadBtn').disabled = (this.pendingSupportFiles.length === 0);
        this.renderSupportDocsList();
    }

    removeUploadedDoc(index) {
        this.uploadedSupportDocs.splice(index, 1);
        this.renderSupportDocsList();
    }

    clearAllDocs() {
        this.pendingSupportFiles = [];
        this.uploadedSupportDocs = [];
        document.getElementById('supportUploadBtn').disabled = true;
        this.renderSupportDocsList();
    }

    async uploadSupportingDocuments() {
        if (!this.pendingSupportFiles || this.pendingSupportFiles.length === 0) return;

        const btn = document.getElementById('supportUploadBtn');
        btn.disabled = true;
        btn.textContent = 'Uploading...';

        const failed = [];
        for (const file of [...this.pendingSupportFiles]) {
            try {
                const res = await API.uploadSupportingDocument(file);
                this.uploadedSupportDocs.push(res);
                // remove from pending on success
                this.pendingSupportFiles = this.pendingSupportFiles.filter(f => f !== file);
            } catch (error) {
                console.error('Upload error:', error);
                failed.push(`${file.name}: ${error.message}`);
            }
        }

        this.renderSupportDocsList();
        btn.disabled = (this.pendingSupportFiles.length === 0);
        btn.textContent = 'Upload Supporting Documents';

        if (failed.length > 0) {
            alert('Some files failed to upload:\n' + failed.join('\n'));
        }
    }

    renderSupportDocsList() {
        const container = document.getElementById('supportDocsList');
        const pending  = this.pendingSupportFiles  || [];
        const uploaded = this.uploadedSupportDocs || [];

        if (pending.length === 0 && uploaded.length === 0) {
            container.innerHTML = '<p class="small" style="margin-top:10px;color:#999;">No documents selected.</p>';
            return;
        }

        const totalCount = pending.length + uploaded.length;
        let html = '<div class="doc-list">';

        // Header with Clear All
        html += `
            <div class="doc-list-header">
                <span class="doc-list-title">
                    ${uploaded.length} uploaded&nbsp;&nbsp;·&nbsp;&nbsp;${pending.length} pending
                </span>
                ${totalCount > 0
                    ? `<button class="btn-clear-all" onclick="window._app.clearAllDocs()">&#10005; Clear All</button>`
                    : ''}
            </div>`;

        // Uploaded docs (permanent until removed)
        uploaded.forEach((d, i) => {
            html += `
                <div class="doc-row">
                    <span class="doc-row-icon">📄</span>
                    <span class="doc-row-name" title="${UI.escapeHtml(d.filename)}">${UI.escapeHtml(d.filename)}</span>
                    <span class="doc-row-badge uploaded">✔ Uploaded</span>
                    <span class="doc-row-id" title="${UI.escapeHtml(d.doc_id)}">${UI.escapeHtml(d.doc_id.substring(0, 8))}&hellip;</span>
                    <button class="btn-remove-doc" title="Remove" onclick="window._app.removeUploadedDoc(${i})">&times;</button>
                </div>`;
        });

        // Pending (selected but not yet uploaded)
        pending.forEach((f, i) => {
            html += `
                <div class="doc-row pending">
                    <span class="doc-row-icon">⏳</span>
                    <span class="doc-row-name" title="${UI.escapeHtml(f.name)}">${UI.escapeHtml(f.name)}</span>
                    <span class="doc-row-badge pending">Pending</span>
                    <button class="btn-remove-doc" title="Remove" onclick="window._app.removePendingFile(${i})">&times;</button>
                </div>`;
        });

        html += '</div>';
        container.innerHTML = html;
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window._app = new LegalCriticApp();
});
