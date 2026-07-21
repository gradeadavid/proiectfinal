from .tool import Tool


def idea_validation_score(idea_name, impact, confidence, ease,
                          reach=None, effort=None):
   
    idea_name = idea_name.strip()
    impact = float(impact)
    confidence = float(confidence)
    ease = float(ease)

    ice_score = round((impact + confidence + ease) / 3, 2)

    summary = [
        f"ICE score for '{idea_name}': {ice_score}/10 "
        f"(Impact {impact}, Confidence {confidence}, Ease {ease})."
    ]

    if ice_score >= 8:
        summary.append(
            "High priority: strong impact, confidence and ease of "
            "execution. Move forward quickly."
        )
    elif ice_score >= 5:
        summary.append(
            "Medium priority: worth pursuing, but consider de-risking "
            "the weakest dimension (impact, confidence, or ease) first."
        )
    else:
        summary.append(
            "Low priority: reconsider scope, gather more evidence to "
            "raise confidence, or find a cheaper way to test it before "
            "committing resources."
        )

    if reach is not None and effort is not None:
        reach = float(reach)
        effort = float(effort)

        if effort <= 0:
            summary.append(
                "RICE score could not be computed: effort must be "
                "greater than zero."
            )
        else:
            rice_score = round(
                (reach * impact * (confidence / 10)) / effort, 2
            )
            summary.append(
                f"RICE score: {rice_score} (Reach {reach}, Effort "
                f"{effort} person-months). Use this to compare against "
                "other ideas competing for the same resources — higher "
                "is better."
            )

    return " ".join(summary)


idea_validation_tool = Tool(
    name="idea_validation_score",
    description=(
        "Scores a startup idea or feature using the ICE framework "
        "(Impact, Confidence, Ease) on a 1-10 scale, and additionally "
        "computes a RICE score when reach and effort are provided, to "
        "help prioritize which idea to pursue first."
    ),
    parameters={
        "type": "object",
        "properties": {
            "idea_name": {
                "type": "string",
                "description": (
                    "Short description of the idea or feature being "
                    "scored, e.g. 'add referral program'."
                )
            },
            "impact": {
                "type": "number",
                "description": (
                    "Expected impact if it works, on a scale of 1-10."
                )
            },
            "confidence": {
                "type": "number",
                "description": (
                    "Confidence in the impact/reach estimate, on a "
                    "scale of 1-10."
                )
            },
            "ease": {
                "type": "number",
                "description": (
                    "How easy/cheap it is to execute, on a scale of "
                    "1-10 (10 = very easy)."
                )
            },
            "reach": {
                "type": "number",
                "description": (
                    "Optional number of people/customers affected in a "
                    "given time period. Combine with 'effort' to also "
                    "compute a RICE score."
                )
            },
            "effort": {
                "type": "number",
                "description": (
                    "Optional estimated effort in person-months. "
                    "Combine with 'reach' to also compute a RICE score."
                )
            }
        },
        "required": ["idea_name", "impact", "confidence", "ease"]
    },
    callback=idea_validation_score
)
