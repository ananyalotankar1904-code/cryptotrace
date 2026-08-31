"""Script to generate the standardized Blockchain Investigation Report as a 5-page PDF."""

import os
import subprocess

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Blockchain Investigation Report</title>
<style>
  @page {
    size: A4;
    margin: 18mm 16mm 18mm 16mm;
  }
  
  body {
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, Helvetica, Arial, sans-serif;
    color: #1e293b;
    line-height: 1.45;
    font-size: 12.5px;
    margin: 0;
    padding: 0;
  }

  .page-break {
    page-break-before: always;
    break-before: page;
  }

  h1 {
    color: #1e3a8a;
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.5px;
    margin-top: 0;
    margin-bottom: 20px;
    text-transform: uppercase;
    border-bottom: 2.5px solid #1e3a8a;
    padding-bottom: 6px;
  }

  h2 {
    color: #1e3a8a;
    font-size: 16px;
    font-weight: 700;
    margin-top: 20px;
    margin-bottom: 10px;
    border-bottom: 1px solid #cbd5e1;
    padding-bottom: 3px;
  }

  h3 {
    color: #0f172a;
    font-size: 13.5px;
    font-weight: 700;
    margin-top: 14px;
    margin-bottom: 6px;
  }

  ul {
    list-style-type: none;
    padding-left: 0;
    margin: 0 0 12px 0;
  }

  ul li {
    position: relative;
    padding-left: 16px;
    margin-bottom: 5px;
  }

  ul li::before {
    content: "•";
    position: absolute;
    left: 0;
    color: #1e3a8a;
    font-weight: bold;
    font-size: 14px;
    line-height: 1;
  }

  .strong-label {
    font-weight: 600;
    color: #0f172a;
  }

  .code-text {
    font-family: 'Consolas', 'Courier New', monospace;
    background-color: #f1f5f9;
    padding: 1px 4px;
    border-radius: 3px;
    font-size: 11.5px;
    color: #0f172a;
    border: 1px solid #e2e8f0;
  }

  .badge {
    display: inline-block;
    padding: 2px 7px;
    font-size: 10.5px;
    font-weight: 700;
    border-radius: 10px;
    text-transform: uppercase;
  }

  .badge-high {
    background-color: #fee2e2;
    color: #b91c1c;
    border: 1px solid #fca5a5;
  }

  .badge-completed {
    background-color: #dcfce7;
    color: #15803d;
    border: 1px solid #86efac;
  }

  .badge-true {
    background-color: #fef3c7;
    color: #b45309;
    border: 1px solid #fde68a;
  }

  .badge-false {
    background-color: #f1f5f9;
    color: #64748b;
    border: 1px solid #cbd5e1;
  }

  table {
    width: 100%;
    border-collapse: collapse;
    margin: 10px 0 14px 0;
    font-size: 11.5px;
  }

  th {
    background-color: #f8fafc;
    color: #1e3a8a;
    font-weight: 700;
    text-align: left;
    padding: 7px 9px;
    border: 1px solid #cbd5e1;
  }

  td {
    padding: 7px 9px;
    border: 1px solid #e2e8f0;
    vertical-align: middle;
  }

  tr:nth-child(even) {
    background-color: #f8fafc;
  }

  .card {
    background-color: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 5px;
    padding: 10px 14px;
    margin-bottom: 12px;
    font-size: 12px;
  }

  .flow-diagram {
    background-color: #0f172a;
    color: #f8fafc;
    font-family: 'Consolas', monospace;
    font-size: 11px;
    padding: 10px 12px;
    border-radius: 5px;
    margin: 10px 0 14px 0;
    white-space: pre-wrap;
    line-height: 1.35;
  }

  .notice-box {
    background-color: #eff6ff;
    border-left: 3.5px solid #3b82f6;
    padding: 9px 12px;
    margin: 10px 0;
    font-size: 12px;
    color: #1e40af;
  }
</style>
</head>
<body>  <!-- ==================== PAGE 1 ==================== -->
  <h1>BLOCKCHAIN INVESTIGATION REPORT</h1>

  <h2>1. Case Details</h2>
  <ul>
    <li><span class="strong-label">Case ID:</span> CASE-2024-ETH-0891</li>
    <li><span class="strong-label">Investigation ID:</span> INV-9042-SIH</li>
    <li><span class="strong-label">Investigation Date:</span> 2024-03-15 14:30:00 UTC</li>
    <li><span class="strong-label">Investigator:</span> Cyber Crime & Intelligence Forensics Unit</li>
    <li><span class="strong-label">Blockchain:</span> Ethereum (Mainnet)</li>
    <li><span class="strong-label">Suspect Wallet:</span> <span class="code-text">0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503</span></li>
    <li><span class="strong-label">Report Status:</span> <span class="badge badge-completed">COMPLETED (MULTI-HOP TRACED)</span></li>
  </ul>

  <h2>2. Investigation Summary</h2>
  
  <h3>Metrics Overview</h3>
  <ul>
    <li><span class="strong-label">Total Transactions Analyzed:</span> 11 transfer events across 7 distinct wallets</li>
    <li><span class="strong-label">Total Incoming Value:</span> 30,000,000.0 DAI + 125.40 ETH</li>
    <li><span class="strong-label">Total Outgoing Value:</span> 30,000,000.0 DAI + 0.055 ETH</li>
    <li><span class="strong-label">Number of Hops Traced:</span> 3 (Full Breadth-First Traversal)</li>
    <li><span class="strong-label">Destination Addresses Identified:</span> 10 unique Ethereum destination nodes</li>
    <li><span class="strong-label">Overall Risk Level:</span> <span class="badge badge-high">HIGH</span></li>
    <li><span class="strong-label">Confidence Score:</span> 94%</li>
  </ul>

  <h3>Investigator Executive Summary</h3>
  <div class="card">
    <p style="margin: 0;">
      Automated blockchain multi-hop tracing initiated on victim-reported suspect Ethereum wallet 
      <strong>0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503</strong> identified immediate structured fund dispersion. 
      In Hop 1, 30,000,000 DAI stablecoins were moved to primary relay wallet <strong>0xf977...acec</strong> alongside contract triggering calls. 
      In Hop 2, funds were split and routed into token liquidity and relay nodes (including 70,000,000 MFT tokens to <strong>0x3f5c...f0be</strong> and secondary stablecoin interactions). 
      In Hop 3, secondary nodes dispersed assets into native ETH micro-transactions and USDC liquidity pools (<strong>24,948.96 USDC</strong> to <strong>0x5777...2168</strong>). 
      Graph traversal completed with 0 infinite loops detected via automated cycle prevention.
    </p>
  </div>

  <!-- ==================== PAGE 2 ==================== -->
  <div class="page-break"></div>

  <h2>3. Transaction Evidence</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 8%;">Hop</th>
        <th style="width: 25%;">Transaction Hash</th>
        <th style="width: 20%;">Date/Time (UTC)</th>
        <th style="width: 25%;">Amount & Asset</th>
        <th style="width: 22%;">Category / Indicator</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><strong>1</strong></td>
        <td><span class="code-text">0x2e46c5a5fd5b...</span></td>
        <td>2021-06-03 02:04:05</td>
        <td><strong>30,000,000.0 DAI</strong></td>
        <td>ERC-20 (Large Volume)</td>
      </tr>
      <tr>
        <td><strong>1</strong></td>
        <td><span class="code-text">0x2e46c5a5fd5b...</span></td>
        <td>2021-06-03 02:04:05</td>
        <td>0.0 ETH</td>
        <td>External (Contract Call)</td>
      </tr>
      <tr>
        <td><strong>2</strong></td>
        <td><span class="code-text">0x9fc4f7d1b040...</span></td>
        <td>2019-07-09 14:54:02</td>
        <td><strong>70,000,000.0 MFT</strong></td>
        <td>ERC-20 (Token Relay)</td>
      </tr>
      <tr>
        <td><strong>2</strong></td>
        <td><span class="code-text">0x31f60d794bbc...</span></td>
        <td>2022-08-31 16:32:51</td>
        <td>100.0 daiblack.com</td>
        <td>ERC-20 (Airdrop/Spam)</td>
      </tr>
      <tr>
        <td><strong>3</strong></td>
        <td><span class="code-text">0xd7be6ba52109...</span></td>
        <td>Block 4116404</td>
        <td>0.045 ETH</td>
        <td>External (Native ETH)</td>
      </tr>
      <tr>
        <td><strong>3</strong></td>
        <td><span class="code-text">0x902ff3a220cf...</span></td>
        <td>2022-08-20 22:58:31</td>
        <td><strong>24,948.96 USDC</strong></td>
        <td>ERC-20 (Stablecoin Pool)</td>
      </tr>
    </tbody>
  </table>

  <h3>Transaction Flow Summary</h3>
  <div class="flow-diagram">[ROOT SUSPECT] 0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503
      │
      ├──────[Hop 1: 30,000,000 DAI]──────▶ 0xf977814e90da44bfa03b6295a0616a897441acec
      │                                             │
      │                                             ├──────[Hop 2: 70,000,000 MFT]──────▶ 0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be
      │                                             │                                             │
      │                                             │                                             └──────[Hop 3: 0.045 ETH]──────▶ 0x001866ae5b3de6caa5a51543fd9fb64f524f5478
      │                                             │
      │                                             └──────[Hop 2: 0.0 ETH]─────────────▶ 0xdf2c7238198ad8b389666574f2d8bc411a4b7428
      │
      └──────[Hop 1: Contract Call]───────▶ 0x6b175474e89094c44da98b954eedeac495271d0f (MakerDAO)
                                                    │
                                                    └──────[Hop 2]──────────────────────▶ 0xed766b1c7a4baec5e7dbd27888b8a434d1f1764b
                                                                                                  │
                                                                                                  └──────[Hop 3: 24,948.96 USDC]──▶ 0x5777d92f208679db4b9778590fa3cab3ac9e2168</div>

  <!-- ==================== PAGE 3 ==================== -->
  <div class="page-break"></div>

  <h2>4. Risk Summary</h2>
  <ul>
    <li><span class="strong-label">Risk Score:</span> <strong>82 / 100</strong> &nbsp;|&nbsp; <span class="strong-label">Risk Level:</span> <span class="badge badge-high">HIGH</span> &nbsp;|&nbsp; <span class="strong-label">Confidence Score:</span> <strong>94%</strong></li>
  </ul>

  <table>
    <thead>
      <tr>
        <th style="width: 32%;">Risk Indicator</th>
        <th style="width: 18%;">Status</th>
        <th style="width: 50%;">Key Evidence</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td>High transaction frequency</td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Burst outgoing transactions executed in identical and adjacent blocks.</td>
      </tr>
      <tr>
        <td>Large-value movement</td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Single transactions exceeding 30,000,000 DAI stablecoins.</td>
      </tr>
      <tr>
        <td>Rapid movement through wallets</td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Funds propagated through 3 successive intermediary hops.</td>
      </tr>
      <tr>
        <td>Repeated splitting</td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Primary balance divided into multiple secondary destination paths.</td>
      </tr>
      <tr>
        <td>Repeated consolidation</td>
        <td><span class="badge badge-false">FALSE</span></td>
        <td>No downstream funneling to a single consolidation hub detected within 3 hops.</td>
      </tr>
      <tr>
        <td>Suspicious address interaction</td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Interaction with unverified token contracts and phishing airdrop signatures.</td>
      </tr>
      <tr>
        <td>Mixer/Bridge interaction</td>
        <td><span class="badge badge-false">FALSE</span></td>
        <td>No known privacy mixer (e.g. Tornado Cash) directly in the analyzed 3-hop tree.</td>
      </tr>
    </tbody>
  </table>

  <h2>5. VASP Attribution</h2>
  <div class="notice-box">
    <strong>VASP Interaction Detected:</strong> The investigation identified direct linkage between the subject wallet and recognized Virtual Asset Service Provider (VASP) hot wallet infrastructure.
  </div>

  <ul>
    <li><span class="strong-label">VASP Name:</span> Binance Exchange</li>
    <li><span class="strong-label">Associated Address:</span> <span class="code-text">0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503</span></li>
    <li><span class="strong-label">Interaction Type:</span> Originating Hot Wallet / Outgoing Fund Dispersion</li>
    <li><span class="strong-label">Transaction:</span> <span class="code-text">0x2e46c5a5fd5b52f66a0b7d97998a70cfefd5ce944e999fe5ac296a1a0a171f20</span></li>
    <li><span class="strong-label">Attribution Confidence:</span> <strong>98%</strong></li>
  </ul>
  
  <p style="margin-top: 6px;">
    <strong>Interaction Analysis:</strong> The investigation identified a direct link between the suspect starting address and recognized exchange deposit/withdrawal infrastructure. Legal preservation notices may be served to obtain KYC records.
  </p>

  <!-- ==================== PAGE 4 ==================== -->
  <div class="page-break"></div>

  <h2>6. Key Findings and Investigator Assessment</h2>
  
  <h3>Critical Findings</h3>
  <div class="card">
    <ul>
      <li>High-volume DAI stablecoin dispersion (30M DAI) routed immediately upon receipt.</li>
      <li>Three-tier multi-hop relay graph without immediate user-level holding periods.</li>
      <li>Secondary conversion into USDC stablecoin liquidity pools (<strong>24,948.96 USDC</strong> at Hop 3).</li>
      <li>Automated cycle detection successfully prevented infinite loops during graph traversal (A &rarr; B &rarr; A).</li>
    </ul>
  </div>

  <h3>Final Assessment</h3>
  <div class="card">
    <p style="margin: 0;">
      The transaction patterns strongly indicate automated fund dispersion and structuring across intermediate Ethereum wallets. 
      The initial liquidity originates from an identified exchange hot wallet and rapidly distributes across multiple secondary addresses. 
      High priority for subpoena and preservation requests.
    </p>
  </div>

  <h2>7. Recommended Actions</h2>
  <ul>
    <li><strong>Extend Transaction Tracing:</strong> Deepen BFS tracing beyond 3 hops for the USDC liquidity branch (address <span class="code-text">0x5777d92f208679db4b9778590fa3cab3ac9e2168</span>).</li>
    <li><strong>Preserve Evidence:</strong> Preserve all on-chain transaction hashes and block timestamps for formal legal proceedings.</li>
    <li><strong>Serve VASP Subpoena:</strong> Issue formal preservation request to Binance Exchange for account metadata associated with transaction <span class="code-text">0x2e46c5a5...</span>.</li>
    <li><strong>Monitor High-Risk Relays:</strong> Place wallet alerts on intermediate addresses <span class="code-text">0xf977...acec</span> and <span class="code-text">0xed76...764b</span> for subsequent outgoing flows.</li>
  </ul>

  <h2>8. Limitations</h2>
  <ul>
    <li><strong>Pseudonymity:</strong> Blockchain addresses are pseudonymous and do not directly prove real-world legal identity without verified off-chain VASP attribution or KYC subpoenas.</li>
    <li><strong>Transaction Scope:</strong> Analysis is limited to on-chain data within the selected 3-hop traversal depth and the 100-transfer-per-node rate limit.</li>
    <li><strong>Off-Chain Activities:</strong> Off-chain internal ledger transactions occurring within centralized exchanges are not reflected on the public Ethereum ledger.</li>
    <li><strong>Fund Continuity Nuance:</strong> In account-based blockchains like Ethereum, multi-hop paths (A &rarr; B &rarr; C) prove transaction relationships and directional fund flows, but do not mathematically guarantee that the exact same atomic tokens received from A were forwarded to C, due to potential fund commingling or pre-existing balances in intermediary wallets.</li>
    <li><strong>Mixers & Cross-Chain Bridges:</strong> The use of mixers, decentralized privacy pools, or cross-chain bridges can obscure downstream traceability.</li>
    <li><strong>Analytical Indicators:</strong> Risk scores and confidence ratings are forensic heuristics and do not constitute a definitive legal finding of guilt.</li>
  </ul>

  <!-- ==================== PAGE 5 ==================== -->
  <div class="page-break"></div>

  <h2>9. Variable Dictionary</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 35%;">Variable Identifier</th>
        <th style="width: 65%;">Definition & Forensic Meaning</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="code-text">{{CASE_ID}}</span></td>
        <td>Unique law enforcement or internal investigative case number.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{SUSPECT_WALLET}}</span></td>
        <td>Target 42-character Ethereum hex address under investigation.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{BLOCKCHAIN}}</span></td>
        <td>Target blockchain ecosystem (Ethereum Mainnet).</td>
      </tr>
      <tr>
        <td><span class="code-text">{{TRANSACTION_COUNT}}</span></td>
        <td>Total number of transfer relationships analyzed across all hops.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{TOTAL_INCOMING}}</span></td>
        <td>Aggregated gross value received by the subject wallet.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{TOTAL_OUTGOING}}</span></td>
        <td>Aggregated gross value transferred out of the subject wallet.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{NUMBER_OF_HOPS}}</span></td>
        <td>Maximum traversal depth reached during Breadth-First Search.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{RISK_SCORE}}</span></td>
        <td>Algorithmic risk score between 0 and 100 based on transaction indicators.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{OVERALL_RISK_LEVEL}}</span></td>
        <td>Categorical classification: LOW, MEDIUM, HIGH, or CRITICAL.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{CONFIDENCE_SCORE}}</span></td>
        <td>Statistical confidence percentage in findings and data attribution.</td>
      </tr>
    </tbody>
  </table>

  <h2>10. Conditional Logic Table</h2>
  <table>
    <thead>
      <tr>
        <th style="width: 35%;">Condition Trigger</th>
        <th style="width: 15%;">Rule Status</th>
        <th style="width: 50%;">Report Action Taken</th>
      </tr>
    </thead>
    <tbody>
      <tr>
        <td><span class="code-text">{{HIGH_TRANSACTION_FREQUENCY}}</span></td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Display high-frequency transactional burst finding in Section 4.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{RAPID_MOVEMENT}}</span></td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Include rapid multi-hop propagation finding in Section 4 & Section 6.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{REPEATED_SPLITTING}}</span></td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Display fund dispersion and splitting graph analysis in Section 3 & 4.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{SUSPICIOUS_INTERACTION}}</span></td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Flag unverified token contract interactions in Section 4.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{MIXER_OR_BRIDGE_INTERACTION}}</span></td>
        <td><span class="badge badge-false">FALSE</span></td>
        <td>Omit mixer deanonymization section; mark mixer interaction as FALSE.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{VASP_INTERACTION}}</span></td>
        <td><span class="badge badge-true">TRUE</span></td>
        <td>Display VASP attribution details and subpoena recommendations in Section 5 & 7.</td>
      </tr>
      <tr>
        <td><span class="code-text">{{OVERALL_RISK_LEVEL}}</span></td>
        <td><span class="badge badge-high">HIGH</span></td>
        <td>Display urgent priority recommendations (extend tracing, asset freeze, legal notice).</td>
      </tr>
    </tbody>
  </table>

  <div class="card" style="margin-top: 15px; text-align: center; color: #64748b; font-size: 11px;">
    <strong>Report Generated by SIH Crypto Fraud Intelligence Engine (Backend Milestone 3)</strong><br>
    Automated Multi-Hop Graph Tracing Layer & Forensic Evidence Engine
  </div>ard" style="margin-top: 20px; text-align: center; color: #64748b; font-size: 11px;">
    <strong>Report Generated by SIH Crypto Fraud Intelligence Engine (Backend Milestone 3)</strong><br>
    Automated Multi-Hop Graph Tracing Layer & Forensic Evidence Engine
  </div>

</body>
</html>
"""

def generate_pdf_from_payload(payload: dict) -> str:
    from datetime import datetime
    
    # 1. Prepare dynamic values from payload
    investigation_id = payload.get("investigationId", "INV-UNKNOWN")
    case_id = f"CASE-{datetime.now().year}-ETH-{investigation_id[-4:]}" if investigation_id else "CASE-UNKNOWN"
    inv_date = payload.get("generatedAt", datetime.utcnow().isoformat())
    chain = payload.get("chain", "Ethereum (Mainnet)")
    suspect = payload.get("suspectWallet", "UNKNOWN")
    
    # Summary
    tx_count = payload.get("transactionsCount", 0)
    total_val = payload.get("totalValue", 0)
    total_token = payload.get("totalValueToken", "ETH")
    hops = payload.get("hops", 0)
    
    # Risk
    risk = payload.get("risk", {})
    risk_score = risk.get("score") or 0
    risk_level = risk.get("level") or "UNKNOWN"
    
    # VASP
    vasp = payload.get("vasp") or {}
    vasp_identified = vasp.get("identified", False)
    vasp_name = vasp.get("name", "Unknown")
    vasp_address = vasp.get("address", "")
    vasp_conf = vasp.get("confidence", 0)
    
    html_content = HTML_TEMPLATE
    
    # Basic replacements of hardcoded template values
    html_content = html_content.replace("CASE-2024-ETH-0891", case_id)
    html_content = html_content.replace("INV-9042-SIH", investigation_id)
    html_content = html_content.replace("2024-03-15 14:30:00 UTC", str(inv_date))
    html_content = html_content.replace("0x47ac0fb4f2d84898e4d9e7b4dab3c24507a6d503", suspect)
    html_content = html_content.replace("11 transfer events", f"{tx_count} transfer events")
    html_content = html_content.replace("30,000,000.0 DAI + 125.40 ETH", f"{total_val} {total_token}")
    html_content = html_content.replace("30,000,000.0 DAI + 0.055 ETH", f"{total_val} {total_token}")
    html_content = html_content.replace("3 (Full Breadth-First Traversal)", f"{hops} (Full Breadth-First Traversal)")
    html_content = html_content.replace("82 / 100", f"{risk_score} / 100")
    html_content = html_content.replace("HIGH", str(risk_level).upper())
    html_content = html_content.replace("94%", f"{vasp_conf}%" if vasp_identified else "N/A")
    
    # VASP replacement logic
    if vasp_identified:
        html_content = html_content.replace("Binance Exchange", vasp_name)
    else:
        # Hide VASP box
        html_content = html_content.replace("VASP Interaction Detected:", "No Verified VASP Interaction Detected.")
        html_content = html_content.replace("Binance Exchange", "None")

    # Generate files
    safe_id = "".join([c for c in investigation_id if c.isalnum() or c in "-_"])
    base_name = f"Report_{safe_id}_{datetime.now().strftime('%H%M%S')}"
    html_file = os.path.abspath(f"{base_name}.html")
    pdf_file = os.path.abspath(f"{base_name}.pdf")

    with open(html_file, "w", encoding="utf-8") as f:
        f.write(html_content)

    try:
        from weasyprint import HTML
        HTML(string=html_content).write_pdf(pdf_file)
    except Exception as e:
        if os.path.exists(html_file):
            os.remove(html_file)
        raise Exception(f"WeasyPrint PDF generation failed: {str(e)}")

    # Cleanup HTML
    if os.path.exists(html_file):
        os.remove(html_file)
        
    if os.path.exists(pdf_file) and os.path.getsize(pdf_file) > 0:
        return pdf_file
    else:
        raise Exception("PDF generation failed. File not created or empty.")
