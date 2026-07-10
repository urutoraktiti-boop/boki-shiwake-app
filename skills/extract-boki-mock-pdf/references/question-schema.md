# Question-set schema

Use UTF-8 JSON. Keep the file in `draft` status until every question is visually reviewed and the validator passes.

## Root fields

| Field | Requirement |
|---|---|
| `schemaVersion` | Integer `2` |
| `name` | `2025年度2級直前模試 第N回（第1問・第4問(1)）` |
| `status` | `draft` |
| `source` | Filename, SHA-256, round, expected counts, and selected pages |
| `questions` | Exactly 8 question objects |

## Question fields

| Field | Requirement |
|---|---|
| `questionId` | Stable ASCII ID: `2025-mock-rN-commercial-q1` etc. Never derive from display order later. |
| `section` | `commercial` or `industrial` |
| `questionNo` | Commercial `1..5`; industrial `1..3` |
| `label` | Human-readable round/section/question label |
| `category` | Reviewed learning category; do not leave `未分類` |
| `topic` | Exact problem title from [references/title-map.json](title-map.json) |
| `text` | Problem wording, including explicit subparts |
| `options` | Symbol-to-account mapping for this problem only |
| `debit` / `credit` | Arrays of `[symbol, positive_integer_amount]` |
| `subTransactions` | Optional array preserving separate journal entries within one top-level question |
| `expl` | Concise source-based explanation and calculations |
| `explanationImages` | Array of reviewed cropped-PNG records; use `[]` when no figure adds explanatory value |
| `group` | Round-specific group supplied by the template |
| `points` | Integer `4` |
| `sourcePages` | One-indexed `problem`, `answer`, and `explanation` page arrays, narrowed to pages containing that question after review |
| `reviewStatus` | `reviewed` only after visual comparison |

The current app uses flattened `debit` and `credit`. When `subTransactions` exists, the flattened rows must equal the combined subtransaction rows as multisets.

## Composite question example

```json
{
  "questionId": "2025-mock-r3-commercial-q1",
  "section": "commercial",
  "questionNo": 1,
  "label": "第3回 第1問 問1",
  "category": "純資産（株式・剰余金）",
  "topic": "複数取引を含む設問",
  "text": "問題文（例示）",
  "options": {"ア": "現金", "イ": "当座預金"},
  "debit": [["イ", 1000], ["ア", 200]],
  "credit": [["ア", 1000], ["イ", 200]],
  "subTransactions": [
    {"label": "(1)", "debit": [["イ", 1000]], "credit": [["ア", 1000]], "points": 2},
    {"label": "(2)", "debit": [["ア", 200]], "credit": [["イ", 200]], "points": 2}
  ],
  "expl": "出典に沿った解説",
  "explanationImages": [],
  "group": "2025年度2級直前模試 第3回・第1問",
  "points": 4,
  "sourcePages": {"problem": [1], "answer": [11], "explanation": [16]},
  "reviewStatus": "reviewed"
}
```

## Category guidance

For commercial questions, prefer an existing app category:

`現金・預金`, `商品売買`, `手形・電子記録債権`, `有価証券`, `固定資産`, `リース取引`, `引当金`, `税金・税効果`, `純資産（株式・剰余金）`, `収益認識・サービス業`, `外貨建取引`, `本支店会計`, `連結会計`, `決算整理・その他`.

For industrial questions, use a specific category beginning with `工業簿記・`, such as `工業簿記・材料費`, `工業簿記・労務費`, `工業簿記・製造間接費`, `工業簿記・差異分析`, or `工業簿記・本社工場会計`. Prefer the tested learning objective over the underlying cost element: when a question explicitly asks to record a named variance, use `工業簿記・差異分析`; otherwise use materials, labor, overhead, or head-office/factory accounting as appropriate. These categories require corresponding additions to the app category master when the import feature is implemented.
