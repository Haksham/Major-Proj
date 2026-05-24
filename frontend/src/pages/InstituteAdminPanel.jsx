import { useEffect, useState } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { instituteAdminAPI } from "../services/api";
import { useAuthStore } from "../store";
import {
  UsersIcon,
  BuildingOfficeIcon,
  ChartBarIcon,
  ShieldCheckIcon,
  PlusIcon,
  MagnifyingGlassIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

function InstituteAdminPanel() {
  const location = useLocation();

  const nav = [
    { name: "Overview", href: "/institute-admin", icon: ChartBarIcon },
    { name: "Pending", href: "/institute-admin/pending", icon: ShieldCheckIcon },
    { name: "Departments", href: "/institute-admin/departments", icon: BuildingOfficeIcon },
    { name: "Faculty", href: "/institute-admin/faculty", icon: UsersIcon },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Institute Admin Panel</h1>
        <p className="mt-1 text-gray-500">Manage your institution's departments and faculty</p>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {nav.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  "flex items-center py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap",
                  isActive
                    ? "border-primary-500 text-primary-600"
                    : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
                )}
              >
                <item.icon className="h-5 w-5 mr-2" />
                {item.name}
              </Link>
            );
          })}
        </nav>
      </div>

      <Routes>
        <Route index element={<IAOverview />} />
        <Route path="pending" element={<IAPending />} />
        <Route path="departments" element={<IADepartments />} />
        <Route path="faculty" element={<IAFaculty />} />
      </Routes>
    </div>
  );
}

// ─── Overview ──────────────────────────────────────────────────────────────────

function IAOverview() {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    instituteAdminAPI.getStats()
      .then((r) => setStats(r.data))
      .catch(() => setStats(null))
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <div className="flex items-center justify-center h-48"><div className="loader" /></div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Institution" value={stats?.institution ?? "—"} icon={BuildingOfficeIcon} color="indigo" text />
        <StatCard title="Faculty" value={stats?.total_faculty ?? 0} icon={UsersIcon} color="blue" />
        <StatCard title="HoDs" value={stats?.total_hod ?? 0} icon={UsersIcon} color="purple" />
        <StatCard title="Pending Approvals" value={stats?.pending_approvals ?? 0} icon={ShieldCheckIcon} color="yellow" />
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/institute-admin/pending" className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <ShieldCheckIcon className="h-8 w-8 text-yellow-500" />
            <p className="mt-2 font-medium text-gray-900">Pending Approvals</p>
            <p className="text-sm text-gray-500">Approve or reject faculty registrations</p>
          </Link>
          <Link to="/institute-admin/departments" className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <BuildingOfficeIcon className="h-8 w-8 text-purple-600" />
            <p className="mt-2 font-medium text-gray-900">Departments</p>
            <p className="text-sm text-gray-500">Create and manage departments</p>
          </Link>
          <Link to="/institute-admin/faculty" className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <UsersIcon className="h-8 w-8 text-primary-600" />
            <p className="mt-2 font-medium text-gray-900">Faculty</p>
            <p className="text-sm text-gray-500">View and manage faculty members</p>
          </Link>
        </div>
      </div>
    </div>
  );
}

// ─── Pending Approvals ─────────────────────────────────────────────────────────

function IAPending() {
  const [pending, setPending] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [acting, setActing] = useState(null);

  const load = () => {
    setIsLoading(true);
    instituteAdminAPI.getPending()
      .then((r) => setPending(r.data || []))
      .catch(() => setPending([]))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleApprove = async (wallet, name) => {
    setActing(wallet);
    try {
      await instituteAdminAPI.approveUser(wallet);
      setPending((p) => p.filter((u) => u.wallet_address !== wallet));
    } catch (err) {
      alert(err.response?.data?.detail || `Failed to approve ${name}`);
    } finally {
      setActing(null);
    }
  };

  const handleReject = async (wallet, name) => {
    if (!confirm(`Reject registration for ${name}? This will delete their account.`)) return;
    setActing(wallet);
    try {
      await instituteAdminAPI.rejectUser(wallet);
      setPending((p) => p.filter((u) => u.wallet_address !== wallet));
    } catch (err) {
      alert(err.response?.data?.detail || `Failed to reject ${name}`);
    } finally {
      setActing(null);
    }
  };

  if (isLoading) return <div className="flex items-center justify-center h-48"><div className="loader" /></div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Pending Faculty Registrations</h2>
          <p className="text-sm text-gray-500">Approve or reject self-registered faculty/HoD</p>
        </div>
        <span className="badge badge-pending">{pending.length} pending</span>
      </div>

      {pending.length === 0 ? (
        <div className="card text-center py-12">
          <ShieldCheckIcon className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-3 text-gray-500">No pending registrations</p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Name</th>
                  <th className="table-header">Role</th>
                  <th className="table-header">Designation</th>
                  <th className="table-header">Email</th>
                  <th className="table-header">Employee ID</th>
                  <th className="table-header">Wallet</th>
                  <th className="table-header">Date</th>
                  <th className="table-header">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {pending.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium text-gray-900">{u.name}</td>
                    <td className="table-cell">
                      <span className={clsx("badge", u.role === "hod" ? "badge-pending" : "badge-approved")}>{u.role}</span>
                    </td>
                    <td className="table-cell text-gray-500 text-sm">
                      {u.designation
                        ? u.designation.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
                        : "—"}
                    </td>
                    <td className="table-cell text-gray-500">{u.email || "—"}</td>
                    <td className="table-cell text-gray-500">{u.employee_id || "—"}</td>
                    <td className="table-cell font-mono text-xs text-gray-400">
                      {u.wallet_address.slice(0, 10)}...{u.wallet_address.slice(-6)}
                    </td>
                    <td className="table-cell text-gray-500 text-sm">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="table-cell">
                      <div className="flex space-x-2">
                        <button
                          onClick={() => handleApprove(u.wallet_address, u.name)}
                          disabled={acting === u.wallet_address}
                          className="btn-primary text-xs py-1 px-3"
                        >
                          {acting === u.wallet_address ? <div className="loader" /> : "Approve"}
                        </button>
                        <button
                          onClick={() => handleReject(u.wallet_address, u.name)}
                          disabled={acting === u.wallet_address}
                          className="btn-secondary text-xs py-1 px-3 text-red-600 border-red-200 hover:bg-red-50"
                        >
                          Reject
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

// ─── Departments ───────────────────────────────────────────────────────────────

function IADepartments() {
  const { user } = useAuthStore();
  const [departments, setDepartments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  const institutionId = user?.institution_id;

  const load = () => {
    setIsLoading(true);
    instituteAdminAPI.getDepartments()
      .then((r) => setDepartments(r.data || []))
      .catch(() => setDepartments([]))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => { load(); }, []);

  if (isLoading) return <div className="flex items-center justify-center h-48"><div className="loader" /></div>;

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={() => setShowAdd(true)}
          disabled={!institutionId}
          title={!institutionId ? "No institution assigned to your account" : undefined}
          className="btn-primary inline-flex items-center disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Department
        </button>
      </div>

      {!institutionId && (
        <div className="p-3 bg-yellow-50 border border-yellow-200 rounded text-sm text-yellow-700">
          Your account has no institution assigned. Contact the master admin.
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {departments.map((dept) => (
          <div key={dept.id} className="card">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">{dept.name}</h3>
                <p className="text-sm text-gray-500">Code: {dept.code}</p>
              </div>
              <span className={clsx("badge", dept.is_active ? "badge-approved" : "badge-rejected")}>
                {dept.is_active ? "Active" : "Inactive"}
              </span>
            </div>
            <div className="mt-2 text-sm text-gray-500">HoD ID: {dept.hod_id ?? "Not assigned"}</div>
          </div>
        ))}
        {departments.length === 0 && (
          <div className="col-span-2 text-center py-12 text-gray-400">No departments yet.</div>
        )}
      </div>

      {showAdd && institutionId && (
        <AddDeptModal onClose={() => setShowAdd(false)} onSuccess={load} />
      )}
    </div>
  );
}

function AddDeptModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ code: "", name: "", hod_wallet_address: "" });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await instituteAdminAPI.createDepartment({
        code: form.code.toUpperCase(),
        name: form.name,
        hod_wallet_address: form.hod_wallet_address || undefined,
      });
      onSuccess();
      onClose();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0]?.msg : detail || err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose} />
        <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Create Department</h2>
          {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Code *</label>
              <input required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value.toUpperCase() })} className="input" placeholder="CSE" />
            </div>
            <div>
              <label className="label">Name *</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" placeholder="Computer Science Engineering" />
            </div>
            <div>
              <label className="label">HoD Wallet (optional)</label>
              <input value={form.hod_wallet_address} onChange={(e) => setForm({ ...form, hod_wallet_address: e.target.value })} className="input font-mono" placeholder="0x..." />
            </div>
            <div className="flex justify-end space-x-3 pt-2">
              <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
              <button type="submit" disabled={isSubmitting} className="btn-primary">
                {isSubmitting ? <div className="loader" /> : "Create"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

// ─── Faculty List ──────────────────────────────────────────────────────────────

function IAFaculty() {
  const [users, setUsers] = useState([]);
  const [search, setSearch] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [acting, setActing] = useState(null);

  const load = () => {
    setIsLoading(true);
    instituteAdminAPI.getUsers()
      .then((r) => setUsers(r.data || []))
      .catch(() => setUsers([]))
      .finally(() => setIsLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleAssignHod = async (wallet, name) => {
    if (!confirm(`Promote ${name} to HoD?`)) return;
    setActing(wallet);
    try {
      await instituteAdminAPI.assignHod(wallet);
      load();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to assign HoD");
    } finally {
      setActing(null);
    }
  };

  const filtered = users.filter((u) =>
    u.name.toLowerCase().includes(search.toLowerCase()) ||
    (u.email || "").toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) return <div className="flex items-center justify-center h-48"><div className="loader" /></div>;

  return (
    <div className="space-y-4">
      <div className="relative max-w-md">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search faculty..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input pl-10"
        />
      </div>

      <div className="card overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="table-header">Name</th>
                <th className="table-header">Role</th>
                <th className="table-header">Designation</th>
                <th className="table-header">Email</th>
                <th className="table-header">Credits</th>
                <th className="table-header">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              {filtered.map((u) => (
                <tr key={u.id} className="hover:bg-gray-50">
                  <td className="table-cell font-medium text-gray-900">{u.name}</td>
                  <td className="table-cell">
                    <span className={clsx("badge", u.role === "hod" ? "badge-pending" : "badge-approved")}>{u.role}</span>
                  </td>
                  <td className="table-cell text-gray-500 text-sm">
                    {u.designation
                      ? u.designation.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
                      : "—"}
                  </td>
                  <td className="table-cell text-gray-500">{u.email || "—"}</td>
                  <td className="table-cell font-medium text-green-600">{u.total_credits}</td>
                  <td className="table-cell">
                    {u.role === "faculty" && (
                      <button
                        onClick={() => handleAssignHod(u.wallet_address, u.name)}
                        disabled={acting === u.wallet_address}
                        className="text-primary-600 hover:text-primary-700 text-sm font-medium"
                      >
                        {acting === u.wallet_address ? "..." : "Make HoD"}
                      </button>
                    )}
                  </td>
                </tr>
              ))}
              {filtered.length === 0 && (
                <tr><td colSpan={6} className="table-cell text-center text-gray-400 py-8">No faculty found.</td></tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

// ─── Shared ─────────────────────────────────────────────────────────────────────

function StatCard({ title, value, icon: Icon, color, text }) {
  const colorClasses = {
    blue: "bg-blue-100 text-blue-600",
    purple: "bg-purple-100 text-purple-600",
    green: "bg-green-100 text-green-600",
    yellow: "bg-yellow-100 text-yellow-600",
    indigo: "bg-indigo-100 text-indigo-600",
  };

  return (
    <div className="card">
      <div className="flex items-center space-x-4">
        <div className={clsx("p-3 rounded-lg shrink-0", colorClasses[color])}>
          <Icon className="h-6 w-6" />
        </div>
        <div className="min-w-0">
          <p className={clsx("font-bold text-gray-900 truncate", text ? "text-base" : "text-2xl")}>{value}</p>
          <p className="text-sm text-gray-500">{title}</p>
        </div>
      </div>
    </div>
  );
}

export default InstituteAdminPanel;
