"""
Mortgage Compliance Rules Database
Texas-specific and Federal rules for home equity and mortgage loans.
Each rule includes the threshold, how to calculate it, and what data fields are needed.
"""

RULES = {

    # ─────────────────────────────────────────
    # TEXAS SECTION 50(a)(6) — HOME EQUITY LOANS
    # ─────────────────────────────────────────

    "TX_50A6_FEE_CAP": {
        "name": "Texas 50(a)(6) — 3% Fee Cap",
        "jurisdiction": "Texas",
        "source": "Texas Constitution, Article XVI, Section 50(a)(6)(E)",
        "description": (
            "Total fees, points, and charges paid by the borrower at or before closing "
            "cannot exceed 3% of the original principal loan amount. This includes origination "
            "fees, underwriting fees, processing fees, and broker fees. It excludes title insurance, "
            "appraisal, and certain third-party charges."
        ),
        "threshold": 0.03,
        "fields_needed": ["loan_amount", "total_fees"],
        "calculation": "total_fees / loan_amount",
        "unit": "percentage",
    },

    "TX_50A6_LTV_CAP": {
        "name": "Texas 50(a)(6) — 80% LTV Cap",
        "jurisdiction": "Texas",
        "source": "Texas Constitution, Article XVI, Section 50(a)(6)(B)",
        "description": (
            "The principal loan amount cannot exceed 80% of the fair market value of the homestead "
            "on the date the loan is made. This is a hard cap with no exceptions."
        ),
        "threshold": 0.80,
        "fields_needed": ["loan_amount", "appraised_value"],
        "calculation": "loan_amount / appraised_value",
        "unit": "percentage",
    },

    "TX_50A6_COOLING_OFF": {
        "name": "Texas 50(a)(6) — 12-Day Cooling Off Period",
        "jurisdiction": "Texas",
        "source": "Texas Constitution, Article XVI, Section 50(a)(6)(M)(ii)",
        "description": (
            "The borrower must wait at least 12 calendar days after submitting the loan application "
            "OR receiving the required disclosures (whichever is later) before the loan can close. "
            "Closing before this period expires voids the lien."
        ),
        "threshold": 12,
        "fields_needed": ["application_date", "closing_date"],
        "calculation": "days between application_date and closing_date",
        "unit": "days",
    },

    "TX_50A6_PRIMARY_RESIDENCE": {
        "name": "Texas 50(a)(6) — Primary Residence Only",
        "jurisdiction": "Texas",
        "source": "Texas Constitution, Article XVI, Section 50(a)(6)",
        "description": (
            "Texas home equity loans under Section 50(a)(6) can only be made against the borrower's "
            "primary homestead. Investment properties and second homes are not eligible."
        ),
        "threshold": None,
        "fields_needed": ["property_type"],
        "calculation": "property_type must be 'primary_residence'",
        "unit": "categorical",
    },

    "TX_50A6_ONE_LOAN_AT_A_TIME": {
        "name": "Texas 50(a)(6) — One Home Equity Loan at a Time",
        "jurisdiction": "Texas",
        "source": "Texas Constitution, Article XVI, Section 50(a)(6)(K)",
        "description": (
            "A borrower may have only one home equity loan outstanding on a homestead at any time. "
            "A new 50(a)(6) loan cannot be closed until any existing home equity loan is paid off. "
            "There must also be at least 12 months between any two home equity loans on the same property."
        ),
        "threshold": 12,
        "fields_needed": ["existing_home_equity_loan", "months_since_last_home_equity_loan"],
        "calculation": "existing_home_equity_loan must be False; months_since_last >= 12",
        "unit": "months",
    },

    # ─────────────────────────────────────────
    # FEDERAL — HOEPA (HIGH-COST MORTGAGES)
    # ─────────────────────────────────────────

    "FED_HOEPA_APR_TRIGGER": {
        "name": "HOEPA — High-Cost APR Trigger",
        "jurisdiction": "Federal",
        "source": "15 U.S.C. § 1602(bb); Regulation Z § 1026.32",
        "description": (
            "A first-lien mortgage is classified as a high-cost mortgage if the APR exceeds "
            "the Average Prime Offer Rate (APOR) by more than 6.5 percentage points. "
            "For second liens, the threshold is 8.5 points above APOR. "
            "High-cost classification triggers significant additional disclosure requirements "
            "and restricts certain loan terms. Current APOR is updated weekly by the CFPB."
        ),
        "threshold": {
            "first_lien": 6.5,
            "second_lien": 8.5,
        },
        "fields_needed": ["apr", "apor", "lien_position"],
        "calculation": "apr - apor > threshold based on lien_position",
        "unit": "percentage_points",
    },

    "FED_HOEPA_POINTS_FEES_TRIGGER": {
        "name": "HOEPA — High-Cost Points and Fees Trigger",
        "jurisdiction": "Federal",
        "source": "Regulation Z § 1026.32(a)(1)(ii)",
        "description": (
            "A loan is classified as high-cost if total points and fees exceed 5% of the total "
            "loan amount for loans of $24,866 or more (2024 threshold, adjusted annually). "
            "For smaller loans, the threshold is the lesser of 8% or $1,243."
        ),
        "threshold": {
            "large_loan_pct": 0.05,
            "large_loan_min": 24866,
            "small_loan_pct": 0.08,
            "small_loan_max_dollars": 1243,
        },
        "fields_needed": ["loan_amount", "total_points_and_fees"],
        "calculation": "total_points_and_fees / loan_amount vs threshold",
        "unit": "percentage",
    },

    # ─────────────────────────────────────────
    # FEDERAL — TILA (TRUTH IN LENDING ACT)
    # ─────────────────────────────────────────

    "FED_TILA_APR_DISCLOSURE": {
        "name": "TILA — APR Accuracy Requirement",
        "jurisdiction": "Federal",
        "source": "15 U.S.C. § 1638; Regulation Z § 1026.22",
        "description": (
            "The disclosed APR must be accurate within 1/8 of 1 percentage point (0.125%) "
            "for regular transactions. If the disclosed APR is understated by more than this "
            "tolerance, the lender must provide corrected disclosures and may need to refund "
            "charges to the borrower."
        ),
        "threshold": 0.125,
        "fields_needed": ["disclosed_apr", "calculated_apr"],
        "calculation": "abs(disclosed_apr - calculated_apr)",
        "unit": "percentage_points",
    },

    "FED_TILA_THREE_DAY_RESCISSION": {
        "name": "TILA — 3-Day Right of Rescission",
        "jurisdiction": "Federal",
        "source": "15 U.S.C. § 1635; Regulation Z § 1026.23",
        "description": (
            "For non-purchase money loans secured by a primary residence (including refinances "
            "and home equity loans), the borrower has 3 business days after closing to rescind "
            "the transaction. The lender cannot disburse funds until this period has expired. "
            "Failure to provide proper rescission notice extends the right to rescind to 3 years."
        ),
        "threshold": 3,
        "fields_needed": ["closing_date", "disbursement_date", "loan_purpose"],
        "calculation": "business days between closing_date and disbursement_date",
        "unit": "business_days",
    },

    # ─────────────────────────────────────────
    # FEDERAL — QM (QUALIFIED MORTGAGE)
    # ─────────────────────────────────────────

    "FED_QM_DTI": {
        "name": "Qualified Mortgage — DTI Limit",
        "jurisdiction": "Federal",
        "source": "Regulation Z § 1026.43(e); CFPB QM Rule",
        "description": (
            "For a loan to qualify as a General QM, the borrower's debt-to-income ratio "
            "cannot exceed 43% at the time of consummation. DTI is calculated as total monthly "
            "debt obligations divided by gross monthly income. Exceeding this threshold does not "
            "make the loan illegal but removes QM safe harbor protections for the lender."
        ),
        "threshold": 0.43,
        "fields_needed": ["monthly_debt", "gross_monthly_income"],
        "calculation": "monthly_debt / gross_monthly_income",
        "unit": "percentage",
    },

    "FED_QM_POINTS_FEES": {
        "name": "Qualified Mortgage — Points and Fees Cap",
        "jurisdiction": "Federal",
        "source": "Regulation Z § 1026.43(e)(3)",
        "description": (
            "For a loan to be a Qualified Mortgage, total points and fees cannot exceed 3% "
            "of the total loan amount for loans above $120,000 (2024, adjusted annually). "
            "Higher thresholds apply for smaller loans. Exceeding this cap disqualifies the "
            "loan from QM status, removing lender safe harbor protections."
        ),
        "threshold": {
            "tier_1": {"min_loan": 120000, "max_fee_pct": 0.03},
            "tier_2": {"min_loan": 72000, "max_fee_pct": 0.04},
            "tier_3": {"min_loan": 24000, "max_fee_pct": 0.05},
            "tier_4": {"min_loan": 12000, "max_fee_pct": 0.06},
            "tier_5": {"min_loan": 0, "max_fee_pct": 0.08},
        },
        "fields_needed": ["loan_amount", "total_points_and_fees"],
        "calculation": "total_points_and_fees / loan_amount vs tier threshold",
        "unit": "percentage",
    },

}


def get_rules_for_prompt() -> str:
    """Format rules into a clean string for the system prompt."""
    lines = []
    for rule_id, rule in RULES.items():
        lines.append(f"## {rule['name']}")
        lines.append(f"Source: {rule['source']}")
        lines.append(f"Jurisdiction: {rule['jurisdiction']}")
        lines.append(f"Rule: {rule['description']}")
        if rule["threshold"] is not None:
            lines.append(f"Threshold: {rule['threshold']}")
        lines.append("")
    return "\n".join(lines)


# Add RESPA rules to RULES dict
RULES.update({

    "FED_RESPA_KICKBACK": {
        "name": "RESPA — Section 8 Kickback Prohibition",
        "jurisdiction": "Federal",
        "source": "12 U.S.C. § 2607; Regulation X § 1024.14",
        "description": (
            "No person may give or receive any fee, kickback, or thing of value pursuant to "
            "any agreement that business incident to a real estate settlement service will be "
            "referred. This prohibits yield spread premiums paid as kickbacks, unearned fees "
            "split between parties, and referral arrangements between lenders, brokers, title "
            "companies, and other settlement service providers."
        ),
        "threshold": None,
        "fields_needed": ["broker_compensation_type", "referral_arrangements"],
        "calculation": "qualitative — flag any referral fee or unearned fee arrangement",
        "unit": "categorical",
    },

    "FED_RESPA_GFE_TOLERANCE": {
        "name": "RESPA — Loan Estimate Fee Tolerance",
        "jurisdiction": "Federal",
        "source": "Regulation Z § 1026.19(e)(3); TRID Rules",
        "description": (
            "Under TRID, certain fees cannot increase from the Loan Estimate to the Closing Disclosure. "
            "Lender and broker fees have zero tolerance — they cannot increase at all. "
            "Third-party fees where the borrower was not permitted to shop have zero tolerance. "
            "Third-party fees where the borrower could shop have a 10% aggregate tolerance. "
            "Prepaid interest, property insurance premiums, and escrow amounts have no tolerance limit."
        ),
        "threshold": {
            "zero_tolerance_fees": 0.0,
            "ten_pct_tolerance_fees": 0.10,
        },
        "fields_needed": ["loan_estimate_fees", "closing_disclosure_fees"],
        "calculation": "(closing_fees - le_fees) / le_fees vs tolerance bucket",
        "unit": "percentage",
    },

})
