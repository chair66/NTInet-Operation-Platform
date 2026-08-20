from __future__ import annotations

import re

# Matches NANP numbers entered as plain digits or with common punctuation.
# Examples: 8038542105, +1 803-854-2105, (803) 854-2105.
_NANP_PATTERN = re.compile(
    r"(?<!\d)(?:\+?1[\s.\-]*)?\(?\d{3}\)?[\s.\-]*\d{3}[\s.\-]*\d{4}(?!\d)"
)


def normalize_e164(value: str) -> str:
    """Normalize one US/Canada telephone number to E.164."""
    digits = re.sub(r"\D", "", str(value or ""))
    if len(digits) == 10:
        digits = "1" + digits
    if len(digits) != 11 or not digits.startswith("1"):
        raise ValueError(
            f"Telephone number '{value}' is not a valid US/Canada number."
        )
    return "+" + digits


def parse_phone_numbers(text: str) -> list[str]:
    """Parse and normalize one or more NANP numbers from free-form input.

    Accepts numbers separated by spaces, commas, semicolons, tabs, or newlines,
    while still supporting spaces inside a formatted number such as
    ``(803) 854-2105``. Duplicate numbers are removed while preserving order.
    """
    source = str(text or "").strip()
    if not source:
        raise ValueError("Enter at least one telephone number.")

    matches = [match.group(0).strip() for match in _NANP_PATTERN.finditer(source)]
    if not matches:
        raise ValueError(
            f"Telephone number '{source}' is not a valid US/Canada number."
        )

    # Reject any non-separator content that was not part of a recognized number.
    remainder = _NANP_PATTERN.sub("", source)
    remainder = re.sub(r"[\s,;|/]+", "", remainder)
    if remainder:
        raise ValueError(
            f"Unable to recognize all telephone numbers near '{remainder}'. "
            "Separate numbers with spaces, commas, semicolons, or new lines."
        )

    normalized: list[str] = []
    seen: set[str] = set()
    for value in matches:
        number = normalize_e164(value)
        if number not in seen:
            seen.add(number)
            normalized.append(number)
    return normalized
