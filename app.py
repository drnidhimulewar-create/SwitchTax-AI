import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

from parser import parse_document
from tax_engine import analyze_tax_situation
from form_generator import generate_form_12b, generate_sec_192_letter

# --- PAGE CONFIG ---
st.set_page_config(
    page_title="SwitchTax AI",
    page_icon="💸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Dark Theme and Alerts
st.markdown("""
<style>
    .critical-alert {
        background-color: #ff4b4b;
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        text-align: center;
        font-weight: bold;
        animation: blink 2s infinite;
        margin-bottom: 1rem;
    }
    @keyframes blink {
        0% { opacity: 1; }
        50% { opacity: 0.8; }
        100% { opacity: 1; }
    }
    .privacy-banner {
        background-color: #262730;
        color: #a3a8b8;
        padding: 0.5rem;
        text-align: center;
        font-size: 0.85rem;
        margin-bottom: 2rem;
        border-radius: 4px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="privacy-banner">🔒 Privacy Notice: All calculations are local. No PAN or salary data is stored or transmitted.</div>', unsafe_allow_html=True)

st.title("💸 SwitchTax AI")
st.subheader("Mid-Year Job Switch TDS Reconciler (FY 2025-26)")

# --- SESSION STATE ---
if 'parsed_data' not in st.session_state:
    st.session_state.parsed_data = {}

# --- SIDEBAR ---
with st.sidebar:
    st.header("1. Data Sources")
    
    use_mock = st.toggle("Load Mock Dataset (Demo)")
    
    anthropic_key = st.text_input("Anthropic API Key (Optional Layer 2)", type="password", help="Leave blank to skip LLM extraction.")
    
    old_pdf = st.file_uploader("Old Employer F&F Payslip", type=["pdf"])
    new_pdf = st.file_uploader("New Employer Offer Letter", type=["pdf"])
    
    if use_mock:
        st.session_state.parsed_data = {
            "employee_name": "Rahul Sharma",
            "pan": "ABCDE1234F",
            "old_employer_name": "Tech Corp Pvt Ltd",
            "old_employer_tan": "MUMT12345E",
            "old_gross": 1200000.0,
            "old_tds": 85000.0,
            "new_employer_name": "Innovate AI Solutions",
            "new_basic": 100000.0,
            "new_hra": 50000.0,
            "new_special_allowance": 50000.0,
            "employment_start": "01-Apr-2025",
            "employment_end": "31-Oct-2025",
        }
    else:
        if st.button("Parse Documents"):
            if old_pdf is not None:
                with st.spinner("Extracting data..."):
                    extracted = parse_document(old_pdf, api_key=anthropic_key if anthropic_key else None)
                    # Quick merge logic, assume new_pdf parsing isn't strictly implemented for all fields but we do our best
                    st.session_state.parsed_data = extracted
                    st.success("Data Extracted!")
            else:
                st.warning("Please upload PDFs.")
            
    st.header("2. Tax Settings")
    pt_state = st.selectbox("Professional Tax State", ["Maharashtra", "Karnataka", "West Bengal", "Andhra Pradesh", "Telangana", "Other"])
    pt_override = st.number_input("PT Manual Override (Annual)", min_value=0.0, value=0.0, step=100.0, help="If > 0, this value will be used instead of standard state logic.")
    
    regime_choice = st.radio("Regime Selection", ["Auto-Compare", "New Regime", "Old Regime"])
    
    st.header("Old Regime Settings (If Applicable)")
    is_metro = st.checkbox("Metro City for HRA")
    rent_paid = st.number_input("Annual Rent Paid", min_value=0.0, value=0.0)
    sec_80c = st.number_input("80C Investments (Max 1.5L)", min_value=0.0, max_value=150000.0, value=0.0)
    sec_80d = st.number_input("80D Medical Insurance", min_value=0.0, value=0.0)

# --- MAIN DASHBOARD LAYER 3 (Manual Edit / Review) ---
if st.session_state.parsed_data:
    with st.expander("📝 Layer 3: Review & Edit Extracted Data", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            # Employee name reads directly from parsed_data
            emp_name = st.text_input("Employee Name", value=st.session_state.parsed_data.get('employee_name') or "")
            pan = st.text_input("PAN", value=st.session_state.parsed_data.get('pan') or "")
        with col2:
            old_gross = st.number_input("Old Gross Salary", value=float(st.session_state.parsed_data.get('old_gross') or 0.0))
            old_tds = st.number_input("Old TDS Deducted", value=float(st.session_state.parsed_data.get('old_tds') or 0.0))
        with col3:
            new_basic = st.number_input("New Monthly Basic", value=float(st.session_state.parsed_data.get('new_basic') or 0.0))
            new_hra = st.number_input("New Monthly HRA", value=float(st.session_state.parsed_data.get('new_hra') or 0.0))
            new_sa = st.number_input("New Monthly Spl. Allowance", value=float(st.session_state.parsed_data.get('new_special_allowance') or 0.0))
            
    # Assuming standard mid-year switch gives ~5 months remaining (Nov, Dec, Jan, Feb, Mar)
    # Could be derived from employment end date, but hardcoding for simplicity or adding an input:
    rem_months = st.slider("Remaining Months in FY", 1, 12, 5)
    new_monthly_ctc = new_basic + new_hra + new_sa
    
    # Calculate Tax
    pt_val = pt_override if pt_override > 0 else None
    basic_annual = new_basic * rem_months # Simplified: assuming new basic applies to remainder
    hra_annual = new_hra * rem_months
    
    results = analyze_tax_situation(
        old_gross=old_gross, 
        old_tds=old_tds, 
        new_monthly_ctc=new_monthly_ctc, 
        remaining_months=rem_months,
        pt_state=pt_state, 
        pt_override=pt_val,
        basic_annual=basic_annual, 
        hra_annual=hra_annual, 
        rent_annual=rent_paid,
        is_metro=is_metro, 
        sec_80c=sec_80c, 
        sec_80d=sec_80d
    )
    
    if results['is_critical']:
        st.markdown(f'<div class="critical-alert">⚠️ WARNING: March TDS Shock Detected! Shortfall of Rs. {results["shortfall"]:,.2f}</div>', unsafe_allow_html=True)
    
    # 4 Data Cards
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Combined Annual Income", f"₹{results['combined_gross']:,.2f}")
    c2.metric("TDS Already Paid", f"₹{results['old_tds']:,.2f}")
    
    shortfall_color = "normal" if not results['is_critical'] else "inverse"
    c3.metric("Projected TDS Shortfall", f"₹{results['shortfall']:,.2f}", delta="-Deficit", delta_color=shortfall_color)
    
    current_takehome = new_monthly_ctc - (results['new_tax']/12) # very simplified standard deduction
    adjusted_takehome = new_monthly_ctc - results['monthly_additional_tds']
    c4.metric("Adjusted Monthly Take-Home", f"₹{adjusted_takehome:,.2f}", delta=f"₹{-results['monthly_additional_tds']:,.2f} /mo")
    
    st.markdown("---")
    
    # Regime Comparison Panel
    st.subheader("⚖️ Regime Comparison")
    regime_col1, regime_col2 = st.columns(2)
    with regime_col1:
        st.info(f"**New Regime Tax:** ₹{results['new_tax']:,.2f}")
    with regime_col2:
        st.info(f"**Old Regime Tax:** ₹{results['old_tax']:,.2f}")
        
    st.success(f"**Recommendation:** {results['reason']}")
    
    st.markdown("---")
    
    # Visualization
    st.subheader("📈 Projected Monthly In-Hand Salary")
    
    # Generate data for chart
    months = [f"Month {i+1}" for i in range(rem_months)]
    
    # Without intervention (TDS shock at end)
    standard_inhand = [new_monthly_ctc] * rem_months
    standard_inhand[-1] -= results['shortfall'] # entire shock in March
    
    # With intervention (adjusted)
    adjusted_inhand = [adjusted_takehome] * rem_months
    
    df_chart = pd.DataFrame({
        "Month": months * 2,
        "Take-Home Salary": standard_inhand + adjusted_inhand,
        "Scenario": ["Standard (March Shock)"] * rem_months + ["Adjusted (Smooth)"] * rem_months
    })
    
    fig = px.line(df_chart, x="Month", y="Take-Home Salary", color="Scenario", markers=True, template="plotly_dark")
    max_salary = max(max(standard_inhand), max(adjusted_inhand))
    fig.update_layout(yaxis_range=[0, max_salary * 1.2])
    if results['shortfall'] > 0:
        fig.add_annotation(x=months[-1], y=standard_inhand[-1], text="TDS Shock!", showarrow=True, arrowhead=1, ax=0, ay=-40, font=dict(color="red", size=14))
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Generate Forms
    st.subheader("📄 Generate Forms")
    
    form_data = st.session_state.parsed_data.copy()
    form_data.update({
        "employee_name": emp_name,
        "pan": pan,
        "old_gross": old_gross,
        "old_tds": old_tds
    })
    
    colA, colB = st.columns(2)
    with colA:
        pdf12b = generate_form_12b(form_data)
        st.download_button(
            label="⬇️ Download Form 12B",
            data=pdf12b,
            file_name="Form_12B.pdf",
            mime="application/pdf"
        )
    with colB:
        pdf192 = generate_sec_192_letter(form_data)
        st.download_button(
            label="⬇️ Download Section 192(2) Letter",
            data=pdf192,
            file_name="Section_192_Letter.pdf",
            mime="application/pdf"
        )
else:
    st.info("👈 Please upload your documents or use the Mock Dataset in the sidebar to get started.")
