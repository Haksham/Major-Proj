import { useEffect, useState } from "react";
import { Routes, Route, Link, useLocation } from "react-router-dom";
import { adminAPI } from "../services/api";
import {
  UsersIcon,
  BuildingOfficeIcon,
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
    { name: "Faculty", href: "/admin/faculty", icon: UsersIcon },
    {
      name: "Departments",
      href: "/admin/departments",
      icon: BuildingOfficeIcon,
    },
    { name: "Blockchain", href: "/admin/blockchain", icon: CubeIcon },
  ];

  return (
    <div className="space-y-6">
      {/* Admin header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Admin Panel</h1>
        <p className="mt-1 text-gray-500">
          Manage faculty, departments, and system settings
        </p>
      </div>

      {/* Admin navigation */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {adminNavigation.map((item) => {
            const isActive = location.pathname === item.href;
            return (
              <Link
                key={item.name}
                to={item.href}
                className={clsx(
                  "flex items-center py-4 px-1 border-b-2 font-medium text-sm",
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

      {/* Admin routes */}
      <Routes>
        <Route index element={<AdminOverview />} />
        <Route path="faculty" element={<FacultyManagement />} />
        <Route path="departments" element={<DepartmentManagement />} />
        <Route path="blockchain" element={<BlockchainStats />} />
      </Routes>
    </div>
  );
}

// Admin Overview Component
function AdminOverview() {
  const [stats, setStats] = useState({
    totalFaculty: 0,
    totalDepartments: 0,
    totalContributions: 0,
    pendingReviews: 0,
    validatedRecords: 0,
    totalCredits: 0,
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const response = await adminAPI.getSystemStats();
        setStats(response.data);
      } catch (error) {
        console.error("Failed to fetch stats:", error);
        // Set mock data for demo
        setStats({
          totalFaculty: 45,
          totalDepartments: 8,
          totalContributions: 324,
          pendingReviews: 12,
          validatedRecords: 287,
          totalCredits: 4560,
        });
      } finally {
        setIsLoading(false);
      }
    };

    fetchStats();
  }, []);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loader" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <StatCard
          title="Total Faculty"
          value={stats.totalFaculty}
          icon={UsersIcon}
          color="blue"
        />
        <StatCard
          title="Departments"
          value={stats.totalDepartments}
          icon={BuildingOfficeIcon}
          color="purple"
        />
        <StatCard
          title="Total Contributions"
          value={stats.totalContributions}
          icon={ChartBarIcon}
          color="green"
        />
        <StatCard
          title="Pending Reviews"
          value={stats.pendingReviews}
          icon={ShieldCheckIcon}
          color="yellow"
        />
        <StatCard
          title="Validated Records"
          value={stats.validatedRecords}
          icon={CubeIcon}
          color="emerald"
        />
        <StatCard
          title="Total Credits Issued"
          value={stats.totalCredits}
          icon={ChartBarIcon}
          color="indigo"
        />
      </div>

      {/* Quick actions */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Quick Actions
        </h3>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <Link
            to="/admin/faculty"
            className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <UsersIcon className="h-8 w-8 text-primary-600" />
            <p className="mt-2 font-medium text-gray-900">Register Faculty</p>
            <p className="text-sm text-gray-500">Add new faculty members</p>
          </Link>
          <Link
            to="/admin/departments"
            className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <BuildingOfficeIcon className="h-8 w-8 text-purple-600" />
            <p className="mt-2 font-medium text-gray-900">Manage Departments</p>
            <p className="text-sm text-gray-500">
              Create or update departments
            </p>
          </Link>
          <Link
            to="/reviews"
            className="p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
          >
            <ShieldCheckIcon className="h-8 w-8 text-green-600" />
            <p className="mt-2 font-medium text-gray-900">Review Queue</p>
            <p className="text-sm text-gray-500">Process pending reviews</p>
          </Link>
        </div>
      </div>

      {/* System status */}
      <div className="card bg-gradient-to-r from-gray-800 to-gray-900 text-white">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <CubeIcon className="h-10 w-10 text-blue-400" />
            <div>
              <h3 className="text-lg font-semibold">System Status</h3>
              <p className="text-gray-400">All services operational</p>
            </div>
          </div>
          <div className="flex items-center space-x-4">
            <StatusIndicator label="Blockchain" status="online" />
            <StatusIndicator label="IPFS" status="online" />
            <StatusIndicator label="AI Engine" status="online" />
          </div>
        </div>
      </div>
    </div>
  );
}

// Faculty Management Component
function FacultyManagement() {
  const [faculty, setFaculty] = useState([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [showAddModal, setShowAddModal] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchFaculty = async () => {
      try {
        const response = await adminAPI.getAllFaculty();
        setFaculty(response.data.faculty || []);
      } catch (error) {
        console.error("Failed to fetch faculty:", error);
        // Mock data
        setFaculty([
          {
            id: 1,
            name: "Dr. John Smith",
            department: "Computer Science",
            wallet_address: "0x1234...5678",
            is_active: true,
            total_credits: 125,
          },
          {
            id: 2,
            name: "Dr. Sarah Johnson",
            department: "Physics",
            wallet_address: "0x2345...6789",
            is_active: true,
            total_credits: 98,
          },
          {
            id: 3,
            name: "Dr. Michael Brown",
            department: "Mathematics",
            wallet_address: "0x3456...7890",
            is_active: true,
            total_credits: 156,
          },
        ]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchFaculty();
  }, []);

  const filteredFaculty = faculty.filter(
    (f) =>
      f.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      f.department.toLowerCase().includes(searchQuery.toLowerCase()),
  );

  return (
    <div className="space-y-4">
      {/* Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="relative flex-1 max-w-md">
          <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search faculty..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input pl-10"
          />
        </div>
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary inline-flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Register Faculty
        </button>
      </div>

      {/* Faculty table */}
      <div className="card overflow-hidden">
        {isLoading ? (
          <div className="flex items-center justify-center h-64">
            <div className="loader" />
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="table-header">Name</th>
                  <th className="table-header">Department</th>
                  <th className="table-header">Wallet Address</th>
                  <th className="table-header">Total Credits</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {filteredFaculty.map((f) => (
                  <tr key={f.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium text-gray-900">
                      {f.name}
                    </td>
                    <td className="table-cell text-gray-500">{f.department}</td>
                    <td className="table-cell font-mono text-sm text-gray-500">
                      {f.wallet_address}
                    </td>
                    <td className="table-cell font-medium text-green-600">
                      {f.total_credits}
                    </td>
                    <td className="table-cell">
                      <span
                        className={clsx(
                          "badge",
                          f.is_active ? "badge-approved" : "badge-rejected",
                        )}
                      >
                        {f.is_active ? "Active" : "Inactive"}
                      </span>
                    </td>
                    <td className="table-cell">
                      <button className="text-primary-600 hover:text-primary-700 text-sm font-medium">
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Add Faculty Modal */}
      {showAddModal && (
        <AddFacultyModal onClose={() => setShowAddModal(false)} />
      )}
    </div>
  );
}

// Add Faculty Modal
function AddFacultyModal({ onClose }) {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    department: "",
    employee_id: "",
    wallet_address: "",
  });

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await adminAPI.registerFaculty(formData);
      onClose();
    } catch (error) {
      console.error("Failed to register faculty:", error);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4">
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75"
          onClick={onClose}
        />
        <div className="relative bg-white rounded-xl shadow-xl max-w-md w-full p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Register Faculty
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Full Name</label>
              <input
                type="text"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                className="input"
                required
              />
            </div>
            <div>
              <label className="label">Email</label>
              <input
                type="email"
                value={formData.email}
                onChange={(e) =>
                  setFormData({ ...formData, email: e.target.value })
                }
                className="input"
                required
              />
            </div>
            <div>
              <label className="label">Department</label>
              <input
                type="text"
                value={formData.department}
                onChange={(e) =>
                  setFormData({ ...formData, department: e.target.value })
                }
                className="input"
                required
              />
            </div>
            <div>
              <label className="label">Employee ID</label>
              <input
                type="text"
                value={formData.employee_id}
                onChange={(e) =>
                  setFormData({ ...formData, employee_id: e.target.value })
                }
                className="input"
                required
              />
            </div>
            <div>
              <label className="label">Wallet Address</label>
              <input
                type="text"
                value={formData.wallet_address}
                onChange={(e) =>
                  setFormData({ ...formData, wallet_address: e.target.value })
                }
                placeholder="0x..."
                className="input font-mono"
                required
              />
            </div>
            <div className="flex justify-end space-x-3 pt-4">
              <button type="button" onClick={onClose} className="btn-secondary">
                Cancel
              </button>
              <button type="submit" className="btn-primary">
                Register
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

// Department Management Component
function DepartmentManagement() {
  const [departments, setDepartments] = useState([
    {
      id: 1,
      name: "Computer Science",
      code: "CS",
      hod: "Dr. John Smith",
      faculty_count: 12,
    },
    {
      id: 2,
      name: "Physics",
      code: "PHY",
      hod: "Dr. Sarah Johnson",
      faculty_count: 8,
    },
    {
      id: 3,
      name: "Mathematics",
      code: "MATH",
      hod: "Dr. Michael Brown",
      faculty_count: 10,
    },
    { id: 4, name: "Chemistry", code: "CHEM", hod: null, faculty_count: 6 },
  ]);
  const [showAddModal, setShowAddModal] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex justify-end">
        <button
          onClick={() => setShowAddModal(true)}
          className="btn-primary inline-flex items-center"
        >
          <PlusIcon className="h-5 w-5 mr-2" />
          Create Department
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {departments.map((dept) => (
          <div key={dept.id} className="card">
            <div className="flex items-start justify-between">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">
                  {dept.name}
                </h3>
                <p className="text-sm text-gray-500">Code: {dept.code}</p>
              </div>
              <BuildingOfficeIcon className="h-8 w-8 text-gray-300" />
            </div>
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Head of Department:</span>
                <span className="font-medium text-gray-900">
                  {dept.hod || "Not Assigned"}
                </span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-500">Faculty Count:</span>
                <span className="font-medium text-gray-900">
                  {dept.faculty_count}
                </span>
              </div>
            </div>
            <div className="mt-4 flex space-x-2">
              <button className="btn-secondary text-sm flex-1">Edit</button>
              <button className="btn-secondary text-sm flex-1">
                Assign HoD
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Blockchain Stats Component
function BlockchainStats() {
  const [stats, setStats] = useState({
    totalBlocks: 1234,
    totalTransactions: 567,
    networkPeers: 4,
    lastBlockTime: new Date().toISOString(),
  });

  return (
    <div className="space-y-6">
      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="card">
          <p className="text-sm text-gray-500">Total Blocks</p>
          <p className="text-2xl font-bold text-gray-900">
            {stats.totalBlocks}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Total Transactions</p>
          <p className="text-2xl font-bold text-gray-900">
            {stats.totalTransactions}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Network Peers</p>
          <p className="text-2xl font-bold text-gray-900">
            {stats.networkPeers}
          </p>
        </div>
        <div className="card">
          <p className="text-sm text-gray-500">Last Block</p>
          <p className="text-sm font-mono text-gray-900">
            {new Date(stats.lastBlockTime).toLocaleString()}
          </p>
        </div>
      </div>

      {/* Network info */}
      <div className="card bg-gradient-to-r from-gray-800 to-gray-900 text-white">
        <h3 className="text-lg font-semibold mb-4">Network Configuration</h3>
        <div className="grid grid-cols-2 gap-4">
          <div>
            <p className="text-sm text-gray-400">Chain ID</p>
            <p className="font-mono">1337</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Consensus</p>
            <p>IBFT 2.0 (PoA)</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Block Period</p>
            <p>2 seconds</p>
          </div>
          <div>
            <p className="text-sm text-gray-400">Network</p>
            <p>Hyperledger Besu</p>
          </div>
        </div>
      </div>

      {/* Contract addresses */}
      <div className="card">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">
          Deployed Contracts
        </h3>
        <div className="space-y-3">
          <ContractInfo
            name="SALFAccessControl"
            address="0x5FbDB2315678afecb367f032d93F642f64180aa3"
          />
          <ContractInfo
            name="AcademicCreditLedger"
            address="0xe7f1725E7734CE288F8367e1Bb143E90bb3F0512"
          />
          <ContractInfo
            name="ContributionRegistry"
            address="0x9fE46736679d2D9a65F0992F2272dE9f3c7fa6e0"
          />
        </div>
      </div>
    </div>
  );
}

// Contract Info Component
function ContractInfo({ name, address }) {
  return (
    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
      <div>
        <p className="font-medium text-gray-900">{name}</p>
        <p className="font-mono text-sm text-gray-500">{address}</p>
      </div>
      <div className="flex items-center space-x-2">
        <span className="w-2 h-2 bg-green-500 rounded-full" />
        <span className="text-sm text-green-600">Deployed</span>
      </div>
    </div>
  );
}

// Stat Card Component
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
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          <p className="text-sm text-gray-500">{title}</p>
        </div>
      </div>
    </div>
  );
}

// Status Indicator Component
function StatusIndicator({ label, status }) {
  return (
    <div className="flex items-center space-x-2">
      <span
        className={clsx(
          "w-2 h-2 rounded-full",
          status === "online" ? "bg-green-500" : "bg-red-500",
        )}
      />
      <span className="text-sm text-gray-300">{label}</span>
    </div>
  );
}

export default AdminPanel;
