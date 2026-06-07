import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const experimentsAPI = {
  analyze: (data) => api.post('/experiments/analyze', data),
  getAll: () => api.get('/experiments/'),
  getOne: (id) => api.get(`/experiments/${id}`),
  create: (data) => api.post('/experiments/', data),
  update: (id, data) => api.patch(`/experiments/${id}`, data),
  start: (id) => api.post(`/experiments/${id}/start`),
  stop: (id) => api.post(`/experiments/${id}/stop`),
  delete: (id) => api.delete(`/experiments/${id}`),
  generateReport: (id) => api.post(`/experiments/${id}/generate-report`),
};

export const analysisAPI = {
  getResults: (id) => api.get(`/analysis/${id}/results`),
  getSnapshots: (id) => api.get(`/analysis/${id}/snapshots`),
  getPower: (id) => api.get(`/analysis/${id}/power`),
  getSegments: (id) => api.get(`/analysis/${id}/segments`),
};

export default api;
