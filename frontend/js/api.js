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
