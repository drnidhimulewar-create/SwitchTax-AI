def calculate_pt(state: str, manual_override: float = None) -> float:
    """Calculate annual Professional Tax."""
    if manual_override is not None:
        return float(manual_override)
    
    state = state.lower().strip()
    if state == "maharashtra":
        return 2500.0  # 200*11 + 300
    elif state in ["karnataka", "west bengal", "andhra pradesh", "telangana"]:
        return 2400.0  # 200*12
    return 0.0

def calculate_new_regime_tax(gross_income: float, pt_annual: float) -> float:
    """Calculate tax as per FY 2025-26 New Regime slabs."""
    std_deduction = 75000.0
    taxable_income = max(0.0, gross_income - std_deduction - pt_annual)
    
    tax = 0.0
    if taxable_income > 2400000:
        tax += (taxable_income - 2400000) * 0.30
        taxable_income = 2400000
    if taxable_income > 2000000:
        tax += (taxable_income - 2000000) * 0.25
        taxable_income = 2000000
    if taxable_income > 1600000:
        tax += (taxable_income - 1600000) * 0.20
        taxable_income = 1600000
    if taxable_income > 1200000:
        tax += (taxable_income - 1200000) * 0.15
        taxable_income = 1200000
    if taxable_income > 800000:
        tax += (taxable_income - 800000) * 0.10
        taxable_income = 800000
    if taxable_income > 400000:
        tax += (taxable_income - 400000) * 0.05
        taxable_income = 400000
        
    # Section 87A rebate
    net_taxable = max(0.0, gross_income - std_deduction - pt_annual)
    if net_taxable <= 1200000:
        tax = max(0.0, tax - 60000.0)
        
    # Health and Education Cess 4%
    tax += tax * 0.04
    return tax

def calculate_old_regime_tax(gross_income: float, pt_annual: float, 
                             basic_annual: float, hra_annual: float, rent_annual: float, 
                             is_metro: bool, sec_80c: float, sec_80d: float) -> float:
    """Calculate tax as per Old Regime slabs."""
    std_deduction = 50000.0
    
    # HRA Exemption
    hra_exemption = 0.0
    if hra_annual > 0 and rent_annual > 0:
        rent_minus_10_basic = max(0.0, rent_annual - 0.10 * basic_annual)
        basic_percent = 0.50 if is_metro else 0.40
        hra_exemption = min(hra_annual, basic_percent * basic_annual, rent_minus_10_basic)
        
    sec_80c_allowed = min(150000.0, sec_80c)
    
    deductions = std_deduction + pt_annual + hra_exemption + sec_80c_allowed + sec_80d
    taxable_income = max(0.0, gross_income - deductions)
    
    tax = 0.0
    if taxable_income > 1000000:
        tax += (taxable_income - 1000000) * 0.30
        taxable_income = 1000000
    if taxable_income > 500000:
        tax += (taxable_income - 500000) * 0.20
        taxable_income = 500000
    if taxable_income > 250000:
        tax += (taxable_income - 250000) * 0.05
        taxable_income = 250000
        
    # 87A for Old Regime (Usually up to 5L)
    net_taxable = max(0.0, gross_income - deductions)
    if net_taxable <= 500000:
        tax = max(0.0, tax - 12500.0)
        
    # Cess 4%
    tax += tax * 0.04
    return tax

def analyze_tax_situation(old_gross: float, old_tds: float, 
                          new_monthly_ctc: float, remaining_months: int,
                          pt_state: str, pt_override: float = None,
                          basic_annual: float = 0, hra_annual: float = 0, rent_annual: float = 0,
                          is_metro: bool = False, sec_80c: float = 0, sec_80d: float = 0):
    
    combined_gross = old_gross + (new_monthly_ctc * remaining_months)
    pt_annual = calculate_pt(pt_state, pt_override)
    
    new_tax = calculate_new_regime_tax(combined_gross, pt_annual)
    old_tax = calculate_old_regime_tax(combined_gross, pt_annual, basic_annual, hra_annual, rent_annual, is_metro, sec_80c, sec_80d)
    
    # We will compute shortfall based on New Regime by default or whatever is better
    recommended_regime = "New Regime"
    true_tax_liability = new_tax
    savings = old_tax - new_tax
    reason = f"New Regime saves ₹{savings:,.2f}"
    
    if old_tax < new_tax:
        recommended_regime = "Old Regime"
        true_tax_liability = old_tax
        savings = new_tax - old_tax
        reason = f"Old Regime saves ₹{savings:,.2f}"
    elif old_tax == new_tax:
        reason = "Both regimes result in the same tax liability."
        
    shortfall = max(0.0, true_tax_liability - old_tds)
    monthly_additional_tds = shortfall / remaining_months if remaining_months > 0 else shortfall
    
    is_critical = shortfall > 10000
    
    return {
        "combined_gross": combined_gross,
        "pt_annual": pt_annual,
        "new_tax": new_tax,
        "old_tax": old_tax,
        "recommended_regime": recommended_regime,
        "true_tax_liability": true_tax_liability,
        "savings": savings,
        "reason": reason,
        "old_tds": old_tds,
        "shortfall": shortfall,
        "monthly_additional_tds": monthly_additional_tds,
        "is_critical": is_critical,
        "remaining_months": remaining_months
    }
