import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import "./index.css";
import { sanitizeLedgerConsoleText } from "./utils/formatWalletError";

["error", "warn"].forEach((method) => {
  const orig = console[method].bind(console);
  console[method] = (...args) => {
    orig(
      ...args.map((a) => (typeof a === "string" ? sanitizeLedgerConsoleText(a) : a)),
    );
  };
});

// Dev chains often emit huge RPC traces — quiet the noisiest unhandled viem-style rejections.
window.addEventListener("unhandledrejection", (event) => {
  const r = event.reason;
  const s = typeof r?.message === "string" ? r.message : String(r ?? "");
  if (/TransactionExecutionError/i.test(s) && /StackOverflow/i.test(s)) {
    event.preventDefault();
  }
});

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>,
);
