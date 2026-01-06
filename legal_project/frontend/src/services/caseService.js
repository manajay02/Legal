import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

const caseService = {
  // Similar Cases Finder
  findSimilarCases: (caseText, caseType = 'Civil', limit = 5) => {
    return apiClient.post('/similar-cases/find', {
      caseText,
      caseType,
      limit,
    });
  },

  uploadCase: (caseText, title, caseType, court, year) => {
    return apiClient.post('/similar-cases/upload', {
      caseText,
      title,
      caseType,
      court,
      year,
    });
  },

  getAllCases: (page = 1, limit = 10, caseType = null) => {
    const params = { page, limit };
    if (caseType) {
      params.caseType = caseType;
    }
    return apiClient.get('/similar-cases', { params });
  },

  getCaseById: (id) => {
    return apiClient.get(`/similar-cases/${id}`);
  },

  // Case Classification
  classifyCase: (caseText) => {
    return apiClient.post('/cases/classify', { caseText });
  },

  uploadPDF: (formData) => {
    return apiClient.post('/cases/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Upload and convert file to text
  uploadAndConvertFile: (formData) => {
    return apiClient.post('/similar-cases/upload-file', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Compliance Auditor
  auditCompliance: (documentText) => {
    return apiClient.post('/compliance/audit', { documentText });
  },

  // Document Analyzer
  analyzeDocument: (documentText) => {
    return apiClient.post('/documents/analyze', { documentText });
  },

  // Argument Analyzer
  analyzeArgument: (argumentText) => {
    return apiClient.post('/arguments/analyze', { argumentText });
  },

  // Health Check
  checkHealth: () => {
    return apiClient.get('/health');
  },

  // Add case manually
  addCase: (caseData) => {
    return apiClient.post('/similar-cases/add-case', caseData);
  },

  // Get stored cases
  getStoredCases: (caseType = null, page = 1, limit = 10) => {
    const params = { page, limit };
    if (caseType) {
      params.caseType = caseType;
    }
    return apiClient.get('/similar-cases/stored-cases', { params });
  },

  // Get database statistics
  getCaseStats: () => {
    return apiClient.get('/similar-cases/stored-cases/stats');
  },

  // Delete case
  deleteCase: (caseId) => {
    return apiClient.delete(`/similar-cases/${caseId}`);
  },
};

export default caseService;
