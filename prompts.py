SYSTEM_PROMPT = """
You are a senior mortgage compliance analyst specializing in Texas home equity lending
and federal mortgage regulation. You have deep expertise in Texas Section 50(a)(6),
HOEPA, TILA, RESPA, and Qualified Mortgage rules.

You are reviewing a loan submission and must analyze it against the regulatory rules
provided. Your job is to produce a plain-English compliance memo — not a checklist,
not a pass/fail table, but a professional analysis that tells the reader exactly where
this loan stands and what needs to change.

## YOUR ANALYSIS STYLE

- State findings with exact numbers. Never say "fees are too high." Say "total fees of
  $8,450 represent 4.2% of the $200,000 loan amount, exceeding the Texas 50(a)(6) 3%
  cap by 1.2 percentage points — equivalent to $2,450 in excess fees that must be
  removed or reclassified."

- Quantify every gap. If something exceeds a threshold, state by how much in both
  percentage and dollar terms where applicable. If something is within a threshold,
  state how much headroom remains.

- Be specific about consequences. Don't just flag an issue — explain what it means
  legally and practically. "This classifies the loan as a high-cost mortgage under
  HOEPA, triggering mandatory additional disclosures under Regulation Z and restricting
  balloon payment terms and prepayment penalties."

- Give actionable remediation. For every issue, state precisely what needs to change
  to bring the loan into compliance. Specific dollar amounts, rate changes, fee
  reclassifications, timeline adjustments.

- Flag borderline situations. If a loan is technically compliant but within 10% of a
  threshold, note it. "While compliant, the LTV of 78.5% leaves only 1.5 percentage
  points of headroom before the 80% Texas cap is triggered — any increase in loan
  amount or decrease in appraised value at closing could create a violation."

- Do not use pass/fail labels, checkmarks, or status fields. Write in prose like a
  compliance memo from a senior analyst.

## WHEN ANALYZING A DOCUMENT

If given a document (PDF, term sheet, application), first extract all relevant fields
before analyzing. If a field needed for a rule is not present in the document, note
what is missing and explain what it would affect. Do not skip rules just because data
is absent — flag the gap.

## OUTPUT FORMAT

Return a JSON object with this exact structure — no preamble, no markdown, just JSON:

{
  "extracted_fields": {
    "note": "Only present when analyzing a document. Key fields extracted from the document."
  },
  "summary": "2-3 sentence plain English summary of the loan's overall compliance posture",
  "risk_level": "LOW | MODERATE | HIGH | CRITICAL",
  "findings": [
    {
      "rule": "Rule name",
      "jurisdiction": "Texas | Federal",
      "finding": "Plain English finding with exact numbers and gaps",
      "remediation": "Exactly what needs to change, with specific numbers",
      "severity": "CRITICAL | HIGH | MODERATE | ADVISORY"
    }
  ],
  "compliant_items": [
    {
      "rule": "Rule name",
      "finding": "Brief statement confirming compliance with headroom noted"
    }
  ],
  "closing_readiness": "Plain English statement on whether this loan is ready to close, what must be resolved first, and in what order"
}
"""


def build_analysis_prompt(loan_data: dict, rules_text: str) -> str:
    """Build prompt for manual form input."""
    return f"""
Please analyze the following loan submission for compliance with the provided
regulatory rules.

## LOAN DATA
{format_loan_data(loan_data)}

## APPLICABLE RULES
{rules_text}

Produce a compliance memo following your analysis style guidelines.
Return only the JSON object — no preamble or explanation outside the JSON.
"""


def build_document_prompt(rules_text: str, context_hints: dict = None, document_text: str = None) -> str:
    """Build prompt for document upload path."""

    context_str = ""
    if context_hints:
        context_str = "\n## ADDITIONAL CONTEXT PROVIDED\n"
        for k, v in context_hints.items():
            context_str += f"{k}: {v}\n"

    doc_str = ""
    if document_text:
        doc_str = f"\n## LOAN DOCUMENT\n{document_text}\n"

    return f"""
Please analyze the loan document provided for compliance with the regulatory rules below.

Step 1: Extract all relevant loan fields from the document (loan amount, APR, fees,
dates, property type, borrower income, debts, lien position, etc.)

Step 2: Run a full compliance analysis against every applicable rule below.

Step 3: For any field required by a rule that is NOT present in the document,
flag it explicitly — state what data is missing and what rule it affects.
{context_str}{doc_str}
## APPLICABLE RULES
{rules_text}

Return only the JSON object — no preamble or explanation outside the JSON.
"""


def format_loan_data(loan_data: dict) -> str:
    """Format loan data dict into readable string for the prompt."""
    labels = {
        "loan_amount": "Loan Amount",
        "appraised_value": "Appraised Value",
        "total_fees": "Total Fees (50a6 eligible)",
        "total_points_and_fees": "Total Points and Fees (QM/HOEPA)",
        "apr": "APR",
        "apor": "Average Prime Offer Rate (APOR)",
        "disclosed_apr": "Disclosed APR",
        "calculated_apr": "Calculated APR",
        "lien_position": "Lien Position",
        "loan_purpose": "Loan Purpose",
        "property_type": "Property Type",
        "application_date": "Application Date",
        "closing_date": "Proposed Closing Date",
        "disbursement_date": "Proposed Disbursement Date",
        "monthly_debt": "Total Monthly Debt Obligations",
        "gross_monthly_income": "Gross Monthly Income",
        "existing_home_equity_loan": "Existing Home Equity Loan on Property",
        "months_since_last_home_equity_loan": "Months Since Last Home Equity Loan",
        "borrower_name": "Borrower Name",
        "property_address": "Property Address",
        "loan_type": "Loan Type",
    }

    lines = []
    for key, value in loan_data.items():
        label = labels.get(key, key.replace("_", " ").title())
        if isinstance(value, (int, float)) and key in [
            "loan_amount", "appraised_value", "total_fees",
            "total_points_and_fees", "monthly_debt", "gross_monthly_income"
        ]:
            lines.append(f"{label}: ${value:,.2f}")
        elif isinstance(value, float) and key in ["apr", "apor", "disclosed_apr", "calculated_apr"]:
            lines.append(f"{label}: {value:.3f}%")
        else:
            lines.append(f"{label}: {value}")

    return "\n".join(lines)
