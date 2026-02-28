// API Configuration
const CONFIG = {
    // Use 127.0.0.1 instead of localhost to avoid IPv6 (::1) resolution issues
    // when the backend is bound to IPv4 only.
    API_URL: 'http://127.0.0.1:8000',
    ENDPOINTS: {
        ANALYZE: '/api/v1/analyze',
        ANALYZE_GROUNDED: '/api/v1/analyze_grounded',
        UPLOAD: '/api/v1/upload',
        DOCUMENT_UPLOAD: '/api/v1/documents/upload',
        HEALTH: '/api/v1/health'
    },
    MAX_TEXT_LENGTH: 10000,
    MIN_TEXT_LENGTH: 50,
    MAX_FILE_SIZE: 10 * 1024 * 1024 // 10MB
};
