import { Routes, Route, Navigate } from "react-router-dom";
import { useEffect, useState } from "react";
import { useAuthStore } from "./store";

// Layouts
import DashboardLayout from "./components/layout/DashboardLayout";

// Pages
import Login from "./pages/Login";
import Dashboard from "./pages/Dashboard";
import Contributions from "./pages/Contributions";
import SubmitContribution from "./pages/SubmitContribution";
import Portfolio from "./pages/Portfolio";
import Reviews from "./pages/Reviews";
import HodFacultyView from "./pages/HodFacultyView";
import AdminPanel from "./pages/AdminPanel";
import InstituteAdminPanel from "./pages/InstituteAdminPanel";
import Profile from "./pages/Profile";
import PublicPortfolio from "./pages/PublicPortfolio";
import TransactionExplorer from "./pages/TransactionExplorer";
import NotFound from "./pages/NotFound";

// Protected Route Component
const ProtectedRoute = ({ children, allowedRoles = [] }) => {
  const { user, token, isConnected } = useAuthStore();

  if (!token || !isConnected) {
    return <Navigate to="/login" replace />;
  }

  if (allowedRoles.length > 0 && !allowedRoles.includes(user?.role)) {
    return <Navigate to="/dashboard" replace />;
  }

  return children;
};

function App() {
  const { token, getCurrentUser } = useAuthStore();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const initializeAuth = async () => {
      if (token) {
        try {
          await getCurrentUser();
        } catch (error) {
          console.error("Failed to get current user:", error);
        }
      }
      setIsLoading(false);
    };

    initializeAuth();
  }, [token, getCurrentUser]);

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <div className="loader mx-auto mb-4"></div>
          <p className="text-gray-600">Loading SALF...</p>
        </div>
      </div>
    );
  }

  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={<Login />} />
      <Route path="/public/portfolio/:walletAddress" element={<PublicPortfolio />} />

      {/* Protected Routes */}
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <DashboardLayout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="contributions" element={<Contributions />} />
        <Route path="contributions/new" element={<SubmitContribution />} />
        <Route path="transactions" element={<TransactionExplorer />} />
        <Route path="portfolio" element={<Portfolio />} />
        <Route
          path="profile"
          element={
            <ProtectedRoute allowedRoles={["faculty", "hod"]}>
              <Profile />
            </ProtectedRoute>
          }
        />

        {/* HoD Routes */}
        <Route
          path="reviews"
          element={
            <ProtectedRoute allowedRoles={["hod", "admin"]}>
              <Reviews />
            </ProtectedRoute>
          }
        />
        <Route
          path="hod/faculty"
          element={
            <ProtectedRoute allowedRoles={["hod"]}>
              <HodFacultyView />
            </ProtectedRoute>
          }
        />

        {/* Master Admin Routes */}
        <Route
          path="admin/*"
          element={
            <ProtectedRoute allowedRoles={["admin"]}>
              <AdminPanel />
            </ProtectedRoute>
          }
        />

        {/* Institute Admin Routes */}
        <Route
          path="institute-admin/*"
          element={
            <ProtectedRoute allowedRoles={["institute_admin"]}>
              <InstituteAdminPanel />
            </ProtectedRoute>
          }
        />
      </Route>

      {/* 404 */}
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}

export default App;
