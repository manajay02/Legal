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
        const response = await fetch(`${CONFIG.API_URL}${CONFIG.ENDPOINTS.ANALYZE_GROUNDED}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text, doc_ids, include_case_corpus })
        });

        if (!response.ok) {
            const message = await response.text();
            throw new Error(message || `HTTP error! status: ${response.status}`);
        }

        return await response.json();
    },

    /**
     * Upload supporting document (PDF/TXT). Returns { doc_id, filename, file_type, text_length }
     */
    async uploadSupportingDocument(file) {
        const formData = new FormData();
        formData.append('file', file);

        const url = `${CONFIG.API_URL}${CONFIG.ENDPOINTS.DOCUMENT_UPLOAD}`;

        try {
            const response = await fetch(url, {
                method: 'POST',
                body: formData
            });

            if (!response.ok) {
                const message = await response.text();
                throw new Error(message || `HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
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
