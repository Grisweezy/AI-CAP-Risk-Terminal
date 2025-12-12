import streamlit as st
import json
from datetime import datetime

st.set_page_config(page_title="AICAP Risk Terminal", layout="centered")

st.title("AICAP Risk Terminal")
st.caption("Continuous audit readiness for high-impact AI systems")

# ---------------------------
# Section 1: System Metadata
# ---------------------------
st.header("Describe Your AI System")

name = st.text_input("System Name", "Benefits Eligibility Assistant")
owner = st.text_input("Owner / Program Office", "AFLCMC Benefits Modernization PMO")
use_case = st.text_area(
    "What does this AI system do?",
    "Helps case workers analyze benefits eligibility inquiries."
)

rights_impacting = st.checkbox("⚖️ Impacts rights, eligibility, or access to services?", True)
safety_impacting = st.checkbox("🚨 Impacts physical safety?", False)
risk_level = st.selectbox("Overall Risk Level", ["low", "medium", "high"], index=2)

# ---------------------------
# Section 2: Documentation
# ---------------------------
st.header("Documentation & Required Artifacts")

col1, col2 = st.columns(2)

with col1:
    model_card = st.checkbox("Model Card Exists", True)
    data_sheet = st.checkbox("Data Sheet Exists", True)
    pia = st.checkbox("Privacy Impact Assessment (PIA) Completed", False)

with col2:
    bias_eval = st.checkbox("Bias / Fairness Evaluation Performed", True)
    oversight_plan = st.checkbox("Human Oversight Plan Documented", False)

# ---------------------------
# Section 3: Monitoring
# ---------------------------
st.header("Monitoring & Logging")

col3, col4 = st.columns(2)

with col3:
    logs_enabled = st.checkbox("Logging Enabled", True)
    drift_monitoring = st.checkbox("Model Drift Monitoring Enabled", True)

with col4:
    bias_monitoring = st.checkbox("Ongoing Bias Monitoring", False)


# ---------------------------
# Audit Engine
# ---------------------------

def run_audit(system_data):
    """
    Returns:
      {
        status: PASS | CONDITIONAL | FAIL,
        score: int,
        findings: [
          {
            "rule": str,
            "severity": HIGH|MEDIUM|LOW,
            "message": str,
            "remediation": str
          }, ...
        ],
        generated_at: iso str
      }
    """
    findings = []
    score = 100

    # Helper to add a finding and adjust score
    def add_finding(rule, severity, message, remediation, penalty):
        nonlocal score
        score -= penalty
        findings.append(
            {
                "rule": rule,
                "severity": severity,
                "message": message,
                "remediation": remediation,
            }
        )

    # 1) Rights-impacting requires PIA
    if system_data["rights_impacting"] and not system_data["artifacts"]["pia"]:
        add_finding(
            rule="DOC-PIA-001",
            severity="HIGH",
            message="Rights-impacting system is missing a Privacy Impact Assessment (PIA).",
            remediation="Conduct and document a Privacy Impact Assessment, then store it as an official artifact and link it in your inventory.",
            penalty=25,
        )

    # 2) High risk requires human oversight plan
    if system_data["risk_level"] == "high" and not system_data["artifacts"]["oversight_plan"]:
        add_finding(
            rule="GOV-OVERSIGHT-003",
            severity="HIGH",
            message="High-risk system has no documented human oversight & escalation plan.",
            remediation="Define who reviews outputs, when humans must intervene, and how escalation works. Document this as a formal oversight plan.",
            penalty=25,
        )

    # 3) High risk should have ongoing bias monitoring
    if system_data["risk_level"] == "high" and not system_data["monitoring"]["bias_monitoring"]:
        add_finding(
            rule="MON-BIAS-004",
            severity="MEDIUM",
            message="High-risk system does not have ongoing bias / outcome monitoring.",
            remediation="Set up periodic or continuous bias checks on key segments and protected groups, with thresholds and alerts when metrics drift.",
            penalty=15,
        )

    # 4) Logging must be enabled for auditability
    if not system_data["monitoring"]["logs_enabled"]:
        add_finding(
            rule="MON-LOG-005",
            severity="MEDIUM",
            message="Logging is disabled; decisions and usage are not auditable.",
            remediation="Enable detailed logging for inputs, outputs, decisions, and key configuration changes, and retain them per policy.",
            penalty=10,
        )

    # 5) Drift monitoring recommended
    if not system_data["monitoring"]["drift_monitoring"]:
        add_finding(
            rule="MON-DRIFT-006",
            severity="LOW",
            message="Model drift is not being monitored.",
            remediation="Implement drift monitoring on key performance metrics and data distributions. Review on a regular cadence.",
            penalty=5,
        )

    score = max(0, score)

    if score >= 85 and len([f for f in findings if f["severity"] == "HIGH"]) == 0:
        status = "PASS"
    elif score >= 60:
        status = "CONDITIONAL"
    else:
        status = "FAIL"

    return {
        "status": status,
        "score": score,
        "findings": findings,
        "generated_at": datetime.utcnow().isoformat() + "Z"
    }


# ---------------------------
# Run Audit Button
# ---------------------------
if st.button("Run AICAP Audit"):
    system_data = {
        "name": name,
        "owner": owner,
        "use_case": use_case,
        "rights_impacting": rights_impacting,
        "safety_impacting": safety_impacting,
        "risk_level": risk_level,
        "artifacts": {
            "model_card": model_card,
            "data_sheet": data_sheet,
            "pia": pia,
            "bias_eval": bias_eval,
            "oversight_plan": oversight_plan,
        },
        "monitoring": {
            "logs_enabled": logs_enabled,
            "drift_monitoring": drift_monitoring,
            "bias_monitoring": bias_monitoring,
        },
    }

    result = run_audit(system_data)

    st.subheader("📊 Audit Result")
    st.metric("Overall Status", result["status"])
    st.metric("Compliance Score", result["score"])

    # High-level guidance
    if result["status"] == "PASS":
        st.success("PASS – This system meets all current checks. Maintain documentation and monitoring to stay compliant.")
    elif result["status"] == "CONDITIONAL":
        st.warning("CONDITIONAL – Some gaps found. Fix the items below to reach a full PASS.")
    else:
        st.error("FAIL – Significant gaps found. The highest-severity items below must be fixed before this system is audit-ready.")

    # Detailed findings + how to fix
    st.subheader("🔎 Findings & How to Pass")

    if not result["findings"]:
        st.write("No findings.")
    else:
        # Sort by severity: HIGH -> MEDIUM -> LOW
        severity_rank = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        sorted_findings = sorted(
            result["findings"],
            key=lambda f: severity_rank.get(f["severity"], 3)
        )

        for f in sorted_findings:
            sev = f["severity"]
            title = f["message"]
            remediation = f["remediation"]
            rule = f["rule"]

            if sev == "HIGH":
                box = st.error
            elif sev == "MEDIUM":
                box = st.warning
            else:
                box = st.info

            box(f"**[{sev}] {rule}** – {title}\n\n➡️ **To pass:** {remediation}")

    # Raw evidence JSON
    st.subheader("📁 Raw JSON Evidence")
    st.code(json.dumps({"system": system_data, "audit": result}, indent=2), language="json")
