# Verified 2025 mock-exam layouts

All six files contain a usable Japanese text layer. OCR is not the primary extraction method. Page numbers are one-indexed.

| Round | Pages | Commercial problem | Commercial answer | Commercial explanation | Industrial problem | Industrial answer | Industrial explanation |
|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | 24 | 1 | 11 | 16 | 7 | 14 | 21-22 |
| 2 | 23 | 1 | 11 | 16 | 7 | 14 | 20-21 |
| 3 | 25 | 1 | 11 | 16 | 7 | 14 | 21-22 |
| 4 | 24 | 1 | 11 | 16 | 7 | 14 | 22-23 |
| 5 | 24 | 1 | 11 | 16 | 7 | 14 | 22 |
| 6 | 23 | 1 | 11 | 16 | 7 | 14 | 21 |

Use headings rather than fixed page numbers. The table is an expected-value check, not the selection algorithm.

## Verified invariants

- Each round has 5 top-level commercial journal questions and 3 top-level industrial journal questions.
- Each selected top-level question is worth 4 points; each round totals 32 selected points.
- All 48 selected top-level questions balance, and their problem choices, answer symbols, and explanation entries show no obvious mismatch.
- The 第4問 total shown on the answer page is 28 points because it includes part (2); selected part (1) is only 12 points.

## Known layout variations

- Round 3 commercial question 1 contains two explicit subtransactions worth 2 points each but remains one four-point top-level question.
- Other rounds also contain top-level questions with more than one journal entry. Preserve `subTransactions` while keeping one top-level question.
- Account names often extract with artificial character spacing.
- Wrapped Japanese words and currency numbers may split across lines or contain spaces inside digits.
- Answer tables contain many empty parentheses and can flatten debit/credit columns. Use explanation entries as the semantic source and the answer table as the independent check.
- Industrial explanations can start mid-page and can cross one page boundary. Stop at the top-level 第4問(2) heading.

## Verified explanation figures

The 48 target questions across all six rounds were visually audited at 170 dpi. Preserve only these three figures; all other target questions use `explanationImages: []`.

| Round | Question ID | Explanation page | Crop box `[left, top, right, bottom]` | Output filename |
|---:|---|---:|---|---|
| 1 | `2025-mock-r1-industrial-q2` | 22 | `[92, 284, 1203, 638]` | `2025-mock-r1-industrial-q2-figure-1.png` |
| 2 | `2025-mock-r2-industrial-q2` | 21 | `[235, 500, 1315, 985]` | `2025-mock-r2-industrial-q2-figure-1.png` |
| 5 | `2025-mock-r5-industrial-q2` | 22 | `[125, 820, 1320, 1500]` | `2025-mock-r5-industrial-q2-figure-1.png` |

- Round 1 shows the T-account-style calculation of labor rate variance.
- Round 2 shows fixed-budget manufacturing-overhead variance decomposition.
- Round 5 shows formula flexible-budget manufacturing-overhead variance decomposition.
- Rounds 3, 4, and 6 have no required explanation figures in the eight selected questions.
- Tables or box diagrams appearing under 第4問(2) are outside the selected scope even when they share an explanation page.
