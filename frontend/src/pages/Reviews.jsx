import { useEffect, useState } from "react";
import { useContributionStore, useAuthStore } from "../store";
import { useNavigate } from "react-router-dom";
import {
  ClipboardDocumentCheckIcon,
  CheckCircleIcon,
  XCircleIcon,
  EyeIcon,
  DocumentMagnifyingGlassIcon,
  FunnelIcon,
  CubeIcon,
  ArrowTopRightOnSquareIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

function TxToast({ txHash, action, onClose }) {
  const navigate = useNavigate();
  const label = action === "validate" ? "✅ Validated" : action === "reject" ? "❌ Rejected" : action === "flag" ? "⚑ Flagged" : "✅ Submitted";
  const color = action === "validate" ? "border-green-500 bg-green-50" : action === "reject" ? "border-red-500 bg-red-50" : "border-yellow-500 bg-yellow-50";

  return (
    <div className={`fixed bottom-6 right-6 z-50 max-w-sm w-full rounded-xl border-l-4 shadow-2xl p-4 ${color} animate-slide-up`}>
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <p className="font-semibold text-gray-900 text-sm">{label} — Blockchain Confirmed</p>
          <p className="text-xs text-gray-500 mt-0.5">Transaction recorded on-chain</p>
          <p className="text-xs font-mono text-gray-700 mt-1 truncate">{txHash}</p>
        </div>
        <button onClick={onClose} className="text-gray-400 hover:text-gray-600 text-lg leading-none shrink-0">×</button>
      </div>
      <button
        onClick={() => { navigate("/transactions"); onClose(); }}
        className="mt-3 w-full flex items-center justify-center gap-1.5 text-xs font-semibold text-primary-700 bg-white border border-primary-200 rounded-lg py-1.5 hover:bg-primary-50 transition"
      >
        <ArrowTopRightOnSquareIcon className="h-3.5 w-3.5" />
        View in Transaction Explorer
      </button>
    </div>
  );
}

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
  const [reviewAction, setReviewAction] = useState(null);
  const [reviewComment, setReviewComment] = useState("");
  const [reviewError, setReviewError] = useState(null);
  const [filter, setFilter] = useState("all");
  const [toast, setToast] = useState(null); // { txHash, action }

  useEffect(() => {
    fetchPendingReviews();
  }, [fetchPendingReviews]);

  const handleReview = async (action) => {
    if (!selectedReview) return;
    setReviewError(null);

    const backendAction = action === "approve" ? "validate" : action;

    try {
      const result = await reviewContribution(selectedReview.id, {
        action: backendAction,
        notes: reviewComment || "",
      });
      await fetchPendingReviews();
      setSelectedReview((prev) => (prev ? { ...prev, ...result } : null));
      setReviewAction(null);
      setReviewComment("");
      setReviewError(null);

      const txHash = result?.review_tx_hash || result?.blockchain_tx_hash;
      if (txHash) {
        setToast({ txHash, action: backendAction });
        setTimeout(() => setToast(null), 12000);
      }
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
    <>
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Review Queue</h1>
          <p className="mt-1 text-gray-500">
            Review and validate faculty contributions
          </p>
        </div>
        <div className="flex items-center mt-4 space-x-4 sm:mt-0">
          <div className="flex items-center space-x-2 text-sm text-gray-500">
            <span className="font-medium">{pendingReviews.length}</span>
            <span>pending reviews</span>
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="border-yellow-200 card bg-yellow-50">
          <div className="flex items-center space-x-3">
            <ClipboardDocumentCheckIcon className="w-8 h-8 text-yellow-600" />
            <div>
              <p className="text-sm text-yellow-700">Pending Review</p>
              <p className="text-2xl font-bold text-yellow-900">
                {pendingReviews.filter((r) => r.status === "pending").length}
              </p>
            </div>
          </div>
        </div>
        <div className="border-blue-200 card bg-blue-50">
          <div className="flex items-center space-x-3">
            <DocumentMagnifyingGlassIcon className="w-8 h-8 text-blue-600" />
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
        <div className="border-green-200 card bg-green-50">
          <div className="flex items-center space-x-3">
            <CheckCircleIcon className="w-8 h-8 text-green-600" />
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
          <FunnelIcon className="w-5 h-5 text-gray-400" />
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
        <div className="py-12 text-center card">
          <ClipboardDocumentCheckIcon className="w-12 h-12 mx-auto text-gray-300" />
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

    {toast && (
      <TxToast
        txHash={toast.txHash}
        action={toast.action}
        onClose={() => setToast(null)}
      />
    )}
  </>
  );
}

// Review Card Component
function ReviewCard({ review, onView }) {
  return (
    <div className="transition-shadow card hover:shadow-md">
      <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
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

          <div className="flex flex-wrap items-center gap-4 mt-4">
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
            <div className="p-2 mt-3 border border-red-200 rounded-lg bg-red-50">
              <p className="text-sm font-medium text-red-700">
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
            className="inline-flex items-center btn-primary"
          >
            <EyeIcon className="w-4 h-4 mr-2" />
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
  const isReviewComplete =
    review.status === "validated" || review.status === "rejected";

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 pt-4 pb-20 text-center sm:p-0">
        {/* Backdrop */}
        <div
          className="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75"
          onClick={onClose}
        />

        {/* Modal */}
        <div className="relative w-full max-w-3xl mx-auto overflow-hidden bg-white shadow-xl rounded-xl">
          {/* Header */}
          <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
            <h2 className="text-xl font-bold text-gray-900">
              Review Contribution
            </h2>
          </div>

          {/* Content */}
          <div className="px-6 py-4 max-h-[60vh] overflow-y-auto">
            <div className="space-y-4 text-left">
              {isReviewComplete && (
                <div
                  className={clsx(
                    "rounded-lg border p-4",
                    review.status === "validated"
                      ? "border-green-200 bg-green-50"
                      : "border-red-200 bg-red-50",
                  )}
                >
                  <p
                    className={clsx(
                      "font-medium",
                      review.status === "validated"
                        ? "text-green-900"
                        : "text-red-900",
                    )}
                  >
                    {review.status === "validated"
                      ? "Contribution validated successfully."
                      : "Contribution rejected."}
                  </p>
                  <p className="mt-2 text-xs font-medium uppercase tracking-wide text-gray-600">
                    Transaction ID
                  </p>
                  <p className="mt-1 break-all font-mono text-sm text-gray-900">
                    {review.review_tx_hash ||
                      "Blockchain transaction not available for this action."}
                  </p>
                </div>
              )}

              <div>
                <label className="label">Title</label>
                <p className="font-medium text-gray-900">{review.title}</p>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Category</label>
                  <p className="text-gray-900">{categoryLabel(review.category)}</p>
                </div>
                <div>
                  <label className="label">Submitted By</label>
                  <p className="font-mono text-sm text-gray-900">
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
                  <p className="p-3 text-sm text-gray-700 rounded-lg bg-gray-50">
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
                    className="inline-flex items-center text-sm font-medium underline text-primary-600 hover:text-primary-700"
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

              {(review.blockchain_tx_hash || review.review_tx_hash) && (
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
                  <div>
                    <label className="label">Submission Transaction ID</label>
                    <p className="font-mono text-xs text-gray-600 break-all">
                      {review.blockchain_tx_hash || "—"}
                    </p>
                  </div>
                  <div>
                    <label className="label">Review Transaction ID</label>
                    <p className="font-mono text-xs text-gray-600 break-all">
                      {review.review_tx_hash ||
                        (isReviewComplete
                          ? "—"
                          : "Will appear after you submit this review")}
                    </p>
                  </div>
                </div>
              )}

              {/* AI Evaluation Results */}
              {review.ai_quality_score > 0 ? (
                <div className="p-4 border border-blue-200 rounded-lg bg-blue-50">
                  <h4 className="flex items-center font-medium text-blue-900">
                    <CubeIcon className="w-5 h-5 mr-2" />
                    AI Evaluation Results
                  </h4>
                  <div className="grid grid-cols-2 gap-4 mt-3">
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
                <div className="p-3 text-sm text-yellow-700 border border-yellow-200 rounded-lg bg-yellow-50">
                  AI evaluation is pending — scores will appear once processing completes.
                </div>
              )}

              {!isReviewComplete && (
              <>
              {/* Review Action */}
              <div className="pt-4 border-t border-gray-200">
                <label className="label">Your Decision</label>
                <div className="flex mt-2 space-x-4">
                  <button
                    onClick={() => setReviewAction("approve")}
                    className={clsx(
                      "flex-1 p-4 rounded-lg border-2 transition-all",
                      reviewAction === "approve"
                        ? "border-green-500 bg-green-50"
                        : "border-gray-200 hover:border-green-300",
                    )}
                  >
                    <CheckCircleIcon className="w-8 h-8 mx-auto text-green-500" />
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
                    <XCircleIcon className="w-8 h-8 mx-auto text-red-500" />
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
                    ? "Rejection Reason (Optional)"
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
              </>
              )}

              {isReviewComplete && review.review_notes && (
                <div className="pt-2 border-t border-gray-200">
                  <label className="label">Review notes</label>
                  <p className="text-sm text-gray-700">{review.review_notes}</p>
                </div>
              )}
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-gray-200 bg-gray-50">
            {reviewError && (
              <div className="p-3 mb-3 text-sm text-red-600 border border-red-200 rounded bg-red-50">
                {reviewError}
              </div>
            )}
            <div className="flex justify-end space-x-3">
            {!isReviewComplete && (
            <button onClick={onClose} className="btn-secondary">
              Cancel
            </button>
            )}
            {isReviewComplete && (
              <button type="button" onClick={onClose} className="btn-primary">
                Close
              </button>
            )}
            {!isReviewComplete && reviewAction === "approve" && (
              <button
                onClick={onApprove}
                disabled={isLoading}
                className="flex items-center btn-success"
              >
                {isLoading ? (
                  <div className="mr-2 loader" />
                ) : (
                  <CheckCircleIcon className="w-5 h-5 mr-2" />
                )}
                Approve & Validate
              </button>
            )}
            {!isReviewComplete && reviewAction === "reject" && (
              <button
                onClick={onReject}
                disabled={isLoading}
                className="flex items-center btn-danger"
              >
                {isLoading ? (
                  <div className="mr-2 loader" />
                ) : (
                  <XCircleIcon className="w-5 h-5 mr-2" />
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
