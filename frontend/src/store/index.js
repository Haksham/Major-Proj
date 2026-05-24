import { create } from "zustand";
import { persist } from "zustand/middleware";

/**
 * Authentication Store using Zustand
 * Manages user authentication state, wallet connection, and JWT tokens
 */
export const useAuthStore = create(
  persist(
    (set, get) => ({
      // State
      user: null,
      token: null,
      walletAddress: null,
      isConnected: false,
      isLoading: false,
      error: null,
      needsRegistration: false,
      pendingApproval: false,

      // Actions
      setUser: (user) => set({ user }),
      setToken: (token) => set({ token }),
      setWalletAddress: (walletAddress) =>
        set({ walletAddress, isConnected: !!walletAddress }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
      setNeedsRegistration: (val) => set({ needsRegistration: val }),
      setPendingApproval: (val) => set({ pendingApproval: val }),

      // Connect wallet
      connectWallet: async () => {
        set({ isLoading: true, error: null });

        try {
          if (!window.ethereum) {
            throw new Error(
              "MetaMask is not installed. Please install MetaMask to continue.",
            );
          }

          const accounts = await window.ethereum.request({
            method: "eth_requestAccounts",
          });

          if (accounts.length === 0) {
            throw new Error("No accounts found. Please connect your wallet.");
          }

          const walletAddress = accounts[0];
          set({ walletAddress, isConnected: true, isLoading: false });

          return walletAddress;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      // Disconnect wallet
      disconnectWallet: () => {
        set({
          user: null,
          token: null,
          walletAddress: null,
          isConnected: false,
          error: null,
        });
      },

      // Login with backend
      login: async (walletAddress, signature, nonce) => {
        set({ isLoading: true, error: null });

        try {
          const response = await fetch("/api/v1/auth/login", {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
            },
            body: JSON.stringify({
              wallet_address: walletAddress,
              signature: signature,
              nonce: nonce,
            }),
          });

          if (!response.ok) {
            const errorData = await response.json();
            const detail = errorData.detail || "Login failed";
            // 403 "not registered" → prompt registration
            if (
              response.status === 403 &&
              typeof detail === "string" &&
              detail.toLowerCase().includes("not registered")
            ) {
              set({ needsRegistration: true, isLoading: false, error: null });
              return null;
            }
            // 403 "pending_approval" → show waiting screen
            if (response.status === 403 && detail === "pending_approval") {
              set({ pendingApproval: true, isLoading: false, error: null });
              return null;
            }
            throw new Error(detail);
          }

          const data = await response.json();
          set({
            user: data.user,
            token: data.access_token,
            needsRegistration: false,
            pendingApproval: false,
            isLoading: false,
          });

          return data;
        } catch (error) {
          set({ error: error.message, isLoading: false });
          throw error;
        }
      },

      // Get current user
      getCurrentUser: async () => {
        const { token } = get();
        if (!token) return null;

        try {
          const response = await fetch("/api/v1/auth/me", {
            headers: {
              Authorization: `Bearer ${token}`,
            },
          });

          if (!response.ok) {
            throw new Error("Failed to get current user");
          }

          const user = await response.json();
          set({ user });
          return user;
        } catch (error) {
          set({ error: error.message });
          return null;
        }
      },

      // Logout
      logout: () => {
        set({
          user: null,
          token: null,
          walletAddress: null,
          isConnected: false,
          error: null,
          needsRegistration: false,
          pendingApproval: false,
        });
      },
    }),
    {
      name: "salf-auth-storage",
      partialize: (state) => ({
        token: state.token,
        walletAddress: state.walletAddress,
        user: state.user,
      }),
      onRehydrateStorage: () => (state) => {
        if (!state) return;
        const walletAddress = state.walletAddress;
        state.isConnected = !!walletAddress;
      },
    },
  ),
);

/**
 * Contribution Store
 * Manages contribution submissions and review state
 */
export const useContributionStore = create((set, get) => ({
  // State
  contributions: [],
  currentContribution: null,
  pendingReviews: [],
  isLoading: false,
  error: null,

  // Actions
  setContributions: (contributions) => set({ contributions }),
  setCurrentContribution: (contribution) =>
    set({ currentContribution: contribution }),
  setPendingReviews: (pendingReviews) => set({ pendingReviews }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  // Fetch contributions
  fetchContributions: async () => {
    const token = useAuthStore.getState().token;
    set({ isLoading: true, error: null });

    try {
      const response = await fetch("/api/v1/contributions/", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch contributions");
      }

      const data = await response.json();
      set({ contributions: data.contributions || data, isLoading: false });
      return data;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },

  // Submit contribution
  submitContribution: async (contributionData) => {
    const token = useAuthStore.getState().token;
    set({ isLoading: true, error: null });

    try {
      const isFormData =
        typeof FormData !== "undefined" && contributionData instanceof FormData;

      const response = await fetch("/api/v1/contributions/submit", {
        method: "POST",
        headers: {
          Authorization: `Bearer ${token}`,
          ...(isFormData ? {} : { "Content-Type": "application/json" }),
        },
        body: isFormData ? contributionData : JSON.stringify(contributionData),
      });

      if (!response.ok) {
        let errorMessage = "Failed to submit contribution";
        try {
          const errorData = await response.json();
          if (typeof errorData?.detail === "string") errorMessage = errorData.detail;
          if (Array.isArray(errorData?.detail) && errorData.detail[0]?.msg) {
            errorMessage = errorData.detail[0].msg;
          }
        } catch {
          // ignore JSON parse errors
        }
        throw new Error(errorMessage);
      }

      const data = await response.json();
      const { contributions } = get();
      set({
        contributions: [data, ...contributions],
        isLoading: false,
      });

      return data;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },

  // Review contribution (HoD)
  reviewContribution: async (contributionId, reviewData) => {
    const token = useAuthStore.getState().token;
    set({ isLoading: true, error: null });

    try {
      const response = await fetch(
        `/api/v1/contributions/${contributionId}/review`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify(reviewData),
        },
      );

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Failed to review contribution");
      }

      const data = await response.json();

      // Update contribution in list
      const { contributions, pendingReviews } = get();
      set({
        contributions: contributions.map((c) =>
          c.id === contributionId ? { ...c, ...data } : c,
        ),
        pendingReviews: pendingReviews.filter((r) => r.id !== contributionId),
        isLoading: false,
      });

      return data;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },

  // Fetch pending reviews (HoD)
  fetchPendingReviews: async () => {
    const token = useAuthStore.getState().token;
    set({ isLoading: true, error: null });

    try {
      const response = await fetch("/api/v1/contributions/pending/review", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch pending reviews");
      }

      const data = await response.json();
      set({ pendingReviews: data.contributions || data, isLoading: false });
      return data;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
}));

/**
 * Portfolio Store
 * Manages faculty portfolio and credit scores
 */
export const usePortfolioStore = create((set) => ({
  // State
  portfolio: null,
  creditScore: null,
  recentActivity: [],
  statistics: null,
  isLoading: false,
  error: null,

  // Actions
  setPortfolio: (portfolio) => set({ portfolio }),
  setCreditScore: (creditScore) => set({ creditScore }),
  setStatistics: (statistics) => set({ statistics }),
  setLoading: (isLoading) => set({ isLoading }),
  setError: (error) => set({ error }),

  // Fetch portfolio
  fetchPortfolio: async (facultyId = null) => {
    const token = useAuthStore.getState().token;
    set({ isLoading: true, error: null });

    try {
      const url = facultyId
        ? `/api/v1/portfolio/${facultyId}`
        : "/api/v1/portfolio/me";

      const response = await fetch(url, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch portfolio");
      }

      const data = await response.json();
      set({
        portfolio: data,
        creditScore: data.total_credits,
        recentActivity: data.recent_activity || [],
        isLoading: false,
      });

      return data;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },

  // Fetch statistics
  fetchStatistics: async () => {
    const token = useAuthStore.getState().token;
    set({ isLoading: true, error: null });

    try {
      const response = await fetch("/api/v1/portfolio/statistics", {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (!response.ok) {
        throw new Error("Failed to fetch statistics");
      }

      const data = await response.json();
      set({ statistics: data, isLoading: false });
      return data;
    } catch (error) {
      set({ error: error.message, isLoading: false });
      throw error;
    }
  },
}));

/**
 * UI Store
 * Manages UI state like sidebar, notifications, modals
 */
export const useUIStore = create((set) => ({
  // State
  sidebarOpen: true,
  notifications: [],
  activeModal: null,
  modalData: null,

  // Actions
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  addNotification: (notification) =>
    set((state) => ({
      notifications: [
        ...state.notifications,
        { id: Date.now(), ...notification },
      ],
    })),

  removeNotification: (id) =>
    set((state) => ({
      notifications: state.notifications.filter((n) => n.id !== id),
    })),

  openModal: (modalName, data = null) =>
    set({ activeModal: modalName, modalData: data }),

  closeModal: () => set({ activeModal: null, modalData: null }),
}));
