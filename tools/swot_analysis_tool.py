from .tool import Tool


def swot_analysis(strengths=None, weaknesses=None,
                  opportunities=None, threats=None):
    categories = {
        "Strengths": strengths,
        "Weaknesses": weaknesses,
        "Opportunities": opportunities,
        "Threats": threats,
    }

    if not any(categories.values()):
        return (
            "No SWOT inputs were provided. Please share at least one "
            "strength, weakness, opportunity, or threat to generate "
            "an analysis."
        )

    summary = ["SWOT Analysis:"]
    for label, value in categories.items():
        if value:
            items = [item.strip() for item in value.split(",") if item.strip()]
            summary.append(f"{label}: {', '.join(items)}.")
        else:
            summary.append(f"{label}: not specified.")

    if opportunities and threats:
        summary.append(
            "Focus on leveraging the identified opportunities while "
            "actively mitigating the identified threats."
        )
    elif opportunities:
        summary.append(
            "Consider how your strengths can help you capture the "
            "identified opportunities."
        )
    elif threats:
        summary.append(
            "Consider how your strengths can help you defend against "
            "the identified threats."
        )

    return " ".join(summary)


swot_analysis_tool = Tool(
    name="swot_analysis",
    description=(
        "Generates a structured SWOT (Strengths, Weaknesses, "
        "Opportunities, Threats) analysis summary for a startup "
        "based on founder-provided inputs."
    ),
    parameters={
        "type": "object",
        "properties": {
            "strengths": {
                "type": "string",
                "description": (
                    "Optional comma-separated list of internal strengths."
                )
            },
            "weaknesses": {
                "type": "string",
                "description": (
                    "Optional comma-separated list of internal weaknesses."
                )
            },
            "opportunities": {
                "type": "string",
                "description": (
                    "Optional comma-separated list of external "
                    "opportunities."
                )
            },
            "threats": {
                "type": "string",
                "description": (
                    "Optional comma-separated list of external threats."
                )
            }
        },
        "required": []
    },
    callback=swot_analysis
)
