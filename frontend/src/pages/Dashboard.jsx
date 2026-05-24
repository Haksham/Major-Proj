import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuthStore, useContributionStore, usePortfolioStore } from "../store";
import { adminAPI, instituteAdminAPI, contributionsAPI } from "../services/api";
import {
  DocumentTextIcon,
  AcademicCapIcon,
  ClockIcon,
  CheckCircleIcon,
  ChartBarIcon,
  ArrowTrendingUpIcon,
  PlusIcon,
  CubeIcon,
  UsersIcon,
  BuildingOffice2Icon,
  ClipboardDocumentCheckIcon,
  ShieldCheckIcon,
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

const COLORS = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899"];

const CATEGORY_NAMES = [
  "Guest Lectures", "Journal", "Book", "Book Chapter", "Patent",
  "Conference", "Workshop", "Seminar", "Project", "Award",
  "Faculty Development Program",
];

// ─── Master Admin Dashboard ─────────────────────────────────────────────────

function AdminDashboard({ user }) {
  const [stats, setStats] = useState(null);
  const [pending, setPending] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [metricsRes, pendingRes, instsRes] = await Promise.allSettled([
          fetch("/api/v1/metrics", { headers: { Authorization: `Bearer ${useAuthStore.getState().token}` } }).then(r => r.json()),
          adminAPI.getPendingUsers(),
          adminAPI.listInstitutions(),
        ]);
        setStats({
          totalUsers: metricsRes.status === "fulfilled" ? metricsRes.value.total_users : 0,
          totalContributions: metricsRes.status === "fulfilled" ? metricsRes.value.total_contributions : 0,
          pendingApprovals: pendingRes.status === "fulfilled" ? (pendingRes.value.data?.users || pendingRes.value.data || []).length : 0,
          totalInstitutions: instsRes.status === "fulfilled" ? (instsRes.value.data?.institutions || instsRes.value.data || []).length : 0,
        });
        if (pendingRes.status === "fulfilled") {
          const list = pendingRes.value.data?.users || pendingRes.value.data || [];
          setPending(list.slice(0, 5));
        }
      } catch (e) {
        console.error(e);
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, []);

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="loader" /></div>;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome, {user?.name}!</h1>
        <p className="mt-1 text-gray-500">System overview — Master Admin</p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Users" value={stats?.totalUsers ?? "—"} icon={UsersIcon} color="blue" />
        <StatCard title="Total Institutions" value={stats?.totalInstitutions ?? "—"} icon={BuildingOffice2Icon} color="purple" />
        <StatCard title="Total Contributions" value={stats?.totalContributions ?? "—"} icon={DocumentTextIcon} color="green" />
        <StatCard title="Pending Approvals" value={stats?.pendingApprovals ?? "—"} icon={ClockIcon} color="yellow" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Pending Institute Approvals</h3>
            <Link to="/admin" className="text-sm text-primary-600 hover:text-primary-700 font-medium">Manage →</Link>
          </div>
          {pending.length > 0 ? (
            <ul className="divide-y divide-gray-100">
              {pending.map((u) => (
                <li key={u.wallet_address} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{u.name}</p>
                    <p className="text-xs text-gray-500">{u.email}</p>
                  </div>
                  <Link to="/admin" className="text-xs text-primary-600 hover:underline">Review</Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 py-4 text-center">No pending approvals</p>
          )}
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
          </div>
          <div className="space-y-3">
            <Link to="/admin" className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
              <ShieldCheckIcon className="h-5 w-5 text-primary-600 mr-3" />
              <span className="text-sm font-medium text-gray-700">Manage Institutions & Users</span>
            </Link>
            <Link to="/admin" className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
              <CubeIcon className="h-5 w-5 text-blue-600 mr-3" />
              <span className="text-sm font-medium text-gray-700">Blockchain Status</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Institute Admin Dashboard ───────────────────────────────────────────────

function InstituteAdminDashboard({ user }) {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    instituteAdminAPI.getStats()
      .then(res => setStats(res.data))
      .catch(console.error)
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="loader" /></div>;

  const inst = stats?.institution;
  const users = stats?.users;
  const depts = stats?.departments;
  const contribs = stats?.contributions;

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Welcome, {user?.name}!</h1>
        <p className="mt-1 text-gray-500">{inst?.name || "Your Institution"} — Institute Admin</p>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Faculty" value={users?.total ?? "—"} icon={UsersIcon} color="blue" />
        <StatCard title="Departments" value={depts?.total ?? "—"} icon={BuildingOffice2Icon} color="purple" />
        <StatCard title="Contributions" value={contribs?.total ?? "—"} icon={DocumentTextIcon} color="green" />
        <StatCard title="Pending Approvals" value={users?.pending ?? "—"} icon={ClockIcon} color="yellow" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-gray-900 mb-4">Users by Role</h3>
          {users?.by_role ? (
            <ul className="space-y-2">
              {Object.entries(users.by_role).map(([role, count]) => (
                <li key={role} className="flex items-center justify-between">
                  <span className="text-sm text-gray-600 capitalize">{role.replace("_", " ")}</span>
                  <span className="text-sm font-semibold text-gray-900">{count}</span>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500">No data</p>
          )}
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Quick Actions</h3>
          </div>
          <div className="space-y-3">
            <Link to="/institute-admin" className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
              <UsersIcon className="h-5 w-5 text-primary-600 mr-3" />
              <span className="text-sm font-medium text-gray-700">Approve Pending Faculty</span>
            </Link>
            <Link to="/institute-admin" className="flex items-center p-3 rounded-lg border border-gray-200 hover:bg-gray-50 transition-colors">
              <BuildingOffice2Icon className="h-5 w-5 text-purple-600 mr-3" />
              <span className="text-sm font-medium text-gray-700">Manage Departments</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── HoD Dashboard ───────────────────────────────────────────────────────────

function HodDashboard({ user }) {
  const { contributions, fetchContributions } = useContributionStore();
  const [pendingReviews, setPendingReviews] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([
      fetchContributions(),
      contributionsAPI.getPending().then(r => setPendingReviews(r.data?.contributions || r.data || [])),
    ]).finally(() => setIsLoading(false));
  }, [fetchContributions]);

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="loader" /></div>;

  const totalContributions = contributions.length;
  const myApproved = contributions.filter(c => c.status === "approved" || c.status === "validated").length;
  const myPending = contributions.filter(c => c.status === "pending" || c.status === "under_review").length;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome, {user?.name}!</h1>
          <p className="mt-1 text-gray-500">Head of Department overview</p>
        </div>
        <Link to="/contributions/new" className="mt-4 sm:mt-0 btn-primary inline-flex items-center">
          <PlusIcon className="h-5 w-5 mr-2" />
          New Contribution
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Pending Reviews" value={pendingReviews.length} icon={ClipboardDocumentCheckIcon} color="yellow" />
        <StatCard title="My Contributions" value={totalContributions} icon={DocumentTextIcon} color="blue" />
        <StatCard title="My Approved" value={myApproved} icon={CheckCircleIcon} color="emerald" />
        <StatCard title="My Pending" value={myPending} icon={ClockIcon} color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Pending Reviews</h3>
            <Link to="/reviews" className="text-sm text-primary-600 hover:text-primary-700 font-medium">View all →</Link>
          </div>
          {pendingReviews.slice(0, 5).length > 0 ? (
            <ul className="divide-y divide-gray-100">
              {pendingReviews.slice(0, 5).map(c => (
                <li key={c.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{c.title}</p>
                    <p className="text-xs text-gray-500">{CATEGORY_NAMES[c.category] || "Other"}</p>
                  </div>
                  <Link to="/reviews" className="text-xs text-primary-600 hover:underline font-medium ml-4 shrink-0">Review →</Link>
                </li>
              ))}
            </ul>
          ) : (
            <p className="text-sm text-gray-500 py-4 text-center">No pending reviews</p>
          )}
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">My Recent Contributions</h3>
            <Link to="/contributions" className="text-sm text-primary-600 hover:text-primary-700 font-medium">View all →</Link>
          </div>
          {contributions.slice(0, 5).length > 0 ? (
            <ul className="divide-y divide-gray-100">
              {contributions.slice(0, 5).map(c => (
                <li key={c.id} className="py-3 flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-900">{c.title}</p>
                    <p className="text-xs text-gray-500">{CATEGORY_NAMES[c.category] || "Other"}</p>
                  </div>
                  <StatusBadge status={c.status} />
                </li>
              ))}
            </ul>
          ) : (
            <div className="text-center py-8">
              <p className="text-sm text-gray-500">No contributions yet</p>
              <Link to="/contributions/new" className="mt-2 inline-block text-sm text-primary-600 hover:underline">Submit one</Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Faculty Dashboard ────────────────────────────────────────────────────────

function FacultyDashboard({ user }) {
  const { contributions, fetchContributions } = useContributionStore();
  const { portfolio, fetchPortfolio, fetchStatistics } = usePortfolioStore();
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.allSettled([fetchContributions(), fetchPortfolio(), fetchStatistics()])
      .finally(() => setIsLoading(false));
  }, [fetchContributions, fetchPortfolio, fetchStatistics]);

  const totalContributions = contributions.length;
  const pendingCount = contributions.filter(c => c.status === "pending" || c.status === "under_review").length;
  const approvedCount = contributions.filter(c => c.status === "approved" || c.status === "validated").length;
  const totalCredits = portfolio?.total_credits || 0;

  const categoryData = CATEGORY_NAMES.map((name, index) => ({
    name,
    value: contributions.filter(c => c.category === index).length,
  })).filter(item => item.value > 0);

  const monthlyData = [
    { month: "Jan", contributions: 2 }, { month: "Feb", contributions: 4 },
    { month: "Mar", contributions: 3 }, { month: "Apr", contributions: 5 },
    { month: "May", contributions: 4 }, { month: "Jun", contributions: 6 },
  ];

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="loader" /></div>;

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Welcome back, {user?.name || "Faculty"}!</h1>
          <p className="mt-1 text-gray-500">Here's an overview of your academic contributions.</p>
        </div>
        <Link to="/contributions/new" className="mt-4 sm:mt-0 btn-primary inline-flex items-center">
          <PlusIcon className="h-5 w-5 mr-2" />
          New Contribution
        </Link>
      </div>

      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        <StatCard title="Total Contributions" value={totalContributions} icon={DocumentTextIcon} color="blue" change="+12%" />
        <StatCard title="Total Credits" value={totalCredits} icon={AcademicCapIcon} color="green" change="+8%" />
        <StatCard title="Pending Review" value={pendingCount} icon={ClockIcon} color="yellow" />
        <StatCard title="Validated" value={approvedCount} icon={CheckCircleIcon} color="emerald" change="+5%" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Contributions Over Time</h3>
            <ChartBarIcon className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={monthlyData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                <XAxis dataKey="month" stroke="#6b7280" fontSize={12} />
                <YAxis stroke="#6b7280" fontSize={12} />
                <Tooltip contentStyle={{ backgroundColor: "white", border: "1px solid #e5e7eb", borderRadius: "8px" }} />
                <Bar dataKey="contributions" fill="#3b82f6" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-gray-900">Category Distribution</h3>
            <ArrowTrendingUpIcon className="h-5 w-5 text-gray-400" />
          </div>
          <div className="h-64 flex items-center justify-center">
            {categoryData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={categoryData} cx="50%" cy="50%" innerRadius={60} outerRadius={80} paddingAngle={5} dataKey="value"
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={false}>
                    {categoryData.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
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

      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-semibold text-gray-900">Recent Contributions</h3>
          <Link to="/contributions" className="text-sm text-primary-600 hover:text-primary-700 font-medium">View all →</Link>
        </div>
        {contributions.slice(0, 5).length > 0 ? (
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
                {contributions.slice(0, 5).map(c => (
                  <tr key={c.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium text-gray-900">{c.title}</td>
                    <td className="table-cell text-gray-500">{CATEGORY_NAMES[c.category] || "Other"}</td>
                    <td className="table-cell"><StatusBadge status={c.status} /></td>
                    <td className="table-cell text-gray-900 font-medium">{c.final_credits || "—"}</td>
                    <td className="table-cell text-gray-500">{new Date(c.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="text-center py-12">
            <CubeIcon className="h-12 w-12 mx-auto text-gray-300" />
            <p className="mt-2 text-gray-500">No contributions yet</p>
            <Link to="/contributions/new" className="mt-4 inline-block btn-primary">Submit your first contribution</Link>
          </div>
        )}
      </div>

      <div className="card bg-gradient-to-r from-primary-50 to-blue-50 border-primary-200">
        <div className="flex items-center space-x-4">
          <div className="p-3 bg-primary-100 rounded-lg">
            <CubeIcon className="h-8 w-8 text-primary-600" />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Blockchain Status</h3>
            <p className="text-sm text-gray-600">All your contributions are securely stored on Hyperledger Besu</p>
          </div>
          <div className="ml-auto flex items-center space-x-2">
            <div className="w-3 h-3 bg-green-500 rounded-full pulse-blockchain" />
            <span className="text-sm font-medium text-green-600">Connected</span>
          </div>
        </div>
      </div>
    </div>
  );
}

// ─── Router ───────────────────────────────────────────────────────────────────

function Dashboard() {
  const { user } = useAuthStore();

  if (user?.role === "admin") return <AdminDashboard user={user} />;
  if (user?.role === "institute_admin") return <InstituteAdminDashboard user={user} />;
  if (user?.role === "hod") return <HodDashboard user={user} />;
  return <FacultyDashboard user={user} />;
}

// ─── Shared components ────────────────────────────────────────────────────────

function StatCard({ title, value, icon: Icon, color, change }) {
  const colorClasses = {
    blue: "bg-blue-100 text-blue-600",
    green: "bg-green-100 text-green-600",
    yellow: "bg-yellow-100 text-yellow-600",
    emerald: "bg-emerald-100 text-emerald-600",
    red: "bg-red-100 text-red-600",
    purple: "bg-purple-100 text-purple-600",
  };

  return (
    <div className="card">
      <div className="flex items-center justify-between">
        <div className={clsx("p-3 rounded-lg", colorClasses[color])}>
          <Icon className="h-6 w-6" />
        </div>
        {change && <span className="text-sm font-medium text-green-600">{change}</span>}
      </div>
      <div className="mt-4">
        <p className="text-2xl font-bold text-gray-900">{value}</p>
        <p className="text-sm text-gray-500">{title}</p>
      </div>
    </div>
  );
}

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
