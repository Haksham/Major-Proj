import { useEffect, useState, useRef } from "react";
import { useParams, Link } from "react-router-dom";
import {
  AcademicCapIcon,
  DocumentTextIcon,
  TrophyIcon,
  CubeIcon,
  CheckCircleIcon,
  ClockIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  ArrowDownTrayIcon,
  BeakerIcon,
  BookOpenIcon,
  PresentationChartBarIcon,
  BriefcaseIcon,
  CalendarDaysIcon,
  UserCircleIcon,
  BuildingLibraryIcon,
  EnvelopeIcon,
  IdentificationIcon,
  ClipboardDocumentIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

const CATEGORY_LABELS = {
  refereed_journal: "Refereed Journal",
  international_book: "International Book",
  national_book: "National Book",
  book_chapter: "Book Chapter",
  international_lecture: "International Lecture / Talk",
  national_conference: "National Conference",
  patent_filed: "Patent Filed",
  patent_granted: "Patent Granted",
  editorial_work: "Editorial Work",
  research_project: "Research Project",
};

const DESIGNATION_LABELS = {
  professor: "Professor",
  associate_professor: "Associate Professor",
  assistant_professor: "Assistant Professor",
  staff: "Staff",
};

const STATUS_CONFIG = {
  validated: { label: "Validated", color: "bg-green-100 text-green-700 border-green-200", dot: "bg-green-500", icon: CheckCircleIcon },
  pending: { label: "Pending Review", color: "bg-yellow-100 text-yellow-700 border-yellow-200", dot: "bg-yellow-400", icon: ClockIcon },
  under_review: { label: "Under Review", color: "bg-blue-100 text-blue-700 border-blue-200", dot: "bg-blue-500", icon: ClockIcon },
  rejected: { label: "Rejected", color: "bg-red-100 text-red-700 border-red-200", dot: "bg-red-500", icon: XCircleIcon },
  flagged: { label: "Flagged", color: "bg-orange-100 text-orange-700 border-orange-200", dot: "bg-orange-500", icon: ExclamationTriangleIcon },
};

export default function PublicPortfolio() {
  const { walletAddress } = useParams();
  const [data, setData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [isExporting, setIsExporting] = useState(false);
  const [activeSection, setActiveSection] = useState("contributions");
  const printRef = useRef(null);

  useEffect(() => {
    fetch(`/api/v1/portfolio/public/${walletAddress}`)
      .then((r) => {
        if (!r.ok) throw new Error(r.status === 404 ? "Faculty not found." : "Failed to load portfolio.");
        return r.json();
      })
      .then(setData)
      .catch((e) => setError(e.message))
      .finally(() => setIsLoading(false));
  }, [walletAddress]);

  const handleExportPDF = async () => {
    if (!printRef.current) return;
    setIsExporting(true);
    try {
      const { default: jsPDF } = await import("jspdf");
      const { default: html2canvas } = await import("html2canvas");
      const canvas = await html2canvas(printRef.current, { scale: 2, useCORS: true, backgroundColor: "#ffffff" });
      const imgData = canvas.toDataURL("image/png");
      const pdf = new jsPDF({ orientation: "portrait", unit: "mm", format: "a4" });
      const pageW = pdf.internal.pageSize.getWidth();
      const pageH = pdf.internal.pageSize.getHeight();
      const imgH = (canvas.height * pageW) / canvas.width;
      let left = imgH; let pos = 0;
      pdf.addImage(imgData, "PNG", 0, pos, pageW, imgH);
      left -= pageH;
      while (left > 0) { pos -= pageH; pdf.addPage(); pdf.addImage(imgData, "PNG", 0, pos, pageW, imgH); left -= pageH; }
      pdf.save(`${data.faculty.name.replace(/\s+/g, "_")}_Portfolio.pdf`);
    } catch (e) { console.error(e); }
    finally { setIsExporting(false); }
  };

  if (isLoading) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="text-center"><div className="loader mx-auto mb-3" /><p className="text-gray-500">Loading portfolio...</p></div>
    </div>
  );

  if (error) return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center px-4">
      <div className="text-center">
        <AcademicCapIcon className="h-16 w-16 text-gray-300 mx-auto mb-4" />
        <h2 className="text-xl font-bold text-gray-700">{error}</h2>
        <Link to="/login" className="mt-6 inline-block btn-primary">Go to SALF</Link>
      </div>
    </div>
  );

  const { faculty, stats, contributions, lectures, projects, courses } = data;

  const sections = [
    { id: "contributions", label: "Contributions", count: contributions.length, icon: DocumentTextIcon },
    { id: "lectures", label: "Lectures & Talks", count: lectures.length, icon: PresentationChartBarIcon },
    { id: "projects", label: "Research Projects", count: projects.length, icon: BeakerIcon },
    { id: "courses", label: "Courses Handled", count: courses.length, icon: BookOpenIcon },
  ];

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Top bar */}
      <div className="bg-primary-700 text-white py-3 px-6 flex items-center justify-between sticky top-0 z-20">
        <div className="flex items-center space-x-3">
          <CubeIcon className="h-6 w-6" />
          <span className="font-bold text-lg">SALF</span>
          <span className="text-primary-300 text-sm hidden sm:inline">Secure Academic Ledger Framework</span>
        </div>
        <button
          onClick={handleExportPDF}
          disabled={isExporting}
          className="inline-flex items-center text-sm font-medium bg-white text-primary-700 px-3 py-1.5 rounded-lg hover:bg-primary-50 transition-colors disabled:opacity-60"
        >
          <ArrowDownTrayIcon className="h-4 w-4 mr-1.5" />
          {isExporting ? "Exporting..." : "Export PDF"}
        </button>
      </div>

      <div ref={printRef} className="max-w-4xl mx-auto px-4 py-8 space-y-6">

        {/* ── Faculty header card ── */}
        <div className="bg-white rounded-2xl shadow-sm overflow-hidden">
          <div className="h-3 bg-gradient-to-r from-primary-500 to-blue-500" />
          <div className="p-6">
            <div className="flex flex-col sm:flex-row sm:items-start sm:space-x-6 space-y-4 sm:space-y-0">
              <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center shrink-0">
                <UserCircleIcon className="h-12 w-12 text-primary-500" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex flex-wrap items-center gap-3">
                  <h1 className="text-2xl font-bold text-gray-900">{faculty.name}</h1>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-700 border border-green-200">
                    <CheckCircleIcon className="h-3.5 w-3.5 mr-1" />Blockchain Verified
                  </span>
                </div>
                {faculty.designation && (
                  <p className="text-primary-600 font-medium mt-1">
                    {DESIGNATION_LABELS[faculty.designation] || faculty.designation}
                  </p>
                )}
                {faculty.years_experience && (
                  <p className="text-gray-500 text-sm mt-0.5">{faculty.years_experience} years of experience</p>
                )}

                <div className="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-sm text-gray-500">
                  {faculty.email && (
                    <span className="flex items-center"><EnvelopeIcon className="h-4 w-4 mr-1.5 text-gray-400" />{faculty.email}</span>
                  )}
                  {faculty.employee_id && (
                    <span className="flex items-center"><IdentificationIcon className="h-4 w-4 mr-1.5 text-gray-400" />ID: {faculty.employee_id}</span>
                  )}
                  <WalletAddress address={faculty.wallet_address} />
                </div>

                {faculty.bio && (
                  <p className="mt-4 text-gray-600 text-sm leading-relaxed border-t border-gray-100 pt-4">{faculty.bio}</p>
                )}
              </div>
            </div>
          </div>
        </div>

        {/* ── Stats row ── */}
        <div className="grid grid-cols-2 sm:grid-cols-5 gap-3">
          <StatCard icon={TrophyIcon} label="Credits" value={stats.total_credits.toFixed(1)} color="primary" span />
          <StatCard icon={DocumentTextIcon} label="Total" value={stats.total_contributions} color="blue" />
          <StatCard icon={CheckCircleIcon} label="Validated" value={stats.validated_count} color="green" />
          <StatCard icon={ClockIcon} label="Pending" value={stats.pending_count} color="yellow" />
          <StatCard icon={XCircleIcon} label="Rejected" value={stats.rejected_count} color="red" />
        </div>

        {/* ── Section tabs ── */}
        <div className="bg-white rounded-xl shadow-sm overflow-hidden">
          <div className="flex overflow-x-auto border-b border-gray-200">
            {sections.map((s) => (
              <button
                key={s.id}
                onClick={() => setActiveSection(s.id)}
                className={clsx(
                  "flex items-center whitespace-nowrap px-5 py-3.5 text-sm font-medium border-b-2 transition-colors",
                  activeSection === s.id
                    ? "border-primary-500 text-primary-600 bg-primary-50"
                    : "border-transparent text-gray-500 hover:text-gray-700"
                )}
              >
                <s.icon className="h-4 w-4 mr-2" />
                {s.label}
                <span className="ml-2 px-1.5 py-0.5 rounded-full text-xs bg-gray-100 text-gray-600">
                  {s.count}
                </span>
              </button>
            ))}
          </div>

          <div className="p-5">
            {/* CONTRIBUTIONS */}
            {activeSection === "contributions" && (
              contributions.length === 0 ? (
                <EmptyState icon={DocumentTextIcon} text="No contributions yet." />
              ) : (
                <div className="space-y-3">
                  {contributions.map((c) => {
                    const sc = STATUS_CONFIG[c.status] || STATUS_CONFIG.pending;
                    const StatusIcon = sc.icon;
                    return (
                      <div key={c.id} className="border border-gray-200 rounded-lg p-4 hover:border-gray-300 transition-colors">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 flex-wrap">
                              <p className="font-medium text-gray-900 leading-snug">{c.title}</p>
                              <span className={clsx("inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border", sc.color)}>
                                <StatusIcon className="h-3 w-3 mr-1" />{sc.label}
                              </span>
                            </div>
                            <p className="text-xs text-primary-600 font-medium mt-1">
                              {CATEGORY_LABELS[c.category] || c.category}
                            </p>
                            {c.journal_name && (
                              <p className="text-sm text-gray-500 mt-1">{c.journal_name}</p>
                            )}
                            {c.abstract && (
                              <p className="text-sm text-gray-500 mt-1 line-clamp-2">{c.abstract}</p>
                            )}
                            <div className="mt-2 flex flex-wrap gap-x-4 gap-y-1 text-xs text-gray-400">
                              {c.doi && <span>DOI: {c.doi}</span>}
                              {c.isbn && <span>ISBN: {c.isbn}</span>}
                              {c.issn && <span>ISSN: {c.issn}</span>}
                              {c.co_authors && <span>Co-authors: {c.co_authors}</span>}
                              {c.submission_time && (
                                <span className="flex items-center">
                                  <CalendarDaysIcon className="h-3 w-3 mr-1" />
                                  {new Date(c.submission_time).toLocaleDateString("en-IN", { day: "numeric", month: "short", year: "numeric" })}
                                </span>
                              )}
                            </div>
                          </div>
                          <div className="text-right shrink-0 space-y-1">
                            {c.final_credits > 0 && (
                              <p className="text-base font-bold text-primary-600">{Number(c.final_credits).toFixed(1)} pts</p>
                            )}
                            {c.ai_quality_score > 0 && (
                              <p className="text-xs text-gray-400">Quality: {c.ai_quality_score}%</p>
                            )}
                            {c.novelty_percentage > 0 && (
                              <p className="text-xs text-gray-400">Novelty: {c.novelty_percentage}%</p>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )
            )}

            {/* LECTURES */}
            {activeSection === "lectures" && (
              lectures.length === 0 ? (
                <EmptyState icon={PresentationChartBarIcon} text="No lectures added yet." />
              ) : (
                <div className="space-y-4">
                  {lectures.map((l, i) => (
                    <div key={i} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between gap-4">
                        <div className="flex-1">
                          <p className="font-medium text-gray-900">{l.subject}</p>
                          {l.details && <p className="text-sm text-gray-500 mt-1 leading-relaxed">{l.details}</p>}
                        </div>
                        <div className="text-right shrink-0 text-sm text-gray-500">
                          {l.year && <p className="font-medium text-gray-700">{l.year}</p>}
                          {l.semester && <p className="text-xs">{l.semester}</p>}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}

            {/* PROJECTS */}
            {activeSection === "projects" && (
              projects.length === 0 ? (
                <EmptyState icon={BeakerIcon} text="No research projects added yet." />
              ) : (
                <div className="space-y-4">
                  {projects.map((p, i) => (
                    <div key={i} className="border border-gray-200 rounded-lg p-4">
                      <div className="flex items-start justify-between gap-4 flex-wrap">
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 flex-wrap">
                            <p className="font-medium text-gray-900">{p.title}</p>
                            {p.status && (
                              <span className={clsx(
                                "px-2 py-0.5 rounded-full text-xs font-medium border",
                                p.status === "ongoing" ? "bg-blue-50 text-blue-700 border-blue-200"
                                  : p.status === "completed" ? "bg-green-50 text-green-700 border-green-200"
                                  : "bg-gray-50 text-gray-600 border-gray-200"
                              )}>
                                {p.status.charAt(0).toUpperCase() + p.status.slice(1)}
                              </span>
                            )}
                          </div>
                          {p.description && <p className="text-sm text-gray-500 mt-1 leading-relaxed">{p.description}</p>}
                          <div className="mt-2 flex flex-wrap gap-x-5 gap-y-1 text-sm text-gray-500">
                            {p.funding_source && (
                              <span className="flex items-center">
                                <BriefcaseIcon className="h-3.5 w-3.5 mr-1 text-gray-400" />
                                {p.funding_source}
                              </span>
                            )}
                            {p.funding_amount && (
                              <span className="font-medium text-green-700">{p.funding_amount}</span>
                            )}
                          </div>
                        </div>
                        {(p.year_start || p.year_end) && (
                          <div className="text-right shrink-0 text-sm text-gray-500">
                            <span>{p.year_start || "?"}</span>
                            {p.year_end ? <span> – {p.year_end}</span> : <span className="text-blue-500"> – Present</span>}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}

            {/* COURSES */}
            {activeSection === "courses" && (
              courses.length === 0 ? (
                <EmptyState icon={BookOpenIcon} text="No courses added yet." />
              ) : (
                <div className="overflow-x-auto">
                  <table className="min-w-full divide-y divide-gray-200 text-sm">
                    <thead>
                      <tr className="bg-gray-50">
                        <th className="px-4 py-3 text-left font-medium text-gray-600">Course</th>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">Year</th>
                        <th className="px-4 py-3 text-left font-medium text-gray-600">Semester</th>
                        <th className="px-4 py-3 text-right font-medium text-gray-600">Students</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-gray-100">
                      {courses.map((c, i) => (
                        <tr key={i} className="hover:bg-gray-50">
                          <td className="px-4 py-3 font-medium text-gray-900">{c.name}</td>
                          <td className="px-4 py-3 text-gray-500">{c.year || "—"}</td>
                          <td className="px-4 py-3 text-gray-500">{c.semester || "—"}</td>
                          <td className="px-4 py-3 text-right text-gray-700">{c.students_count ?? "—"}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            )}
          </div>
        </div>

        {/* Footer */}
        <div className="text-center py-4 text-xs text-gray-400 space-y-1">
          <p>Portfolio verified and recorded on Hyperledger Besu · SALF</p>
          <p>Generated {new Date().toLocaleDateString("en-IN", { day: "numeric", month: "long", year: "numeric" })}</p>
        </div>
      </div>
    </div>
  );
}

function WalletAddress({ address }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(address).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <span className="flex items-center gap-1.5 font-mono text-xs text-gray-400">
      <BuildingLibraryIcon className="h-4 w-4 shrink-0 text-gray-400" />
      {address.slice(0, 14)}...{address.slice(-8)}
      <button
        onClick={handleCopy}
        title={copied ? "Copied!" : "Copy wallet address"}
        className="ml-0.5 text-gray-400 hover:text-gray-600 transition-colors"
      >
        {copied
          ? <CheckCircleIcon className="h-3.5 w-3.5 text-green-500" />
          : <ClipboardDocumentIcon className="h-3.5 w-3.5" />
        }
      </button>
      {copied && <span className="text-green-500 not-mono font-sans">Copied!</span>}
    </span>
  );
}

function StatCard({ icon: Icon, label, value, color, span }) {
  const colors = {
    primary: "bg-primary-50 text-primary-600",
    blue: "bg-blue-50 text-blue-600",
    green: "bg-green-50 text-green-600",
    yellow: "bg-yellow-50 text-yellow-600",
    red: "bg-red-50 text-red-600",
    purple: "bg-purple-50 text-purple-600",
  };
  return (
    <div className={clsx("bg-white rounded-xl shadow-sm p-4 flex items-center space-x-3", span && "col-span-2 sm:col-span-1")}>
      <div className={clsx("p-2 rounded-lg shrink-0", colors[color])}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <p className="text-xl font-bold text-gray-900">{value}</p>
        <p className="text-xs text-gray-500">{label}</p>
      </div>
    </div>
  );
}

function EmptyState({ icon: Icon, text }) {
  return (
    <div className="text-center py-12">
      <Icon className="h-10 w-10 text-gray-200 mx-auto mb-3" />
      <p className="text-gray-400 text-sm">{text}</p>
    </div>
  );
}
