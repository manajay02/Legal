import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';

const caseService = {
  uploadPDF: (formData) => {
    return axios.post(`${API_URL}/cases/upload`, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  classifyCase: (data) => {
    return axios.post(`${API_URL}/cases/classify`, data);
  },

  getCases: () => {
    return axios.get(`${API_URL}/cases`);
  },

  getCase: (id) => {
    return axios.get(`${API_URL}/cases/${id}`);
  },

  findSimilarCases: (caseId) => {
    return axios.get(`${API_URL}/cases/${caseId}/similar`);
  },

  deleteCase: (id) => {
    return axios.delete(`${API_URL}/cases/${id}`);
  },
};

export default caseService;
