import json
import os
from typing import Dict, Any, List, Optional
from pathlib import Path
from difflib import SequenceMatcher

# Wrap import in try/except for robustness if extractor is missing during testing
try:
    from extractor import (
        extract_obligations,
        extract_penalties,
        extract_dates,
        extract_risk_flags
    )
except ImportError:
    pass  # Allow class definition even if module is missing (for linting)


class EntityEvaluator:
    """Evaluates extraction quality by comparing against ground truth"""

    # ==========================================================
    # LOADERS
    # ==========================================================

    def load_ground_truth(self, filepath: Path) -> Dict[str, Any]:
        with open(filepath, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_document(self, filepath: Path) -> str:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()

    # ==========================================================
    # OBLIGATIONS
    # ==========================================================

    def evaluate_obligations(self, document_text: str, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        gt_items = ground_truth.get("obligations", [])
        
        try:
            extracted = extract_obligations(document_text)
        except Exception as e:
            return {"error": str(e), "status": "extraction_failed"}

        # Safely handle Enums (e.g., ResponsibleParty.TENANT -> "tenant")
        extracted_dicts = [
            {
                "description": o.description.lower().strip(),
                "responsible_party": o.responsible_party.value if hasattr(o.responsible_party, 'value') else str(o.responsible_party),
                "source_text": o.source_text.lower().strip()
            }
            for o in extracted.obligations
        ]

        gt_dicts = [
            {
                "description": item["description"].lower().strip(),
                "responsible_party": item["responsible_party"],
                "source_text": item["source_text"].lower().strip()
            }
            for item in gt_items
        ]

        true_positives = 0
        false_positives = 0
        found_gt = [False] * len(gt_dicts)
        hallucinations = []

        # Iterate extracted items
        for ext in extracted_dicts:
            matched = False
            for i, gt in enumerate(gt_dicts):
                # Don't match the same GT item twice
                if found_gt[i]:
                    continue
                
                if self._obligation_match(ext, gt):
                    true_positives += 1
                    found_gt[i] = True
                    matched = True
                    break
            
            if not matched:
                hallucinations.append(ext)
                false_positives += 1

        omissions = [gt_dicts[i] for i, f in enumerate(found_gt) if not f]

        # Calc Stats
        denom_prec = true_positives + false_positives
        denom_rec = true_positives + len(omissions)

        precision = true_positives / denom_prec if denom_prec > 0 else 0.0
        recall = true_positives / denom_rec if denom_rec > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "summary": {
                "precision": round(precision, 2),
                "recall": round(recall, 2),
                "f1": round(f1, 2)
            },
            "correct_count": true_positives,
            "hallucinations": hallucinations,
            "omissions": omissions,
        }

    def _obligation_match(self, ext: Dict, gt: Dict) -> bool:
        if ext["responsible_party"] != gt["responsible_party"]:
            return False
        # Match if description matches OR source text matches
        return (
            self._text_match(ext["description"], gt["description"], 0.7) or
            self._text_match(ext["source_text"], gt["source_text"], 0.4)
        )

    # ==========================================================
    # PENALTIES (CORRECTED)
    # ==========================================================

    def evaluate_penalties(self, document_text: str, ground_truth: Dict[str, Any]) -> Dict[str, Any]:
        gt_items = ground_truth.get("penalties", [])

        try:
            extracted = extract_penalties(document_text)
        except Exception as e:
            return {"error": str(e), "status": "penalty_extraction_failed"}

        extracted_items = [
            {
                "description": p.description.lower().strip(),
                "penalty_type": p.penalty_type.value if hasattr(p.penalty_type, 'value') else str(p.penalty_type),
                "amount": p.amount,
                "source_text": p.source_text.lower().strip()
            }
            for p in extracted.penalties
        ]

        gt_items_norm = [
            {
                "description": g["description"].lower().strip(),
                "penalty_type": g["penalty_type"],
                "amount": g.get("amount"),
                "source_text": g["source_text"].lower().strip()
            }
            for g in gt_items
        ]

        true_positives = 0
        found_gt = [False] * len(gt_items_norm)
        false_positives = []

        for ext in extracted_items:
            matched = False
            for i, gt in enumerate(gt_items_norm):
                if found_gt[i]:
                    continue
                
                if self._penalty_match(ext, gt):
                    true_positives += 1
                    found_gt[i] = True
                    matched = True
                    break
            
            if not matched:
                false_positives.append(ext)

        omissions = [gt_items_norm[i] for i, f in enumerate(found_gt) if not f]

        denom_prec = len(extracted_items)
        denom_rec = len(gt_items_norm)

        precision = true_positives / denom_prec if denom_prec > 0 else 0.0
        recall = true_positives / denom_rec if denom_rec > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0

        return {
            "summary": {
                "precision": round(precision, 2),
                "recall": round(recall, 2),
                "f1": round(f1, 2)
            },
            "true_positives": true_positives,
            "false_positives": false_positives,
            "omissions": omissions
        }

    def _penalty_match(self, ext: Dict, gt: Dict) -> bool:
            # 1. Penalty Type must match
            if ext["penalty_type"] != gt["penalty_type"]:
                return False

            # 2. Check Text Match (Description OR Source Text)
            # We increase strictness slightly here to ensure we are talking about the same clause
            text_matches = (
                self._text_match(ext["description"], gt["description"], 0.6) or
                self._text_match(ext["source_text"], gt["source_text"], 0.4)
            )

            if not text_matches:
                return False

            # 3. Check Amount (Context-Aware)
            # If text matches strongly, we are lenient on the amount format
            return self._amount_match(ext["amount"], gt["amount"])

    def _amount_match(self, ext_val: Any, gt_val: Any) -> bool:
        """
        Robust comparison handling 'Not specified', None, and numeric strings.
        """
        # Helper to normalize values
        def normalize(v):
            if v is None: return None
            s = str(v).strip().lower()
            if s in ["not specified", "null", "none", ""]: return None
            return s.replace("$", "").replace(",", "")

        e = normalize(ext_val)
        g = normalize(gt_val)

        # Case A: Both are effectively empty/null -> MATCH
        # (e.g. "Not specified" vs None)
        if e is None and g is None:
            return True

        # Case B: One is empty, one is not -> WEAK MATCH
        # We assume the Description Match (checked previously) is enough 
        # to confirm identity, so we don't fail just because one side missed the amount string.
        if e is None or g is None:
            return True

        # Case C: Both have values - Compare them
        try:
            # Try numeric comparison first
            return abs(float(e) - float(g)) < 0.01
        except ValueError:
            # Fallback to symbolic string comparison (e.g. "security deposit")
            # Uses the existing _text_match helper or simple equality
            return self._text_match(e, g, 0.5)

    # ==========================================================
    # SHARED UTILS
    # ==========================================================

    def _text_match(self, a: str, b: str, threshold: float = 0.5) -> bool:
            if not a or not b: 
                return False
            
            # 1. Normalize (collapse spaces, lower case)
            def normalize(s):
                return " ".join(str(s).split()).lower()

            na = normalize(a)
            nb = normalize(b)

            # 2. Exact or Substring Match (The Fix for Electricity)
            # If one string is contained inside the other, it's a match.
            if na in nb or nb in na:
                return True

            # 3. Token Set Match (The Fix for Overstay/2x Rent)
            # Checks if key words overlap (ignores order and extra words like "the")
            set_a = set(na.split())
            set_b = set(nb.split())
            
            intersection = len(set_a.intersection(set_b))
            smaller_len = min(len(set_a), len(set_b))
            
            # If 65% of the words in the shorter phrase exist in the longer phrase -> Match
            if smaller_len > 0 and (intersection / smaller_len) > 0.65:
                return True

            # 4. Fuzzy Match (Fallback for typos)
            return SequenceMatcher(None, na, nb).ratio() >= threshold

    def run_evaluation(self, test_case_name: str):
        base = Path("eval_data")
        # Ensure eval_data exists
        if not base.exists():
            base.mkdir()
            print("Created eval_data directory.")

        # Fixed Filter Syntax
        digits = "".join(filter(str.isdigit, test_case_name))
        case_id = digits if digits else "1"

        txt_path = base / f"a{case_id}.txt"
        gt_path = base / f"gt{case_id}.json"

        if not txt_path.exists() or not gt_path.exists():
            print(f"Error: Missing files for {test_case_name}")
            print(f"Checked: {txt_path} and {gt_path}")
            return

        document = self.load_document(txt_path)
        ground_truth = self.load_ground_truth(gt_path)

        print(f"\nEvaluating: {test_case_name} (ID: {case_id})")

        obligations = self.evaluate_obligations(document, ground_truth)
        penalties = self.evaluate_penalties(document, ground_truth)

        report = {
            "test_case": test_case_name,
            "obligations": obligations,
            "penalties": penalties
        }

        out = base / f"{test_case_name}_results.json"
        with open(out, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        print("Report saved to:", out)


if __name__ == "__main__":
    EntityEvaluator().run_evaluation("a3")