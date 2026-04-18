import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import {
  useAuthStore,
  useContributionStore,
  usePortfolioStore,
} from "../store";
import {
  DocumentTextIcon,
  AcademicCapIcon,
  ClockIcon,
  CheckCircleIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  PlusIcon,
  CubeIcon,
} from "@heroicons/react/24/outline";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import clsx from "clsx";

const COLORS = [
  "#3b82f6",
  "#10b981",
  "#f59e0b",
  "#ef4444",
  "#8b5cf6",
  "#ec4899",
];

const CATEGORY_NAMES = [
  "Research Paper",
  "Journal",
  "Book",
  "Book Chapter",
  "Patent",
  "Conference",
  "Workshop",
  "Seminar",
  "Project",
  "Award",
];

function Dashboard() {
  const { user } = useAuthStore();
  const { contributions, fetchContributions } = useContributionStore();
  const { portfolio, fetchPortfolio, statistics, fetchStatistics } =
    usePortfolioStore();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadData = async () => {
      try {
        await Promise.all([
          fetchContributions(),
          fetchPortfolio(),
          fetchStatistics(),
        ]);
      } catch (error) {
        console.error("Failed to load dashboard data:", error);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, [fetchContributions, fetchPortfolio, fetchStatistics]);

  // Calculate stats
  const totalContributions = contributions.length;
  const pendingCount = contributions.filter(
    (c) => c.status === "pending" || c.status === "under_review",
  ).length;
  const approvedCount = contributions.filter(
    (c) => c.status === "approved" || c.status === "validated",
  ).length;
  const totalCredits = portfolio?.total_credits || 0;

  // Category distribution for pie chart
  const categoryData = CATEGORY_NAMES.map((name, index) => ({
    name,
    value: contributions.filter((c) => c.category === index).length,
  })).filter((item) => item.value > 0);

  // Monthly contributions for bar chart
  const monthlyData = [
    { month: "Jan", contributions: 2 },
    { month: "Feb", contributions: 4 },
    { month: "Mar", contributions: 3 },
    { month: "Apr", contributions: 5 },
    { month: "May", contributions: 4 },
    { month: "Jun", contributions: 6 },
  ];

  // Recent contributions
  const recentContributions = contributions.slice(0, 5);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loader" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Welcome header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">
            Welcome back, {user?.name || "Faculty"}!
          </h1>
          <p className="mt-1 text-gray-500">
            Here's an overview of your academic contributions.
          </p>
        </div>
        <Link
          to="/contributions/new"
          className="mt-4 sm:mt-0 btn-primary inline-flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          New Contribution
        </Link>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard
          title="Total Contributions"
          value={totalContributions}
          icon={DocumentTextIcon}
          color="blue"
          change="+12%"
        />
        <StatCard
          title="Total Credits"
          value={totalCredits}
          icon={AcademicCapIcon}
          color="green"
          change="+8%"
        />
        <StatCard
          title="Pending Review"
          value={pendingCount}
          icon={ClockIcon}
          color="yellow"
        />
        <StatCard
          title="Validated"
          value={approvedCount}
          icon={CheckCircleIcon}
          color="emerald"
          change="+5%"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Monthly contributions */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Contributions Over Time
            </h3>
            <ChartBarIcon className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: "white",
                    border: "1px solid #e5e7eb",
                    borderRadius: "8px",
                  }}
                />
                <Bar
                  dataKey="contributions"
                  fill="#3b82f6"
                  radius={[4, 4, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Category distribution */}
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">
              Category Distribution
            </h3>
            <ArrowTrendingUpIcon className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-64 flex items-center justify-center">
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={categoryData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                    label={({ name, percent }) =>
                      `${name} ${(percent * 100).toFixed(0)}%`
                    }
                    labelLine={false}
                  >
                    {categoryData.map((entry, index) => (
                      <Cell
                        key={`cell-${index}`}
                        fill={COLORS[index % COLORS.length]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="text-center text-gray-500">
                <DocumentTextIcon className="h-12 w-12 mx-auto text-gray-300" />
                <p className="mt-2">No contributions yet</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent contributions */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">
            Recent Contributions
          </h3>
          <Link
            to="/contributions"
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View all →
          </Link>
        </div>

        {recentContributions.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="table-header">Title</th>
                  <th className="table-header">Category</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Credits</th>
                  <th className="table-header">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {recentContributions.map((contribution) => (
                  <tr key={contribution.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium text-gray-900">
                      {contribution.title}
                    </td>
                    <td className="table-cell text-gray-500">
                      {CATEGORY_NAMES[contribution.category] || "Other"}
                    </td>
                    <td className="table-cell">
                      <StatusBadge status={contribution.status} />
                    </td>
                    <td className="table-cell text-gray-900 font-medium">
                      {contribution.final_credits || "-"}
                    </td>
                    <td className="table-cell text-gray-500">
                      {new Date(contribution.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <CubeIcon className="h-12 w-12 mx-auto text-gray-300" />
            <p className="mt-2 text-gray-500">No contributions yet</p>
            <Link
              to="/contributions/new"
              className="mt-4 inline-block btn-primary"
            >
              Submit your first contribution
            </Link>
          </div>
        )}
      </div>

      {/* Blockchain status */}
      <div className="card bg-gradient-to-r from-primary-50 to-blue-50 border-primary-200">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-primary-100 rounded-lg">
            <CubeIcon className="h-8 w-8 text-primary-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">
              Blockchain Status
            </h3>
            <p className="text-sm text-gray-600">
              All your contributions are securely stored on Hyperledger Besu
            </p>
          </div>
          <div className="ml-auto flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full pulse-blockchain" />
            <span className="text-sm font-medium text-green-600">
              Connected
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}

// Stat Card Component
function StatCard({ title, value, icon: Icon, color, change }) {
  const colorClasses = {
    blue: "bg-blue-100 text-blue-600",
    green: "bg-green-100 text-green-600",
    yellow: "bg-yellow-100 text-yellow-600",
    emerald: "bg-emerald-100 text-emerald-600",
    red: "bg-red-100 text-red-600",
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className={clsx("p-3 rounded-lg", colorClasses[color])}>
          <Icon className="h-6 w-6" />
        </div>
        {change && (
          <span className="text-sm font-medium text-green-600">{change}</span>
        )}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{title}</p>
      </div>
    </div>
  );
}

// Status Badge Component
function StatusBadge({ status }) {
  const statusConfig = {
    pending: { label: "Pending", class: "badge-pending" },
    under_review: { label: "Under Review", class: "badge-pending" },
    approved: { label: "Approved", class: "badge-approved" },
    rejected: { label: "Rejected", class: "badge-rejected" },
    validated: { label: "Validated", class: "badge-validated" },
  };

  const config = statusConfig[status] || statusConfig.pending;

  return <span className={clsx("badge", config.class)}>{config.label}</span>;
}

export default Dashboard;
