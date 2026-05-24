/**
 * RPC / Hardhat / viem traces label the simulated sender as "From:".
 * Surface "Transaction ID" wording; keep signer separate when no hash exists (typical for eth_call).
 */
export function sanitizeLedgerConsoleText(s) {
  if (typeof s !== "string" || !s) return s;

  let out = s;

  const txHash = out.match(/\b(0x[a-fA-F0-9]{64})\b/)?.[1];
  const fromWallet = out.match(/\bFrom:\s*(0x[a-fA-F0-9]{40})\b/i)?.[1];

  if (txHash && fromWallet) {
    out = out.replace(/\bFrom:\s*0x[a-fA-F0-9]{40}\b/i, `Transaction ID: ${txHash}`);
  } else if (fromWallet) {
    out = out.replace(
      /\bFrom:\s*0x[a-fA-F0-9]{40}\b/i,
      `Transaction ID: —\nSigner: ${fromWallet}`,
    );
  } else {
    out = out.replace(/\bFrom:\s*/gi, "Transaction ID: ");
  }

  out = out.replace(
    /TransactionExecutionError:\s*StackOverflow\b/gi,
    "TransactionExecutionError: stack overflow during simulation",
  );

  return out;
}

/**
 * Short UI-safe message derived from ethers / RPC errors.
 */
export function formatWalletError(err) {
  if (!err) return "Something went wrong.";

  const raw =
    (typeof err === "string" ? err : null) ||
    err.shortMessage ||
    err.message ||
    String(err);

  const cleaned = sanitizeLedgerConsoleText(raw);
  const oneLine = cleaned
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter(Boolean)
    .join(" — ");

  return oneLine.slice(0, 400);
}
