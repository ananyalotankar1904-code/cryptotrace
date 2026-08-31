# Crypto Trace (frontend, Phase 1–4)

Demonstration dashboard for a Law Enforcement Agency investigator workflow.
This app uses **mock data only**. It does not call a blockchain, backend, or VASP service.

## Run locally

```bash
cd CryptoTrace
npm install
npm run dev
```

Open the URL printed in the terminal (usually `http://localhost:5173`).

## Current mock-data flow

1. The investigator enters an address (or clicks **Try Demo Investigation**).
2. `src/pages/Dashboard.jsx` calls `traceWallet()` from `src/services/api.js`.
3. `traceWallet()` waits briefly, then returns data from `src/data/mockData.js`.
4. The dashboard renders summary cards, VASP/risk panels, and a transaction table.

Later, only `src/services/api.js` should need to change when a real backend is ready.
