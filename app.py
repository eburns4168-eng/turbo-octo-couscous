import streamlit as st
import anthropic
import json
import base64

from rules import get_rules_for_prompt
from prompts import SYSTEM_PROMPT, build_analysis_prompt, build_document_prompt

st.set_page_config(
    page_title="LienSafe",
    layout="wide",
    page_icon="🛡️",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;900&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

.stApp {
    background-color: #0a0a0a;
    color: #ffffff;
}

section[data-testid="stSidebar"] {
    background-color: #111111;
}

.block-container {
    padding: 2rem 3rem;
    max-width: 900px;
}

h1, h2, h3 {
    color: #ffffff !important;
}

.stButton > button {
    background-color: #00ff88;
    color: #000000;
    border: none;
    border-radius: 6px;
    font-weight: 700;
    font-size: 15px;
    padding: 0.75rem 2rem;
    width: 100%;
    letter-spacing: 0.02em;
    transition: all 0.2s;
}

.stButton > button:hover {
    background-color: #00cc6a;
    color: #000000;
}

.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stSelectbox > div > div {
    background-color: #1a1a1a !important;
    border: 1px solid #2a2a2a !important;
    color: #ffffff !important;
    border-radius: 6px !important;
}

.stRadio > div {
    background-color: #111111;
    border-radius: 8px;
    padding: 0.5rem;
}

.stRadio label {
    color: #ffffff !important;
}

.stExpander {
    background-color: #111111 !important;
    border: 1px solid #1f1f1f !important;
    border-radius: 8px !important;
}

.stExpander summary {
    color: #ffffff !important;
}

.stFileUploader {
    background-color: #111111 !important;
    border: 1px dashed #2a2a2a !important;
    border-radius: 8px !important;
    padding: 1rem !important;
}

.stFileUploader > div {
    background-color: #1a1a1a !important;
    border: none !important;
}

.stFileUploader > div > div {
    background-color: #1a1a1a !important;
    color: #666 !important;
}

[data-testid="stFileUploaderDropzone"] {
    background-color: #1a1a1a !important;
    border: 1px dashed #2a2a2a !important;
    color: #666 !important;
}

[data-testid="stFileUploaderDropzone"] * {
    color: #666 !important;
}

[data-testid="stFileUploaderDropzone"] button {
    background-color: #2a2a2a !important;
    color: #aaa !important;
    border: 1px solid #333 !important;
}

.stAlert {
    background-color: #1a1a1a !important;
    border-radius: 8px !important;
}

.stMetric {
    background-color: #111111;
    border-radius: 8px;
    padding: 1rem;
    border: 1px solid #1f1f1f;
}

.stMetric label {
    color: #888888 !important;
    font-size: 12px !important;
    text-transform: uppercase;
    letter-spacing: 0.08em;
}

.stMetric [data-testid="stMetricValue"] {
    color: #ffffff !important;
    font-size: 22px !important;
    font-weight: 700 !important;
}

div[data-testid="stHorizontalBlock"] {
    gap: 1rem;
}

.stDivider {
    border-color: #1f1f1f !important;
}

p, li, label {
    color: #cccccc !important;
}

.stCheckbox label {
    color: #cccccc !important;
}

.stDateInput input {
    background-color: #1a1a1a !important;
    color: #ffffff !important;
    border: 1px solid #2a2a2a !important;
}

/* Hide streamlit branding */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────

st.markdown("""
<div style="margin-bottom: 2.5rem; padding-bottom: 2rem; border-bottom: 1px solid #1f1f1f;">
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 8px;">
        <span style="font-size: 28px; font-weight: 900; color: #ffffff; letter-spacing: -0.03em;">LIEN<span style="color: #00ff88;">SAFE</span></span>
        <span style="background: #1a1a1a; border: 1px solid #2a2a2a; color: #888; font-size: 11px; padding: 3px 10px; border-radius: 20px; font-weight: 500; letter-spacing: 0.05em;">BETA</span>
    </div>
    <p style="color: #666; font-size: 14px; margin: 0;">Texas mortgage compliance · Plain English · 30 seconds</p>
    <p style="color: #444; font-size: 12px; margin: 8px 0 0;">For informational purposes only. Does not constitute legal compliance advice. Do not upload documents with real borrower PII during testing. Consult a licensed compliance professional before making lending decisions.</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────
# INPUT TOGGLE
# ─────────────────────────────────────────

input_method = st.radio(
    "",
    ["📄 Upload Document", "✏️ Enter Manually"],
    horizontal=True
)

loan_data = {}
uploaded_text = None

# ─────────────────────────────────────────
# DOCUMENT UPLOAD
# ─────────────────────────────────────────

if input_method == "📄 Upload Document":
    st.markdown("<p style='color:#888; font-size:13px; margin-bottom:0.5rem;'>Upload a loan term sheet, application, or closing disclosure. LienSafe extracts all fields and runs the full compliance check automatically.</p>", unsafe_allow_html=True)

    uploaded_file = st.file_uploader(
        "PDF or TXT",
        type=["pdf", "txt"],
        label_visibility="collapsed"
    )

    if uploaded_file:
        file_type = uploaded_file.type
        if file_type == "application/pdf":
            pdf_bytes = uploaded_file.read()
            pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
            uploaded_text = ("pdf", pdf_b64)
            st.success(f"✅ {uploaded_file.name} loaded")
        elif file_type == "text/plain":
            uploaded_text = ("text", uploaded_file.read().decode("utf-8"))
            st.success(f"✅ {uploaded_file.name} loaded")

    col1, col2 = st.columns(2)
    with col1:
        apor_hint = st.number_input("Current APOR (%)", min_value=0.0, value=6.80, step=0.01, format="%.3f", help="From CFPB weekly table")
    with col2:
        loan_type_hint = st.selectbox("Loan Type", ["", "home_equity", "refinance", "purchase", "heloc"])

    analyze_button = st.button("→ Run Compliance Check", disabled=uploaded_file is None)

# ─────────────────────────────────────────
# MANUAL FORM
# ─────────────────────────────────────────

else:
    with st.expander("Property & Loan", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            loan_data["borrower_name"] = st.text_input("Borrower Name")
            loan_data["property_address"] = st.text_input("Property Address")
            loan_data["property_type"] = st.selectbox("Property Type", ["primary_residence", "second_home", "investment_property"])
            loan_data["loan_type"] = st.selectbox("Loan Type", ["home_equity", "refinance", "purchase", "heloc"])
            loan_data["lien_position"] = st.selectbox("Lien Position", ["first_lien", "second_lien"])
            loan_data["loan_purpose"] = st.selectbox("Loan Purpose", ["cash_out_refinance", "rate_term_refinance", "purchase", "home_equity"])
        with col2:
            loan_data["loan_amount"] = st.number_input("Loan Amount ($)", min_value=0, value=200000, step=1000)
            loan_data["appraised_value"] = st.number_input("Appraised Value ($)", min_value=0, value=280000, step=1000)
            loan_data["total_fees"] = st.number_input("Total Fees — 50(a)(6) ($)", min_value=0, value=6500, step=100)
            loan_data["total_points_and_fees"] = st.number_input("Total Points & Fees — QM/HOEPA ($)", min_value=0, value=7200, step=100)
            loan_data["apr"] = st.number_input("APR (%)", min_value=0.0, value=7.25, step=0.01, format="%.3f")
            loan_data["apor"] = st.number_input("APOR (%)", min_value=0.0, value=6.80, step=0.01, format="%.3f")
            loan_data["disclosed_apr"] = st.number_input("Disclosed APR (%)", min_value=0.0, value=7.25, format="%.3f")
            loan_data["calculated_apr"] = st.number_input("Calculated APR (%)", min_value=0.0, value=7.26, format="%.3f")

    with st.expander("Income & Debt", expanded=True):
        col3, col4 = st.columns(2)
        with col3:
            loan_data["gross_monthly_income"] = st.number_input("Gross Monthly Income ($)", min_value=0, value=8500, step=100)
            loan_data["monthly_debt"] = st.number_input("Total Monthly Debt ($)", min_value=0, value=3200, step=100)
        with col4:
            loan_data["existing_home_equity_loan"] = st.checkbox("Existing Home Equity Loan on Property")
            loan_data["months_since_last_home_equity_loan"] = st.number_input("Months Since Last Home Equity Loan", min_value=0, value=0)

    with st.expander("Dates", expanded=True):
        col5, col6, col7 = st.columns(3)
        with col5:
            loan_data["application_date"] = str(st.date_input("Application Date"))
        with col6:
            loan_data["closing_date"] = str(st.date_input("Proposed Closing Date"))
        with col7:
            loan_data["disbursement_date"] = str(st.date_input("Disbursement Date"))

    analyze_button = st.button("→ Run Compliance Check")

# ─────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────

if analyze_button:
    rules_text = get_rules_for_prompt()
    client = anthropic.Anthropic()

    with st.spinner("Analyzing..."):
        if input_method == "📄 Upload Document" and uploaded_text:
            file_type, file_content = uploaded_text
            context_hints = {}
            if apor_hint:
                context_hints["apor"] = apor_hint
            if loan_type_hint:
                context_hints["loan_type"] = loan_type_hint

            if file_type == "pdf":
                messages = [{"role": "user", "content": [
                    {"type": "document", "source": {"type": "base64", "media_type": "application/pdf", "data": file_content}},
                    {"type": "text", "text": build_document_prompt(rules_text, context_hints)}
                ]}]
            else:
                messages = [{"role": "user", "content": build_document_prompt(rules_text, context_hints, file_content)}]
        else:
            messages = [{"role": "user", "content": build_analysis_prompt(loan_data, rules_text)}]

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4000,
            system=SYSTEM_PROMPT,
            messages=messages
        )

    raw = response.content[0].text
    clean = raw.strip()
    if "```" in clean:
        parts = clean.split("```")
        clean = parts[1] if len(parts) > 1 else parts[0]
        if clean.startswith("json"):
            clean = clean[4:]
    clean = clean.strip()

    try:
        result = json.loads(clean)
    except json.JSONDecodeError:
        st.error("Could not parse response.")
        st.code(raw)
        st.stop()

    # ─────────────────────────────────────────
    # RESULTS
    # ─────────────────────────────────────────

    risk = result.get("risk_level", "UNKNOWN")
    findings = result.get("findings", [])
    compliant = result.get("compliant_items", [])

    risk_color = {"LOW": "#00ff88", "MODERATE": "#ffcc00", "HIGH": "#ff8800", "CRITICAL": "#ff4444"}.get(risk, "#888888")
    severity_color = {"CRITICAL": "#ff4444", "HIGH": "#ff8800", "MODERATE": "#ffcc00", "ADVISORY": "#4488ff"}

    st.markdown("<div style='height: 2rem'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='border-left: 4px solid {risk_color}; padding: 1.25rem 1.5rem; background: #111; border-radius: 0 8px 8px 0; margin-bottom: 1.5rem;'>
        <div style='font-size: 11px; color: #666; letter-spacing: 0.08em; text-transform: uppercase; margin-bottom: 6px;'>Risk Assessment</div>
        <div style='font-size: 24px; font-weight: 900; color: {risk_color}; letter-spacing: -0.02em; margin-bottom: 8px;'>{risk}</div>
        <div style='font-size: 14px; color: #aaa; line-height: 1.6;'>{result.get("summary", "")}</div>
    </div>
    """, unsafe_allow_html=True)

    if findings:
        st.markdown(f"<p style='font-size:11px; color:#666; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:1rem;'>Issues Found — {len(findings)}</p>", unsafe_allow_html=True)
        for f in findings:
            sev = f.get("severity", "MODERATE")
            color = severity_color.get(sev, "#888")
            st.markdown(f"""
            <div style='border-left: 3px solid {color}; padding: 1rem 1.25rem; background: #111; border-radius: 0 8px 8px 0; margin-bottom: 12px;'>
                <div style='display:flex; justify-content:space-between; margin-bottom:6px;'>
                    <span style='font-size:14px; font-weight:600; color:#fff;'>{f.get("rule","")}</span>
                    <span style='font-size:11px; color:{color}; font-weight:600; letter-spacing:0.05em;'>{sev}</span>
                </div>
                <div style='font-size:13px; color:#bbb; line-height:1.6; margin-bottom:8px;'>{f.get("finding","")}</div>
                <div style='font-size:12px; color:#666;'>→ {f.get("remediation","")}</div>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='background:#111; border:1px solid #1f1f1f; border-radius:8px; padding:1rem 1.25rem; color:#00ff88; font-size:14px;'>✓ No compliance issues found</div>", unsafe_allow_html=True)

    if compliant:
        with st.expander(f"✓ Confirmed Compliant ({len(compliant)})"):
            for c in compliant:
                st.markdown(f"<div style='font-size:13px; color:#888; padding:6px 0; border-bottom:1px solid #1a1a1a;'><span style='color:#00ff88;'>✓</span> <strong style='color:#ccc;'>{c.get('rule','')}</strong> — {c.get('finding','')}</div>", unsafe_allow_html=True)

    st.markdown("<div style='height:1.5rem'></div>", unsafe_allow_html=True)
    closing = result.get("closing_readiness", "")
    is_blocked = any(w in closing.lower() for w in ["cannot", "must resolve", "not ready", "ineligible"])
    border = "#ff4444" if is_blocked else "#00ff88"
    label = "NOT READY TO CLOSE" if is_blocked else "CLOSING STATUS"
    st.markdown(f"""
    <div style='border:1px solid {border}; border-radius:8px; padding:1.25rem 1.5rem; background:#111;'>
        <div style='font-size:11px; color:#666; letter-spacing:0.08em; text-transform:uppercase; margin-bottom:8px;'>{label}</div>
        <div style='font-size:14px; color:#ccc; line-height:1.6;'>{closing}</div>
    </div>
    """, unsafe_allow_html=True)

    with st.expander("Raw JSON"):
        st.json(result)
