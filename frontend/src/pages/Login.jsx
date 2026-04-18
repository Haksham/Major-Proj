import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../store";
import { web3Service } from "../services/web3";
import {
  CubeIcon,
  ShieldCheckIcon,
  AcademicCapIcon,
} from "@heroicons/react/24/outline";

function Login() {
  const navigate = useNavigate();
  const {
    token,
    isConnected,
    walletAddress,
    connectWallet,
    login,
    setError,
    error,
    isLoading,
  } = useAuthStore();
  const [step, setStep] = useState(1); // 1: Connect, 2: Sign, 3: Authenticating

  useEffect(() => {
    if (token && isConnected) {
      navigate("/dashboard");
    }
  }, [token, isConnected, navigate]);

  const handleConnectWallet = async () => {
    try {
      await web3Service.initialize();
      const address = await web3Service.connectWallet();

      // Update store with wallet address
      useAuthStore.getState().setWalletAddress(address);
      setStep(2);
    } catch (error) {
      console.error("Failed to connect wallet:", error);
      setError(error.message);
    }
  };

  const handleSignAndLogin = async () => {
    try {
      setStep(3);

      // 1) Get nonce + message from backend
      const nonceResp = await fetch("/api/v1/auth/nonce", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ wallet_address: walletAddress }),
      });
      if (!nonceResp.ok) {
        throw new Error("Failed to fetch nonce");
      }
      const { nonce, message } = await nonceResp.json();

      // 2) Sign message with MetaMask
      const signature = await web3Service.signMessage(message);

      // 3) Login with backend (send nonce + signature)
      await login(walletAddress, signature, nonce);

      navigate("/dashboard");
    } catch (error) {
      console.error("Failed to sign and login:", error);
      setError(error.message);
      setStep(2);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-600 via-primary-700 to-primary-900 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Background pattern */}
      <div className="absolute inset-0 bg-grid-pattern opacity-10" />

      <div className="relative sm:mx-auto sm:w-full sm:max-w-md">
        {/* Logo and title */}
        <div className="text-center mb-8">
          <div className="mx-auto w-20 h-20 bg-white rounded-2xl flex items-center justify-center shadow-lg">
            <CubeIcon className="h-12 w-12 text-primary-600" />
          </div>
          <h1 className="mt-6 text-4xl font-bold text-white">SALF</h1>
          <p className="mt-2 text-primary-200">
            Secure Academic Ledger Framework
          </p>
        </div>

        {/* Login card */}
        <div className="bg-white py-8 px-6 shadow-xl rounded-2xl sm:px-10">
          <div className="space-y-6">
            {/* Features */}
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

            {/* Connection steps */}
            <div className="space-y-4">
              {/* Step 1: Connect Wallet */}
              <div
                className={`p-4 rounded-lg border-2 transition-all ${
                  step === 1
                    ? "border-primary-500 bg-primary-50"
                    : "border-gray-200 bg-gray-50"
                }`}
              >
                <div className="flex items-center justify-between">
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
                      <p className="font-medium text-gray-900">
                        Connect Wallet
                      </p>
                      <p className="text-sm text-gray-500">
                        Connect your MetaMask wallet
                      </p>
                    </div>
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
                        <img
                          src="/metamask.svg"
                          alt="MetaMask"
                          className="w-5 h-5"
                        />
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
                <div className="flex items-center justify-between">
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
                      <p className="font-medium text-gray-900">
                        Sign & Authenticate
                      </p>
                      <p className="text-sm text-gray-500">
                        Sign message to verify ownership
                      </p>
                    </div>
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

              {/* Step 3: Authenticating */}
              {step === 3 && (
                <div className="p-4 rounded-lg border-2 border-primary-500 bg-primary-50">
                  <div className="flex items-center space-x-3">
                    <div className="loader" />
                    <p className="text-primary-700 font-medium">
                      Authenticating...
                    </p>
                  </div>
                </div>
              )}
            </div>

            {/* Error message */}
            {error && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            {/* Help text */}
            <p className="text-xs text-center text-gray-500">
              By connecting, you agree to the terms of service and privacy
              policy. Your wallet address will be used for authentication only.
            </p>
          </div>
        </div>

        {/* Footer */}
        <p className="mt-8 text-center text-sm text-primary-200">
          Powered by Hyperledger Besu • IPFS • AI Evaluation
        </p>
      </div>
    </div>
  );
}

export default Login;
