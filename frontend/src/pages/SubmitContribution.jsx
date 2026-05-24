import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useContributionStore } from "../store";
import {
  CloudArrowUpIcon,
  DocumentTextIcon,
  XMarkIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  ArrowLeftIcon,
  SparklesIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

const CATEGORIES = [
  {
    value: "refereed_journal",
    label: "Refereed Journal",
    description: "Peer-reviewed journal publication",
    basePoints: 25,
  },
  {
    value: "international_book",
    label: "International Book",
    description: "International book publication",
    basePoints: 30,
  },
  {
    value: "national_book",
    label: "National Book",
    description: "National book publication",
    basePoints: 20,
  },
  {
    value: "book_chapter",
    label: "Book Chapter",
    description: "Chapter contribution to a book",
    basePoints: 5,
  },
  {
    value: "international_lecture",
    label: "International Lecture",
    description: "International lecture / invited talk",
    basePoints: 7,
  },
  {
    value: "national_conference",
    label: "National Conference",
    description: "National conference presentation",
    basePoints: 10,
  },
  {
    value: "patent_filed",
    label: "Patent Filed",
    description: "Patent filed",
    basePoints: 15,
  },
  {
    value: "patent_granted",
    label: "Patent Granted",
    description: "Patent granted",
    basePoints: 30,
  },
  {
    value: "editorial_work",
    label: "Editorial Work",
    description: "Editorial board / reviewing responsibilities",
    basePoints: 10,
  },
  {
    value: "research_project",
    label: "Research Project",
    description: "Funded research project",
    basePoints: 20,
  },
];

function SubmitContribution() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);
  const { submitContribution, isLoading, error } = useContributionStore();

  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({
    category: "refereed_journal",
    title: "",
    description: "",
    abstract: "",
    authors: "",
    publication_venue: "",
    publication_date: "",
    doi: "",
    keywords: "",
  });
  const [files, setFiles] = useState([]);
  const [validationErrors, setValidationErrors] = useState({});
  const [submitSuccess, setSubmitSuccess] = useState(false);

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear validation error for this field
    if (validationErrors[name]) {
      setValidationErrors((prev) => ({ ...prev, [name]: null }));
    }
  };

  const handleFileSelect = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const validFiles = selectedFiles.filter((file) => {
      const validTypes = ["application/pdf"];
      const maxSize = 50 * 1024 * 1024; // 50MB (matches backend default)
      return validTypes.includes(file.type) && file.size <= maxSize;
    });

    setFiles(validFiles.slice(0, 1));

    if (validationErrors.file) {
      setValidationErrors((prev) => ({ ...prev, file: null }));
    }
  };

  const removeFile = (index) => {
    setFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const validateStep = (currentStep) => {
    const errors = {};

    if (currentStep === 1) {
      if (!formData.title.trim()) {
        errors.title = "Title is required";
      }
      if (!formData.description.trim()) {
        errors.description = "Description is required";
      }
      if (formData.description.trim().length < 50) {
        errors.description = "Description must be at least 50 characters";
      }
    }

    if (currentStep === 2) {
      if (!formData.abstract.trim()) {
        errors.abstract = "Abstract is required";
      } else if (formData.abstract.trim().length < 100) {
        errors.abstract = "Abstract must be at least 100 characters";
      }
    }

    if (currentStep === 3) {
      if (files.length === 0) {
        errors.file = "Please upload a PDF file";
      } else if (files.length > 1) {
        errors.file = "Please upload only one PDF file";
      }
    }

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleNext = () => {
    if (validateStep(step)) {
      setStep((prev) => prev + 1);
    }
  };

  const handleBack = () => {
    setStep((prev) => prev - 1);
  };

  const handleSubmit = async () => {
    if (!validateStep(step)) return;

    try {
      const pdf = files[0];
      const fd = new FormData();
      fd.append("category", formData.category);
      fd.append("title", formData.title);
      fd.append("abstract", formData.abstract);
      fd.append("doi", formData.doi || "");
      fd.append("journal_name", formData.publication_venue || "");
      fd.append("co_authors", formData.authors || "");
      fd.append("file", pdf, pdf.name);

      await submitContribution(fd);
      setSubmitSuccess(true);

      // Redirect after success
      setTimeout(() => {
        navigate("/contributions");
      }, 2000);
    } catch (err) {
      console.error("Failed to submit contribution:", err);
    }
  };

  const selectedCategory = CATEGORIES.find(
    (c) => c.value === formData.category,
  );

  if (submitSuccess) {
    return <SubmitSuccessScreen
      onViewContributions={() => navigate("/contributions")}
      onSubmitAnother={() => {
        setSubmitSuccess(false);
        setStep(1);
        setFormData({
          category: "refereed_journal",
          title: "",
          description: "",
          abstract: "",
          authors: "",
          publication_venue: "",
          publication_date: "",
          doi: "",
          keywords: "",
        });
        setFiles([]);
      }}
    />;
  }

  return (
    <div className="max-w-3xl mx-auto">
      {/* Header */}
      <div className="mb-6">
        <button
          onClick={() => navigate("/contributions")}
          className="flex items-center text-gray-600 hover:text-gray-900 mb-4"
        >
          <ArrowLeftIcon className="h-4 w-4 mr-2" />
          Back to Contributions
        </button>
        <h1 className="text-2xl font-bold text-gray-900">
          Submit New Contribution
        </h1>
        <p className="mt-1 text-gray-500">
          Submit your academic contribution for evaluation and blockchain
          verification
        </p>
      </div>

      {/* Progress steps */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          {["Category & Info", "Details", "Documents", "Review"].map(
            (label, index) => (
              <div
                key={label}
                className={clsx("flex items-center", index < 3 && "flex-1")}
              >
                <div
                  className={clsx(
                    "flex items-center justify-center w-8 h-8 rounded-full text-sm font-medium",
                    step > index + 1
                      ? "bg-green-500 text-white"
                      : step === index + 1
                        ? "bg-primary-600 text-white"
                        : "bg-gray-200 text-gray-600",
                  )}
                >
                  {step > index + 1 ? "✓" : index + 1}
                </div>
                <span
                  className={clsx(
                    "ml-2 text-sm",
                    step === index + 1
                      ? "text-primary-600 font-medium"
                      : "text-gray-500",
                  )}
                >
                  {label}
                </span>
                {index < 3 && (
                  <div
                    className={clsx(
                      "flex-1 h-0.5 mx-4",
                      step > index + 1 ? "bg-green-500" : "bg-gray-200",
                    )}
                  />
                )}
              </div>
            ),
          )}
        </div>
      </div>

      {/* Form content */}
      <div className="card">
        {/* Step 1: Category & Basic Info */}
        {step === 1 && (
          <div className="space-y-6">
            <div>
              <label className="label">Contribution Category</label>
              <div className="grid grid-cols-2 gap-3 mt-2">
                {CATEGORIES.map((category) => (
                  <button
                    key={category.value}
                    type="button"
                    onClick={() =>
                      setFormData((prev) => ({
                        ...prev,
                        category: category.value,
                      }))
                    }
                    className={clsx(
                      "p-4 rounded-lg border-2 text-left transition-all",
                      formData.category === category.value
                        ? "border-primary-500 bg-primary-50"
                        : "border-gray-200 hover:border-gray-300",
                    )}
                  >
                    <div className="font-medium text-gray-900">
                      {category.label}
                    </div>
                    <div className="text-sm text-gray-500">
                      {category.description}
                    </div>
                    <div className="mt-1 text-xs text-primary-600">
                      Base Points: {category.basePoints}
                    </div>
                  </button>
                ))}
              </div>
            </div>

            <div>
              <label className="label">Title *</label>
              <input
                type="text"
                name="title"
                value={formData.title}
                onChange={handleInputChange}
                placeholder="Enter contribution title"
                className={clsx(
                  "input",
                  validationErrors.title && "border-red-500",
                )}
              />
              {validationErrors.title && (
                <p className="mt-1 text-sm text-red-500">
                  {validationErrors.title}
                </p>
              )}
            </div>

            <div>
              <label className="label">Description *</label>
              <textarea
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                rows={4}
                placeholder="Provide a detailed description of your contribution (min 50 characters)"
                className={clsx(
                  "input",
                  validationErrors.description && "border-red-500",
                )}
              />
              <div className="flex justify-between mt-1">
                {validationErrors.description ? (
                  <p className="text-sm text-red-500">
                    {validationErrors.description}
                  </p>
                ) : (
                  <span />
                )}
                <span className="text-sm text-gray-400">
                  {formData.description.length} characters
                </span>
              </div>
            </div>
          </div>
        )}

        {/* Step 2: Details */}
        {step === 2 && (
          <div className="space-y-6">
            <div>
              <label className="label">Abstract *</label>
              <textarea
                name="abstract"
                value={formData.abstract}
                onChange={handleInputChange}
                rows={6}
                placeholder="Enter the abstract of your contribution. This will be used for AI evaluation."
                className={clsx(
                  "input",
                  validationErrors.abstract && "border-red-500",
                )}
              />
              {validationErrors.abstract && (
                <p className="mt-1 text-sm text-red-500">
                  {validationErrors.abstract}
                </p>
              )}
              <p className="mt-1 text-sm text-gray-500">
                The AI evaluation system will analyze your abstract against 36
                benchmark attributes
              </p>
            </div>

            <div>
              <label className="label">Authors/Co-authors</label>
              <input
                type="text"
                name="authors"
                value={formData.authors}
                onChange={handleInputChange}
                placeholder="Enter authors separated by commas"
                className="input"
              />
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">Publication Venue</label>
                <input
                  type="text"
                  name="publication_venue"
                  value={formData.publication_venue}
                  onChange={handleInputChange}
                  placeholder="Journal/Conference name"
                  className="input"
                />
              </div>
              <div>
                <label className="label">Publication Date</label>
                <input
                  type="date"
                  name="publication_date"
                  value={formData.publication_date}
                  onChange={handleInputChange}
                  className="input"
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="label">DOI (if available)</label>
                <input
                  type="text"
                  name="doi"
                  value={formData.doi}
                  onChange={handleInputChange}
                  placeholder="10.xxxx/xxxxx"
                  className="input"
                />
              </div>
              <div>
                <label className="label">Keywords</label>
                <input
                  type="text"
                  name="keywords"
                  value={formData.keywords}
                  onChange={handleInputChange}
                  placeholder="Enter keywords separated by commas"
                  className="input"
                />
              </div>
            </div>
          </div>
        )}

        {/* Step 3: Documents */}
        {step === 3 && (
          <div className="space-y-6">
            <div>
              <label className="label">Upload Supporting Documents</label>
              <p className="text-sm text-gray-500 mb-4">
                Upload a single PDF (max 50MB). The file will be stored on IPFS.
              </p>

              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center cursor-pointer hover:border-primary-500 hover:bg-primary-50 transition-colors"
              >
                <CloudArrowUpIcon className="h-12 w-12 mx-auto text-gray-400" />
                <p className="mt-2 text-gray-600">
                  Click to upload or drag and drop
                </p>
                <p className="text-sm text-gray-400">
                  PDF up to 50MB
                </p>
              </div>
              <input
                ref={fileInputRef}
                type="file"
                accept=".pdf,application/pdf"
                onChange={handleFileSelect}
                className="hidden"
              />
              {validationErrors.file && (
                <p className="mt-2 text-sm text-red-600">
                  {validationErrors.file}
                </p>
              )}
            </div>

            {files.length > 0 && (
              <div className="space-y-2">
                <label className="label">Selected Files</label>
                {files.map((file, index) => (
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
                  >
                    <div className="flex items-center space-x-3">
                      <DocumentTextIcon className="h-8 w-8 text-gray-400" />
                      <div>
                        <p className="font-medium text-gray-900">{file.name}</p>
                        <p className="text-sm text-gray-500">
                          {(file.size / 1024 / 1024).toFixed(2)} MB
                        </p>
                      </div>
                    </div>
                    <button
                      onClick={() => removeFile(index)}
                      className="p-1 text-gray-400 hover:text-red-500"
                    >
                      <XMarkIcon className="h-5 w-5" />
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Step 4: Review */}
        {step === 4 && (
          <div className="space-y-6">
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 className="font-medium text-blue-900">
                Review Your Submission
              </h3>
              <p className="mt-1 text-sm text-blue-700">
                Please review all details before submitting. Once submitted,
                your contribution will be evaluated by the AI system and then
                reviewed by your HoD.
              </p>
            </div>

            <div className="grid grid-cols-2 gap-6">
              <div>
                <label className="label">Category</label>
                <p className="text-gray-900">{selectedCategory?.label}</p>
              </div>
              <div>
                <label className="label">Base Points</label>
                <p className="text-green-600 font-medium">
                  {selectedCategory?.basePoints}
                </p>
              </div>
            </div>

            <div>
              <label className="label">Title</label>
              <p className="text-gray-900">{formData.title}</p>
            </div>

            <div>
              <label className="label">Description</label>
              <p className="text-gray-700">{formData.description}</p>
            </div>

            {formData.abstract && (
              <div>
                <label className="label">Abstract</label>
                <p className="text-gray-700">{formData.abstract}</p>
              </div>
            )}

            {formData.authors && (
              <div>
                <label className="label">Authors</label>
                <p className="text-gray-700">{formData.authors}</p>
              </div>
            )}

            {formData.publication_venue && (
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="label">Publication Venue</label>
                  <p className="text-gray-700">{formData.publication_venue}</p>
                </div>
                <div>
                  <label className="label">Publication Date</label>
                  <p className="text-gray-700">{formData.publication_date}</p>
                </div>
              </div>
            )}

            {files.length > 0 && (
              <div>
                <label className="label">Documents ({files.length})</label>
                <ul className="list-disc list-inside text-gray-700">
                  {files.map((file, index) => (
                    <li key={index}>{file.name}</li>
                  ))}
                </ul>
              </div>
            )}

            {error && (
              <div className="flex items-start space-x-2 p-4 bg-red-50 border border-red-200 rounded-lg">
                <ExclamationTriangleIcon className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{error}</p>
              </div>
            )}
          </div>
        )}

        {/* Navigation buttons */}
        <div className="flex justify-between mt-8 pt-6 border-t border-gray-200">
          {step > 1 ? (
            <button onClick={handleBack} className="btn-secondary">
              Back
            </button>
          ) : (
            <span />
          )}

          {step < 4 ? (
            <button onClick={handleNext} className="btn-primary">
              Continue
            </button>
          ) : (
            <button
              onClick={handleSubmit}
              disabled={isLoading}
              className="btn-primary flex items-center"
            >
              {isLoading ? (
                <>
                  <div className="loader mr-2" />
                  Submitting...
                </>
              ) : (
                <>
                  <CheckCircleIcon className="h-5 w-5 mr-2" />
                  Submit Contribution
                </>
              )}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

const EVAL_DELAY_MS = 60_000; // 1 minute

function SubmitSuccessScreen({ onViewContributions, onSubmitAnother }) {
  const [elapsed, setElapsed] = useState(0);
  const evaluating = elapsed < EVAL_DELAY_MS;
  const progress = Math.min(100, (elapsed / EVAL_DELAY_MS) * 100);

  useEffect(() => {
    const start = Date.now();
    const interval = setInterval(() => {
      const e = Date.now() - start;
      setElapsed(e);
      if (e >= EVAL_DELAY_MS) clearInterval(interval);
    }, 500);
    return () => clearInterval(interval);
  }, []);

  const secondsLeft = Math.max(0, Math.ceil((EVAL_DELAY_MS - elapsed) / 1000));

  return (
    <div className="max-w-2xl mx-auto">
      <div className="card text-center py-12 px-8">
        {evaluating ? (
          <>
            <div className="mx-auto w-16 h-16 bg-primary-100 rounded-full flex items-center justify-center mb-4">
              <SparklesIcon className="h-8 w-8 text-primary-600 animate-pulse" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900">Submitted Successfully!</h2>
            <p className="mt-2 text-gray-500">
              Your contribution has been uploaded. The AI evaluation engine is now
              analysing quality and novelty scores…
            </p>

            <div className="mt-6 space-y-2">
              <div className="flex justify-between text-sm text-gray-500">
                <span>AI Evaluation in progress</span>
                <span>{secondsLeft}s remaining</span>
              </div>
              <div className="w-full bg-gray-100 rounded-full h-2.5 overflow-hidden">
                <div
                  className="h-2.5 rounded-full bg-primary-500 transition-all duration-500"
                  style={{ width: `${progress}%` }}
                />
              </div>
            </div>

            <p className="mt-4 text-xs text-gray-400">
              Scores will be visible once evaluation completes.
            </p>
          </>
        ) : (
          <>
            <CheckCircleIcon className="h-16 w-16 mx-auto text-green-500" />
            <h2 className="mt-4 text-2xl font-bold text-gray-900">
              Evaluation Complete!
            </h2>
            <p className="mt-2 text-gray-600">
              Quality and novelty scores are ready. Your contribution is now
              pending HoD review.
            </p>
            <div className="mt-6 flex justify-center space-x-4">
              <button onClick={onViewContributions} className="btn-primary">
                View Contributions
              </button>
              <button onClick={onSubmitAnother} className="btn-secondary">
                Submit Another
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default SubmitContribution;
