import { useEffect, useState } from "react";
import { profileAPI } from "../services/api";
import {
  UserCircleIcon,
  PlusIcon,
  TrashIcon,
  CheckIcon,
} from "@heroicons/react/24/outline";
import clsx from "clsx";

const DESIGNATIONS = [
  { value: "professor", label: "Professor" },
  { value: "associate_professor", label: "Associate Professor" },
  { value: "assistant_professor", label: "Assistant Professor" },
  { value: "staff", label: "Staff" },
];

const PROJECT_STATUSES = ["ongoing", "completed", "planned"];

export default function Profile() {
  const [profile, setProfile] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);
  const [error, setError] = useState(null);

  // Editable fields
  const [name, setName] = useState("");
  const [designation, setDesignation] = useState("");
  const [yearsExp, setYearsExp] = useState("");
  const [bio, setBio] = useState("");
  const [lectures, setLectures] = useState([]);
  const [projects, setProjects] = useState([]);
  const [courses, setCourses] = useState([]);

  useEffect(() => {
    profileAPI.getProfile()
      .then((r) => {
        const d = r.data;
        setProfile(d);
        setName(d.name || "");
        setDesignation(d.designation || "");
        setYearsExp(d.years_experience ?? "");
        setBio(d.bio || "");
        setLectures(d.lectures || []);
        setProjects(d.projects || []);
        setCourses(d.courses || []);
      })
      .catch(() => setError("Failed to load profile."))
      .finally(() => setIsLoading(false));
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    setError(null);
    try {
      await profileAPI.updateProfile({
        name: name.trim() || undefined,
        designation: designation || undefined,
        years_experience: yearsExp !== "" ? parseInt(yearsExp) : undefined,
        bio: bio.trim() || undefined,
        lectures,
        projects,
        courses,
      });
      setSaved(true);
      setTimeout(() => setSaved(false), 2500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0]?.msg : detail || "Failed to save.");
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) return <div className="flex items-center justify-center h-64"><div className="loader" /></div>;

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">My Profile</h1>
          <p className="mt-1 text-gray-500">Update your academic profile and metadata</p>
        </div>
        <button
          onClick={handleSave}
          disabled={isSaving}
          className={clsx(
            "btn-primary inline-flex items-center",
            saved && "bg-green-600 hover:bg-green-700 border-green-600"
          )}
        >
          {isSaving ? (
            <div className="loader" />
          ) : saved ? (
            <><CheckIcon className="h-5 w-5 mr-2" />Saved</>
          ) : (
            "Save Changes"
          )}
        </button>
      </div>

      {error && (
        <div className="p-4 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">{error}</div>
      )}

      {/* Basic Info */}
      <Section title="Basic Information" icon={UserCircleIcon}>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Full Name</label>
            <input className="input" value={name} onChange={(e) => setName(e.target.value)} placeholder="Dr. Jane Smith" />
          </div>
          <div>
            <label className="label">Designation</label>
            <select className="input" value={designation} onChange={(e) => setDesignation(e.target.value)}>
              <option value="">Select designation...</option>
              {DESIGNATIONS.map((d) => (
                <option key={d.value} value={d.value}>{d.label}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Email</label>
            <input className="input bg-gray-50" value={profile?.email || "—"} disabled />
          </div>
          <div>
            <label className="label">Employee ID</label>
            <input className="input bg-gray-50" value={profile?.employee_id || "—"} disabled />
          </div>
        </div>

        <div className="mt-4 grid grid-cols-1 sm:grid-cols-2 gap-4">
          <div>
            <label className="label">Years of Experience</label>
            <input
              type="number"
              min={0}
              max={60}
              className="input"
              value={yearsExp}
              onChange={(e) => setYearsExp(e.target.value)}
              placeholder="e.g. 12"
            />
          </div>
        </div>

        <div className="mt-4">
          <label className="label">Bio / About</label>
          <textarea
            className="input h-24 resize-none"
            value={bio}
            onChange={(e) => setBio(e.target.value)}
            placeholder="Brief description of your academic background and interests..."
          />
        </div>
      </Section>

      {/* Lectures */}
      <DynamicSection
        title="Guest Lectures & Invited Talks"
        items={lectures}
        setItems={setLectures}
        emptyItem={{ subject: "", year: "", semester: "", details: "" }}
        renderItem={(item, _idx, onChange) => (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="sm:col-span-2">
              <label className="label">Subject / Topic *</label>
              <input className="input" value={item.subject} onChange={(e) => onChange("subject", e.target.value)} placeholder="e.g. Introduction to Machine Learning" />
            </div>
            <div>
              <label className="label">Year</label>
              <input type="number" className="input" value={item.year || ""} onChange={(e) => onChange("year", e.target.value ? parseInt(e.target.value) : null)} placeholder="2023" />
            </div>
            <div>
              <label className="label">Semester / Term</label>
              <input className="input" value={item.semester || ""} onChange={(e) => onChange("semester", e.target.value)} placeholder="e.g. Odd Semester, Jan 2023" />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Details</label>
              <textarea className="input h-16 resize-none" value={item.details || ""} onChange={(e) => onChange("details", e.target.value)} placeholder="Topics covered, audience, institution where delivered..." />
            </div>
          </div>
        )}
      />

      {/* Projects */}
      <DynamicSection
        title="Research Projects"
        items={projects}
        setItems={setProjects}
        emptyItem={{ title: "", description: "", funding_source: "", funding_amount: "", status: "ongoing", year_start: "", year_end: "" }}
        renderItem={(item, _idx, onChange) => (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="sm:col-span-2">
              <label className="label">Project Title *</label>
              <input className="input" value={item.title} onChange={(e) => onChange("title", e.target.value)} placeholder="e.g. AI-Based Crop Disease Detection" />
            </div>
            <div className="sm:col-span-2">
              <label className="label">Description</label>
              <textarea className="input h-16 resize-none" value={item.description || ""} onChange={(e) => onChange("description", e.target.value)} placeholder="Brief overview of the project scope and objectives..." />
            </div>
            <div>
              <label className="label">Funding Agency</label>
              <input className="input" value={item.funding_source || ""} onChange={(e) => onChange("funding_source", e.target.value)} placeholder="e.g. DST, SERB, UGC, DRDO" />
            </div>
            <div>
              <label className="label">Funding Amount</label>
              <input className="input" value={item.funding_amount || ""} onChange={(e) => onChange("funding_amount", e.target.value)} placeholder="e.g. ₹25 Lakhs" />
            </div>
            <div>
              <label className="label">Status</label>
              <select className="input" value={item.status || "ongoing"} onChange={(e) => onChange("status", e.target.value)}>
                {PROJECT_STATUSES.map((s) => (
                  <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                ))}
              </select>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="label">Year Start</label>
                <input type="number" className="input" value={item.year_start || ""} onChange={(e) => onChange("year_start", e.target.value ? parseInt(e.target.value) : null)} placeholder="2021" />
              </div>
              <div>
                <label className="label">Year End</label>
                <input type="number" className="input" value={item.year_end || ""} onChange={(e) => onChange("year_end", e.target.value ? parseInt(e.target.value) : null)} placeholder="2024" />
              </div>
            </div>
          </div>
        )}
      />

      {/* Courses */}
      <DynamicSection
        title="Courses Handled"
        items={courses}
        setItems={setCourses}
        emptyItem={{ name: "", year: "", semester: "", students_count: "" }}
        renderItem={(item, _idx, onChange) => (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            <div className="sm:col-span-2">
              <label className="label">Course Name *</label>
              <input className="input" value={item.name} onChange={(e) => onChange("name", e.target.value)} placeholder="e.g. Database Management Systems" />
            </div>
            <div>
              <label className="label">Year</label>
              <input type="number" className="input" value={item.year || ""} onChange={(e) => onChange("year", e.target.value ? parseInt(e.target.value) : null)} placeholder="2023" />
            </div>
            <div>
              <label className="label">Semester</label>
              <input className="input" value={item.semester || ""} onChange={(e) => onChange("semester", e.target.value)} placeholder="e.g. Even, 4th Semester" />
            </div>
            <div>
              <label className="label">No. of Students</label>
              <input type="number" className="input" value={item.students_count || ""} onChange={(e) => onChange("students_count", e.target.value ? parseInt(e.target.value) : null)} placeholder="60" />
            </div>
          </div>
        )}
      />
    </div>
  );
}

// ─── Reusable components ──────────────────────────────────────────────────────

function Section({ title, icon: Icon, children }) {
  return (
    <div className="card">
      <div className="flex items-center space-x-3 mb-5">
        <div className="p-2 bg-primary-50 rounded-lg">
          <Icon className="h-5 w-5 text-primary-600" />
        </div>
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
      </div>
      {children}
    </div>
  );
}

function DynamicSection({ title, items, setItems, emptyItem, renderItem }) {
  const update = (idx, field, value) => {
    setItems((prev) => prev.map((item, i) => i === idx ? { ...item, [field]: value } : item));
  };

  const add = () => setItems((prev) => [...prev, { ...emptyItem }]);

  const remove = (idx) => setItems((prev) => prev.filter((_, i) => i !== idx));

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-5">
        <h2 className="text-lg font-semibold text-gray-900">{title}</h2>
        <button
          type="button"
          onClick={add}
          className="inline-flex items-center text-sm text-primary-600 hover:text-primary-700 font-medium"
        >
          <PlusIcon className="h-4 w-4 mr-1" />
          Add
        </button>
      </div>

      {items.length === 0 ? (
        <p className="text-sm text-gray-400 text-center py-6">
          No entries yet. Click <span className="font-medium text-primary-500">Add</span> to get started.
        </p>
      ) : (
        <div className="space-y-4">
          {items.map((item, idx) => (
            <div key={idx} className="relative p-4 border border-gray-200 rounded-lg bg-gray-50">
              <button
                type="button"
                onClick={() => remove(idx)}
                className="absolute top-3 right-3 p-1 text-gray-400 hover:text-red-500 transition-colors"
                title="Remove"
              >
                <TrashIcon className="h-4 w-4" />
              </button>
              {renderItem(item, idx, (field, value) => update(idx, field, value))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
