import { useEffect, useState } from "react";
import { useContributionStore, useAuthStore } from "../store";
import {
  ClipboardDocumentCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  DocumentMagnifyingGlassIcon,
  FunnelIcon,
  CubeIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

async function openDocument(cid) {
  try {
    const token = useAuthStore.getState().token;
    const res = await fetch(`/api/v1/contributions/ipfs/${cid}`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (!res.ok) throw new Error(`Server returned ${res.status}`);
    const blob = await res.blob();
    window.open(URL.createObjectURL(blob), "_blank");
  } catch (err) {
    alert("Could not load document: " + err.message);
  }
}

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

const categoryLabel = (cat) =>
  CATEGORY_LABELS[cat] || cat?.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase()) || "Unknown";

function Reviews() {
  const { pendingReviews, fetchPendingReviews, reviewContribution, isLoading } =
    useContributionStore();
  const [selectedReview, setSelectedReview] = useState(null);
  const [reviewAction, setReviewAction] = useState(null); // 'approve' | 'reject'
  const [reviewComment, setReviewComment] = useState("");
  const [reviewError, setReviewError] = useState(null);
  const [filter, setFilter] = useState("all");

  useEffect(() => {
    fetchPendingReviews();
  }, [fetchPendingReviews]);

  const handleReview = async (action) => {
    if (!selectedReview) return;
    setReviewError(null);

    const backendAction = action === "approve" ? "validate" : action;

    try {
      await reviewContribution(selectedReview.id, {
        action: backendAction,
        notes: reviewComment || "",
      });

      setSelectedReview(null);
      setReviewAction(null);
      setReviewComment("");
      setReviewError(null);
    } catch (error) {
      setReviewError(error.message || "Failed to submit review. Please try again.");
    }
  };

  const filteredReviews = pendingReviews.filter((review) => {
    if (filter === "all") return true;
    return review.status === filter;
  });

  if (isLoading && pendingReviews.length === 0) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loader" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Review Queue</h1>
          <p className="mt-1 text-gray-500">
            Review and validate faculty contributions
          </p>
        </div>
        <div className="mt-4 sm:mt-0 flex items-center space-x-4">
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span className="font-medium">{pendingReviews.length}</span>
            <span>pending reviews</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="card bg-yellow-50 border-yellow-200">
          <div className="flex items-center space-x-3">
            <ClipboardDocumentCheckIcon className="h-8 w-8 text-yellow-600" />
            <div>
              <p className="text-sm text-yellow-700">Pending Review</p>
              <p className="text-2xl font-bold text-yellow-900">
                {pendingReviews.filter((r) => r.status === "pending").length}
              </p>
            </div>
          </div>
        </div>
        <div className="card bg-blue-50 border-blue-200">
          <div className="flex items-center space-x-3">
            <DocumentMagnifyingGlassIcon className="h-8 w-8 text-blue-600" />
            <div>
              <p className="text-sm text-blue-700">Under Review</p>
              <p className="text-2xl font-bold text-blue-900">
                {
                  pendingReviews.filter((r) => r.status === "under_review")
                    .length
                }
              </p>
            </div>
          </div>
        </div>
        <div className="card bg-green-50 border-green-200">
          <div className="flex items-center space-x-3">
            <CheckCircleIcon className="h-8 w-8 text-green-600" />
            <div>
              <p className="text-sm text-green-700">AI Evaluated</p>
              <p className="text-2xl font-bold text-green-900">
                {pendingReviews.filter((r) => r.ai_quality_score > 0).length}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Filter */}
      <div className="card">
        <div className="flex items-center space-x-4">
          <FunnelIcon className="h-5 w-5 text-gray-400" />
          <div className="flex space-x-2">
            {["all", "pending", "under_review"].map((filterOption) => (
              <button
                key={filterOption}
                onClick={() => setFilter(filterOption)}
                className={clsx(
                  "px-3 py-1 rounded-full text-sm font-medium transition-colors",
                  filter === filterOption
                    ? "bg-primary-100 text-primary-700"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200",
                )}
              >
                {filterOption === "all"
                  ? "All"
                  : filterOption.replace("_", " ")}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Reviews list */}
      {filteredReviews.length > 0 ? (
        <div className="space-y-4">
          {filteredReviews.map((review) => (
            <ReviewCard
              key={review.id}
              review={review}
              onView={() => setSelectedReview(review)}
            />
          ))}
        </div>
      ) : (
        <div className="card text-center py-12">
          <ClipboardDocumentCheckIcon className="h-12 w-12 mx-auto text-gray-300" />
          <h3 className="mt-4 text-lg font-medium text-gray-900">
            No pending reviews
          </h3>
          <p className="mt-2 text-gray-500">
            All contributions have been reviewed
          </p>
        </div>
      )}

      {/* Review Modal */}
      {selectedReview && (
        <ReviewModal
          review={selectedReview}
          onClose={() => {
            setSelectedReview(null);
            setReviewAction(null);
            setReviewComment("");
            setReviewError(null);
          }}
          onApprove={() => handleReview("approve")}
          onReject={() => handleReview("reject")}
          reviewAction={reviewAction}
          setReviewAction={setReviewAction}
          reviewComment={reviewComment}
          setReviewComment={setReviewComment}
          reviewError={reviewError}
          isLoading={isLoading}
        />
      )}
    </div>
  );
}

// Review Card Component
function ReviewCard({ review, onView }) {
  return (
    <div className="card hover:shadow-md transition-shadow">
      <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
        <div className="flex-1">
          <div className="flex items-start justify-between">
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {review.title}
              </h3>
              <p className="mt-1 text-sm text-gray-500">
                {categoryLabel(review.category)} • Submitted by{" "}
                {review.faculty_address
                  ? `${review.faculty_address.slice(0, 8)}...${review.faculty_address.slice(-4)}`
                  : "Faculty"}
              </p>
            </div>
            <span
              className={clsx(
                "badge",
                review.ai_quality_score > 0 ? "badge-validated" : "badge-pending",
              )}
            >
              {review.ai_quality_score > 0 ? "AI Evaluated" : "Pending AI"}
            </span>
          </div>

          {review.description && (
            <p className="mt-2 text-gray-600 line-clamp-2">
              {review.description}
            </p>
          )}

          <div className="mt-4 flex flex-wrap items-center gap-4">
            {review.ai_quality_score > 0 && (
              <>
                <div className="text-sm">
                  <span className="text-gray-500">Quality:</span>
                  <span className="ml-1 font-medium text-gray-900">
                    {review.ai_quality_score.toFixed(1)}%
                  </span>
                </div>
                <div className="text-sm">
                  <span className="text-gray-500">Novelty:</span>
                  <span className="ml-1 font-medium text-gray-900">
                    {review.novelty_percentage.toFixed(1)}%
                  </span>
                </div>
                <div className="text-sm">
                  <span className="text-gray-500">Credits:</span>
                  <span className="ml-1 font-medium text-green-600">
                    {review.final_credits || review.base_credits}
                  </span>
                </div>
              </>
            )}
            <div className="text-sm text-gray-500">
              Submitted: {new Date(review.created_at).toLocaleDateString()}
            </div>
          </div>

          {review.fraud_flags && review.fraud_flags.length > 0 && (
            <div className="mt-3 p-2 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-sm text-red-700 font-medium">
                ⚠️ Fraud Detection Flags:
              </p>
              <ul className="text-sm text-red-600 list-disc list-inside">
                {review.fraud_flags.map((flag, index) => (
                  <li key={index}>{flag}</li>
                ))}
              </ul>
            </div>
          )}
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onView}
            className="btn-primary inline-flex items-center"
          >
            <EyeIcon className="h-4 w-4 mr-2" />
            Review
          </button>
        </div>
      </div>
    </div>
  );
}

// Review Modal Component
function ReviewModal({
  review,
  onClose,
  onApprove,
  onReject,
  reviewAction,
  setReviewAction,
  reviewComment,
  setReviewComment,
  reviewError,
  isLoading,
}) {
  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        {/* Backdrop */}
        <div
          className="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative bg-white rounded-xl shadow-xl max-w-3xl w-full mx-auto overflow-hidden">
          {/* Header */}
          <div className="bg-gray-50 px-6 py-4 border-b border-gray-200">
            <h2 className="text-xl font-bold text-gray-900">
              Review Contribution
            </h2>
          </div>

          {/* Content */}
          <div className="px-6 py-4 max-h-[60vh] overflow-y-auto">
            <div className="space-y-4 text-left">
              <div>
                <label className="label">Title</label>
                <p className="text-gray-900 font-medium">{review.title}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Category</label>
                  <p className="text-gray-900">{categoryLabel(review.category)}</p>
                </div>
                <div>
                  <label className="label">Submitted By</label>
                  <p className="text-gray-900 font-mono text-sm">
                    {review.faculty_address
                      ? `${review.faculty_address.slice(0, 10)}...${review.faculty_address.slice(-6)}`
                      : "—"}
                  </p>
                </div>
              </div>

              <div>
                <label className="label">Description</label>
                <p className="text-gray-700">{review.description}</p>
              </div>

              {review.abstract && (
                <div>
                  <label className="label">Abstract</label>
                  <p className="text-gray-700 text-sm bg-gray-50 p-3 rounded-lg">
                    {review.abstract}
                  </p>
                </div>
              )}

              {/* Document View */}
              {review.ipfs_hash && (
                <div>
                  <label className="label">Document</label>
                  <button
                    type="button"
                    onClick={() => openDocument(review.ipfs_hash)}
                    className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium underline"
                  >
                    View uploaded document ↗
                  </button>
                </div>
              )}

              {/* Credits */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Base Credits (UGC)</label>
                  <p className="text-2xl font-bold text-gray-900">{review.base_credits ?? "—"}</p>
                </div>
                <div>
                  <label className="label">Final Credits</label>
                  <p className="text-2xl font-bold text-green-600">
                    {review.final_credits > 0 ? review.final_credits : <span className="text-sm text-gray-400">Pending AI</span>}
                  </p>
                </div>
              </div>

              {/* AI Evaluation Results */}
              {review.ai_quality_score > 0 ? (
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <h4 className="font-medium text-blue-900 flex items-center">
                    <CubeIcon className="h-5 w-5 mr-2" />
                    AI Evaluation Results
                  </h4>
                  <div className="mt-3 grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-sm text-blue-700">Quality Score</p>
                      <p className="text-2xl font-bold text-blue-900">
                        {review.ai_quality_score.toFixed(1)}%
                      </p>
                    </div>
                    <div>
                      <p className="text-sm text-blue-700">Novelty Score</p>
                      <p className="text-2xl font-bold text-blue-900">
                        {review.novelty_percentage.toFixed(1)}%
                      </p>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-3 text-sm text-yellow-700">
                  AI evaluation is pending — scores will appear once processing completes.
                </div>
              )}

              {/* Review Action */}
              <div className="border-t border-gray-200 pt-4">
                <label className="label">Your Decision</label>
                <div className="flex space-x-4 mt-2">
                  <button
                    onClick={() => setReviewAction("approve")}
                    className={clsx(
                      "flex-1 p-4 rounded-lg border-2 transition-all",
                      reviewAction === "approve"
                        ? "border-green-500 bg-green-50"
                        : "border-gray-200 hover:border-green-300",
                    )}
                  >
                    <CheckCircleIcon className="h-8 w-8 mx-auto text-green-500" />
                    <p className="mt-2 font-medium text-green-700">Approve</p>
                    <p className="text-sm text-gray-500">
                      Validate on blockchain
                    </p>
                  </button>
                  <button
                    onClick={() => setReviewAction("reject")}
                    className={clsx(
                      "flex-1 p-4 rounded-lg border-2 transition-all",
                      reviewAction === "reject"
                        ? "border-red-500 bg-red-50"
                        : "border-gray-200 hover:border-red-300",
                    )}
                  >
                    <XCircleIcon className="h-8 w-8 mx-auto text-red-500" />
                    <p className="mt-2 font-medium text-red-700">Reject</p>
                    <p className="text-sm text-gray-500">
                      Return with feedback
                    </p>
                  </button>
                </div>
              </div>

              {/* Comments */}
              <div>
                <label className="label">
                  {reviewAction === "reject"
                    ? "Rejection Reason *"
                    : "Comments (Optional)"}
                </label>
                <textarea
                  value={reviewComment}
                  onChange={(e) => setReviewComment(e.target.value)}
                  rows={3}
                  placeholder={
                    reviewAction === "reject"
                      ? "Provide reason for rejection..."
                      : "Add any comments or notes..."
                  }
                  className="input"
                />
              </div>
            </div>
          </div>

          {/* Footer */}
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
            {reviewError && (
              <div className="mb-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">
                {reviewError}
              </div>
            )}
            <div className="flex justify-end space-x-3">
            <button onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            {reviewAction === "approve" && (
              <button
                onClick={onApprove}
                disabled={isLoading}
                className="btn-success flex items-center"
              >
                {isLoading ? (
                  <div className="loader mr-2" />
                ) : (
                  <CheckCircleIcon className="h-5 w-5 mr-2" />
                )}
                Approve & Validate
              </button>
            )}
            {reviewAction === "reject" && (
              <button
                onClick={onReject}
                disabled={isLoading || !reviewComment.trim()}
                className="btn-danger flex items-center"
              >
                {isLoading ? (
                  <div className="loader mr-2" />
                ) : (
                  <XCircleIcon className="h-5 w-5 mr-2" />
                )}
                Reject Contribution
              </button>
            )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default Reviews;
