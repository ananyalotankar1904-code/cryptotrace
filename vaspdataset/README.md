# VASP Intelligence Dataset - Ethereum Seed Labels

## Deliverables

- `vasp_intelligence_addresses.csv`: flat, backend-friendly rows.
- `vasp_intelligence_addresses.json`: the same rows in an API-friendly envelope.
- `VASP_Intelligence_Dataset.xlsx`: reviewer-friendly workbook with Addresses, Rules, Confidence, Sources, and Limitations sheets.
- `attribution_rules.json`: machine-readable match policy and confidence categories.

## Evidence method

Every seed address has a direct public Etherscan address-page URL that explicitly labels the address with the exchange entity. `source_date` is null because the respective public label pages do not publish a label publication date; `source_checked_date` records the retrieval date. The dataset uses `known_verified` only for these explicit public labels.

## Confidence policy

`high` means an exact Ethereum address match to an active seed record with explicit source evidence. It does not mean the address identifies a particular person, customer account, or criminal. `medium` and `low` are reserved for separately collected indirect evidence; no such heuristic-only address is included in this seed dataset.

## Important limitations

1. Public explorer labels can change, be incomplete, or lag an exchange's wallet rotation. Refresh before production or legal use.
2. A VASP attribution identifies the service, not the owner of a customer account. Customer identity requires a lawful request to the VASP.
3. The dataset covers Ethereum only and is intentionally small. Do not reuse an address label across chains without chain-specific evidence.
4. Exact matching alone misses unlabeled deposit addresses, routing contracts, bridges, and new wallets.
5. Heuristic clustering is investigative lead generation, not verification. Keep its evidence, method, timestamps, and confidence separate from source-backed labels.
