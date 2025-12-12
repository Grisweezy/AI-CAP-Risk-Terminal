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
# Audit Engine (Simplified)
# ---------------------------
def run_audit(system_data):
    findings = []
    score = 100

    # Rights-impacting requires PIA
    if system_data["rights_impacting"] and not system_data["artifacts"]["pia"]:
        findings.append(("HIGH", "Missing Privacy Impact Assessment (PIA)"))
        score -= 25

    # High risk requires oversight plan
    if system_data["risk_level"] == "high" and not system_data["artifacts"]["oversight_plan"]:
        findings.append(("HIGH", "Missing human oversight & escalation plan"))
        score -= 25

    # Bias monitoring expected for high risk
    if system_data["risk_level"] == "high" and not system_data["monitoring"]["bias_monitoring"]:
        findings.append(("MEDIUM", "No ongoing bias monitoring configured"))
        score -= 15

    # Logging requirement
    if not system_data["monitoring"]["logs_enabled"]:
        findings.append(("MEDIUM", "Logging disabled — reduces auditability"))
        score -= 10

    # Drift monitoring suggestion
    if not system_data["monitoring"]["drift_monitoring"]:
        findings.append(("LOW", "Model drift not monitored"))
        score -= 5

    score = max(0, score)

    if score >= 85:
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

    st.subheader("🔎 Findings")
    if not result["findings"]:
        st.success("No findings — system meets all current audit requirements.")
    else:
        for sev, msg in result["findings"]:
            st.error(f"[{sev}] {msg}")

    st.subheader("📁 Raw JSON Evidence")
    st.code(json.dumps({"system": system_data, "audit": result}, indent=2), language="json")
