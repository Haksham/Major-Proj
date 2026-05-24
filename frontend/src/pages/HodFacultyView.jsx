import { useEffect, useState } from "react";
import { contributionsAPI } from "../services/api";
import {
  UsersIcon,
  DocumentTextIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  AcademicCapIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

const CATEGORY_LABELS = {
  refereed_journal: "Refereed Journal",
  international_book: "International Book",
  national_book: "National Book",
  book_chapter: "Book Chapter",
  international_lecture: "International Lecture",
  national_conference: "National Conference",
  patent_filed: "Patent Filed",
  patent_granted: "Patent Granted",
  editorial_work: "Editorial Work",
  research_project: "Research Project",
};

const STATUS_CONFIG = {
  pending: { label: "Pending", cls: "badge-pending" },
  under_review: { label: "Under Review", cls: "badge-pending" },
  validated: { label: "Validated", cls: "badge-validated" },
  rejected: { label: "Rejected", cls: "badge-rejected" },
  flagged: { label: "Flagged", cls: "badge-rejected" },
};

function HodFacultyView() {
  const [faculty, setFaculty] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [expanded, setExpanded] = useState(null);
  const [contribs, setContribs] = useState({});
  const [loadingContribs, setLoadingContribs] = useState(null);

  useEffect(() => {
    contributionsAPI.getDepartmentFaculty()
      .then((r) => setFaculty(r.data || []))
      .catch(() => setFaculty([]))
      .finally(() => setIsLoading(false));
  }, []);

  const toggleExpand = async (member) => {
    if (expanded === member.wallet_address) {
      setExpanded(null);
      return;
    }
    setExpanded(member.wallet_address);
    if (!contribs[member.wallet_address]) {
      setLoadingContribs(member.wallet_address);
      try {
        const res = await contributionsAPI.getDepartmentContributions(member.wallet_address);
        setContribs((prev) => ({ ...prev, [member.wallet_address]: res.data || [] }));
      } catch {
        setContribs((prev) => ({ ...prev, [member.wallet_address]: [] }));
      } finally {
        setLoadingContribs(null);
      }
    }
  };

  const filtered = faculty.filter(
    (f) =>
      f.name.toLowerCase().includes(search.toLowerCase()) ||
      (f.email || "").toLowerCase().includes(search.toLowerCase()),
  );

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loader" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Department Faculty</h1>
        <p className="mt-1 text-gray-500">
          View contributions and performance of faculty in your department
        </p>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <StatCard
          icon={UsersIcon}
          color="blue"
          title="Total Faculty"
          value={faculty.length}
        />
        <StatCard
          icon={DocumentTextIcon}
          color="indigo"
          title="Total Contributions"
          value={faculty.reduce((s, f) => s + f.total_contributions, 0)}
        />
        <StatCard
          icon={ClockIcon}
          color="yellow"
          title="Pending Review"
          value={faculty.reduce((s, f) => s + f.pending, 0)}
        />
        <StatCard
          icon={AcademicCapIcon}
          color="green"
          title="Total Credits"
          value={faculty.reduce((s, f) => s + (f.total_credits || 0), 0).toFixed(1)}
        />
      </div>

      {/* Search */}
      <div className="relative max-w-md">
        <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400" />
        <input
          type="text"
          placeholder="Search by name or email..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="input pl-10"
        />
      </div>

      {/* Faculty list */}
      {filtered.length === 0 ? (
        <div className="card text-center py-12">
          <UsersIcon className="mx-auto h-12 w-12 text-gray-300" />
          <p className="mt-3 text-gray-500">No faculty found in your department.</p>
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((member) => (
            <div key={member.id} className="card overflow-hidden">
              {/* Faculty row */}
              <button
                className="w-full text-left"
                onClick={() => toggleExpand(member)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-4 min-w-0">
                    <div className="p-2 bg-primary-50 rounded-lg shrink-0">
                      <UsersIcon className="h-6 w-6 text-primary-600" />
                    </div>
                    <div className="min-w-0">
                      <div className="flex items-center space-x-2 flex-wrap gap-y-1">
                        <p className="font-semibold text-gray-900">{member.name}</p>
                        <span className={clsx("badge", member.role === "hod" ? "badge-pending" : "badge-approved")}>
                          {member.role === "hod" ? "HoD" : "Faculty"}
                        </span>
                        {member.designation && (
                          <span className="text-xs text-gray-500">
                            {member.designation.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())}
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-500 truncate">{member.email || "—"}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-6 shrink-0 ml-4">
                    <div className="hidden sm:flex space-x-4 text-sm">
                      <span className="flex items-center space-x-1 text-gray-500">
                        <DocumentTextIcon className="h-4 w-4" />
                        <span>{member.total_contributions}</span>
                      </span>
                      <span className="flex items-center space-x-1 text-yellow-600">
                        <ClockIcon className="h-4 w-4" />
                        <span>{member.pending}</span>
                      </span>
                      <span className="flex items-center space-x-1 text-green-600">
                        <CheckCircleIcon className="h-4 w-4" />
                        <span>{member.validated}</span>
                      </span>
                      <span className="flex items-center space-x-1 text-red-500">
                        <XCircleIcon className="h-4 w-4" />
                        <span>{member.rejected}</span>
                      </span>
                      <span className="font-semibold text-green-700">
                        {member.total_credits.toFixed(1)} cr
                      </span>
                    </div>
                    {expanded === member.wallet_address
                      ? <ChevronUpIcon className="h-5 w-5 text-gray-400" />
                      : <ChevronDownIcon className="h-5 w-5 text-gray-400" />}
                  </div>
                </div>
              </button>

              {/* Contributions panel */}
              {expanded === member.wallet_address && (
                <div className="mt-4 border-t border-gray-100 pt-4">
                  {loadingContribs === member.wallet_address ? (
                    <div className="flex justify-center py-6"><div className="loader" /></div>
                  ) : (contribs[member.wallet_address] || []).length === 0 ? (
                    <p className="text-sm text-gray-400 text-center py-4">No contributions yet.</p>
                  ) : (
                    <div className="overflow-x-auto">
                      <table className="min-w-full divide-y divide-gray-100 text-sm">
                        <thead>
                          <tr className="text-left text-gray-500">
                            <th className="py-2 pr-4 font-medium">Title</th>
                            <th className="py-2 pr-4 font-medium">Category</th>
                            <th className="py-2 pr-4 font-medium">Status</th>
                            <th className="py-2 pr-4 font-medium">Quality</th>
                            <th className="py-2 pr-4 font-medium">Novelty</th>
                            <th className="py-2 pr-4 font-medium">Credits</th>
                            <th className="py-2 font-medium">Date</th>
                          </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-50">
                          {(contribs[member.wallet_address] || []).map((c) => {
                            const sc = STATUS_CONFIG[c.status] || STATUS_CONFIG.pending;
                            return (
                              <tr key={c.id} className="hover:bg-gray-50">
                                <td className="py-2 pr-4 font-medium text-gray-900 max-w-xs truncate">{c.title}</td>
                                <td className="py-2 pr-4 text-gray-500">
                                  {CATEGORY_LABELS[c.category] || c.category}
                                </td>
                                <td className="py-2 pr-4">
                                  <span className={clsx("badge", sc.cls)}>{sc.label}</span>
                                </td>
                                <td className="py-2 pr-4 text-gray-700">
                                  {c.ai_quality_score > 0 ? `${c.ai_quality_score.toFixed(1)}%` : "—"}
                                </td>
                                <td className="py-2 pr-4 text-gray-700">
                                  {c.novelty_percentage > 0 ? `${c.novelty_percentage.toFixed(1)}%` : "—"}
                                </td>
                                <td className="py-2 pr-4 font-medium text-green-600">
                                  {c.final_credits > 0 ? c.final_credits : c.base_credits}
                                </td>
                                <td className="py-2 text-gray-400 text-xs whitespace-nowrap">
                                  {new Date(c.submission_time).toLocaleDateString()}
                                </td>
                              </tr>
                            );
                          })}
                        </tbody>
                      </table>
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({ icon: Icon, color, title, value }) {
  const colors = {
    blue: "bg-blue-50 text-blue-600",
    indigo: "bg-indigo-50 text-indigo-600",
    yellow: "bg-yellow-50 text-yellow-600",
    green: "bg-green-50 text-green-600",
  };
  return (
    <div className="card">
      <div className="flex items-center space-x-3">
        <div className={clsx("p-2 rounded-lg shrink-0", colors[color])}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <p className="text-xl font-bold text-gray-900">{value}</p>
          <p className="text-xs text-gray-500">{title}</p>
        </div>
      </div>
    </div>
  );
}

export default HodFacultyView;
