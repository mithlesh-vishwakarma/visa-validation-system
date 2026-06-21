import axios from 'axios';
import type { Submission, EligibilityScore } from '../types';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('accessToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor to handle JWT refresh
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;
    if (
      error.response?.status === 401 &&
      !originalRequest._retry &&
      originalRequest.url !== 'auth/token/' &&
      originalRequest.url !== 'auth/token/refresh/'
    ) {
      originalRequest._retry = true;
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const res = await axios.post(`${API_URL}auth/token/refresh/`, {
            refresh: refreshToken,
          });
          const { access, refresh } = res.data;
          localStorage.setItem('accessToken', access);
          if (refresh) localStorage.setItem('refreshToken', refresh);
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        } catch (refreshError) {
          localStorage.removeItem('accessToken');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      }
    }
    return Promise.reject(error);
  }
);

// ---------------------------------------------------------------------------
// Typed API Helpers
// ---------------------------------------------------------------------------

/** Trigger full AI assessment pipeline for a submission. Returns updated Submission. */
export const runAIAssessment = (submissionId: string): Promise<Submission> =>
  api.post<Submission>(`submissions/${submissionId}/ai_assess/`).then((r) => r.data);

/** Run the rules engine validation for a submission. */
export const runValidation = (submissionId: string) =>
  api.post(`submissions/${submissionId}/validate_rules/`).then((r) => r.data);

/** Fetch the AI eligibility score for a specific submission. */
export const getEligibilityScore = (submissionId: string): Promise<EligibilityScore> =>
  api.get<EligibilityScore>(`eligibility/by-submission/${submissionId}/`).then((r) => r.data);

/** Download the enhanced PDF report for a submission. */
export const downloadReport = async (submissionId: string, applicationId: string): Promise<void> => {
  const response = await api.get(`submissions/${submissionId}/download_report/`, {
    responseType: 'blob',
  });
  const blob = new Blob([response.data], { type: 'application/pdf' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `VisaFlow_Report_${applicationId}.pdf`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
};

/** Fetch processing logs for a submission. */
export const getProcessingLogs = (submissionId: string) =>
  api.get(`submissions/${submissionId}/processing_logs/`).then((r) => r.data);

export default api;
