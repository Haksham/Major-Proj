import { useState } from "react";
import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { useAuthStore, useUIStore } from "../../store";
import clsx from "clsx";
import {
  HomeIcon,
  DocumentTextIcon,
  PlusCircleIcon,
  BriefcaseIcon,
  ClipboardDocumentCheckIcon,
  Cog6ToothIcon,
  Bars3Icon,
  XMarkIcon,
  ArrowRightOnRectangleIcon,
  UserCircleIcon,
  ChevronDownIcon,
  BellIcon,
  CubeIcon,
  BuildingOffice2Icon,
} from "@heroicons/react/24/outline";

const navigation = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: HomeIcon,
    roles: ["faculty", "hod", "institute_admin", "admin"],
  },
  {
    name: "My Contributions",
    href: "/contributions",
    icon: DocumentTextIcon,
    roles: ["faculty", "hod"],
  },
  {
    name: "Submit New",
    href: "/contributions/new",
    icon: PlusCircleIcon,
    roles: ["faculty", "hod"],
  },
  {
    name: "Portfolio",
    href: "/portfolio",
    icon: BriefcaseIcon,
    roles: ["faculty", "hod"],
  },
  {
    name: "Review Queue",
    href: "/reviews",
    icon: ClipboardDocumentCheckIcon,
    roles: ["hod"],
  },
  {
    name: "Institute Admin",
    href: "/institute-admin",
    icon: BuildingOffice2Icon,
    roles: ["institute_admin"],
  },
  {
    name: "Admin Panel",
    href: "/admin",
    icon: Cog6ToothIcon,
    roles: ["admin"],
  },
];

const ROLE_LABELS = {
  admin: "Master Admin",
  institute_admin: "Institute Admin",
  hod: "Head of Department",
  faculty: "Faculty",
};

function DashboardLayout() {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, walletAddress, logout } = useAuthStore();
  const { sidebarOpen, toggleSidebar } = useUIStore();
  const [userMenuOpen, setUserMenuOpen] = useState(false);

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  const filteredNavigation = navigation.filter((item) =>
    item.roles.includes(user?.role || "faculty"),
  );

  const shortenAddress = (address) => {
    if (!address) return "";
    return `${address.slice(0, 6)}...${address.slice(-4)}`;
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar backdrop */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 bg-gray-600 bg-opacity-75 lg:hidden"
          onClick={toggleSidebar}
        />
      )}

      {/* Sidebar */}
      <aside
        className={clsx(
          "fixed inset-y-0 left-0 z-50 w-64 bg-white shadow-lg transform transition-transform duration-300 ease-in-out lg:translate-x-0",
          sidebarOpen ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="flex h-full flex-col">
          {/* Logo */}
          <div className="flex h-16 items-center justify-between px-6 border-b border-gray-200">
            <Link to="/dashboard" className="flex items-center space-x-2">
              <CubeIcon className="h-8 w-8 text-primary-600" />
              <span className="text-xl font-bold text-gray-900">SALF</span>
            </Link>
            <button
              className="lg:hidden text-gray-500 hover:text-gray-700"
              onClick={toggleSidebar}
            >
              <XMarkIcon className="h-6 w-6" />
            </button>
          </div>

          {/* Navigation */}
          <nav className="flex-1 px-4 py-6 space-y-1 overflow-y-auto">
            {filteredNavigation.map((item) => {
              const isActive =
                location.pathname === item.href ||
                (item.href !== "/dashboard" &&
                  location.pathname.startsWith(item.href));

              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={clsx(
                    "flex items-center px-4 py-3 text-sm font-medium rounded-lg transition-colors",
                    isActive
                      ? "bg-primary-50 text-primary-700"
                      : "text-gray-600 hover:bg-gray-50 hover:text-gray-900",
                  )}
                >
                  <item.icon
                    className={clsx(
                      "mr-3 h-5 w-5",
                      isActive ? "text-primary-600" : "text-gray-400",
                    )}
                  />
                  {item.name}
                </Link>
              );
            })}
          </nav>

          {/* Blockchain Status */}
          <div className="px-4 py-4 border-t border-gray-200">
            <div className="flex items-center px-4 py-2 bg-green-50 rounded-lg">
              <div className="w-2 h-2 bg-green-500 rounded-full mr-2 pulse-blockchain" />
              <span className="text-xs text-green-700 font-medium">
                Blockchain Connected
              </span>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div
        className={clsx(
          "transition-all duration-300",
          sidebarOpen ? "lg:ml-64" : "lg:ml-64",
        )}
      >
        {/* Top header */}
        <header className="sticky top-0 z-30 bg-white shadow-sm">
          <div className="flex h-16 items-center justify-between px-4 sm:px-6 lg:px-8">
            {/* Mobile menu button */}
            <button
              className="lg:hidden text-gray-500 hover:text-gray-700"
              onClick={toggleSidebar}
            >
              <Bars3Icon className="h-6 w-6" />
            </button>

            {/* Page title placeholder */}
            <div className="flex-1 lg:ml-0" />

            {/* Right side actions */}
            <div className="flex items-center space-x-4">
              {/* Notifications */}
              <button className="relative p-2 text-gray-400 hover:text-gray-600 rounded-full hover:bg-gray-100">
                <BellIcon className="h-6 w-6" />
                <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
              </button>

              {/* User menu */}
              <div className="relative">
                <button
                  className="flex items-center space-x-3 p-2 rounded-lg hover:bg-gray-50"
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                >
                  <UserCircleIcon className="h-8 w-8 text-gray-400" />
                  <div className="hidden sm:block text-left">
                    <p className="text-sm font-medium text-gray-700">
                      {user?.name || "User"}
                    </p>
                    <p className="text-xs text-gray-500">
                      {shortenAddress(walletAddress)}
                    </p>
                  </div>
                  <ChevronDownIcon className="h-4 w-4 text-gray-400" />
                </button>

                {/* Dropdown menu */}
                {userMenuOpen && (
                  <div className="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg py-1 border border-gray-200">
                    <div className="px-4 py-2 border-b border-gray-100">
                      <p className="text-sm font-medium text-gray-900">
                        {user?.name}
                      </p>
                      <p className="text-xs text-gray-500">
                        {ROLE_LABELS[user?.role] || user?.role}
                      </p>
                    </div>
                    {(user?.role === "faculty" || user?.role === "hod") && (
                      <Link
                        to="/portfolio"
                        className="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-50"
                        onClick={() => setUserMenuOpen(false)}
                      >
                        My Portfolio
                      </Link>
                    )}
                    <button
                      onClick={handleLogout}
                      className="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 flex items-center"
                    >
                      <ArrowRightOnRectangleIcon className="h-4 w-4 mr-2" />
                      Disconnect
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </header>

        {/* Page content */}
        <main className="p-4 sm:p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}

export default DashboardLayout;
