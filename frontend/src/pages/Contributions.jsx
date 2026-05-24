import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuthStore, useContributionStore } from "../store";
import {
  PlusIcon,
  FunnelIcon,
  MagnifyingGlassIcon,
  EyeIcon,
  DocumentArrowDownIcon,
  CubeIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

const CATEGORY_NAMES = [
  "Guest Lectures",
  "Journal Publication",
  "Book",
  "Book Chapter",
  "Patent",
  "Conference",
  "Workshop",
  "Seminar",
  "Project",
  "Award",
  "Faculty Development Program",
];

const STATUS_OPTIONS = [
  { value: "all", label: "All Status" },
  { value: "pending", label: "Pending" },
  { value: "under_review", label: "Under Review" },
  { value: "approved", label: "Approved" },
  { value: "validated", label: "Validated" },
  { value: "rejected", label: "Rejected" },
];

const CATEGORY_OPTIONS = [
  { value: "all", label: "All Categories" },
  ...CATEGORY_NAMES.map((name, index) => ({
    value: index.toString(),
    label: name,
  })),
];

function Contributions() {
  const { contributions, fetchContributions, isLoading } =
    useContributionStore();
  const token = useAuthStore((s) => s.token);
  const [searchQuery, setSearchQuery] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");
  const [categoryFilter, setCategoryFilter] = useState("all");
  const [selectedContribution, setSelectedContribution] = useState(null);

  useEffect(() => {
    fetchContributions();
  }, [fetchContributions]);

  // Filter contributions
  const filteredContributions = contributions.filter((c) => {
    const matchesSearch =
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.description?.toLowerCase().includes(searchQuery.toLowerCase());
    const matchesStatus = statusFilter === "all" || c.status === statusFilter;
    const matchesCategory =
      categoryFilter === "all" || c.category === parseInt(categoryFilter);

    return matchesSearch && matchesStatus && matchesCategory;
  });

  const openDocument = async (cid) => {
    if (!cid) return;
    if (!token) throw new Error("You must be logged in to view documents");

    const response = await fetch(`/api/v1/contributions/ipfs/${cid}`, {
      headers: { Authorization: `Bearer ${token}` },
    });

    if (!response.ok) {
      let message = "Failed to load document";
      try {
        const data = await response.json();
        if (typeof data?.detail === "string") message = data.detail;
      } catch {
        // ignore JSON parse errors
      }
      throw new Error(message);
    }

    const blob = await response.blob();
    const url = URL.createObjectURL(blob);
    window.open(url, "_blank", "noopener,noreferrer");
    window.setTimeout(() => URL.revokeObjectURL(url), 60_000);
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Contributions</h1>
          <p className="mt-1 text-gray-500">
            View and manage your academic contributions
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

      {/* Filters */}
      <div className="card">
        <div className="flex flex-col lg:flex-row lg:items-center gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search contributions..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="input pl-10"
            />
          </div>

          {/* Status filter */}
          <div className="flex items-center space-x-2">
            <FunnelIcon className="h-5 w-5 text-gray-400" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="input w-auto"
            >
              {STATUS_OPTIONS.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* Category filter */}
          <select
            value={categoryFilter}
            onChange={(e) => setCategoryFilter(e.target.value)}
            className="input w-auto"
          >
            {CATEGORY_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Contributions list */}
      {isLoading ? (
        <div className="flex items-center justify-center h-64">
          <div className="loader" />
        </div>
      ) : filteredContributions.length > 0 ? (
        <div className="space-y-4">
          {filteredContributions.map((contribution) => (
            <ContributionCard
              key={contribution.id}
              contribution={contribution}
              onView={() => setSelectedContribution(contribution)}
              onViewDocument={() => openDocument(contribution.ipfs_hash)}
            />
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <CubeIcon className="h-12 w-12 mx-auto text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            No contributions found
          </h3>
          <p className="mt-2 text-gray-500">
            {searchQuery || statusFilter !== "all" || categoryFilter !== "all"
              ? "Try adjusting your filters"
              : "Start by submitting your first contribution"}
          </p>
          {!searchQuery &&
            statusFilter === "all" &&
            categoryFilter === "all" && (
              <Link
                to="/contributions/new"
                className="mt-4 inline-block btn-primary"
              >
                Submit Contribution
              </Link>
            )}
        </div>
      )}

      {/* Contribution detail modal */}
      {selectedContribution && (
        <ContributionDetailModal
          contribution={selectedContribution}
          onClose={() => setSelectedContribution(null)}
          onViewDocument={() => openDocument(selectedContribution.ipfs_hash)}
        />
      )}
    </div>
  );
}

// Contribution Card Component
function ContributionCard({ contribution, onView, onViewDocument }) {
  const statusConfig = {
    pending: { label: "Pending", class: "badge-pending" },
    under_review: { label: "Under Review", class: "badge-pending" },
    approved: { label: "Approved", class: "badge-approved" },
    rejected: { label: "Rejected", class: "badge-rejected" },
    validated: { label: "Validated", class: "badge-validated" },
  };

  const status = statusConfig[contribution.status] || statusConfig.pending;

  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {contribution.title}
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                {CATEGORY_NAMES[contribution.category] || "Other"}
              </p>
            </div>
            <span className={clsx("badge", status.class)}>{status.label}</span>
          </div>

          {contribution.description && (
            <p className="mt-2 text-gray-600 line-clamp-2">
              {contribution.description}
            </p>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-4 text-sm text-gray-500">
            <span>
              Submitted:{" "}
              {new Date(contribution.created_at).toLocaleDateString()}
            </span>
            {contribution.final_credits && (
              <span className="font-medium text-green-600">
                {contribution.final_credits} Credits
              </span>
            )}
            {contribution.quality_score && (
              <span>Quality: {contribution.quality_score}%</span>
            )}
            {contribution.ipfs_hash && (
              <span className="flex items-center">
                <CubeIcon className="h-4 w-4 mr-1" />
                IPFS Stored
              </span>
            )}
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onView}
            className="btn-secondary inline-flex items-center text-sm"
          >
            <EyeIcon className="h-4 w-4 mr-1" />
            View
          </button>
          {contribution.ipfs_hash && (
            <button
              type="button"
              onClick={onViewDocument}
              className="btn-secondary inline-flex items-center text-sm"
            >
              <DocumentArrowDownIcon className="h-4 w-4 mr-1" />
              Document
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

// Contribution Detail Modal — always fetches fresh data when opened
function ContributionDetailModal({ contribution: initial, onClose, onViewDocument }) {
  const token = useAuthStore((s) => s.token);
  const [contribution, setContribution] = useState(initial);

  useEffect(() => {
    // Re-fetch so the modal always shows the latest AI scores, not the stale list cache
    fetch(`/api/v1/contributions/${initial.id}`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((r) => r.ok ? r.json() : null)
      .then((data) => { if (data) setContribution(data); })
      .catch(() => {});
  }, [initial.id, token]);

  const qualityScore = contribution.ai_quality_score;
  const noveltyScore = contribution.novelty_percentage;
  const credits = contribution.final_credits;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        <div className="relative bg-white rounded-xl shadow-xl max-w-2xl w-full mx-auto p-6 overflow-hidden">
          <h2 className="text-xl font-bold text-gray-900 mb-4">
            Contribution Details
          </h2>

          <div className="space-y-4 text-left">
            <div>
              <label className="label">Title</label>
              <p className="text-gray-900">{contribution.title}</p>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Category</label>
                <p className="text-gray-900">
                  {CATEGORY_NAMES[contribution.category] || contribution.category}
                </p>
              </div>
              <div>
                <label className="label">Status</label>
                <p className="text-gray-900 capitalize">{contribution.status}</p>
              </div>
            </div>

            {contribution.abstract && (
              <div>
                <label className="label">Abstract</label>
                <p className="text-gray-700 text-sm line-clamp-4">{contribution.abstract}</p>
              </div>
            )}

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="label">Quality Score</label>
                <p className="text-gray-900 font-medium">
                  {qualityScore > 0 ? `${qualityScore.toFixed(1)}%` : "Pending"}
                </p>
              </div>
              <div>
                <label className="label">Novelty Score</label>
                <p className="text-gray-900 font-medium">
                  {noveltyScore > 0 ? `${noveltyScore.toFixed(1)}%` : "Pending"}
                </p>
              </div>
              <div>
                <label className="label">Final Credits</label>
                <p className="text-green-600 font-bold">
                  {credits > 0 ? credits : "Pending"}
                </p>
              </div>
            </div>

            {contribution.base_credits > 0 && (
              <p className="text-xs text-gray-400">
                Base credits: {contribution.base_credits} — final credits awarded on HoD validation
              </p>
            )}

            {contribution.is_flagged && contribution.flag_reason && (
              <div className="p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
                Flagged: {contribution.flag_reason}
              </div>
            )}

            {contribution.review_notes && (
              <div>
                <label className="label">Review Notes</label>
                <p className="text-gray-700 text-sm">{contribution.review_notes}</p>
              </div>
            )}

            {contribution.blockchain_tx_hash && (
              <div>
                <label className="label">Blockchain Transaction</label>
                <p className="font-mono text-xs text-gray-500 break-all">{contribution.blockchain_tx_hash}</p>
              </div>
            )}

            {contribution.ipfs_hash && (
              <div>
                <label className="label">IPFS Hash</label>
                <p className="font-mono text-xs text-gray-500 break-all">{contribution.ipfs_hash}</p>
              </div>
            )}
          </div>

          <div className="mt-6 flex justify-end space-x-3">
            <button onClick={onClose} className="btn-secondary">Close</button>
            {contribution.ipfs_hash && (
              <button type="button" onClick={onViewDocument} className="btn-primary">
                View Document
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default Contributions;
