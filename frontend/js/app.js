// Main Application Logic
class LegalCriticApp {
    constructor() {
        this.selectedFile = null;
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
        // Tab switching
        document.querySelectorAll('.tab').forEach(tab => {
            tab.addEventListener('click', (e) => this.switchTab(e.target.dataset.tab));
        });

        // Text analysis
        const argumentText = document.getElementById('argumentText');
        argumentText.addEventListener('input', () => {
            UI.updateCharCount(argumentText.value.length);
        });

        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeText();
        });

        // File upload
        const fileInput = document.getElementById('fileInput');
        const fileUploadArea = document.getElementById('fileUploadArea');

        fileUploadArea.addEventListener('click', () => {
            fileInput.click();
        });

        fileInput.addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        // Drag and drop
        fileUploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            fileUploadArea.classList.add('dragover');
        });

        fileUploadArea.addEventListener('dragleave', () => {
            fileUploadArea.classList.remove('dragover');
        });

        fileUploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            fileUploadArea.classList.remove('dragover');
            
            const file = e.dataTransfer.files[0];
            if (file) {
                this.handleFileSelect(file);
            }
        });

        document.getElementById('uploadBtn').addEventListener('click', () => {
            this.uploadFile();
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
     * Switch between tabs
     */
    switchTab(tabName) {
        // Update tab buttons
        document.querySelectorAll('.tab').forEach(tab => {
            tab.classList.remove('active');
            if (tab.dataset.tab === tabName) {
                tab.classList.add('active');
            }
        });

        // Update tab content
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });

        if (tabName === 'text') {
            document.getElementById('textTab').classList.add('active');
        } else if (tabName === 'file') {
            document.getElementById('fileTab').classList.add('active');
        }
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
            const data = await API.analyzeText(text);
            UI.displayResults(data, 'textResults');
        } catch (error) {
            console.error('Analysis error:', error);
            UI.showError('textResults', error.message);
        } finally {
            analyzeBtn.disabled = false;
            analyzeBtn.textContent = 'Analyze Argument';
        }
    }

    /**
     * Handle file selection
     */
    handleFileSelect(file) {
        if (!file) return;

        // Validate file type
        const validTypes = ['.pdf', '.txt'];
        const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
        
        if (!validTypes.includes(fileExtension)) {
            alert('Please select a PDF or TXT file');
            return;
        }

        // Validate file size
        if (file.size > CONFIG.MAX_FILE_SIZE) {
            alert(`File size must not exceed ${CONFIG.MAX_FILE_SIZE / 1024 / 1024}MB`);
            return;
        }

        this.selectedFile = file;
        UI.updateFileDisplay(file.name, file.size);
        document.getElementById('uploadBtn').disabled = false;
    }

    /**
     * Upload and analyze file
     */
    async uploadFile() {
        if (!this.selectedFile) return;

        const uploadBtn = document.getElementById('uploadBtn');

        // Show loading state
        uploadBtn.disabled = true;
        uploadBtn.textContent = 'Uploading...';
        UI.showLoading('fileResults', 'Uploading and analyzing file... This may take 20-60 seconds.');

        try {
            const data = await API.uploadFile(this.selectedFile);
            
            const fileInfo = {
                filename: data.filename || this.selectedFile.name,
                text_length: data.text_length || 0
            };
            
            UI.displayResults(data, 'fileResults', fileInfo);
        } catch (error) {
            console.error('Upload error:', error);
            UI.showError('fileResults', error.message);
        } finally {
            uploadBtn.disabled = false;
            uploadBtn.textContent = 'Upload & Analyze';
        }
    }
}

// Initialize the app when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    new LegalCriticApp();
});
