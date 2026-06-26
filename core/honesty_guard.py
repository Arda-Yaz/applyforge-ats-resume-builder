def check_blocked_claims(text: str, blocked_terms: list[str]) -> list[str]:
    text_lower = text.lower()

    triggered = []
    for term in blocked_terms:
        if term.lower() in text_lower:
            triggered.append(term)

    return triggered


def validate_bullet(bullet: dict, blocked_terms: list[str]) -> dict:
    text = bullet.get("text", "")
    triggered_terms = check_blocked_claims(text, blocked_terms)

    has_metric_language = len(triggered_terms) > 0
    metrics_available = bullet.get("metrics_available", False)

    allowed = True
    reason = "Allowed"

    if has_metric_language and not metrics_available:
        allowed = False
        reason = f"Blocked unsupported metric/performance claim: {', '.join(triggered_terms)}"

    return {
        "text": text,
        "allowed": allowed,
        "reason": reason,
        "triggered_terms": triggered_terms
    }


def filter_allowed_bullets(bullets: list[dict], blocked_terms: list[str]) -> tuple[list[dict], list[dict]]:
    allowed = []
    blocked = []

    for bullet in bullets:
        validation = validate_bullet(bullet, blocked_terms)

        if validation["allowed"]:
            allowed.append(bullet)
        else:
            blocked.append({
                **bullet,
                "block_reason": validation["reason"]
            })

    return allowed, blocked