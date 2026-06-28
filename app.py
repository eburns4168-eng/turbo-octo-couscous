import streamlit as st
import anthropic
import json
import base64

from rules import get_rules_for_prompt
from prompts import SYSTEM_PROMPT, build_analysis_prompt, build_document_prompt

st.set_page_config(page_title="Mortgage Compliance Analyzer", layout="wide", page_icon="📋")

# ─────────────────────────────────────────
# HEADER
# ─────────────────────────────────────────

st.title("📋 Mortgage Compliance Analyzer")
st.caption("Texas Section 50(a)(6) · HOEPA · TILA · RESPA · Qualified Mortgage")
st.markdown(
    "Upload a loan term sheet or application and get an instant compliance analysis "
    "against Texas and federal mortgage lending rules — in plain English, with exact numbers."
)
st.divider()

# ─────────────────────────────────────────
# INPUT METHOD TOGGLE
# ─────────────────────────────────────────

input_method = st.radio(
    "How would you like to submit the loan?",
    ["📄 Upload Document", "✏️ Enter Loan Details Manually"],
    horizontal=True
)

loan_data = {}
uploaded_text = None

# ─────────────────────────────────────────
# DOCUMENT UPLOAD PATH
# ─────────────────────────────────────────

if input_method == "📄 Upload Document":
    st.subheader("Upload Loan Document")
    st.markdown(
        "Upload a loan term sheet, application, or closing disclosure. "
        "The AI will extract the relevant fields and run compliance analysis automatically."
    )

    uploaded_file = st.file_uploader(
        "Supported formats: PDF, TXT",
        type=["pdf", "txt"],
        help="Loan term sheets, 1003 applications, closing disclosures, commitment letters"
    )

    if uploaded_file:
        file_type = uploaded_file.type

        if file_type == "application/pdf":
            # Encode PDF as base64 for Claude's document API
            pdf_bytes = uploaded_file.read()
            pdf_b64 = base64.standard_b64encode(pdf_bytes).decode("utf-8")
            uploaded_text = ("pdf", pdf_b64)
            st.success(f"✅ Loaded: {uploaded_file.name} ({len(pdf_bytes):,} bytes)")

        elif file_type == "text/plain":
            uploaded_text = ("text", uploaded_file.read().decode("utf-8"))
            st.success(f"✅ Loaded: {uploaded_file.name}")
            with st.expander("Preview document"):
                st.text(uploaded_text[1][:2000] + ("..." if len(uploaded_text[1]) > 2000 else ""))

    # Optional context fields for document upload
    with st.expander("Add context (optional — helps if not in document)"):
        col1, col2 = st.columns(2)
        with col1:
            apor_hint = st.number_input(
                "Current APOR (%)",
                min_value=0.0, value=6.80, step=0.01, format="%.3f",
                help="Average Prime Offer Rate from CFPB weekly table. Required for HOEPA trigger."
            )
        with col2:
            loan_type_hint = st.selectbox(
                "Loan Type (if not in document)",
                ["", "home_equity", "refinance", "purchase", "heloc"]
            )

    analyze_button = st.button(
        "🔍 Analyze Document",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None
    )

# ─────────────────────────────────────────
# MANUAL FORM PATH
# ─────────────────────────────────────────

else:
    st.subheader("Loan Details")

    with st.expander("Property & Loan", expanded=True):
        col1, col2 = st.columns(2)
        with col1:
            loan_data["borrower_name"] = st.text_input("Borrower Name")
            loan_data["property_address"] = st.text_input("Property Address")
            loan_data["property_type"] = st.selectbox(
                "Property Type",
                ["primary_residence", "second_home", "investment_property"]
            )
            loan_data["loan_type"] = st.selectbox(
                "Loan Type", ["home_equity", "refinance", "purchase", "heloc"]
            )
            loan_data["lien_position"] = st.selectbox("Lien Position", ["first_lien", "second_lien"])
            loan_data["loan_purpose"] = st.selectbox(
                "Loan Purpose",
                ["cash_out_refinance", "rate_term_refinance", "purchase", "home_equity"]
            )
        with col2:
            loan_data["loan_amount"] = st.number_input("Loan Amount ($)", min_value=0, value=200000, step=1000)
            loan_data["appraised_value"] = st.number_input("Appraised Value ($)", min_value=0, value=280000, step=1000)
            loan_data["total_fees"] = st.number_input(
                "Total Fees — 50(a)(6) eligible ($)", min_value=0, value=6500, step=100,
                help="Origination, underwriting, processing, broker fees. Excludes title and appraisal."
            )
            loan_data["total_points_and_fees"] = st.number_input(
                "Total Points & Fees — QM/HOEPA ($)", min_value=0, value=7200, step=100
            )
            loan_data["apr"] = st.number_input("APR (%)", min_value=0.0, value=7.25, step=0.01, format="%.3f")
            loan_data["apor"] = st.number_input(
                "APOR (%) — from CFPB weekly table", min_value=0.0, value=6.80, step=0.01, format="%.3f"
            )
            loan_data["disclosed_apr"] = st.number_input("Disclosed APR (%)", min_value=0.0, value=7.25, format="%.3f")
            loan_data["calculated_apr"] = st.number_input("Calculated APR (%)", min_value=0.0, value=7.26, format="%.3f")

    with st.expander("Income & Debt", expanded=True):
        col3, col4 = st.columns(2)
        with col3:
            loan_data["gross_monthly_income"] = st.number_input("Gross Monthly Income ($)", min_value=0, value=8500, step=100)
            loan_data["monthly_debt"] = st.number_input(
                "Total Monthly Debt Obligations ($)", min_value=0, value=3200, step=100,
                help="Includes proposed mortgage payment plus all other monthly debts"
            )
        with col4:
            loan_data["existing_home_equity_loan"] = st.checkbox("Existing Home Equity Loan on This Property")
            loan_data["months_since_last_home_equity_loan"] = st.number_input(
                "Months Since Last Home Equity Loan", min_value=0, value=0, step=1
            )

    with st.expander("Dates", expanded=True):
        col5, col6, col7 = st.columns(3)
        with col5:
            loan_data["application_date"] = str(st.date_input("Application Date"))
        with col6:
            loan_data["closing_date"] = str(st.date_input("Proposed Closing Date"))
        with col7:
            loan_data["disbursement_date"] = str(st.date_input("Proposed Disbursement Date"))

    analyze_button = st.button("🔍 Run Compliance Analysis", type="primary", use_container_width=True)

# ─────────────────────────────────────────
# RUN ANALYSIS
# ─────────────────────────────────────────

if analyze_button:
    rules_text = get_rules_for_prompt()
    client = anthropic.Anthropic()

    with st.spinner("Reading loan and analyzing compliance against Texas and federal rules..."):

        # Build the right message depending on input method
        if input_method == "📄 Upload Document" and uploaded_text:
            file_type, file_content = uploaded_text

            context_hints = {}
            if apor_hint:
                context_hints["apor"] = apor_hint
            if loan_type_hint:
                context_hints["loan_type"] = loan_type_hint

            if file_type == "pdf":
                messages = [
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "document",
                                "source": {
                                    "type": "base64",
                                    "media_type": "application/pdf",
                                    "data": file_content
                                }
                            },
                            {
                                "type": "text",
                                "text": build_document_prompt(rules_text, context_hints)
                            }
                        ]
                    }
                ]
            else:
                messages = [
                    {
                        "role": "user",
                        "content": build_document_prompt(rules_text, context_hints, file_content)
                    }
                ]
        else:
            messages = [
                {
                    "role": "user",
                    "content": build_analysis_prompt(loan_data, rules_text)
                }
            ]

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
        st.error("Could not parse compliance response. Raw output:")
        st.code(raw)
        st.stop()

    # ─────────────────────────────────────────
    # RESULTS
    # ─────────────────────────────────────────

    risk_colors = {"LOW": "🟢", "MODERATE": "🟡", "HIGH": "🟠", "CRITICAL": "🔴"}
    severity_colors = {
        "CRITICAL": "#ff4444",
        "HIGH": "#ff8800",
        "MODERATE": "#ffcc00",
        "ADVISORY": "#4488ff"
    }

    risk = result.get("risk_level", "UNKNOWN")
    icon = risk_colors.get(risk, "⚪")

    st.divider()

    # Summary bar
    col_risk, col_issues = st.columns([1, 3])
    with col_risk:
        st.metric("Risk Level", f"{icon} {risk}")
    with col_issues:
        findings = result.get("findings", [])
        compliant = result.get("compliant_items", [])
        critical = len([f for f in findings if f.get("severity") == "CRITICAL"])
        high = len([f for f in findings if f.get("severity") == "HIGH"])
        st.metric("Issues Found", len(findings), delta=f"{critical} critical, {high} high" if findings else "None")

    st.write(result.get("summary", ""))

    # Issues
    if findings:
        st.subheader(f"⚠️ Issues Requiring Attention")
        for f in findings:
            severity = f.get("severity", "MODERATE")
            color = severity_colors.get(severity, "#888888")
            st.markdown(
                f"<div style='border-left: 4px solid {color}; padding: 12px 16px; "
                f"margin-bottom: 16px; background: rgba(0,0,0,0.02); border-radius: 0 6px 6px 0;'>"
                f"<div style='display:flex; justify-content:space-between; margin-bottom:6px;'>"
                f"<strong>{f.get('rule', '')}</strong>"
                f"<span style='color:{color}; font-size:0.8em; font-weight:600;'>{severity} &nbsp;·&nbsp; "
                f"<span style='color:#888;'>{f.get('jurisdiction', '')}</span></span></div>"
                f"<div style='margin-bottom:8px;'>{f.get('finding', '')}</div>"
                f"<div style='color:#555; font-size:0.9em;'>→ <em>{f.get('remediation', '')}</em></div>"
                f"</div>",
                unsafe_allow_html=True
            )
    else:
        st.success("No compliance issues found.")

    # Compliant items
    if compliant:
        with st.expander(f"✅ Confirmed Compliant ({len(compliant)} items)"):
            for c in compliant:
                st.markdown(f"**{c.get('rule', '')}** — {c.get('finding', '')}")

    # Closing readiness
    st.divider()
    st.subheader("📅 Closing Readiness")
    closing = result.get("closing_readiness", "")
    if any(word in closing.lower() for word in ["cannot", "must resolve", "not ready", "ineligible"]):
        st.error(closing)
    elif any(word in closing.lower() for word in ["ready", "compliant", "no issues"]):
        st.success(closing)
    else:
        st.warning(closing)

    # Raw JSON for debugging
    with st.expander("View raw analysis JSON"):
        st.json(result)
