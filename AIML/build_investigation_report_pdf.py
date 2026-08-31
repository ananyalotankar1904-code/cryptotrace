"""
High-Fidelity PDF Report Generator for Blockchain Risk Analysis
Project: Real-Time Identification of Fraud-Linked Cryptocurrency Exchanges
Role: AI/ML + Graph Analytics Layer
"""

import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, KeepTogether, PageBreak, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    """Two-pass canvas to dynamically compute and draw total page numbers and running headers."""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super().showPage()
        super().save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#6C757D"))

        # Running Header on pages 2+
        if self._pageNumber > 1:
            self.drawString(40, 762, "BLOCKCHAIN INVESTIGATION REPORT | CONFIDENTIAL & PRIVILEGED")
            self.drawRightString(572, 762, "CASE ID: CR-2026-ETH-08492")
            self.setStrokeColor(colors.HexColor("#E2E8F0"))
            self.setLineWidth(0.75)
            self.line(40, 756, 572, 756)

        # Running Footer on all pages
        self.setStrokeColor(colors.HexColor("#E2E8F0"))
        self.setLineWidth(0.75)
        self.line(40, 42, 572, 42)
        self.drawString(40, 30, "SIH 2026 Forensic Analytics Engine | Real-Time Fraud-Linked VASP Attribution")
        self.drawRightString(572, 30, f"Page {self._pageNumber} of {page_count}")
        self.restoreState()


def create_investigation_report_pdf(output_filename="Blockchain_Investigation_Report.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=40,
        rightMargin=40,
        topMargin=44,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    # Custom Color Palette
    PRIMARY = colors.HexColor("#1D3557")     # Deep Navy
    SECONDARY = colors.HexColor("#457B9D")   # Steel Blue
    ACCENT = colors.HexColor("#2A9D8F")      # Emerald / VASP
    DANGER = colors.HexColor("#E63946")      # Alert Crimson
    DARK_TEXT = colors.HexColor("#2B2D42")   # Charcoal
    LIGHT_BG = colors.HexColor("#F8F9FA")    # Off-white table row
    ALT_ROW = colors.HexColor("#F1F5F9")     # Light slate

    # Typography Styles
    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=12
    )

    h1_style = ParagraphStyle(
        "ReportH1",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=10,
        spaceAfter=6
    )

    h2_style = ParagraphStyle(
        "ReportH2",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=10,
        leading=14,
        textColor=SECONDARY,
        spaceBefore=6,
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "ReportBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12,
        textColor=DARK_TEXT
    )

    body_bold = ParagraphStyle(
        "ReportBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    callout_style = ParagraphStyle(
        "ReportCallout",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=12.5,
        textColor=DARK_TEXT
    )

    tbl_header_style = ParagraphStyle(
        "TblHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white
    )

    tbl_cell_style = ParagraphStyle(
        "TblCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=7.5,
        leading=9.5,
        textColor=DARK_TEXT
    )

    tbl_cell_bold = ParagraphStyle(
        "TblCellBold",
        parent=tbl_cell_style,
        fontName="Helvetica-Bold"
    )

    tbl_cell_danger = ParagraphStyle(
        "TblCellDanger",
        parent=tbl_cell_style,
        fontName="Helvetica-Bold",
        textColor=DANGER
    )

    tbl_cell_success = ParagraphStyle(
        "TblCellSuccess",
        parent=tbl_cell_style,
        fontName="Helvetica-Bold",
        textColor=ACCENT
    )

    story = []

    # ==========================================
    # PAGE 1: HEADER & CASE DETAILS
    # ==========================================
    story.append(Paragraph("BLOCKCHAIN INVESTIGATION REPORT", title_style))
    story.append(HRFlowable(width="100%", thickness=2, color=PRIMARY, spaceBefore=0, spaceAfter=10))

    # Section 1: Case Details
    story.append(Paragraph("1. Case Details", h1_style))
    case_details_data = [
        [Paragraph("&bull; <b>Case ID:</b> CR-2026-ETH-08492", body_style), Paragraph("&bull; <b>Investigation ID:</b> INV-0XMOCK_SUS", body_style)],
        [Paragraph("&bull; <b>Investigation Date:</b> 2026-08-30T11:15:00Z", body_style), Paragraph("&bull; <b>Investigator:</b> Cyber Crime Cell / SIU", body_style)],
        [Paragraph("&bull; <b>Blockchain:</b> Ethereum (ERC-20 & Native ETH)", body_style), Paragraph("&bull; <b>Report Status:</b> <font color='#2A9D8F'><b>ACTIONABLE FORENSIC EVIDENCE</b></font>", body_style)],
        [Paragraph("&bull; <b>Suspect Wallet:</b> <font name='Courier'>0xMOCK_SUSPECT_A0000000000000000000000000000</font>", body_style), ""]
    ]
    t_case = Table(case_details_data, colWidths=[265, 265])
    t_case.setStyle(TableStyle([
        ('SPAN', (0, 3), (1, 3)),
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_case)
    story.append(Spacer(1, 8))

    # Section 2: Investigation Summary
    story.append(Paragraph("2. Investigation Summary", h1_style))
    story.append(Paragraph("Metrics Overview", h2_style))
    
    metrics_data = [
        [Paragraph("&bull; <b>Total Transactions:</b> 6", body_style), Paragraph("&bull; <b>Destination Addresses Identified:</b> 5 (1 VASP Exit)", body_style)],
        [Paragraph("&bull; <b>Total Incoming Value:</b> 3.50 ETH + 1,000.00 USDT", body_style), Paragraph("&bull; <b>Overall Risk Level:</b> <font color='#E63946'><b>CRITICAL (85 / 100)</b></font>", body_style)],
        [Paragraph("&bull; <b>Total Outgoing Value:</b> 3.50 ETH + 1,000.00 USDT", body_style), Paragraph("&bull; <b>Confidence Score:</b> <font color='#2A9D8F'><b>80% (Verified VASP Match)</b></font>", body_style)],
        [Paragraph("&bull; <b>Number of Hops Traced:</b> 3 Sequential Hops", body_style), ""]
    ]
    t_metrics = Table(metrics_data, colWidths=[265, 265])
    t_metrics.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
        ('RIGHTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_metrics)
    story.append(Spacer(1, 6))

    story.append(Paragraph("Investigator Executive Summary", h2_style))
    exec_summary_text = (
        "Automated graph analytics performed on the victim-reported seed suspect wallet (<b>0xMOCK_SUSPECT_A...</b>) revealed an "
        "immediate, multi-hop fund-layering sequence. Within 45 minutes of initial receipt, <b>3.50 ETH</b> and <b>1,000.00 USDT</b> were dispersed "
        "across two intermediary transit wallets exhibiting a classic peel-chain pattern before terminating into a verified <b>Binance "
        "Centralized Exchange Deposit Address</b> (0xmock_vasp_binance_f...). The high transaction frequency (18.0 tx/hr) and rapid turnover "
        "interval (avg 9.0 mins) indicate automated script dispersal intended to obfuscate fund origin before fiat liquidation."
    )
    story.append(Paragraph(exec_summary_text, callout_style))
    story.append(Spacer(1, 8))

    # Section 3: Transaction Evidence Table
    story.append(Paragraph("3. Transaction Evidence", h1_style))
    evidence_headers = ["Evidence ID", "Tx Hash", "From → To", "Date / Time", "Amount", "Risk Indicator"]
    evidence_rows = [
        [Paragraph(h, tbl_header_style) for h in evidence_headers],
        [
            Paragraph("EVID-001", tbl_cell_bold),
            Paragraph("0xmock_tx_001_a_to_b...", tbl_cell_style),
            Paragraph("0xMOCK_SUSP_A → 0xMOCK_INTER_B", tbl_cell_style),
            Paragraph("2026-08-30 10:00", tbl_cell_style),
            Paragraph("<b>2.50 ETH</b>", tbl_cell_style),
            Paragraph("<font color='#E63946'>Rapid Outflow (Hop 1)</font>", tbl_cell_style)
        ],
        [
            Paragraph("EVID-002", tbl_cell_bold),
            Paragraph("0xmock_tx_002_a_to_b...", tbl_cell_style),
            Paragraph("0xMOCK_SUSP_A → 0xMOCK_INTER_B", tbl_cell_style),
            Paragraph("2026-08-30 10:05", tbl_cell_style),
            Paragraph("<b>1,000 USDT</b>", tbl_cell_style),
            Paragraph("Multi-Asset (ERC-20)", tbl_cell_style)
        ],
        [
            Paragraph("EVID-003", tbl_cell_bold),
            Paragraph("0xmock_tx_003_a_to_c...", tbl_cell_style),
            Paragraph("0xMOCK_SUSP_A → 0xMOCK_INTER_C", tbl_cell_style),
            Paragraph("2026-08-30 10:10", tbl_cell_style),
            Paragraph("<b>1.00 ETH</b>", tbl_cell_style),
            Paragraph("Fund Splitting / Fan-Out", tbl_cell_style)
        ],
        [
            Paragraph("EVID-004", tbl_cell_bold),
            Paragraph("0xmock_tx_004_b_to_d...", tbl_cell_style),
            Paragraph("0xMOCK_INTER_B → 0xMOCK_MULE_D", tbl_cell_style),
            Paragraph("2026-08-30 10:20", tbl_cell_style),
            Paragraph("<b>2.40 ETH</b>", tbl_cell_style),
            Paragraph("Peel Forwarding (Hop 2)", tbl_cell_style)
        ],
        [
            Paragraph("EVID-005", tbl_cell_bold),
            Paragraph("0xmock_tx_005_b_to_e...", tbl_cell_style),
            Paragraph("0xMOCK_INTER_B → 0xMOCK_COLD_E", tbl_cell_style),
            Paragraph("2026-08-30 10:22", tbl_cell_style),
            Paragraph("<b>0.08 ETH</b>", tbl_cell_style),
            Paragraph("Secondary Peel / Cold Wallet", tbl_cell_style)
        ],
        [
            Paragraph("EVID-006", tbl_cell_bold),
            Paragraph("0xmock_tx_006_d_to_f...", tbl_cell_style),
            Paragraph("0xMOCK_MULE_D → 0xMOCK_VASP_BIN", tbl_cell_style),
            Paragraph("2026-08-30 10:45", tbl_cell_style),
            Paragraph("<b>2.35 ETH</b>", tbl_cell_style),
            Paragraph("<font color='#2A9D8F'><b>VASP Ingress / Cash-Out</b></font>", tbl_cell_style)
        ],
    ]
    t_evidence = Table(evidence_rows, colWidths=[52, 98, 140, 78, 62, 100])
    t_evidence.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ALT_ROW]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_evidence)

    # ==========================================
    # PAGE 2: GRAPH VISUALIZATION & RISK SUMMARY
    # ==========================================
    story.append(PageBreak())

    story.append(Paragraph("Transaction Flow Summary", h2_style))
    flow_text = (
        "Seed Suspect Wallet (0xMOCK_SUSPECT_A...) split funds to Intermediary B (2.50 ETH + 1,000 USDT) and Intermediary C (1.00 ETH). "
        "Intermediary B immediately forwarded 2.40 ETH to Mule D, peeling 0.08 ETH to Address E. Mule D deposited 2.35 ETH into "
        "Binance within 45 minutes of the theft, preserving >94% of illicit value for cash-out."
    )
    story.append(Paragraph(flow_text, body_style))
    story.append(Spacer(1, 6))

    # Graph Visual
    if os.path.exists("transaction_graph_prototype.png"):
        img = Image("transaction_graph_prototype.png", width=500, height=170)
        story.append(img)
        story.append(Paragraph("<i>Figure 1: Reconstructed Multi-Hop Transaction Graph & VASP Attribution Flow</i>", ParagraphStyle("Cap", parent=body_style, fontName="Helvetica-Oblique", fontSize=7.5, alignment=1, textColor=SECONDARY)))
    story.append(Spacer(1, 10))

    # Section 4: Risk Summary & Indicators
    story.append(Paragraph("4. Risk Summary", h1_style))
    risk_metric_data = [
        [
            Paragraph("&bull; <b>Risk Score:</b> <font color='#E63946'><b>85 / 100</b></font>", body_style),
            Paragraph("&bull; <b>Risk Level:</b> <font color='#E63946'><b>CRITICAL</b></font>", body_style),
            Paragraph("&bull; <b>Attribution Confidence:</b> <font color='#2A9D8F'><b>80% (High)</b></font>", body_style)
        ]
    ]
    t_rm = Table(risk_metric_data, colWidths=[175, 175, 180])
    t_rm.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 1),
        ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_rm)
    story.append(Spacer(1, 4))

    risk_table_headers = ["Risk Indicator", "Status", "Key Evidence & Analytical Rationale"]
    risk_rows = [
        [Paragraph(h, tbl_header_style) for h in risk_table_headers],
        [
            Paragraph("<b>High transaction frequency</b>", tbl_cell_style),
            Paragraph("<font color='#E63946'><b>DETECTED</b></font>", tbl_cell_style),
            Paragraph("18.0 tx/hour burst rate observed during initial disbursement window.", tbl_cell_style)
        ],
        [
            Paragraph("<b>Large-value movement</b>", tbl_cell_style),
            Paragraph("<font color='#E63946'><b>DETECTED</b></font>", tbl_cell_style),
            Paragraph("Over 94% of reported victim funds forwarded in a single continuous session.", tbl_cell_style)
        ],
        [
            Paragraph("<b>Rapid movement through wallets</b>", tbl_cell_style),
            Paragraph("<font color='#E63946'><b>DETECTED</b></font>", tbl_cell_style),
            Paragraph("Average holding time of 9.0 minutes per intermediary transit hop (automated script pattern).", tbl_cell_style)
        ],
        [
            Paragraph("<b>Repeated splitting</b>", tbl_cell_style),
            Paragraph("<font color='#E63946'><b>DETECTED</b></font>", tbl_cell_style),
            Paragraph("Fan-out distribution pattern detected at Hop 1 (Wallets B & C).", tbl_cell_style)
        ],
        [
            Paragraph("<b>Repeated consolidation</b>", tbl_cell_style),
            Paragraph("<font color='#6C757D'><b>NONE</b></font>", tbl_cell_style),
            Paragraph("Primary observed pattern was rapid peeling and dispersion rather than fan-in.", tbl_cell_style)
        ],
        [
            Paragraph("<b>Suspicious address interaction</b>", tbl_cell_style),
            Paragraph("<font color='#E63946'><b>DETECTED</b></font>", tbl_cell_style),
            Paragraph("Interaction with 2 transit mule wallets exhibiting zero balance retention.", tbl_cell_style)
        ],
        [
            Paragraph("<b>Mixer/Bridge interaction</b>", tbl_cell_style),
            Paragraph("<font color='#6C757D'><b>NONE</b></font>", tbl_cell_style),
            Paragraph("No interactions with Tornado Cash or cross-chain bridge contracts within scope.", tbl_cell_style)
        ],
    ]
    t_risk = Table(risk_rows, colWidths=[150, 75, 305])
    t_risk.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ALT_ROW]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_risk)

    # ==========================================
    # PAGE 3: VASP ATTRIBUTION & ACTIONS
    # ==========================================
    story.append(PageBreak())

    # Section 5: VASP Attribution
    story.append(Paragraph("5. VASP Attribution", h1_style))
    vasp_details_data = [
        [Paragraph("&bull; <b>VASP Name:</b> <font color='#2A9D8F'><b>Binance</b></font>", body_style), Paragraph("&bull; <b>Interaction Type:</b> Centralized Exchange Deposit (Hop 3)", body_style)],
        [Paragraph("&bull; <b>Associated Address:</b> <font name='Courier' size='7'>0xmock_vasp_binance_f5555555555555555555555</font>", body_style), Paragraph("&bull; <b>Attribution Confidence:</b> <font color='#2A9D8F'><b>80% (Verified Official Cluster)</b></font>", body_style)],
        [Paragraph("&bull; <b>Transaction Hash:</b> <font name='Courier' size='7'>0xmock_tx_006_d_to_f_binance_eth</font>", body_style), ""]
    ]
    t_vasp = Table(vasp_details_data, colWidths=[310, 220])
    t_vasp.setStyle(TableStyle([
        ('TOPPADDING', (0,0), (-1,-1), 1.5),
        ('BOTTOMPADDING', (0,0), (-1,-1), 1.5),
        ('LEFTPADDING', (0,0), (-1,-1), 0),
    ]))
    story.append(t_vasp)
    story.append(Spacer(1, 4))

    vasp_analysis_text = (
        "<b>Interaction Analysis:</b> The investigation identified an unbroken, time-consistent link between the seed suspect wallet and the "
        "Virtual Asset Service Provider (VASP). Terminal transfer of <b>2.35 ETH</b> was successfully received by the verified Binance Hot Wallet "
        "cluster on <b>2026-08-30 at 10:45:00 UTC</b>. Because centralized exchanges enforce KYC verification upon onboarding, this deposit "
        "address serves as the primary actionable legal bottleneck for asset recovery and suspect deanonymization."
    )
    story.append(Paragraph(vasp_analysis_text, callout_style))
    story.append(Spacer(1, 8))

    # Section 6: Key Findings and Assessment
    story.append(Paragraph("6. Key Findings and Investigator Assessment", h1_style))
    story.append(Paragraph("Critical Findings", h2_style))
    findings_list = [
        "&bull; <b>Direct 3-Hop Trajectory:</b> Clear, unbroken trail from suspect address to Binance deposit gateway.",
        "&bull; <b>High Fund Velocity:</b> Complete dispersion and exit traversal executed in under 45 minutes.",
        "&bull; <b>Identified Asset Value:</b> A total of 2.35 ETH currently sits deposited within the identified Binance exchange account.",
        "&bull; <b>Mule Transit Wallets:</b> Use of two transit intermediary addresses (Mules B and D) exhibiting zero balance retention."
    ]
    for item in findings_list:
        story.append(Paragraph(item, body_style))
    story.append(Spacer(1, 4))

    story.append(Paragraph("Final Assessment", h2_style))
    assessment_text = (
        "The on-chain activity pattern strongly indicates an organized attempt to layer illicit proceeds through intermediate hops before "
        "off-ramping into fiat via Binance. The high speed, low dissipation (<6%), and multi-asset structuring suggest an automated script "
        "rather than standard retail trading."
    )
    story.append(Paragraph(assessment_text, body_style))
    story.append(Spacer(1, 8))

    # Section 7: Recommended Actions
    story.append(Paragraph("7. Recommended Actions", h1_style))
    actions = [
        "&bull; <b>Serve Statutory Legal Notice (Section 91 CrPC / Subpoena):</b> Issue formal directive to Binance Legal Compliance specifying deposit address <font name='Courier' size='7'>0xmock_vasp_binance_f...</font> and tx hash <font name='Courier' size='7'>0xmock_tx_006...</font>.",
        "&bull; <b>Emergency Account Freeze:</b> Request immediate administrative freeze on the beneficiary Binance account and linked fiat withdrawal channels.",
        "&bull; <b>KYC Dossier Acquisition:</b> Subpoena user identification documents, registered email, phone number, login IP audit logs, and associated bank accounts.",
        "&bull; <b>Continuous Ledger Monitoring:</b> Establish automated event listeners on secondary peel address <font name='Courier' size='7'>0xmock_cold_e...</font>."
    ]
    for act in actions:
        story.append(Paragraph(act, body_style))
    story.append(Spacer(1, 8))

    # Section 8: Limitations
    story.append(Paragraph("8. Limitations", h1_style))
    limitations = [
        "&bull; Blockchain addresses are pseudonymous and do not directly prove real-world ownership without off-chain VASP KYC attribution.",
        "&bull; Analysis is limited to observable on-chain data and the selected tracing scope defined in this report.",
        "&bull; Off-chain transactions and internal exchange book matching are not visible on the public ledger.",
        "&bull; VASP customer information requires authorized lawful access to establish legal identity.",
        "&bull; The use of mixers, bridges, and cross-chain transfers reduces tracing certainty and can obscure fund flow.",
        "&bull; Risk and confidence scores are analytical indicators based on observed patterns and do not constitute conclusive legal proof of criminal guilt."
    ]
    for lim in limitations:
        story.append(Paragraph(lim, ParagraphStyle("Lim", parent=body_style, fontSize=7.5, leading=10, textColor=colors.HexColor("#64748B"))))

    # ==========================================
    # PAGE 4: VARIABLE DICTIONARY & CONDITIONAL LOGIC
    # ==========================================
    story.append(PageBreak())

    story.append(Paragraph("9. Variable Dictionary", h1_style))
    var_headers = ["Variable", "Meaning & System Context"]
    var_rows = [
        [Paragraph(h, tbl_header_style) for h in var_headers],
        [Paragraph("{{CASE_ID}}", tbl_cell_bold), Paragraph("Investigation case identifier (e.g. CR-2026-ETH-08492)", tbl_cell_style)],
        [Paragraph("{{INVESTIGATION_ID}}", tbl_cell_bold), Paragraph("Unique internal investigation session identifier", tbl_cell_style)],
        [Paragraph("{{INVESTIGATION_TIMESTAMP}}", tbl_cell_bold), Paragraph("UTC Date and time of investigation execution", tbl_cell_style)],
        [Paragraph("{{INVESTIGATOR_NAME}}", tbl_cell_bold), Paragraph("Investigating agency or officer name", tbl_cell_style)],
        [Paragraph("{{SUSPECT_WALLET}}", tbl_cell_bold), Paragraph("Target seed wallet address under investigation", tbl_cell_style)],
        [Paragraph("{{BLOCKCHAIN}}", tbl_cell_bold), Paragraph("Blockchain network analyzed (Ethereum Mainnet)", tbl_cell_style)],
        [Paragraph("{{REPORT_STATUS}}", tbl_cell_bold), Paragraph("Current status of forensic report (e.g., FINAL / ACTIONABLE)", tbl_cell_style)],
        [Paragraph("{{TRANSACTION_COUNT}}", tbl_cell_bold), Paragraph("Total number of transactions analyzed in the graph", tbl_cell_style)],
        [Paragraph("{{TOTAL_INCOMING}}", tbl_cell_bold), Paragraph("Total native & token value received by the suspect wallet", tbl_cell_style)],
        [Paragraph("{{TOTAL_OUTGOING}}", tbl_cell_bold), Paragraph("Total native & token value sent outward across hops", tbl_cell_style)],
        [Paragraph("{{NUMBER_OF_HOPS}}", tbl_cell_bold), Paragraph("Maximum number of sequential transaction hops traced", tbl_cell_style)],
        [Paragraph("{{DESTINATION_COUNT}}", tbl_cell_bold), Paragraph("Total number of distinct destination addresses identified", tbl_cell_style)],
        [Paragraph("{{RISK_SCORE}}", tbl_cell_bold), Paragraph("Calculated numeric risk score (0–100)", tbl_cell_style)],
        [Paragraph("{{OVERALL_RISK_LEVEL}}", tbl_cell_bold), Paragraph("Categorical risk classification (LOW / MEDIUM / HIGH / CRITICAL)", tbl_cell_style)],
        [Paragraph("{{CONFIDENCE_SCORE}}", tbl_cell_bold), Paragraph("Percentage confidence in analytical findings and attribution", tbl_cell_style)],
        [Paragraph("{{VASP_NAME}}", tbl_cell_bold), Paragraph("Name of identified Virtual Asset Service Provider (e.g., Binance)", tbl_cell_style)],
        [Paragraph("{{VASP_WALLET}}", tbl_cell_bold), Paragraph("Deposit / Hot wallet address belonging to the identified VASP", tbl_cell_style)],
        [Paragraph("{{VASP_CONFIDENCE_SCORE}}", tbl_cell_bold), Paragraph("Attribution confidence score specific to VASP identity match", tbl_cell_style)],
    ]
    t_var = Table(var_rows, colWidths=[160, 370])
    t_var.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ALT_ROW]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_var)
    story.append(Spacer(1, 10))

    story.append(Paragraph("10. Conditional Logic Table", h1_style))
    cond_headers = ["Condition Variable", "Evaluated Rule", "Report Action & Rendering Behavior"]
    cond_rows = [
        [Paragraph(h, tbl_header_style) for h in cond_headers],
        [
            Paragraph("{{HIGH_TRANSACTION_FREQUENCY}}", tbl_cell_bold),
            Paragraph("TRUE", tbl_cell_danger),
            Paragraph("Display high-frequency burst finding in risk indicators table.", tbl_cell_style)
        ],
        [
            Paragraph("{{RAPID_MOVEMENT}}", tbl_cell_bold),
            Paragraph("TRUE", tbl_cell_danger),
            Paragraph("Display rapid velocity finding (< 30 min avg holding time).", tbl_cell_style)
        ],
        [
            Paragraph("{{REPEATED_SPLITTING}}", tbl_cell_bold),
            Paragraph("TRUE", tbl_cell_danger),
            Paragraph("Display fan-out fund splitting analysis and intermediary count.", tbl_cell_style)
        ],
        [
            Paragraph("{{SUSPICIOUS_INTERACTION}}", tbl_cell_bold),
            Paragraph("TRUE", tbl_cell_danger),
            Paragraph("Display mule transit pass-through wallet indicators.", tbl_cell_style)
        ],
        [
            Paragraph("{{MIXER_OR_BRIDGE_INTERACTION}}", tbl_cell_bold),
            Paragraph("TRUE / FALSE", tbl_cell_style),
            Paragraph("If TRUE: Show mixer deanonymization analysis. If FALSE: Flag clean ledger path.", tbl_cell_style)
        ],
        [
            Paragraph("{{VASP_INTERACTION}}", tbl_cell_bold),
            Paragraph("TRUE", tbl_cell_success),
            Paragraph("Display Section 5 VASP details, deposit tx hash, and Section 91 CrPC notice action.", tbl_cell_style)
        ],
        [
            Paragraph("{{OVERALL_RISK_LEVEL}}", tbl_cell_bold),
            Paragraph("CRITICAL / HIGH", tbl_cell_danger),
            Paragraph("Trigger statutory legal notice and emergency account freezing directives.", tbl_cell_style)
        ],
        [
            Paragraph("{{LARGE_VALUE_MOVEMENT}}", tbl_cell_bold),
            Paragraph("TRUE", tbl_cell_danger),
            Paragraph("Display large-value volume preservation finding in executive summary.", tbl_cell_style)
        ],
    ]
    t_cond = Table(cond_rows, colWidths=[175, 75, 280])
    t_cond.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 2.5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 2.5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, ALT_ROW]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ]))
    story.append(t_cond)

    # Build Document with NumberedCanvas
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"[+] Successfully built PDF: {output_filename}")


if __name__ == "__main__":
    create_investigation_report_pdf()
