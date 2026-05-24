import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store";
import { web3Service } from "../services/web3";
import { authAPI, institutesAPI } from "../services/api";
import { BuildingLibraryIcon, UserGroupIcon } from "@heroicons/react/24/outline";
import {
  CubeIcon,
  ShieldCheckIcon,
  AcademicCapIcon,
} from "@heroicons/react/24/outline";

function MetaMaskIcon() {
  return (
    <svg className="w-5 h-5" viewBox="0 0 35 33" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M32.958 1L19.888 10.535l2.436-5.766L32.958 1z" fill="#E17726" stroke="#E17726" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M2.042 1l12.956 9.623-2.32-5.854L2.042 1zM28.18 23.406l-3.48 5.332 7.445 2.049 2.136-7.268-6.101-.113zM1.733 23.519l2.12 7.268 7.43-2.05-3.464-5.33-6.086.112z" fill="#E27625" stroke="#E27625" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M10.903 14.445l-2.074 3.134 7.381.337-.247-7.938-5.06 4.467zM24.097 14.445l-5.138-4.557-.169 8.028 7.381-.337-2.074-3.134zM11.283 28.738l4.44-2.163-3.83-2.986-.61 5.149zM19.277 26.575l4.44 2.163-.594-5.149-3.846 2.986z" fill="#E27625" stroke="#E27625" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M23.717 28.738l-4.44-2.163.355 2.901-.04 1.224 4.125-1.962zM11.283 28.738l4.125 1.962-.025-1.224.34-2.901-4.44 2.163z" fill="#D5BFB2" stroke="#D5BFB2" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M15.47 21.792l-3.69-1.084 2.603-1.193 1.087 2.277zM19.53 21.792l1.087-2.277 2.618 1.193-3.705 1.084z" fill="#233447" stroke="#233447" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M11.283 28.738l.633-5.332-4.097.113 3.464 5.22zM23.084 23.406l.633 5.332 3.464-5.22-4.097-.112zM26.171 17.579l-7.381.337.686 3.876 1.087-2.277 2.618 1.193 2.99-3.129zM11.78 20.708l2.603-1.193 1.072 2.277.7-3.876-7.381-.337 3.006 3.129z" fill="#CC6228" stroke="#CC6228" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M8.829 17.579l3.1 6.047-.1-3.003-3-3.044zM23.186 20.623l-.115 3.003 3.1-6.047-2.985 3.044zM15.47 17.916l-.7 3.876.87 4.494.197-5.924-.367-2.446zM19.53 17.916l-.352 2.43.182 5.94.87-4.494-.7-3.876z" fill="#E27625" stroke="#E27625" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M20.23 21.792l-.87 4.494.625.44 3.846-2.986.115-3.003-3.716.055zM11.78 20.708l.1 3.003 3.845 2.986.625-.44-.855-4.494-3.715-.055z" fill="#F5841F" stroke="#F5841F" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M20.27 30.7l.04-1.224-.33-.284h-4.96l-.315.284.025 1.224-4.125-1.962 1.441 1.179 2.92 2.02h5.003l2.935-2.02 1.426-1.179-4.06 1.962z" fill="#C0AC9D" stroke="#C0AC9D" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M19.277 26.575l-.625-.44h-3.304l-.625.44-.34 2.901.315-.284h4.96l.33.284-.71-2.901z" fill="#161616" stroke="#161616" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M33.518 11.089l1.117-5.374L32.958 1 19.277 10.17l5.076 4.275 7.17 2.093 1.58-1.843-.685-.496 1.087-.99-.839-.65 1.087-.84-.235-.62zM.365 5.715L1.482 11.09l-.25.62 1.103.84-.84.65 1.088.99-.686.496 1.566 1.843 7.17-2.093 5.076-4.275L2.042 1 .365 5.715z" fill="#763E1A" stroke="#763E1A" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M31.523 16.538l-7.17-2.093 2.074 3.134-3.1 6.047 4.082-.056h6.101l-2.12-7.032h.133zM10.647 14.445l-7.17 2.093-2.105 7.032h6.086l4.082.056-3.1-6.047 2.207-3.134zM18.79 17.916l.455-7.746 2.09-5.654h-9.27l2.09 5.654.455 7.746.168 2.46.015 5.909h3.784l.015-5.909.198-2.46z" fill="#F5841F" stroke="#F5841F" strokeWidth=".25" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function Login() {
  const navigate = useNavigate();
  const {
    token,
    isConnected,
    walletAddress,
    login,
    setError,
    error,
    isLoading,
    needsRegistration,
    setNeedsRegistration,
    pendingApproval,
    setPendingApproval,
  } = useAuthStore();
  const [step, setStep] = useState(1);
  // regMode: null | "choice" | "faculty" | "institute"
  const [regMode, setRegMode] = useState(null);

  useEffect(() => {
    if (token && isConnected) navigate("/dashboard");
  }, [token, isConnected, navigate]);

  const handleConnectWallet = async () => {
    try {
      await web3Service.initialize();
      const address = await web3Service.connectWallet();
      useAuthStore.getState().setWalletAddress(address);
      setStep(2);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleSignAndLogin = async () => {
    try {
      setStep(3);
      const nonceResp = await fetch("/api/v1/auth/nonce", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet_address: walletAddress }),
      });
      if (!nonceResp.ok) throw new Error("Failed to fetch nonce");
      const { nonce, message } = await nonceResp.json();
      const signature = await web3Service.signMessage(message);
      const result = await login(walletAddress, signature, nonce);
      if (result) navigate("/dashboard");
      else if (useAuthStore.getState().needsRegistration) setRegMode("choice");
    } catch (err) {
      setError(err.message);
      setStep(2);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      <div className="absolute inset-0 bg-grid-pattern opacity-10" />

      <div className="relative sm:mx-auto sm:w-full sm:max-w-md">
        <div className="text-center mb-8">
          <div className="mx-auto w-20 h-20 bg-white rounded-2xl flex items-center justify-center shadow-lg">
            <CubeIcon className="h-12 w-12 text-primary-600" />
          </div>
          <h1 className="mt-6 text-4xl font-bold text-white">SALF</h1>
          <p className="mt-2 text-primary-200">Secure Academic Ledger Framework</p>
        </div>

        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10">
          <div className="space-y-6">
            <div className="grid grid-cols-2 gap-4 pb-6 border-b border-gray-200">
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <ShieldCheckIcon className="h-5 w-5 text-green-500" />
                <span>Blockchain Secured</span>
              </div>
              <div className="flex items-center space-x-2 text-sm text-gray-600">
                <AcademicCapIcon className="h-5 w-5 text-blue-500" />
                <span>UGC Compliant</span>
              </div>
            </div>

            <div className="space-y-4">
              {/* Step 1: Connect Wallet */}
              <div
                className={`p-4 rounded-lg border-2 transition-all ${
                  step === 1
                    ? "border-primary-500 bg-primary-50"
                    : "border-gray-200 bg-gray-50"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      step > 1
                        ? "bg-green-500 text-white"
                        : step === 1
                          ? "bg-primary-500 text-white"
                          : "bg-gray-300 text-gray-600"
                    }`}
                  >
                    {step > 1 ? "✓" : "1"}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Connect Wallet</p>
                    <p className="text-sm text-gray-500">Connect your MetaMask wallet</p>
                  </div>
                </div>

                {step === 1 && (
                  <button
                    onClick={handleConnectWallet}
                    disabled={isLoading}
                    className="mt-4 w-full btn-primary flex items-center justify-center space-x-2"
                  >
                    {isLoading ? (
                      <div className="loader" />
                    ) : (
                      <>
                        <MetaMaskIcon />
                        <span>Connect with MetaMask</span>
                      </>
                    )}
                  </button>
                )}

                {step > 1 && walletAddress && (
                  <div className="mt-3 px-3 py-2 bg-gray-100 rounded text-sm text-gray-600 font-mono truncate">
                    {walletAddress}
                  </div>
                )}
              </div>

              {/* Step 2: Sign Message */}
              <div
                className={`p-4 rounded-lg border-2 transition-all ${
                  step === 2
                    ? "border-primary-500 bg-primary-50"
                    : step > 2
                      ? "border-gray-200 bg-gray-50"
                      : "border-gray-200 bg-gray-50 opacity-50"
                }`}
              >
                <div className="flex items-center space-x-3">
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium ${
                      step > 2
                        ? "bg-green-500 text-white"
                        : step === 2
                          ? "bg-primary-500 text-white"
                          : "bg-gray-300 text-gray-600"
                    }`}
                  >
                    {step > 2 ? "✓" : "2"}
                  </div>
                  <div>
                    <p className="font-medium text-gray-900">Sign & Authenticate</p>
                    <p className="text-sm text-gray-500">Sign message to verify ownership</p>
                  </div>
                </div>

                {step === 2 && (
                  <button
                    onClick={handleSignAndLogin}
                    disabled={isLoading}
                    className="mt-4 w-full btn-primary flex items-center justify-center space-x-2"
                  >
                    {isLoading ? (
                      <div className="loader" />
                    ) : (
                      <>
                        <ShieldCheckIcon className="w-5 h-5" />
                        <span>Sign & Login</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {step === 3 && !needsRegistration && (
                <div className="p-4 rounded-lg border-2 border-primary-500 bg-primary-50">
                  <div className="flex items-center space-x-3">
                    <div className="loader" />
                    <p className="text-primary-700 font-medium">Authenticating...</p>
                  </div>
                </div>
              )}
            </div>

            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <p className="text-xs text-center text-gray-500">
              By connecting, you agree to the terms of service and privacy policy.
            </p>
          </div>
        </div>

        <p className="mt-8 text-center text-sm text-primary-200">
          Powered by Hyperledger Besu • IPFS • AI Evaluation
        </p>
      </div>

      {regMode === "choice" && walletAddress && (
        <RegistrationChoiceModal
          onFaculty={() => setRegMode("faculty")}
          onInstitute={() => setRegMode("institute")}
          onClose={() => { setRegMode(null); setNeedsRegistration(false); setStep(2); }}
        />
      )}

      {regMode === "faculty" && walletAddress && (
        <RegistrationModal
          walletAddress={walletAddress}
          onClose={() => { setRegMode(null); setNeedsRegistration(false); setStep(2); }}
        />
      )}

      {regMode === "institute" && walletAddress && (
        <InstituteRegistrationModal
          walletAddress={walletAddress}
          onClose={() => { setRegMode(null); setNeedsRegistration(false); setStep(2); }}
        />
      )}

      {pendingApproval && (
        <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
          <div className="fixed inset-0 bg-gray-900 bg-opacity-75" />
          <div className="relative bg-white rounded-2xl shadow-2xl max-w-sm w-full p-8 text-center z-10">
            <div className="mx-auto w-16 h-16 bg-yellow-100 rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-yellow-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h2 className="text-xl font-bold text-gray-900 mb-2">Awaiting Approval</h2>
            <p className="text-gray-500 text-sm mb-6">
              Your registration is pending admin approval. You will be able to log in once an administrator approves your account.
            </p>
            <button
              onClick={() => { setPendingApproval(false); setStep(2); }}
              className="btn-secondary w-full"
            >
              Back to Login
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

function RegistrationModal({ walletAddress, onClose }) {
  const [institutions, setInstitutions] = useState([]);
  const [departments, setDepartments] = useState([]);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formError, setFormError] = useState(null);
  const [form, setForm] = useState({
    name: "",
    email: "",
    employee_id: "",
    role: "faculty",
    designation: "",
    institution_id: "",
    department_code: "",
  });

  useEffect(() => {
    institutesAPI.list().then((r) => setInstitutions(r.data)).catch(() => {});
  }, []);

  const handleInstitutionChange = async (e) => {
    const id = e.target.value;
    setForm((f) => ({ ...f, institution_id: id, department_code: "" }));
    if (!id) { setDepartments([]); return; }
    try {
      const r = await institutesAPI.getDepartments(id);
      setDepartments(r.data);
    } catch {
      setDepartments([]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setFormError(null);
    setIsSubmitting(true);
    try {
      await authAPI.register({
        wallet_address: walletAddress,
        name: form.name,
        email: form.email || undefined,
        employee_id: form.employee_id || undefined,
        role: form.role,
        designation: form.designation || undefined,
        institution_id: parseInt(form.institution_id),
        department_code: form.department_code,
      });

      // Auto-login: get a fresh nonce and re-sign
      // We can't re-sign without MetaMask — just close and ask user to sign again
      onClose();
      // Brief delay then trigger sign+login again
      setTimeout(() => {
        window.location.reload();
      }, 500);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setFormError(
        Array.isArray(detail) ? detail[0]?.msg : detail || err.message
      );
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 py-8">
        <div className="fixed inset-0 bg-gray-900 bg-opacity-75" onClick={onClose} />
        <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 z-10">
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-900">Complete Registration</h2>
            <p className="mt-1 text-sm text-gray-500">
              Your wallet is not registered yet. Fill in your details to create an account.
            </p>
            <div className="mt-2 px-3 py-2 bg-gray-100 rounded text-xs text-gray-500 font-mono truncate">
              {walletAddress}
            </div>
          </div>

          {formError && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-600">
              {formError}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Full Name *</label>
              <input
                type="text"
                required
                value={form.name}
                onChange={(e) => setForm({ ...form, name: e.target.value })}
                className="input"
                placeholder="Dr. Jane Smith"
              />
            </div>

            <div>
              <label className="label">Email</label>
              <input
                type="email"
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="input"
                placeholder="jane.smith@university.edu"
              />
            </div>

            <div>
              <label className="label">Employee ID</label>
              <input
                type="text"
                value={form.employee_id}
                onChange={(e) => setForm({ ...form, employee_id: e.target.value })}
                className="input"
                placeholder="EMP001"
              />
            </div>

            <div>
              <label className="label">Role *</label>
              <select
                required
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="input"
              >
                <option value="faculty">Faculty</option>
                <option value="hod">Head of Department (HoD)</option>
              </select>
            </div>

            <div>
              <label className="label">Designation *</label>
              <select
                required
                value={form.designation}
                onChange={(e) => setForm({ ...form, designation: e.target.value })}
                className="input"
              >
                <option value="">Select designation...</option>
                <option value="professor">Professor</option>
                <option value="associate_professor">Associate Professor</option>
                <option value="assistant_professor">Assistant Professor</option>
                <option value="staff">Staff</option>
              </select>
            </div>

            <div>
              <label className="label">Institution *</label>
              <select
                required
                value={form.institution_id}
                onChange={handleInstitutionChange}
                className="input"
              >
                <option value="">Select institution...</option>
                {institutions.map((inst) => (
                  <option key={inst.id} value={inst.id}>
                    {inst.name}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="label">Department *</label>
              <select
                required
                value={form.department_code}
                onChange={(e) => setForm({ ...form, department_code: e.target.value })}
                className="input"
                disabled={!form.institution_id || departments.length === 0}
              >
                <option value="">
                  {form.institution_id
                    ? departments.length === 0
                      ? "No departments available"
                      : "Select department..."
                    : "Select institution first"}
                </option>
                {departments.map((dept) => (
                  <option key={dept.id} value={dept.code}>
                    {dept.name} ({dept.code})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex justify-end space-x-3 pt-2">
              <button type="button" onClick={onClose} className="btn-secondary">
                Cancel
              </button>
              <button type="submit" disabled={isSubmitting} className="btn-primary">
                {isSubmitting ? <div className="loader" /> : "Register & Continue"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

function RegistrationChoiceModal({ onFaculty, onInstitute, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
      <div className="fixed inset-0 bg-gray-900 bg-opacity-75" onClick={onClose} />
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-sm w-full p-8 z-10">
        <h2 className="text-xl font-bold text-gray-900 mb-2">Create Account</h2>
        <p className="text-sm text-gray-500 mb-6">How would you like to register?</p>
        <div className="space-y-3">
          <button
            onClick={onInstitute}
            className="w-full flex items-center p-4 rounded-xl border-2 border-gray-200 text-left transition-all hover:border-primary-400"
          >
            <BuildingLibraryIcon className="h-8 w-8 text-primary-600 mr-4 shrink-0" />
            <div>
              <p className="font-semibold text-gray-900">Register my Institution</p>
              <p className="text-xs text-gray-500">I'm an admin setting up a new institution</p>
            </div>
          </button>
          <button
            onClick={onFaculty}
            className="w-full flex items-center p-4 rounded-xl border-2 border-gray-200 text-left transition-all hover:border-primary-400"
          >
            <UserGroupIcon className="h-8 w-8 text-green-600 mr-4 shrink-0" />
            <div>
              <p className="font-semibold text-gray-900">I'm Faculty / HoD</p>
              <p className="text-xs text-gray-500">Join an existing institution</p>
            </div>
          </button>
        </div>
        <button onClick={onClose} className="mt-4 w-full btn-secondary text-sm">Cancel</button>
      </div>
    </div>
  );
}

function InstituteRegistrationModal({ walletAddress, onClose }) {
  const [form, setForm] = useState({
    name: "",
    email: "",
    institution_code: "",
    institution_name: "",
  });
  const [error, setError] = useState(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setIsSubmitting(true);
    try {
      await authAPI.registerInstitute({
        wallet_address: walletAddress,
        name: form.name,
        email: form.email || undefined,
        institution_code: form.institution_code,
        institution_name: form.institution_name,
      });
      onClose();
      setTimeout(() => window.location.reload(), 300);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(Array.isArray(detail) ? detail[0]?.msg : detail || err.message);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto">
      <div className="flex items-center justify-center min-h-screen px-4 py-8">
        <div className="fixed inset-0 bg-gray-900 bg-opacity-75" onClick={onClose} />
        <div className="relative bg-white rounded-2xl shadow-2xl max-w-md w-full p-6 z-10">
          <div className="flex items-center mb-4">
            <BuildingLibraryIcon className="h-7 w-7 text-primary-600 mr-3" />
            <div>
              <h2 className="text-xl font-bold text-gray-900">Register Institution</h2>
              <p className="text-xs text-gray-500">Pending master admin approval</p>
            </div>
          </div>

          <div className="mb-4 px-3 py-2 bg-gray-100 rounded text-xs text-gray-500 font-mono truncate">
            {walletAddress}
          </div>

          {error && (
            <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-600">{error}</div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="label">Your Full Name *</label>
              <input required value={form.name} onChange={(e) => setForm({ ...form, name: e.target.value })} className="input" placeholder="Dr. Jane Smith" />
            </div>
            <div>
              <label className="label">Your Email</label>
              <input type="email" value={form.email} onChange={(e) => setForm({ ...form, email: e.target.value })} className="input" />
            </div>
            <hr className="border-gray-200" />
            <div>
              <label className="label">Institution Code *</label>
              <input required value={form.institution_code} onChange={(e) => setForm({ ...form, institution_code: e.target.value.toUpperCase() })} className="input uppercase" placeholder="MIT" maxLength={20} />
              <p className="text-xs text-gray-400 mt-1">Short unique identifier (e.g. MSRIT, IIT-B)</p>
            </div>
            <div>
              <label className="label">Institution Full Name *</label>
              <input required value={form.institution_name} onChange={(e) => setForm({ ...form, institution_name: e.target.value })} className="input" placeholder="Massachusetts Institute of Technology" />
            </div>
            <div className="flex justify-end space-x-3 pt-2">
              <button type="button" onClick={onClose} className="btn-secondary">Cancel</button>
              <button type="submit" disabled={isSubmitting} className="btn-primary">
                {isSubmitting ? <div className="loader" /> : "Submit for Approval"}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}

export default Login;
