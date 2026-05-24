import { useEffect, useState, useRef } from "react";
import {
  useAuthStore,
  usePortfolioStore,
  useContributionStore,
} from "../store";
import {
  AcademicCapIcon,
  DocumentTextIcon,
  ChartBarIcon,
  ArrowDownTrayIcon,
  TrophyIcon,
  CubeIcon,
  LinkIcon,
  ClipboardDocumentCheckIcon,
} from "@heroicons/react/24/outline";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  LineChart,
  Line,
  Legend,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
} from "recharts";
import clsx from "clsx";

const CATEGORY_NAMES = [
  "Guest Lectures",
  "Journal",
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

function Portfolio() {
  const { user, walletAddress } = useAuthStore();
  const { portfolio, fetchPortfolio, isLoading } = usePortfolioStore();
  const { contributions, fetchContributions } = useContributionStore();
  const [activeTab, setActiveTab] = useState("overview");
  const [copied, setCopied] = useState(false);
  const [isExporting, setIsExporting] = useState(false);
  const overviewRef = useRef(null);

  useEffect(() => {
    fetchPortfolio();
    fetchContributions();
  }, [fetchPortfolio, fetchContributions]);

  // Calculate portfolio statistics
  const totalCredits =
    portfolio?.total_credits ||
    contributions.reduce((sum, c) => sum + (c.final_credits || 0), 0);
  const validatedCount = contributions.filter(
    (c) => c.status === "validated",
  ).length;
  const totalContributions = contributions.length;

  // Credits by category
  const creditsByCategory = CATEGORY_NAMES.map((name, index) => ({
    category: name.split(" ")[0], // Shortened name for chart
    credits: contributions
      .filter((c) => c.category === index && c.final_credits)
      .reduce((sum, c) => sum + c.final_credits, 0),
    count: contributions.filter((c) => c.category === index).length,
  })).filter((item) => item.count > 0);

  // Monthly credits trend
  const monthlyTrend = [
    { month: "Jan", credits: 45 },
    { month: "Feb", credits: 70 },
    { month: "Mar", credits: 55 },
    { month: "Apr", credits: 90 },
    { month: "May", credits: 75 },
    { month: "Jun", credits: 110 },
  ];

  // Skills radar data (based on contribution categories)
  const skillsData = [
    { subject: "Research", A: 85 },
    { subject: "Teaching", A: 65 },
    { subject: "Innovation", A: 75 },
    { subject: "Leadership", A: 70 },
    { subject: "Collaboration", A: 80 },
    { subject: "Publication", A: 90 },
  ];

  const handleShare = () => {
    const url = `${window.location.origin}/public/portfolio/${walletAddress}`;
    navigator.clipboard.writeText(url).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2500);
    });
  };

  const handleExportPDF = async () => {
    const target = overviewRef.current;
    if (!target) return;
    setIsExporting(true);
    try {
      const { default: jsPDF } = await import("jspdf");
      const { default: html2canvas } = await import("html2canvas");

      const canvas = await html2canvas(target, {
        scale: 2,
        useCORS: true,
        backgroundColor: "#ffffff",
      });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
      const pageW = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();
      const imgH = (canvas.height * pageW) / canvas.width;
      let left = imgH;
      let pos = 0;
      pdf.addImage(imgData, "PNG", 0, pos, pageW, imgH);
      left -= pageH;
      while (left > 0) {
        pos -= pageH;
        pdf.addPage();
        pdf.addImage(imgData, "PNG", 0, pos, pageW, imgH);
        left -= pageH;
      }
      pdf.save(`${(user?.name || "Portfolio").replace(/\s+/g, "_")}_Portfolio.pdf`);
    } catch (e) {
      console.error("PDF export failed:", e);
    } finally {
      setIsExporting(false);
    }
  };

  // Top contributions
  const topContributions = [...contributions]
    .sort((a, b) => (b.final_credits || 0) - (a.final_credits || 0))
    .slice(0, 5);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="loader" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center space-x-4">
          <div className="w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center">
            <AcademicCapIcon className="h-8 w-8 text-primary-600" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-gray-900">
              {user?.name || "Faculty Portfolio"}
            </h1>
            <p className="text-gray-500">{user?.department || "Department"}</p>
            <p className="text-sm text-gray-400 font-mono">
              {walletAddress?.slice(0, 10)}...{walletAddress?.slice(-8)}
            </p>
          </div>
        </div>
        <div className="mt-4 lg:mt-0 flex space-x-3">
          <button onClick={handleShare} className="btn-secondary inline-flex items-center">
            {copied ? (
              <><ClipboardDocumentCheckIcon className="h-4 w-4 mr-2 text-green-500" />Copied!</>
            ) : (
              <><LinkIcon className="h-4 w-4 mr-2" />Share Portfolio</>
            )}
          </button>
          <button onClick={handleExportPDF} disabled={isExporting} className="btn-primary inline-flex items-center disabled:opacity-60">
            <ArrowDownTrayIcon className="h-4 w-4 mr-2" />
            {isExporting ? "Exporting..." : "Export PDF"}
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="flex space-x-8">
          {[
            { id: "overview", label: "Overview" },
            { id: "contributions", label: "Contributions" },
            { id: "analytics", label: "Analytics" },
            { id: "blockchain", label: "Blockchain Records" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={clsx(
                "py-4 px-1 border-b-2 font-medium text-sm",
                activeTab === tab.id
                  ? "border-primary-500 text-primary-600"
                  : "border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300",
              )}
            >
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Overview Tab */}
      {activeTab === "overview" && (
        <div ref={overviewRef} className="space-y-6">
          {/* Stats cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card bg-gradient-to-br from-primary-500 to-primary-600 text-white">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-primary-100">Total Credits</p>
                  <p className="text-3xl font-bold mt-1">{totalCredits}</p>
                </div>
                <TrophyIcon className="h-10 w-10 text-primary-200" />
              </div>
            </div>
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500">Total Contributions</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">
                    {totalContributions}
                  </p>
                </div>
                <DocumentTextIcon className="h-10 w-10 text-gray-300" />
              </div>
            </div>
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500">Validated</p>
                  <p className="text-3xl font-bold text-green-600 mt-1">
                    {validatedCount}
                  </p>
                </div>
                <CubeIcon className="h-10 w-10 text-gray-300" />
              </div>
            </div>
            <div className="card">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-gray-500">Avg. Quality Score</p>
                  <p className="text-3xl font-bold text-gray-900 mt-1">
                    {contributions.length > 0
                      ? Math.round(
                          contributions.reduce(
                            (sum, c) => sum + (c.quality_score || 0),
                            0,
                          ) /
                            contributions.filter((c) => c.quality_score)
                              .length || 1,
                        )
                      : 0}
                    %
                  </p>
                </div>
                <ChartBarIcon className="h-10 w-10 text-gray-300" />
              </div>
            </div>
          </div>

          {/* Charts */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Credits by Category */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Credits by Category
              </h3>
              <div className="h-64">
                {creditsByCategory.length > 0 ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <BarChart data={creditsByCategory}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                      <XAxis
                        dataKey="category"
                        stroke="#6b7280"
                        fontSize={11}
                      />
                      <YAxis stroke="#6b7280" fontSize={12} />
                      <Tooltip />
                      <Bar
                        dataKey="credits"
                        fill="#3b82f6"
                        radius={[4, 4, 0, 0]}
                      />
                    </BarChart>
                  </ResponsiveContainer>
                ) : (
                  <div className="flex items-center justify-center h-full text-gray-500">
                    No data available
                  </div>
                )}
              </div>
            </div>

            {/* Skills Radar */}
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Competency Profile
              </h3>
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <RadarChart data={skillsData}>
                    <PolarGrid />
                    <PolarAngleAxis dataKey="subject" fontSize={12} />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} />
                    <Radar
                      name="Score"
                      dataKey="A"
                      stroke="#3b82f6"
                      fill="#3b82f6"
                      fillOpacity={0.5}
                    />
                  </RadarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* Top Contributions */}
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Top Contributions
            </h3>
            {topContributions.length > 0 ? (
              <div className="space-y-4">
                {topContributions.map((contribution, index) => (
                  <div
                    key={contribution.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-4">
                      <div
                        className={clsx(
                          "w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold",
                          index === 0
                            ? "bg-yellow-100 text-yellow-700"
                            : index === 1
                              ? "bg-gray-100 text-gray-700"
                              : index === 2
                                ? "bg-orange-100 text-orange-700"
                                : "bg-gray-50 text-gray-500",
                        )}
                      >
                        {index + 1}
                      </div>
                      <div>
                        <p className="font-medium text-gray-900">
                          {contribution.title}
                        </p>
                        <p className="text-sm text-gray-500">
                          {CATEGORY_NAMES[contribution.category]}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="font-bold text-primary-600">
                        {contribution.final_credits || 0} credits
                      </p>
                      <p className="text-sm text-gray-500">
                        Quality: {contribution.quality_score || 0}%
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-center text-gray-500 py-8">
                No contributions yet
              </p>
            )}
          </div>
        </div>
      )}

      {/* Contributions Tab */}
      {activeTab === "contributions" && (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead>
                <tr>
                  <th className="table-header">Title</th>
                  <th className="table-header">Category</th>
                  <th className="table-header">Quality</th>
                  <th className="table-header">Novelty</th>
                  <th className="table-header">Credits</th>
                  <th className="table-header">Status</th>
                  <th className="table-header">Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                {contributions.map((contribution) => (
                  <tr key={contribution.id} className="hover:bg-gray-50">
                    <td className="table-cell font-medium text-gray-900">
                      {contribution.title}
                    </td>
                    <td className="table-cell text-gray-500">
                      {CATEGORY_NAMES[contribution.category]}
                    </td>
                    <td className="table-cell">
                      {contribution.quality_score
                        ? `${contribution.quality_score}%`
                        : "-"}
                    </td>
                    <td className="table-cell">
                      {contribution.novelty_score
                        ? `${contribution.novelty_score}%`
                        : "-"}
                    </td>
                    <td className="table-cell font-medium text-green-600">
                      {contribution.final_credits || "-"}
                    </td>
                    <td className="table-cell">
                      <span
                        className={clsx(
                          "badge",
                          contribution.status === "validated"
                            ? "badge-validated"
                            : contribution.status === "approved"
                              ? "badge-approved"
                              : contribution.status === "rejected"
                                ? "badge-rejected"
                                : "badge-pending",
                        )}
                      >
                        {contribution.status}
                      </span>
                    </td>
                    <td className="table-cell text-gray-500">
                      {new Date(contribution.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Analytics Tab */}
      {activeTab === "analytics" && (
        <div className="space-y-6">
          <div className="card">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">
              Credit Growth Trend
            </h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={monthlyTrend}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis dataKey="month" stroke="#6b7280" />
                  <YAxis stroke="#6b7280" />
                  <Tooltip />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="credits"
                    stroke="#3b82f6"
                    strokeWidth={2}
                    dot={{ fill: "#3b82f6" }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                UGC Credit Breakdown
              </h3>
              <div className="space-y-3">
                {creditsByCategory.map((item, index) => (
                  <div
                    key={item.category}
                    className="flex items-center justify-between"
                  >
                    <div className="flex items-center space-x-3">
                      <div
                        className="w-3 h-3 rounded-full"
                        style={{
                          backgroundColor: `hsl(${index * 36}, 70%, 50%)`,
                        }}
                      />
                      <span className="text-gray-700">{item.category}</span>
                    </div>
                    <div className="flex items-center space-x-4">
                      <span className="text-gray-500">{item.count} items</span>
                      <span className="font-medium text-gray-900">
                        {item.credits} pts
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            <div className="card">
              <h3 className="text-lg font-semibold text-gray-900 mb-4">
                Performance Metrics
              </h3>
              <div className="space-y-4">
                <MetricBar label="Research Impact" value={85} color="blue" />
                <MetricBar
                  label="Publication Quality"
                  value={90}
                  color="green"
                />
                <MetricBar label="Innovation Index" value={75} color="purple" />
                <MetricBar
                  label="Collaboration Score"
                  value={80}
                  color="orange"
                />
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Blockchain Tab */}
      {activeTab === "blockchain" && (
        <div className="space-y-4">
          <div className="card bg-gradient-to-r from-gray-800 to-gray-900 text-white">
            <div className="flex items-center space-x-4">
              <CubeIcon className="h-12 w-12 text-blue-400" />
              <div>
                <h3 className="text-lg font-semibold">
                  Blockchain Verification
                </h3>
                <p className="text-gray-400">
                  All validated contributions are recorded on Hyperledger Besu
                </p>
              </div>
            </div>
          </div>

          {contributions
            .filter((c) => c.blockchain_hash)
            .map((contribution) => (
              <div key={contribution.id} className="card">
                <div className="flex items-start justify-between">
                  <div>
                    <h4 className="font-medium text-gray-900">
                      {contribution.title}
                    </h4>
                    <p className="text-sm text-gray-500 mt-1">
                      {CATEGORY_NAMES[contribution.category]}
                    </p>
                  </div>
                  <span className="badge badge-validated">On-Chain</span>
                </div>
                <div className="mt-4 space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                      Transaction Hash:
                    </span>
                    <code className="text-sm font-mono text-primary-600 bg-primary-50 px-2 py-1 rounded">
                      {contribution.blockchain_hash}
                    </code>
                  </div>
                  {contribution.ipfs_hash && (
                    <div className="flex items-center space-x-2">
                      <span className="text-sm text-gray-500">IPFS CID:</span>
                      <code className="text-sm font-mono text-gray-600 bg-gray-100 px-2 py-1 rounded">
                        {contribution.ipfs_hash}
                      </code>
                    </div>
                  )}
                </div>
              </div>
            ))}

          {contributions.filter((c) => c.blockchain_hash).length === 0 && (
            <div className="card text-center py-12">
              <CubeIcon className="h-12 w-12 mx-auto text-gray-300" />
              <p className="mt-2 text-gray-500">No blockchain records yet</p>
              <p className="text-sm text-gray-400">
                Records appear here once validated by HoD
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// Metric Bar Component
function MetricBar({ label, value, color }) {
  const colorClasses = {
    blue: "bg-blue-500",
    green: "bg-green-500",
    purple: "bg-purple-500",
    orange: "bg-orange-500",
  };

  return (
    <div>
      <div className="flex justify-between mb-1">
        <span className="text-sm text-gray-600">{label}</span>
        <span className="text-sm font-medium text-gray-900">{value}%</span>
      </div>
      <div className="w-full bg-gray-200 rounded-full h-2">
        <div
          className={clsx("h-2 rounded-full", colorClasses[color])}
          style={{ width: `${value}%` }}
        />
      </div>
    </div>
  );
}

export default Portfolio;
