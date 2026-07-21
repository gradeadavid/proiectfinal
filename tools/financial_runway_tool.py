from .tool import Tool


def financial_runway(cash_available, monthly_burn_rate, monthly_revenue=0):
    """Calculate the startup's financial runway in months.

    Parameters:
        cash_available (float): Total cash currently available.
        monthly_burn_rate (float): Total monthly expenses.
        monthly_revenue (float): Optional monthly revenue. Defaults to 0.

    Returns:
        str: A summary of the runway and a recommendation based on it.
    """
    cash_available = float(cash_available)
    monthly_burn_rate = float(monthly_burn_rate)
    monthly_revenue = float(monthly_revenue) if monthly_revenue else 0.0

    if cash_available <= 0:
        return (
            "Cash available is zero or negative, meaning there is no "
            "runway left. Immediate action is needed: cut costs, raise "
            "a bridge round, or generate revenue fast."
        )

    net_burn = monthly_burn_rate - monthly_revenue

    if net_burn <= 0:
        return (
            f"With monthly revenue of {monthly_revenue:.2f} covering "
            f"the monthly burn rate of {monthly_burn_rate:.2f}, the "
            "startup is profitable or breaking even. Runway is "
            "effectively unlimited at the current burn and revenue "
            "levels."
        )

    runway_months = cash_available / net_burn

    summary = [
        f"Estimated runway: {runway_months:.1f} months, based on "
        f"{cash_available:.2f} in cash and a net burn of "
        f"{net_burn:.2f} per month (burn rate "
        f"{monthly_burn_rate:.2f}, revenue {monthly_revenue:.2f})."
    ]

    if runway_months < 3:
        summary.append(
            "This is a critical runway level. Prioritize immediate "
            "cost cuts and/or an emergency fundraise or bridge "
            "financing."
        )
    elif runway_months < 6:
        summary.append(
            "This is an urgent runway level. Start fundraising now, "
            "since raises typically take several months to close."
        )
    elif runway_months < 12:
        summary.append(
            "This is a moderate runway. Begin fundraising "
            "conversations soon, as a good rule of thumb is to start "
            "raising with at least 6 months of runway left."
        )
    else:
        summary.append(
            "This is a healthy runway. Focus on hitting growth "
            "milestones that will strengthen the case for the next "
            "round."
        )

    return " ".join(summary)


financial_runway_tool = Tool(
    name="financial_runway",
    description=(
        "Calculates a startup's financial runway in months based on "
        "cash available, monthly burn rate, and optional monthly "
        "revenue, with a recommendation based on the result."
    ),
    parameters={
        "type": "object",
        "properties": {
            "cash_available": {
                "type": "number",
                "description": (
                    "Total cash currently available, e.g. 150000."
                )
            },
            "monthly_burn_rate": {
                "type": "number",
                "description": (
                    "Total monthly expenses (cash outflow), e.g. 20000."
                )
            },
            "monthly_revenue": {
                "type": "number",
                "description": (
                    "Optional monthly revenue (cash inflow). "
                    "Defaults to 0."
                )
            }
        },
        "required": ["cash_available", "monthly_burn_rate"]
    },
    callback=financial_runway
)
