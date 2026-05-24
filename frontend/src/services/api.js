import axios from "axios";
import { useAuthStore } from "../store";

const api = axios.create({
  baseURL: "/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) config.headers.Authorization = `Bearer ${token}`;
    return config;
  },
  (error) => Promise.reject(error),
);

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      window.location.href = "/login";
    }
    return Promise.reject(error);
  },
);

export const authAPI = {
  getNonce: (walletAddress) =>
    api.post("/auth/nonce", { wallet_address: walletAddress }),

  login: (walletAddress, signature, nonce) =>
    api.post("/auth/login", { wallet_address: walletAddress, signature, nonce }),

  register: (data) => api.post("/auth/register", data),
  registerInstitute: (data) => api.post("/auth/register/institute", data),

  getMe: () => api.get("/auth/me"),

  refreshToken: (refreshToken) =>
    api.post("/auth/refresh", { refresh_token: refreshToken }),
};

export const institutesAPI = {
  list: () => api.get("/institutes"),
  getDepartments: (institutionId) =>
    api.get(`/institutes/${institutionId}/departments`),
};

export const contributionsAPI = {
  submit: (contributionData) => {
    const isFormData =
      typeof FormData !== "undefined" && contributionData instanceof FormData;
    return api.post("/contributions/submit", contributionData, {
      headers: isFormData ? { "Content-Type": "multipart/form-data" } : undefined,
    });
  },

  getById: (id) => api.get(`/contributions/${id}`),
  getMyContributions: (params = {}) => api.get("/contributions/", { params }),
  getPending: (params = {}) =>
    api.get("/contributions/pending/review", { params }),
  review: (id, reviewData) =>
    api.post(`/contributions/${id}/review`, reviewData),
  getDepartmentFaculty: () => api.get("/contributions/department/faculty"),
  getDepartmentContributions: (facultyAddress = null) =>
    api.get("/contributions/department/contributions", {
      params: facultyAddress ? { faculty_address: facultyAddress } : {},
    }),
};

export const portfolioAPI = {
  getMyPortfolio: () => api.get("/portfolio/me"),
  getPortfolio: (walletAddress) =>
    api.get(`/portfolio/faculty/${walletAddress}`),
  getStatistics: () => api.get("/portfolio/statistics"),
  getDashboardStats: () => api.get("/portfolio/dashboard/stats"),
  getLeaderboard: () => api.get("/portfolio/leaderboard"),
};

export const adminAPI = {
  // Users
  createUser: (data) => api.post("/admin/users", data),
  getUsers: (params = {}) => api.get("/admin/users", { params }),
  getPendingUsers: () => api.get("/admin/users/pending"),
  approveUser: (walletAddress) =>
    api.post(`/admin/users/${walletAddress}/approve`),
  updateUser: (walletAddress, data) =>
    api.patch(`/admin/users/${walletAddress}`, data),
  updateUserRole: (walletAddress, role) =>
    api.post(`/admin/users/${walletAddress}/role`, null, {
      params: { new_role: role },
    }),

  // Institutions
  createInstitution: (data) => api.post("/admin/institutes", data),
  listInstitutions: () => api.get("/admin/institutes"),
  deactivateInstitution: (id) =>
    api.patch(`/admin/institutes/${id}/deactivate`),

  // Departments
  createDepartment: (data) => api.post("/admin/departments", data),
  getDepartments: () => api.get("/admin/departments"),

  // Blockchain & config
  getBlockchainStatus: () => api.get("/admin/blockchain/status"),
  getContracts: () => api.get("/admin/contracts"),
  getConfig: () => api.get("/admin/config"),
};

export const instituteAdminAPI = {
  getStats: () => api.get("/institute-admin/stats"),
  getPending: () => api.get("/institute-admin/pending"),
  approveUser: (walletAddress) => api.post(`/institute-admin/users/${walletAddress}/approve`),
  rejectUser: (walletAddress) => api.post(`/institute-admin/users/${walletAddress}/reject`),
  getUsers: () => api.get("/institute-admin/users"),
  assignHod: (walletAddress) => api.post(`/institute-admin/users/${walletAddress}/assign-hod`),
  getDepartments: () => api.get("/institute-admin/departments"),
  createDepartment: (data) => api.post("/institute-admin/departments", data),
};

export const profileAPI = {
  getProfile: () => api.get("/profile/me"),
  updateProfile: (data) => api.patch("/profile/me", data),
};

export const transactionsAPI = {
  lookup: (q) => api.get("/transactions/lookup", { params: { q } }),
  backfill: () => api.post("/transactions/backfill"),
};

export default api;
