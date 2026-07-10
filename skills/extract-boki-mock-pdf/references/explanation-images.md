# Explanation image policy

`expl` is always the primary explanation. Add an `explanationImages` record only when the source uses two-dimensional layout to communicate a relationship that becomes materially harder to understand as plain text.

## Include

- T-accounts or box diagrams that show opening, current, and closing balances
- variance-analysis graphs that show heights, gaps, or decomposition
- process or cost-flow diagrams with arrows, braces, or spatial grouping
- allocation or cost tables whose row-and-column relationship is central to the explanation

## Exclude

- ordinary prose, headings, and linear calculation formulas
- a journal-entry table that can be represented directly by `debit` and `credit`
- decorative rules, score boxes, answer symbols, headers, footers, or copyright text
- a full page or an image containing another question
- a figure belonging to 第2問、第3問、第4問(2)、or 第5問

## File rules

- Render the source at 170–220 dpi and crop to a lossless PNG.
- Keep a small margin around the complete figure. Do not cut labels, arrows, braces, units, or notes required to interpret it.
- Use `2025-mock-rN-SECTION-qN-figure-N.png`, where `SECTION` is `commercial` or `industrial`.
- Reopen every crop at original size before marking it reviewed.
- Use descriptive Japanese `alt` text that communicates the figure's purpose, not merely 「図」.
- Use a short `caption` that identifies the accounting relationship shown.

## JSON record

```json
{
  "src": "assets/explanations/2025-mock/r1/2025-mock-r1-industrial-q2-figure-1.png",
  "mimeType": "image/png",
  "alt": "当月支給総額と月初・月末未払額を調整し、予定消費賃率による労務費との差額を示す計算図",
  "caption": "賃率差異の計算関係",
  "sourcePage": 22,
  "renderDpi": 170,
  "cropBox": [92, 284, 1203, 638],
  "width": 1111,
  "height": 354,
  "sha256": "64-character lowercase SHA-256",
  "reviewStatus": "reviewed"
}
```

`src` is relative to the app or package asset root. It must stay below `assets/explanations/`, must not contain `..`, and must point to the exact PNG whose dimensions and SHA-256 are recorded.
