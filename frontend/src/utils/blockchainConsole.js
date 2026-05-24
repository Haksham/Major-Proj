/**
 * Demo-friendly: log a fresh random 66-char hex id on each blockchain-related UI event.
 * If the API returned a real hash, it is included for reference.
 */
export function logBlockchainConsoleEvent(eventLabel, onChainTxHash = null) {
  const bytes = new Uint8Array(32);
  crypto.getRandomValues(bytes);
  const randomId =
    "0x" +
    Array.from(bytes, (b) => b.toString(16).padStart(2, "0")).join("");
  if (onChainTxHash) {
    console.log(
      `[SALF blockchain] ${eventLabel} transaction_id=${randomId} on_chain_tx=${onChainTxHash}`,
    );
  } else {
    console.log(`[SALF blockchain] ${eventLabel} transaction_id=${randomId}`);
  }
}
