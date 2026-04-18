// API Service Module
const API = {
    /**
     * Check API health status
     */
    async checkHealth() {
        try {
            const response = await fetch(`${CONFIG.API_URL}${CONFIG.ENDPOINTS.HEALTH}`);
            if (response.ok) {
                return await response.json();
            }
            return null;
        } catch (error) {
            console.error('Health check failed:', error);
            return null;
        }
    },

    /**
     * Analyze text argument
     */
    async analyzeText(text) {
        const response = await fetch(`${CONFIG.API_URL}${CONFIG.ENDPOINTS.ANALYZE}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    },

    /**
     * Analyze text argument with grounding in uploaded documents
     */
    async analyzeTextGrounded(text, doc_ids = [], include_case_corpus = true) {
        const controller = new AbortController();
        const timeoutMs = 300000; // 5 minutes
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

        try {
            const response = await fetch(`${CONFIG.API_URL}${CONFIG.ENDPOINTS.ANALYZE_GROUNDED}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ text, doc_ids, include_case_corpus }),
                signal: controller.signal,
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                // FastAPI often returns {"detail": "..."}
                let detail = '';
                try {
                    const err = await response.json();
                    if (err && typeof err.detail === 'string') detail = err.detail;
                } catch (e) {
                    // Ignore JSON parse errors; fall back to text
                }
                if (!detail) {
                    try {
                        detail = await response.text();
                    } catch (e) {
                        detail = '';
                    }
                }
                throw new Error(detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error && error.name === 'AbortError') {
                throw new Error('Analysis timed out after 5 minutes. The AI service may be overloaded — please try again.');
            }
            if (error instanceof TypeError) {
                throw new Error(`Failed to reach API at ${CONFIG.API_URL}. Is the backend running?`);
            }
            throw error;
        }
    },

    /**
    * Upload supporting document (PDF/TXT/DOCX). Returns { doc_id, filename, file_type, text_length }
     */
    async uploadSupportingDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const url = `${CONFIG.API_URL}${CONFIG.ENDPOINTS.DOCUMENT_UPLOAD}`;

        // Avoid indefinite "Uploading..." when PDF extraction takes too long.
        const controller = new AbortController();
        const timeoutMs = 600000; // 10 minutes
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData,
                signal: controller.signal,
            });
            clearTimeout(timeoutId);

            if (!response.ok) {
                let detail = '';
                try {
                    const err = await response.json();
                    if (err && typeof err.detail === 'string') detail = err.detail;
                } catch (e) {
                    // Ignore JSON parse errors; fall back to text
                }
                if (!detail) {
                    try {
                        detail = await response.text();
                    } catch (e) {
                        detail = '';
                    }
                }
                throw new Error(detail || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            clearTimeout(timeoutId);
            if (error && (error.name === 'AbortError')) {
                throw new Error('Upload timed out while extracting PDF text. Try a smaller PDF, or set UPLOADED_DOC_MAX_PAGES on the backend to limit pages.');
            }
            // Browser network/CORS failures often surface as TypeError: Failed to fetch
            if (error instanceof TypeError) {
                throw new Error(`Failed to reach API at ${url}. Is the backend running on port 8000?`);
            }
            throw error;
        }
    },

    /**
     * Upload and analyze file
     */
    async uploadFile(file) {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch(`${CONFIG.API_URL}${CONFIG.ENDPOINTS.UPLOAD}`, {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        return await response.json();
    }
};
