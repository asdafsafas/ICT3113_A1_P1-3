---
type: concept
title: "Ticket Categories"
created: 2026-11-13
updated: 2026-11-13
tags:
  - ict3113
  - concept
status: mature
related:
  - "[[Labelling Protocol]]"
  - "[[Accuracy Results]]"
sources:
  - "[[Assignment 1 Brief]]"
  - "[[Golden Set Summary]]"
complexity: basic
domain: "classification"
aliases:
  - "seven categories"
---

# The Seven Ticket Categories

Fixed by the brief, and still fixed in A2. Definitions from `labeler/protocol.json` v0.3 (summarised). The last column is the measured [[qwen2.5-7b]] recall.

| Category | Golden n | Covers | 7B recall |
|---|---|---|---|
| **Credit reporting** | 42 | Credit reports and bureaus (Equifax, Experian, TransUnion): wrong entries, disputes, identity-theft accounts, credit repair and monitoring | 81.0% |
| **Debt collection** | 17 | How a debt is being collected: calls, threats, debts not owed, verification requests, lawsuits | 82.4% |
| **Mortgage** | 27 | Home loans, escrow, modifications, foreclosure, HELOCs | 92.6% |
| **Credit card** | 18 | Card account: billing disputes, unauthorised charges, fees, limits, rewards | 88.9% |
| **Bank account or service** | 37 | Checking and savings, deposits and withdrawals, overdrafts, frozen funds, debit/ATM cards | 94.6% |
| **Consumer loan** | 24 | Non-mortgage instalment loans: auto, personal, payday, **student loans** (Navient, Nelnet, AES) | 70.8% |
| **Money transfer or service** | 30 | Wires, payment apps (PayPal, Cash App, Zelle, Venmo), remittances, money orders, **prepaid cards, crypto exchanges**, and scams through these | 66.7% |

In the labeller only, an 8th option **None / unclear** was allowed. It was never a final label: such tickets were resolved or excluded.

## Known confusion pairs
- Credit reporting ↔ Debt collection (who is the complaint against?).
- Bank account ↔ Money transfer (account takeover vs the transfer service used).
- Consumer loan ↔ Credit reporting (lender reporting disputes).
