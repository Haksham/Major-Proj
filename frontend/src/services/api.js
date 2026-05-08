import axios from "axios";
import { useAuthStore } from "../store";

// Create axios instance with base configuration
const api = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  },
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - logout user
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

/**
 * Authentication API
 */
export const authAPI = {
  // Get nonce for wallet authentication
  getNonce: (walletAddress) =>
    api.post("/auth/nonce", { wallet_address: walletAddress }),

  // Login with wallet signature
  login: (walletAddress, signature, nonce) =>
    api.post("/auth/login", {
      wallet_address: walletAddress,
      signature,
      nonce,
    }),

  // Get current user
  getMe: () => api.get("/auth/me"),

  // Refresh token
  refreshToken: () => api.post("/auth/refresh"),
};

/**
 * Contributions API
 */
export const contributionsAPI = {
  // Submit a new contribution
  submit: (contributionData) => {
    const isFormData =
      typeof FormData !== "undefined" && contributionData instanceof FormData;
    return api.post("/contributions/submit", contributionData, {
      headers: isFormData ? { "Content-Type": "multipart/form-data" } : undefined,
    });
  },

  // Get contribution by ID
  getById: (id) => api.get(`/contributions/${id}`),

  // Get all contributions for current user
  getMyContributions: (params = {}) => api.get("/contributions/", { params }),

  // Get pending contributions for review (HoD)
  getPending: (params = {}) => api.get("/contributions/pending", { params }),

  // Review a contribution (HoD)
  review: (id, reviewData) =>
    api.post(`/contributions/${id}/review`, reviewData),

  // Validate a contribution on blockchain (HoD)
  validate: (id) => api.post(`/contributions/${id}/validate`),

  // Get contribution history
  getHistory: (id) => api.get(`/contributions/${id}/history`),

  // Upload document (FormData)
  uploadDocument: (formData) =>
    api.post("/contributions/upload", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    }),
};

/**
 * Portfolio API
 */
export const portfolioAPI = {
  // Get current user's portfolio
  getMyPortfolio: () => api.get("/portfolio/me"),

  // Get faculty portfolio by ID
  getPortfolio: (facultyId) => api.get(`/portfolio/${facultyId}`),

  // Get portfolio statistics
  getStatistics: () => api.get("/portfolio/statistics"),

  // Get credit distribution
  getCreditDistribution: () => api.get("/portfolio/credit-distribution"),

  // Export portfolio (PDF)
  exportPortfolio: (format = "pdf") =>
    api.get(`/portfolio/export?format=${format}`, {
      responseType: "blob",
    }),

  // Get recent activity
  getRecentActivity: () => api.get("/portfolio/activity"),
};

/**
 * Admin API
 */
export const adminAPI = {
  // Register new faculty
  registerFaculty: (facultyData) =>
    api.post("/admin/faculty/register", facultyData),

  // Get all faculty
  getAllFaculty: (params = {}) => api.get("/admin/faculty", { params }),

  // Update faculty
  updateFaculty: (id, updateData) =>
    api.put(`/admin/faculty/${id}`, updateData),

  // Deactivate faculty
  deactivateFaculty: (id) => api.post(`/admin/faculty/${id}/deactivate`),

  // Create department
  createDepartment: (departmentData) =>
    api.post("/admin/departments", departmentData),

  // Get all departments
  getDepartments: () => api.get("/admin/departments"),

  // Assign HoD
  assignHoD: (departmentId, facultyId) =>
    api.post(`/admin/departments/${departmentId}/assign-hod`, {
      faculty_id: facultyId,
    }),

  // Get system statistics
  getSystemStats: () => api.get("/admin/statistics"),

  // Get audit logs
  getAuditLogs: (params = {}) => api.get("/admin/audit-logs", { params }),

  // Get blockchain stats
  getBlockchainStats: () => api.get("/admin/blockchain/stats"),
};

/**
 * Evaluation API
 */
export const evaluationAPI = {
  // Get AI evaluation for a contribution
  getEvaluation: (contributionId) => api.get(`/evaluation/${contributionId}`),

  // Request re-evaluation
  requestReEvaluation: (contributionId) =>
    api.post(`/evaluation/${contributionId}/re-evaluate`),

  // Get benchmark attributes
  getBenchmarkAttributes: () => api.get("/evaluation/benchmarks"),
};

/**
 * Transfer API
 */
export const transferAPI = {
  // Request credit transfer
  requestTransfer: (transferData) =>
    api.post("/transfers/request", transferData),

  // Get pending transfers
  getPendingTransfers: () => api.get("/transfers/pending"),

  // Approve transfer (receiving institution)
  approveTransfer: (transferId) => api.post(`/transfers/${transferId}/approve`),

  // Reject transfer
  rejectTransfer: (transferId, reason) =>
    api.post(`/transfers/${transferId}/reject`, { reason }),

  // Get transfer history
  getTransferHistory: () => api.get("/transfers/history"),
};

export default api;
