Version 1: Extraction & Validation Standards

This document outlines the three core pillars for the Version 1 extraction system: Scope, Validation Logic, and System Boundaries.

1. What Information Are We Extracting?

For any legal documentation, the system must extract the following four core entities:

    Key Obligations: Responsibilities assigned to all involved parties.

    Penalties: Specific consequences for non-compliance.

    Important Dates & Time Constraints: Deadlines, effective dates, and periods.

    Risk Flags: Identification of specific clauses that introduce risk.

2. Definition of "Correctness"

"Correct" is defined not just by reasonableness, but by strict adherence to the source text. Below is the validation logic for each entity type.
A. Obligations

Correct means:

    ✅ The obligation exists explicitly in the text.

    ✅ The subject (e.g., Tenant vs. Landlord) is correctly identified.

    ✅ No requirements are invented or hallucinated.

Incorrect means:

    ❌ Inferring obligations that are not written.

    ❌ Mixing Landlord duties with Tenant duties.

B. Penalties

Correct means:

    ✅ Clearly linked to a specific condition.

    ✅ The penalty amount or action is not fabricated.

    ✅ If unclear, it is absent. (Do not guess).

Incorrect means:

    ❌ Vague penalties (e.g., "some fine may apply" when not specified).

    ❌ Hallucinated numbers or consequences.

C. Dates & Time Constraints

Correct means:

    ✅ Date format is valid.

    ✅ Date is explicitly mentioned or unambiguously derived.

    ✅ Event-date mapping is clear.

Incorrect means:

    ❌ Guessing dates.

    ❌ Incorrectly converting relative terms (e.g., converting "end of month" to the wrong specific date).

D. Risk Flags

Correct means:

    ✅ The flag is explainable via a concrete clause.

    ✅ The flag category is predefined (not free text).

    ✅ Low-confidence flags are explicitly marked as such.

Incorrect means:

    ❌ Emotional language.

    ❌ Legal advice.

    ❌ Over-flagging (flagging everything as a risk).

3. Unacceptable Output (System Boundaries)

This section defines the hard boundaries of the system. If these errors occur, the system is considered to have failed.

    CRITICAL RULE: The system extracts and flags. It does not give advice.

A. Hallucinated Facts

    Definition: Obligations that don’t exist, penalties with invented values, or dates not present in the text.

    Severity: This is the worst possible failure.

B. Schema Violations

    Definition: Missing required fields, wrong data types, or returning free-form text where structured data is expected.

    Protocol: If this happens, the system should fail rather than "try its best."

C. False Confidence

    Definition: Placing high confidence scores on ambiguous clauses, with no indication of uncertainty.

    Principle: Confidence must be earned, not assumed.

D. Legal / Advisory Language

    Definition: Using phrases such as "This is illegal," "You should sue," or "This violates the law."

    Protocol: Strictly forbidden. The system must remain neutral and factual.
