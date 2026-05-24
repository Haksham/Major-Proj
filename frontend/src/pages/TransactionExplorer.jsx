import { useState } from "react";
import {
  MagnifyingGlassIcon,
  CubeTransparentIcon,
  CheckCircleIcon,
  XCircleIcon,
  FlagIcon,
  ArrowUpCircleIcon,
  UserCircleIcon,
  ClipboardDocumentIcon,
  InformationCircleIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";
import { transactionsAPI } from "../services/api";

const EVENT_CONFIG = {
  submission: {
    label: "Submitted",
    icon: ArrowUpCircleIcon,
    colorClass: "text-blue-600",
    bgClass: "bg-blue-50 border-blue-200",
    dotClass: "bg-blue-500",
  },
  validation: {
    label: "Validated",
    icon: CheckCircleIcon,
    colorClass: "text-green-600",
    bgClass: "bg-green-50 border-green-200",
    dotClass: "bg-green-500",
  },
  rejection: {
    label: "Rejected",
    icon: XCircleIcon,
    colorClass: "text-red-600",
    bgClass: "bg-red-50 border-red-200",
    dotClass: "bg-red-500",
  },
  flagging: {
    label: "Flagged",
    icon: FlagIcon,
    colorClass: "text-yellow-600",
    bgClass: "bg-yellow-50 border-yellow-200",
    dotClass: "bg-yellow-500",
  },
};

const ROLE_LABELS = {
  faculty: "Faculty",
  hod: "Head of Department",
  institute_admin: "Institute Admin",
  admin: "Admin",
};

const DESIGNATION_LABELS = {
  professor: "Professor",
  associate_professor: "Associate Professor",
  assistant_professor: "Assistant Professor",
  staff: "Staff",
};

function truncateHash(hash) {
  if (!hash) return null;
  return `${hash.slice(0, 10)}...${hash.slice(-8)}`;
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text).catch(() => {});
}

function formatDate(iso) {
  if (!iso) return "—";
  return new Date(iso).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function HashField({ label, value }) {
  const [copied, setCopied] = useState(false);
  if (!value) return null;

  const handleCopy = () => {
    copyToClipboard(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="flex items-center gap-2 mt-1">
      <span className="text-xs text-gray-400 shrink-0">{label}:</span>
      <span className="font-mono text-xs text-gray-500 truncate">{truncateHash(value)}</span>
      <button
        onClick={handleCopy}
        title="Copy full hash"
        className="shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
      >
        {copied ? (
          <CheckCircleIcon className="h-3.5 w-3.5 text-green-500" />
        ) : (
          <ClipboardDocumentIcon className="h-3.5 w-3.5" />
        )}
      </button>
    </div>
  );
}

function WalletInfoCard({ info, address }) {
  return (
    <div className="card border border-gray-200 bg-gray-50 mb-6">
      <div className="flex items-start gap-4">
        <div className="p-2 bg-white border border-gray-200 rounded-lg">
          <UserCircleIcon className="h-8 w-8 text-gray-400" />
        </div>
        <div className="flex-1 min-w-0">
          {info ? (
            <>
              <p className="text-base font-semibold text-gray-900">{info.name || "Unknown"}</p>
              <p className="text-sm text-gray-500">
                {ROLE_LABELS[info.role] || info.role}
                {info.designation ? ` · ${DESIGNATION_LABELS[info.designation] || info.designation}` : ""}
              </p>
              {info.employee_id && (
                <p className="text-xs text-gray-400 mt-0.5">Employee ID: {info.employee_id}</p>
              )}
              {info.total_credits > 0 && (
                <p className="text-sm font-medium text-green-600 mt-1">{info.total_credits.toFixed(2)} Credits</p>
              )}
              <span
                className={clsx(
                  "inline-block mt-1 text-xs font-medium px-2 py-0.5 rounded-full",
                  info.is_active ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
                )}
              >
                {info.is_active ? "Active" : "Inactive"}
              </span>
            </>
          ) : (
            <p className="text-sm text-gray-500">Wallet not registered in SALF</p>
          )}
          <HashField label="Wallet" value={address} />
        </div>
      </div>
    </div>
  );
}

function TransactionCard({ event }) {
  const [expanded, setExpanded] = useState(false);
  const config = EVENT_CONFIG[event.type] || EVENT_CONFIG.submission;
  const Icon = config.icon;

  return (
    <div className={clsx("border rounded-lg p-4 transition-all", config.bgClass)}>
      <div className="flex items-start gap-3">
        <Icon className={clsx("h-5 w-5 mt-0.5 shrink-0", config.colorClass)} />
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-2 flex-wrap">
            <span className={clsx("text-sm font-semibold", config.colorClass)}>{event.label}</span>
            <span className="text-xs text-gray-400">{formatDate(event.timestamp)}</span>
          </div>

          <p className="mt-1 text-sm font-medium text-gray-900 leading-snug">{event.title}</p>

          {event.category_label && (
            <p className="text-xs text-gray-500 mt-0.5">{event.category_label}</p>
          )}

          <div className="mt-2 space-y-0.5">
            {event.tx_hash && (
              <HashField label="Tx Hash" value={event.tx_hash} />
            )}
            {!event.tx_hash && (
              <p className="text-xs text-gray-400 italic">On-chain tx hash not recorded for this action</p>
            )}
            {event.actor_address && (
              <HashField
                label={event.actor_role === "hod" ? "Reviewed by" : "Faculty wallet"}
                value={event.actor_address}
              />
            )}
            <div className="flex items-center gap-3 pt-0.5">
              <span className="text-xs text-gray-400">
                Contribution ID: <span className="font-mono text-gray-600">#{event.contribution_id}</span>
              </span>
              {event.blockchain_id != null && (
                <span className="text-xs text-gray-400">
                  On-chain ID: <span className="font-mono text-gray-600">#{event.blockchain_id}</span>
                </span>
              )}
            </div>
          </div>

          {/* Details toggle */}
          <button
            onClick={() => setExpanded((v) => !v)}
            className="mt-2 text-xs text-gray-400 hover:text-gray-600 flex items-center gap-1"
          >
            <InformationCircleIcon className="h-3.5 w-3.5" />
            {expanded ? "Hide details" : "Show details"}
          </button>

          {expanded && (
            <div className="mt-3 pt-3 border-t border-white/60 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs text-gray-600">
              {event.type === "submission" && (
                <>
                  <span className="text-gray-400">Base Credits</span>
                  <span>{event.details.base_credits}</span>
                  <span className="text-gray-400">AI Quality</span>
                  <span>{event.details.ai_quality_score > 0 ? `${event.details.ai_quality_score.toFixed(1)}%` : "Pending"}</span>
                  <span className="text-gray-400">Novelty</span>
                  <span>{event.details.novelty_percentage > 0 ? `${event.details.novelty_percentage.toFixed(1)}%` : "Pending"}</span>
                  {event.details.ipfs_hash && (
                    <>
                      <span className="text-gray-400">IPFS Hash</span>
                      <span className="font-mono truncate">{truncateHash(event.details.ipfs_hash)}</span>
                    </>
                  )}
                  {event.details.fraud_score > 0 && (
                    <>
                      <span className="text-gray-400">Fraud Score</span>
                      <span>{(event.details.fraud_score * 100).toFixed(1)}%</span>
                    </>
                  )}
                </>
              )}
              {(event.type === "validation" || event.type === "rejection" || event.type === "flagging") && (
                <>
                  {event.details.final_credits > 0 && (
                    <>
                      <span className="text-gray-400">Credits Awarded</span>
                      <span className="font-medium text-green-600">{event.details.final_credits}</span>
                    </>
                  )}
                  {event.details.review_notes && (
                    <>
                      <span className="text-gray-400">Review Notes</span>
                      <span className="col-span-1 break-words">{event.details.review_notes}</span>
                    </>
                  )}
                  {event.details.flag_reason && (
                    <>
                      <span className="text-gray-400">Flag Reason</span>
                      <span className="text-red-600 break-words">{event.details.flag_reason}</span>
                    </>
                  )}
                  {event.details.faculty_address && (
                    <>
                      <span className="text-gray-400">Faculty</span>
                      <span className="font-mono truncate">{truncateHash(event.details.faculty_address)}</span>
                    </>
                  )}
                </>
              )}
              <span className="text-gray-400">Current Status</span>
              <span className="capitalize">{event.current_status}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function detectQueryType(q) {
  const clean = q.trim().toLowerCase();
  if (!clean.startsWith("0x")) return null;
  if (clean.length === 66) return "tx_hash";
  if (clean.length === 42) return "wallet_address";
  return null;
}

export default function TransactionExplorer() {
  const [query, setQuery] = useState("");
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);

  const queryType = detectQueryType(query);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const { data } = await transactionsAPI.lookup(query.trim());
      setResult(data);
    } catch (err) {
      const msg = err.response?.data?.detail || "Lookup failed. Check the hash or address and try again.";
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6 max-w-3xl">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Transaction Explorer</h1>
        <p className="mt-1 text-gray-500">
          Look up any blockchain activity — submissions, approvals, rejections — by transaction hash or wallet address.
        </p>
      </div>

      {/* Search */}
      <form onSubmit={handleSearch} className="card">
        <label className="label mb-1">Transaction Hash or Wallet Address</label>
        <div className="flex gap-3">
          <div className="relative flex-1">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 -translate-y-1/2 h-5 w-5 text-gray-400 pointer-events-none" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="0x... (66 chars for tx hash, 42 chars for wallet address)"
              className="input pl-10 font-mono text-sm"
              spellCheck={false}
            />
          </div>
          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="btn-primary px-6 shrink-0"
          >
            {loading ? "Searching…" : "Search"}
          </button>
        </div>

        {/* Type hint */}
        {query.trim() && (
          <p className="mt-2 text-xs">
            {queryType === "tx_hash" && (
              <span className="text-blue-600">Transaction hash detected (66 chars)</span>
            )}
            {queryType === "wallet_address" && (
              <span className="text-purple-600">Wallet address detected (42 chars)</span>
            )}
            {!queryType && (
              <span className="text-red-500">
                {query.trim().startsWith("0x")
                  ? `Incomplete — ${query.trim().length} chars (need 66 for tx hash, 42 for address)`
                  : "Must start with 0x"}
              </span>
            )}
          </p>
        )}

        {/* Helper chips */}
        <p className="mt-3 text-xs text-gray-400">
          Examples:&nbsp;
          <span className="bg-gray-100 rounded px-1.5 py-0.5 font-mono">0xabc…def</span> (tx hash)&nbsp; or &nbsp;
          <span className="bg-gray-100 rounded px-1.5 py-0.5 font-mono">0x742d…bEb4</span> (wallet)
        </p>
      </form>

      {/* Error */}
      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
          {error}
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="space-y-4">
          {/* Summary bar */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <CubeTransparentIcon className="h-5 w-5 text-gray-400" />
              <span className="text-sm text-gray-600">
                {result.total} event{result.total !== 1 ? "s" : ""} found
                {result.query_type === "wallet_address" ? " for this wallet" : " for this transaction"}
              </span>
            </div>
            <span className="text-xs text-gray-400 font-mono">{truncateHash(result.query)}</span>
          </div>

          {/* Wallet info (address search only) */}
          {result.query_type === "wallet_address" && (
            <WalletInfoCard info={result.wallet_info} address={result.query} />
          )}

          {/* Timeline */}
          {result.transactions.length > 0 ? (
            <div className="space-y-3">
              {result.transactions.map((event, idx) => (
                <TransactionCard key={`${event.contribution_id}-${event.type}-${idx}`} event={event} />
              ))}
            </div>
          ) : (
            <div className="card text-center py-10 text-gray-500">
              No blockchain events recorded for this query.
            </div>
          )}
        </div>
      )}

      {/* Empty state */}
      {!result && !error && !loading && (
        <div className="card text-center py-12 text-gray-400">
          <CubeTransparentIcon className="h-12 w-12 mx-auto mb-3 opacity-40" />
          <p className="text-sm">Enter a transaction hash or wallet address above to explore the ledger.</p>
        </div>
      )}
    </div>
  );
}
