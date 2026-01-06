// API Configuration
const CONFIG = {
    API_URL: 'http://localhost:8000',
    ENDPOINTS: {
        ANALYZE: '/api/v1/analyze',
        UPLOAD: '/api/v1/upload',
        HEALTH: '/api/v1/health'
    },
    MAX_TEXT_LENGTH: 10000,
    MIN_TEXT_LENGTH: 50,
    MAX_FILE_SIZE: 10 * 1024 * 1024 // 10MB
};
