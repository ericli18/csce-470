import datetime

import pytest

from indexer.normalize import normalize
from models import Document

# Abstracts -> my normalized titles
CASES = [
    # plain title, trailing period removed
    (
        {
            "pmid": "42539345",
            "title": "First 3-Day Severe Pediatric Traumatic Brain Injury Guideline Adherence Rates in South American Intensive Care Units by Guideline, Patient, and Clinical Care Characteristics.",
            "abstract": "Severe traumatic brain injury (TBI) is a leading cause of pediatric mortality.",
            "entrez_date": "2026-08-01",
            "mesh": [],
            "keywords": ["adherence", "guideline", "pediatric", "traumatic brain injury"],
        },
        Document(
            doc_id="42539345",
            title="First 3-Day Severe Pediatric Traumatic Brain Injury Guideline Adherence Rates in South American Intensive Care Units by Guideline, Patient, and Clinical Care Characteristics",
            abstract="Severe traumatic brain injury (TBI) is a leading cause of pediatric mortality.",
            date=datetime.date(2026, 8, 1),
            mesh=[],
            meta={"keywords": ["adherence", "guideline", "pediatric", "traumatic brain injury"]},
        ),
    ),
    # missing abstract -> ""
    (
        {
            "pmid": "42538879",
            "title": "Pruritus Ani.",
            "abstract": None,
            "entrez_date": "2026-08-01",
            "mesh": [],
            "keywords": [],
        },
        Document(
            doc_id="42538879",
            title="Pruritus Ani",
            abstract="",
            date=datetime.date(2026, 8, 1),
            mesh=[],
            meta={"keywords": []},
        ),
    ),
    # only one trailing period removed
    (
        {
            "pmid": "42618137",
            "title": "From the Editor's Desk..",
            "abstract": None,
            "entrez_date": "2026-08-19",
            "mesh": [],
            "keywords": [],
        },
        Document(
            doc_id="42618137",
            title="From the Editor's Desk.",
            abstract="",
            date=datetime.date(2026, 8, 19),
            mesh=[],
            meta={"keywords": []},
        ),
    ),
    # bracketed translated title, with MeSH
    (
        {
            "pmid": "42543017",
            "title": "[Angina-induced marked, positive U-waves in leads V1-3].",
            "abstract": "U-wave changes during angina are often not recognized.",
            "entrez_date": "2026-08-02",
            "mesh": [
                {"ui": "D006801", "name": "Humans", "major": False},
                {"ui": "D000787", "name": "Angina Pectoris", "major": True},
                {"ui": "D004562", "name": "Electrocardiography", "major": True},
                {"ui": "D017202", "name": "Myocardial Ischemia", "major": True},
            ],
            "keywords": ["U-hullám", "U-wave", "acute coronary syndrome"],
        },
        Document(
            doc_id="42543017",
            title="Angina-induced marked, positive U-waves in leads V1-3",
            abstract="U-wave changes during angina are often not recognized.",
            date=datetime.date(2026, 8, 2),
            mesh=[
                {"descriptor_id": "D006801", "name": "Humans", "major_topic": False},
                {"descriptor_id": "D000787", "name": "Angina Pectoris", "major_topic": True},
                {"descriptor_id": "D004562", "name": "Electrocardiography", "major_topic": True},
                {"descriptor_id": "D017202", "name": "Myocardial Ischemia", "major_topic": True},
            ],
            meta={"keywords": ["U-hullám", "U-wave", "acute coronary syndrome"]},
        ),
    ),
    # bracketed translated title, no abstract
    (
        {
            "pmid": "42544798",
            "title": "[Research progress and development trends in the non-surgical treatment of distal radius fractures].",
            "abstract": None,
            "entrez_date": "2026-08-03",
            "mesh": [],
            "keywords": ["Distal radius fracture", "Non-operative treatment"],
        },
        Document(
            doc_id="42544798",
            title="Research progress and development trends in the non-surgical treatment of distal radius fractures",
            abstract="",
            date=datetime.date(2026, 8, 3),
            mesh=[],
            meta={"keywords": ["Distal radius fracture", "Non-operative treatment"]},
        ),
    ),
    # double-bracketed title
    (
        {
            "pmid": "42614900",
            "title": "[[One patient, three arrhythmias. Case report]].",
            "abstract": "Postoperative patients with congenital heart disease can develop more than one arrhythmia.",
            "entrez_date": "2026-08-19",
            "mesh": [],
            "keywords": [],
        },
        Document(
            doc_id="42614900",
            title="One patient, three arrhythmias. Case report",
            abstract="Postoperative patients with congenital heart disease can develop more than one arrhythmia.",
            date=datetime.date(2026, 8, 19),
            mesh=[],
            meta={"keywords": []},
        ),
    ),
    # <em> tag removed
    (
        {
            "pmid": "42563350",
            "title": "Diagnosis and Treatment of <em>Brucella</em> Infection of the Cervical Vertebral Bodies and Intervertebral Discs.",
            "abstract": None,
            "entrez_date": "2026-08-07",
            "mesh": [],
            "keywords": [],
        },
        Document(
            doc_id="42563350",
            title="Diagnosis and Treatment of Brucella Infection of the Cervical Vertebral Bodies and Intervertebral Discs",
            abstract="",
            date=datetime.date(2026, 8, 7),
            mesh=[],
            meta={"keywords": []},
        ),
    ),
    # two <em> pairs removed, with MeSH
    (
        {
            "pmid": "42563340",
            "title": "Detection of the <em>VanA</em> and <em>VanB</em> Gene in Clinical Isolates of Vancomycin-Resistant Enterococci.",
            "abstract": "To determine the prevalence of vancomycin-resistant enterococci (VRE) among clinical isolates.",
            "entrez_date": "2026-08-07",
            "mesh": [
                {"ui": "D006801", "name": "Humans", "major": False},
                {"ui": "D065507", "name": "Vancomycin-Resistant Enterococci", "major": True},
                {"ui": "D014640", "name": "Vancomycin", "major": False},
            ],
            "keywords": [],
        },
        Document(
            doc_id="42563340",
            title="Detection of the VanA and VanB Gene in Clinical Isolates of Vancomycin-Resistant Enterococci",
            abstract="To determine the prevalence of vancomycin-resistant enterococci (VRE) among clinical isolates.",
            date=datetime.date(2026, 8, 7),
            mesh=[
                {"descriptor_id": "D006801", "name": "Humans", "major_topic": False},
                {"descriptor_id": "D065507", "name": "Vancomycin-Resistant Enterococci", "major_topic": True},
                {"descriptor_id": "D014640", "name": "Vancomycin", "major_topic": False},
            ],
            meta={"keywords": []},
        ),
    ),
    # <em> removed, Greek letter kept
    (
        {
            "pmid": "42634833",
            "title": "Association of <em>TGFβ2</em> gene polymorphism with growth performance and meat quality traits in Kampung Unggul Balitbangtan chickens under multienzyme supplementation.",
            "abstract": "Improving growth performance and meat quality is a major objective in genetic improvement.",
            "entrez_date": "2026-08-24",
            "mesh": [],
            "keywords": ["TGFβ2 gene", "meat quality"],
        },
        Document(
            doc_id="42634833",
            title="Association of TGFβ2 gene polymorphism with growth performance and meat quality traits in Kampung Unggul Balitbangtan chickens under multienzyme supplementation",
            abstract="Improving growth performance and meat quality is a major objective in genetic improvement.",
            date=datetime.date(2026, 8, 24),
            mesh=[],
            meta={"keywords": ["TGFβ2 gene", "meat quality"]},
        ),
    ),
    # &amp; unescaped
    (
        {
            "pmid": "42633629",
            "title": "Homogeneous Ruthenium-Catalyzed Carbonyl Groups Selective Hydrogenation Towards F&amp;F Industrial Applications.",
            "abstract": "Over the past decades, dsm-firmenich has devoted substantial efforts towards hydrogenation.",
            "entrez_date": "2026-08-23",
            "mesh": [],
            "keywords": ["F&F industry", "Hydrogenation"],
        },
        Document(
            doc_id="42633629",
            title="Homogeneous Ruthenium-Catalyzed Carbonyl Groups Selective Hydrogenation Towards F&F Industrial Applications",
            abstract="Over the past decades, dsm-firmenich has devoted substantial efforts towards hydrogenation.",
            date=datetime.date(2026, 8, 23),
            mesh=[],
            meta={"keywords": ["F&F industry", "Hydrogenation"]},
        ),
    ),
    (
        {
            "pmid": "42756483",
            "title": "Influence of Mother's Self-Efficacy, Social Support &amp; Intention on Exclusive Breastfeeding: A Systematic Review.",
            "abstract": "Breastmilk is widely considered to be the best source of nutrition for infants. ",
            "entrez_date": "2026-09-18",
            "mesh": [],
            "keywords": ["“breastfeeding”", "“self-efficacy”"],
        },
        Document(
            doc_id="42756483",
            title="Influence of Mother's Self-Efficacy, Social Support & Intention on Exclusive Breastfeeding: A Systematic Review",
            abstract="Breastmilk is widely considered to be the best source of nutrition for infants.",
            date=datetime.date(2026, 9, 18),
            mesh=[],
            meta={"keywords": ["“breastfeeding”", "“self-efficacy”"]},
        ),
    ),
    # literal "<" survives
    (
        {
            "pmid": "42545637",
            "title": "Risk Factors Associated with Extrauterine Growth Restriction (EUGR) Among Hospitalised Preterm Neonates <34 Weeks of Gestational Age: A Prospective Cohort Study - Correspondence.",
            "abstract": None,
            "entrez_date": "2026-08-03",
            "mesh": [],
            "keywords": [],
        },
        Document(
            doc_id="42545637",
            title="Risk Factors Associated with Extrauterine Growth Restriction (EUGR) Among Hospitalised Preterm Neonates <34 Weeks of Gestational Age: A Prospective Cohort Study - Correspondence",
            abstract="",
            date=datetime.date(2026, 8, 3),
            mesh=[],
            meta={"keywords": []},
        ),
    ),
    # "<...>" that isn't a formatting tag survives, with MeSH
    (
        {
            "pmid": "42601219",
            "title": "Recommendations to Streamline and Optimize USP Sterilization Informational Chapters: PDA Comments to USP <1229> and <1229.1>.",
            "abstract": "This paper reviews USP's proposed consolidation of sterilization informational chapters.",
            "entrez_date": "2026-08-14",
            "mesh": [
                {"ui": "D006801", "name": "Humans", "major": False},
                {"ui": "D013242", "name": "Sterilization", "major": True},
            ],
            "keywords": ["Sterilization", "USP <1229>", "USP<1229.1>"],
        },
        Document(
            doc_id="42601219",
            title="Recommendations to Streamline and Optimize USP Sterilization Informational Chapters: PDA Comments to USP <1229> and <1229.1>",
            abstract="This paper reviews USP's proposed consolidation of sterilization informational chapters.",
            date=datetime.date(2026, 8, 14),
            mesh=[
                {"descriptor_id": "D006801", "name": "Humans", "major_topic": False},
                {"descriptor_id": "D013242", "name": "Sterilization", "major_topic": True},
            ],
            meta={"keywords": ["Sterilization", "USP <1229>", "USP<1229.1>"]},
        ),
    ),
    (
        {
            "pmid": "42643783",
            "title": "Early (<24 hours) venous thromboembolism prophylaxis in traumatic brain injury: development of the EViTBI algorithm using a national cohort.",
            "abstract": "Optimal timing of venous thromboembolism (VTE) prophylaxis after traumatic brain injury is unclear.",
            "entrez_date": "2026-08-26",
            "mesh": [],
            "keywords": ["Prophylaxis", "Venous thromboembolism"],
        },
        Document(
            doc_id="42643783",
            title="Early (<24 hours) venous thromboembolism prophylaxis in traumatic brain injury: development of the EViTBI algorithm using a national cohort",
            abstract="Optimal timing of venous thromboembolism (VTE) prophylaxis after traumatic brain injury is unclear.",
            date=datetime.date(2026, 8, 26),
            mesh=[],
            meta={"keywords": ["Prophylaxis", "Venous thromboembolism"]},
        ),
    ),
    # "≥" and "<" survive
    (
        {
            "pmid": "42857893",
            "title": "Type 2 diabetes remission following a comprehensive metabolic program including surgery in adults with BMI ≥50 kg/m2 versus BMI <50 kg/m2.",
            "abstract": "Previous reports have suggested that higher baseline BMI   (bBMI) affects remission.",
            "entrez_date": "2026-10-10",
            "mesh": [],
            "keywords": ["diabetes remission", "obesity"],
        },
        Document(
            doc_id="42857893",
            title="Type 2 diabetes remission following a comprehensive metabolic program including surgery in adults with BMI ≥50 kg/m2 versus BMI <50 kg/m2",
            abstract="Previous reports have suggested that higher baseline BMI (bBMI) affects remission.",
            date=datetime.date(2026, 10, 10),
            mesh=[],
            meta={"keywords": ["diabetes remission", "obesity"]},
        ),
    ),
]


@pytest.mark.parametrize("raw, expected", CASES, ids=[r["pmid"] for r, _ in CASES])
def test_normalize(raw, expected):
    assert normalize(raw) == expected
