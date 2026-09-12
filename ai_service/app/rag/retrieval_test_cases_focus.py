"""retrieval_test_cases_focus.py — small eval subset for quick A/B iteration.

Builds on the full TEST_CASES in retrieval_test_cases.py, keeping only the
queries whose behavior changes under the anchor-selection edit under test:

    11 cases where the fix promotes the gold section to primary
       (potential hit@1 fixes)
    28 cases where the fix demotes the gold primary section
       (regression risk)

Usage:
    python -m ai_service.app.rag.eval --cases \
        ai_service/app/rag/retrieval_test_cases_focus.py
"""

from ai_service.app.rag.retrieval_test_cases import TEST_CASES, TestCase

SELECTED_IDS = [
    # 11 where the fix moves primary onto the gold (potential hit@1 fixes)
    "BNSS_003", "BNS_004", "CSS_004", "MBA_001", "ISA_002", "SMA_004",
    "MWPSC_005", "RPWD_002", "DPA_001", "FA_011", "COI_024",
    # 28 where the fix demotes the gold primary (regression risk)
    "BNS_011", "OSH_003", "OSH_006", "CSS_001", "JJ_001", "JJ_002",
    "GWA_002", "GWA_003", "GWA_004", "HMA_002", "HMA_003", "ISA_006",
    "REG_005", "LSA_001", "RTI_006", "MWPSC_001", "MWPSC_003", "DPA_004",
    "FA_008", "COI_004", "COI_013", "COI_012", "LAB_WAGE_004", "LAB_WAGE_009",
    "MVA_001", "MVA_002", "MVA_006", "PA_004",
]

SELECTED = [c for c in TEST_CASES if c.id in SELECTED_IDS]
assert len(SELECTED) == len(SELECTED_IDS), len(SELECTED)

TEST_CASES: list[TestCase] = SELECTED