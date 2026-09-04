import csv
import os
import re

LIFE_SAVING_RULE_CATEGORIES = (
    "Bypassing Safety Controls",
    "Confined Spaces",
    "Driving",
    "Energy Isolation",
    "Hot Work",
    "Line of Fire",
    "Safe Mechanical Lifting",
    "Work Authorisation",
    "Working at Height",
)

LIFE_SAVING_RULE_KEYWORDS = {
    "Bypassing Safety Controls": [
        "bypass", "bypassed", "bypassing",
        "defeated the interlock", "interlock defeated", "interlock was defeated",
        "safety device disabled", "disabled the alarm", "alarm disabled", "disabling it",
        "override", "overridden", "overriding",
        "guard removed", "removed the guard",
        "propped open", "taped over", "taped down",
        "trip logic", "safety interlock",
    ],
    "Confined Spaces": [
        "confined space",
        "vessel entry", "entered the vessel", "entering the vessel",
        "tank entry", "entered the tank", "entering the tank",
        "manhole", "manway", "sump", "silo",
        "pit entry", "entered the pit", "entered the mud pit",
        "gas testing", "gas monitoring", "continuous gas monitoring", "atmosphere testing",
        "standby attendant", "forced ventilation",
        "purged", "purge", "entry permit",
    ],
    "Driving": [
        "seatbelt", "seat belt",
        "speed limit", "speeding", "over the speed limit",
        "mobile phone while driving", "texting while driving",
        "driver", "driving", "drove", "driven", "vehicle", "truck",
        "overtook", "overtaking",
        "haul road", "access road", "lost traction", "traction",
    ],
    "Energy Isolation": [
        "lockout", "tagout", "lock out", "tag out", "loto",
        "energy isolation", "isolation point", "isolation valve",
        "zero energy", "de-energized", "de-energised", "re-energised", "re-energized",
        "personal lock", "lockbox", "stored energy", "bled down",
    ],
    "Hot Work": [
        "hot work", "hot work permit",
        "welding", "welded", "cutting torch", "grinding",
        "fire watch", "open flame", "spark", "sparks",
        "flammable vapour", "flammable vapor",
    ],
    "Line of Fire": [
        "line of fire", "struck by", "caught between", "pinch point",
        "suspended load", "swinging", "sling parted", "fell past",
        "trapped pressure", "blew out", "depressurised", "depressurized",
        "pressure test",
    ],
    "Safe Mechanical Lifting": [
        "crane", "hoist", "rigging", "rigger", "sling", "tag line",
        "lifting plan", "lift plan", "banksman", "tandem lift",
        "outrigger", "lifting point", "load chart", "blind lift",
    ],
    "Work Authorisation": [
        "permit-to-work", "permit to work", "work permit", "ptw",
        "countersigned", "authorization", "authorisation",
        "ground-disturbance permit", "ground disturbance permit",
        "line locate", "verbal go-ahead", "shift handover", "re-validating",
    ],
    "Working at Height": [
        "working at height", "work at height",
        "fall protection", "harness", "lanyard",
        "edge protection", "unprotected edge", "open edge",
        "scaffold", "scaffolding", "ladder", "tied off",
        "man-basket", "man basket", "rope access", "unsecured ladder",
    ],
}

CATEGORY_TIEBREAK_ORDER = (
    "Energy Isolation",
    "Confined Spaces",
    "Hot Work",
    "Working at Height",
    "Line of Fire",
    "Safe Mechanical Lifting",
    "Driving",
    "Work Authorisation",
    "Bypassing Safety Controls",
)

_COMPILED_RULES = {
    category: [re.compile(r"\b" + re.escape(keyword) + r"s?\b", re.IGNORECASE) for keyword in keywords]
    for category, keywords in LIFE_SAVING_RULE_KEYWORDS.items()
}


def tag_narrative(narrative):
    if not narrative:
        return None
    hit_counts = {}
    for category, patterns in _COMPILED_RULES.items():
        hits = sum(1 for pattern in patterns if pattern.search(narrative))
        if hits:
            hit_counts[category] = hits
    if not hit_counts:
        return None
    top_score = max(hit_counts.values())
    tied = [category for category in CATEGORY_TIEBREAK_ORDER if hit_counts.get(category) == top_score]
    return tied[0]


def tag_narratives(narratives):
    return [tag_narrative(n) for n in narratives]


SOURCE_CODE_TO_CATEGORY = {
    "LSR_BYP": "Bypassing Safety Controls",
    "LSR_CS": "Confined Spaces",
    "LSR_DRV": "Driving",
    "LSR_HW": "Hot Work",
    "LSR_ISO": "Energy Isolation",
    "LSR_LIFT": "Safe Mechanical Lifting",
    "LSR_LOF": "Line of Fire",
    "LSR_PTW": "Work Authorisation",
    "LSR_WAH": "Working at Height",
}


def _run_review_sample():
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.dirname(backend_dir)
    oil_path = os.path.join(repo_root, "data", "processed", "oil_validation.csv")
    if not os.path.exists(oil_path):
        print(f"Missing {oil_path} — nothing to review.")
        return

    rows = []
    with open(oil_path, newline="") as f:
        for row in csv.DictReader(f):
            rows.append(row)

    matches = 0
    scored = 0
    print(f"{'expected':<28} {'tagged':<28} narrative")
    print("-" * 120)
    for row in rows:
        expected = SOURCE_CODE_TO_CATEGORY.get(row["source_code"])
        tagged = tag_narrative(row["narrative"])
        if expected is not None:
            scored += 1
            if tagged == expected:
                matches += 1
        marker = "OK " if (expected is None or tagged == expected) else "MISS"
        print(f"{marker:<5}{str(expected):<24} {str(tagged):<28} {row['narrative'][:70]}")

    print("-" * 120)
    print(f"{matches}/{scored} oil_validation LSR rows tagged to the expected category")


if __name__ == "__main__":
    _run_review_sample()
