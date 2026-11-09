import pytest

from indexer.tokenizer import tokenize

# (text, stem, expected tokens). Titles are normalized titles from test_normalize.py.
CASES = [
    # stopwords removed, plural stemmed
    ("Pruritus Ani", True, ["pruritus", "ani"]),
    ("One patient, three arrhythmias. Case report", True, ["one", "patient", "three", "arrhythmia", "case", "report"]),
    # possessive dropped
    ("From the Editor's Desk.", True, ["editor", "desk"]),
    # hyphens split, "&" dropped
    (
        "Influence of Mother's Self-Efficacy, Social Support & Intention on Exclusive Breastfeeding: A Systematic Review",
        True,
        ["influenc", "mother", "self", "efficaci", "social", "support", "intent", "exclus", "breastfeed", "systemat", "review"],
    ),
    (
        "Detection of the VanA and VanB Gene in Clinical Isolates of Vancomycin-Resistant Enterococci",
        True,
        ["detect", "vana", "vanb", "gene", "clinic", "isol", "vancomycin", "resist", "enterococci"],
    ),
    # Greek letter kept inside a token
    (
        "Association of TGFβ2 gene polymorphism with growth performance",
        True,
        ["associ", "tgfβ2", "gene", "polymorph", "growth", "perform"],
    ),
    # "<" and "≥" dropped, numbers kept
    (
        "Hospitalised Preterm Neonates <34 Weeks of Gestational Age",
        True,
        ["hospitalis", "preterm", "neonat", "34", "week", "gestat", "age"],
    ),
    (
        "Type 2 diabetes remission in adults with BMI ≥50 kg/m2 versus BMI <50 kg/m2",
        True,
        ["type", "2", "diabet", "remiss", "adult", "bmi", "50", "kg", "m2", "versus", "bmi", "50", "kg", "m2"],
    ),
    (
        "Early (<24 hours) venous thromboembolism prophylaxis",
        True,
        ["earli", "24", "hour", "venous", "thromboembol", "prophylaxi"],
    ),
    # decimals stay whole
    ("HbA1c ≥6.5% was significant (p < 0.05)", True, ["hba1c", "6.5", "signific", "p", "0.05"]),
    # accents folded, curly possessive dropped
    ("Sjögren’s syndrome in COVID-19 patients", True, ["sjogren", "syndrom", "covid", "19", "patient"]),
    # stem=False: same splitting, words untouched
    ("Sjögren’s syndrome in COVID-19 patients", False, ["sjogren", "syndrome", "covid", "19", "patients"]),
    (
        "Detection of the VanA and VanB Gene in Clinical Isolates of Vancomycin-Resistant Enterococci",
        False,
        ["detection", "vana", "vanb", "gene", "clinical", "isolates", "vancomycin", "resistant", "enterococci"],
    ),
    # queries go through the same function
    ("heart attacks in young women", True, ["heart", "attack", "young", "women"]),
    # nothing left
    ("", True, []),
]


@pytest.mark.parametrize("text, stem, expected", CASES)
def test_tokenize(text, stem, expected):
    assert tokenize(text, stem) == expected
