import { useEffect, useState } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { adminAPI, institutesAPI } from "../services/api";
import {
  UsersIcon,
  BuildingOfficeIcon,
  BuildingLibraryIcon,
  ChartBarIcon,
  CubeIcon,
  PlusIcon,
  MagnifyingGlassIcon,
  ShieldCheckIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

function AdminPanel() {
  const location = useLocation();

  const adminNavigation = [
    { name: "Overview", href: "/admin", icon: ChartBarIcon },
    { name: "Pending", href: "/admin/pending", icon: ShieldCheckIcon },
    { name: "Institutions", href: "/admin/institutions", icon: BuildingLibraryIcon },
    { name: "Departments", href: "/admin/departments", icon: BuildingOfficeIcon },
    { name: "Faculty", href: "/admin/faculty", icon: UsersIcon },
    { name: "Blockchain", href: "/admin/blockchain", icon: CubeIcon },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        <p className="mt-1 text-gray-500">Manage institutions, departments, faculty, and system settings</p>
      </div>

      <div className="border-b border-gray-200">
        <nav className="flex space-x-8 overflow-x-auto">
          {adminNavigation.map((item) => {
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
        <Route index element={<AdminOverview />} />
        <Route path="pending" element={<PendingApprovals />} />
        <Route path="institutions" element={<InstitutionManagement />} />
        <Route path="departments" element={<DepartmentManagement />} />
        <Route path="faculty" element={<FacultyManagement />} />
        <Route path="blockchain" element={<BlockchainStats />} />
      </Routes>
    </div>
  );
}

// ─── Overview ──────────────────────────────────────────────────────────────────

function AdminOverview() {
  const [stats, setStats] = useState(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const [usersResp, deptsResp] = await Promise.all([
          adminAPI.getUsers(),
          adminAPI.getDepartments(),
        ]);
        const users = usersResp.data || [];
        setStats({
          totalFaculty: users.filter((u) => u.role === "faculty").length,
          totalHoD: users.filter((u) => u.role === "hod").length,
          totalDepartments: (deptsResp.data || []).length,
          totalUsers: users.length,
        });
      } catch {
        setStats({ totalFaculty: 0, totalHoD: 0, totalDepartments: 0, totalUsers: 0 });
      } finally {
        setIsLoading(false);
      }
    };
    fetchStats();
  }, []);

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="loader" /></div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total Faculty" value={stats.totalFaculty} icon={UsersIcon} color="blue" />
        <StatCard title="Heads of Department" value={stats.totalHoD} icon={UsersIcon} color="purple" />
        <StatCard title="Departments" value={stats.totalDepartments} icon={BuildingOfficeIcon} color="green" />
        <StatCard title="Total Users" value={stats.totalUsers} icon={ShieldCheckIcon} color="indigo" />
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Quick Actions</h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link to="/admin/institutions" className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <BuildingLibraryIcon className="h-8 w-8 text-indigo-600" />
            <p className="mt-2 font-medium text-gray-900">Manage Institutions</p>
            <p className="text-sm text-gray-500">Create institutions first</p>
          </Link>
          <Link to="/admin/departments" className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <BuildingOfficeIcon className="h-8 w-8 text-purple-600" />
            <p className="mt-2 font-medium text-gray-900">Manage Departments</p>
            <p className="text-sm text-gray-500">Add departments under institutions</p>
          </Link>
          <Link to="/admin/pending" className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors">
            <ShieldCheckIcon className="h-8 w-8 text-yellow-500" />
            <p className="mt-2 font-medium text-gray-900">Pending Approvals</p>
            <p className="text-sm text-gray-500">Approve new registrations</p>
          </Link>
        </div>
      </div>
    </div>
  );
}

// ─── Institution Management ─────────────────────────────────────────────────────

function InstitutionManagement() {
  const [institutions, setInstitutions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  const load = async () => {
    setIsLoading(true);
    try {
      const r = await adminAPI.listInstitutions();
      setInstitutions(r.data || []);
    } catch {
      setInstitutions([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleDeactivate = async (id, name) => {
    if (!confirm(`Deactivate "${name}"? New registrations under it will be blocked.`)) return;
    try {
      await adminAPI.deactivateInstitution(id);
      await load();
    } catch (err) {
      alert(err.response?.data?.detail || "Failed to deactivate");
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => setShowAdd(true)} className="btn-primary inline-flex items-center">
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Institution
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48"><div className="loader" /></div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {institutions.map((inst) => (
            <div key={inst.id} className="card">
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900">{inst.name}</h3>
                  <p className="text-sm text-gray-500">Code: {inst.code}</p>
                  {inst.admin_address && (
                    <p className="text-xs text-gray-400 font-mono mt-1 truncate">{inst.admin_address}</p>
                  )}
                </div>
                <span className={clsx("badge", inst.is_active ? "badge-approved" : "badge-rejected")}>
                  {inst.is_active ? "Active" : "Inactive"}
                </span>
              </div>
              {inst.is_active && (
                <div className="mt-4">
                  <button
                    onClick={() => handleDeactivate(inst.id, inst.name)}
                    className="text-red-600 hover:text-red-700 text-sm font-medium"
                  >
                    Deactivate
                  </button>
                </div>
              )}
            </div>
          ))}
          {institutions.length === 0 && (
            <div className="col-span-2 text-center py-12 text-gray-400">
              No institutions yet. Create one to allow faculty registration.
            </div>
          )}
        </div>
      )}

      {showAdd && <AddInstitutionModal onClose={() => setShowAdd(false)} onSuccess={load} />}
    </div>
  );
}

function AddInstitutionModal({ onClose, onSuccess }) {
  const [form, setForm] = useState({ code: "", name: "", admin_address: "" });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await adminAPI.createInstitution({
        code: form.code.toUpperCase(),
        name: form.name,
        admin_address: form.admin_address || undefined,
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
          <h2 className="text-xl font-bold text-gray-900 mb-4">Create Institution</h2>
          {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Institution Code *</label>
              <input required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="input uppercase" placeholder="MIT" />
            </div>
            <div>
              <label className="label">Full Name *</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" placeholder="Massachusetts Institute of Technology" />
            </div>
            <div>
              <label className="label">Admin Wallet Address</label>
              <input value={form.admin_address} onChange={(e) => setForm({ ...form, admin_address: e.target.value })} className="input font-mono" placeholder="0x..." />
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

// ─── Department Management ─────────────────────────────────────────────────────

function DepartmentManagement() {
  const [departments, setDepartments] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [showAdd, setShowAdd] = useState(false);

  const load = async () => {
    setIsLoading(true);
    try {
      const r = await adminAPI.getDepartments();
      setDepartments(r.data || []);
    } catch {
      setDepartments([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button onClick={() => setShowAdd(true)} className="btn-primary inline-flex items-center">
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Department
        </button>
      </div>

      {isLoading ? (
        <div className="flex items-center justify-center h-48"><div className="loader" /></div>
      ) : (
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
              <div className="mt-3 text-sm text-gray-500">
                HoD ID: {dept.hod_id ?? "Not assigned"}
              </div>
            </div>
          ))}
          {departments.length === 0 && (
            <div className="col-span-2 text-center py-12 text-gray-400">
              No departments yet. Create an institution first, then add departments.
            </div>
          )}
        </div>
      )}

      {showAdd && <AddDepartmentModal onClose={() => setShowAdd(false)} onSuccess={load} />}
    </div>
  );
}

function AddDepartmentModal({ onClose, onSuccess }) {
  const [institutions, setInstitutions] = useState([]);
  const [form, setForm] = useState({ institution_id: "", code: "", name: "", hod_wallet_address: "" });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    adminAPI.listInstitutions().then((r) => setInstitutions(r.data || [])).catch(() => {});
  }, []);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await adminAPI.createDepartment({
        institution_id: parseInt(form.institution_id),
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
              <label className="label">Institution *</label>
              <select required value={form.institution_id} onChange={(e) => setForm({ ...form, institution_id: e.target.value })} className="input">
                <option value="">Select institution...</option>
                {institutions.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Department Code *</label>
              <input required value={form.code} onChange={(e) => setForm({ ...form, code: e.target.value })} className="input uppercase" placeholder="CS" />
            </div>
            <div>
              <label className="label">Department Name *</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" placeholder="Computer Science" />
            </div>
            <div>
              <label className="label">HoD Wallet Address</label>
              <input value={form.hod_wallet_address} onChange={(e) => setForm({ ...form, hod_wallet_address: e.target.value })} className="input font-mono" placeholder="0x... (optional)" />
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

// ─── Faculty Management ─────────────────────────────────────────────────────────

function FacultyManagement() {
  const [users, setUsers] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [roleFilter, setRoleFilter] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  const load = async () => {
    setIsLoading(true);
    try {
      const params = roleFilter ? { role: roleFilter } : {};
      const r = await adminAPI.getUsers(params);
      setUsers(r.data || []);
    } catch {
      setUsers([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, [roleFilter]);

  const filtered = users.filter(
    (u) =>
      u.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (u.email || "").toLowerCase().includes(searchQuery.toLowerCase()) ||
      u.wallet_address.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex gap-3 flex-1">
          <div className="relative flex-1 max-w-md">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search by name, email, or wallet..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </div>
          <select value={roleFilter} onChange={(e) => setRoleFilter(e.target.value)} className="input w-36">
            <option value="">All roles</option>
            <option value="faculty">Faculty</option>
            <option value="hod">HoD</option>
            <option value="admin">Admin</option>
          </select>
        </div>
        <button onClick={() => setShowAddModal(true)} className="btn-primary inline-flex items-center">
          <PlusIcon className="h-5 w-5 mr-2" />
          Add User
        </button>
      </div>

      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-64"><div className="loader" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Name</th>
                  <th className="table-header">Role</th>
                  <th className="table-header">Email</th>
                  <th className="table-header">Wallet</th>
                  <th className="table-header">Credits</th>
                  <th className="table-header">Status</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filtered.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium text-gray-900">{u.name}</td>
                    <td className="table-cell">
                      <span className={clsx("badge", u.role === "admin" ? "badge-flagged" : u.role === "hod" ? "badge-pending" : "badge-approved")}>
                        {u.role}
                      </span>
                    </td>
                    <td className="table-cell text-gray-500">{u.email || "—"}</td>
                    <td className="table-cell font-mono text-xs text-gray-500">
                      {u.wallet_address.slice(0, 10)}...{u.wallet_address.slice(-6)}
                    </td>
                    <td className="table-cell font-medium text-green-600">{u.total_credits}</td>
                    <td className="table-cell">
                      <span className={clsx("badge", u.is_active ? "badge-approved" : "badge-rejected")}>
                        {u.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                  </tr>
                ))}
                {filtered.length === 0 && (
                  <tr>
                    <td colSpan={6} className="table-cell text-center text-gray-400 py-8">No users found.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {showAddModal && <AddUserModal onClose={() => setShowAddModal(false)} onSuccess={load} />}
    </div>
  );
}

function AddUserModal({ onClose, onSuccess }) {
  const [institutions, setInstitutions] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [form, setForm] = useState({
    wallet_address: "",
    name: "",
    email: "",
    employee_id: "",
    role: "faculty",
    institution_id: "",
    department_code: "",
  });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    institutesAPI.list().then((r) => setInstitutions(r.data || [])).catch(() => {});
  }, []);

  const handleInstitutionChange = async (e) => {
    const id = e.target.value;
    setForm((f) => ({ ...f, institution_id: id, department_code: "" }));
    if (!id) { setDepartments([]); return; }
    try {
      const r = await institutesAPI.getDepartments(id);
      setDepartments(r.data || []);
    } catch {
      setDepartments([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await adminAPI.createUser({
        wallet_address: form.wallet_address,
        name: form.name,
        email: form.email || undefined,
        employee_id: form.employee_id || undefined,
        role: form.role,
        institution_id: form.institution_id ? parseInt(form.institution_id) : undefined,
        department_code: form.department_code || undefined,
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
      <div className="flex items-center justify-center min-h-screen px-4 py-8">
        <div className="fixed inset-0 bg-gray-500 bg-opacity-75" onClick={onClose} />
        <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Add User</h2>
          {error && <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">{error}</div>}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Wallet Address *</label>
              <input required value={form.wallet_address} onChange={(e) => setForm({ ...form, wallet_address: e.target.value })} className="input font-mono" placeholder="0x..." />
            </div>
            <div>
              <label className="label">Full Name *</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" />
            </div>
            <div>
              <label className="label">Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input" />
            </div>
            <div>
              <label className="label">Employee ID</label>
              <input value={form.employee_id} onChange={(e) => setForm({ ...form, employee_id: e.target.value })} className="input" />
            </div>
            <div>
              <label className="label">Role *</label>
              <select required value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })} className="input">
                <option value="faculty">Faculty</option>
                <option value="hod">Head of Department</option>
                <option value="admin">Admin</option>
              </select>
            </div>
            <div>
              <label className="label">Institution</label>
              <select value={form.institution_id} onChange={handleInstitutionChange} className="input">
                <option value="">Select institution...</option>
                {institutions.map((i) => <option key={i.id} value={i.id}>{i.name}</option>)}
              </select>
            </div>
            <div>
              <label className="label">Department</label>
              <select
                value={form.department_code}
                onChange={(e) => setForm({ ...form, department_code: e.target.value })}
                className="input"
                disabled={!form.institution_id || departments.length === 0}
              >
                <option value="">{form.institution_id ? "Select department..." : "Select institution first"}</option>
                {departments.map((d) => <option key={d.id} value={d.code}>{d.name} ({d.code})</option>)}
              </select>
            </div>
            <div className="flex justify-end space-x-3 pt-2">
              <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
              <button type="submit" disabled={isSubmitting} className="btn-primary">
                {isSubmitting ? <div className="loader" /> : "Create User"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

// ─── Pending Approvals ─────────────────────────────────────────────────────────

function PendingApprovals() {
  const [pending, setPending] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [approving, setApproving] = useState(null);

  const load = async () => {
    setIsLoading(true);
    try {
      const r = await adminAPI.getPendingUsers();
      setPending(r.data || []);
    } catch {
      setPending([]);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const handleApprove = async (walletAddress, name) => {
    setApproving(walletAddress);
    try {
      await adminAPI.approveUser(walletAddress);
      setPending((prev) => prev.filter((u) => u.wallet_address !== walletAddress));
    } catch (err) {
      alert(err.response?.data?.detail || `Failed to approve ${name}`);
    } finally {
      setApproving(null);
    }
  };

  if (isLoading) return <div className="flex items-center justify-center h-48"><div className="loader" /></div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-semibold text-gray-900">Pending Registrations</h2>
          <p className="text-sm text-gray-500">Users who have registered and are awaiting approval</p>
        </div>
        <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-yellow-100 text-yellow-800">
          {pending.length} pending
        </span>
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
                  <th className="table-header">Email</th>
                  <th className="table-header">Employee ID</th>
                  <th className="table-header">Wallet</th>
                  <th className="table-header">Registered</th>
                  <th className="table-header">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {pending.map((u) => (
                  <tr key={u.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium text-gray-900">{u.name}</td>
                    <td className="table-cell">
                      <span className={clsx("badge", u.role === "hod" ? "badge-pending" : "badge-approved")}>
                        {u.role}
                      </span>
                    </td>
                    <td className="table-cell text-gray-500">{u.email || "—"}</td>
                    <td className="table-cell text-gray-500">{u.employee_id || "—"}</td>
                    <td className="table-cell font-mono text-xs text-gray-500">
                      {u.wallet_address.slice(0, 10)}...{u.wallet_address.slice(-6)}
                    </td>
                    <td className="table-cell text-gray-500 text-sm">
                      {new Date(u.created_at).toLocaleDateString()}
                    </td>
                    <td className="table-cell">
                      <button
                        onClick={() => handleApprove(u.wallet_address, u.name)}
                        disabled={approving === u.wallet_address}
                        className="btn-primary text-sm py-1 px-3"
                      >
                        {approving === u.wallet_address ? <div className="loader" /> : "Approve"}
                      </button>
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

// ─── Blockchain Stats ───────────────────────────────────────────────────────────

function BlockchainStats() {
  const [status, setStatus] = useState(null);
  const [contracts, setContracts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    Promise.all([adminAPI.getBlockchainStatus(), adminAPI.getContracts()])
      .then(([statusResp, contractsResp]) => {
        setStatus(statusResp.data);
        setContracts(contractsResp.data || []);
      })
      .catch(() => {})
      .finally(() => setIsLoading(false));
  }, []);

  if (isLoading) return <div className="flex items-center justify-center h-48"><div className="loader" /></div>;

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Connection</p>
          <p className={clsx("text-lg font-bold", status?.connected ? "text-green-600" : "text-red-600")}>
            {status?.connected ? "Connected" : "Disconnected"}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Chain ID</p>
          <p className="text-lg font-bold text-gray-900">{status?.chain_id ?? "—"}</p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Block Number</p>
          <p className="text-lg font-bold text-gray-900">{status?.block_number ?? "—"}</p>
        </div>
      </div>

      <div className="card bg-gradient-to-r from-gray-800 to-gray-900 text-white">
        <h3 className="text-lg font-semibold mb-4">Network Configuration</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-400">RPC URL</p>
            <p className="font-mono text-sm">{status?.rpc_url ?? "—"}</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Consensus</p>
            <p>IBFT 2.0 (PoA)</p>
          </div>
        </div>
      </div>

      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Deployed Contracts</h3>
        <div className="space-y-3">
          {contracts.map((c) => (
            <div key={c.name} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
              <div>
                <p className="font-medium text-gray-900">{c.name}</p>
                <p className="font-mono text-sm text-gray-500">{c.address}</p>
              </div>
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 bg-green-500 rounded-full" />
                <span className="text-sm text-green-600">Deployed</span>
              </div>
            </div>
          ))}
          {contracts.length === 0 && (
            <p className="text-sm text-gray-400">No contracts configured.</p>
          )}
        </div>
      </div>
    </div>
  );
}

// ─── Shared Components ──────────────────────────────────────────────────────────

function StatCard({ title, value, icon: Icon, color }) {
  const colorClasses = {
    blue: "bg-blue-100 text-blue-600",
    purple: "bg-purple-100 text-purple-600",
    green: "bg-green-100 text-green-600",
    yellow: "bg-yellow-100 text-yellow-600",
    emerald: "bg-emerald-100 text-emerald-600",
    indigo: "bg-indigo-100 text-indigo-600",
  };

  return (
    <div className="card">
      <div className="flex items-center space-x-4">
        <div className={clsx("p-3 rounded-lg", colorClasses[color])}>
          <Icon className="h-6 w-6" />
        </div>
        <div>
          <p className="text-2xl font-bold text-gray-900">{value ?? "—"}</p>
          <p className="text-sm text-gray-500">{title}</p>
        </div>
      </div>
    </div>
  );
}

export default AdminPanel;
