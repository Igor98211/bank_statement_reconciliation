# Bank Statement / Reconciliation

## 1. Goal

Develop a small Odoo module that simulates importing bank transactions from an external banking system and matching them with existing customer invoices.

The main goal is to practice:

- working with Odoo Accounting models;
- importing external data;
- preventing duplicate imports;
- searching for existing invoices;
- automatic and manual transaction matching.

This is a simplified educational implementation. It does not need to implement full Odoo bank reconciliation.

---

## 2. Module

Suggested module name:

`bank_transaction_import`

The module should depend on:

```python
'account'
```

---

## 3. Bank Transaction Model

Create a new model:

`bank.integration.transaction`

Fields:

- `name` — transaction description;
- `transaction_date` — bank transaction date;
- `amount` — transaction amount;
- `partner_id` — customer/vendor;
- `reference` — payment reference supplied by the bank;
- `invoice_id` — matched customer invoice;
- `state` — transaction status:
  - `new`
  - `matched`
  - `ignored`.

Example:

```python
invoice_id = fields.Many2one(
    "account.move",
    string="Invoice",
)
```

The `invoice_id` field points to one existing customer invoice.

### Important relationship

One bank transaction can be matched with one invoice:

```text
Bank Transaction 1 ──────> Invoice 0015
Bank Transaction 2 ──────> Invoice 0016
Bank Transaction 3 ──────> Invoice 0017
```

The imported bank data contains multiple transactions. Each imported transaction becomes a separate `bank.integration.transaction` record.

Matching one bank transaction with multiple invoices is outside the scope of this task.

---

## 4. Bank Transaction List

The main user interface should be a list view of `bank.integration.transaction`.

Example:

```text
Bank Transactions

[Import Bank Transactions]  [Auto Match]

Date        Amount   Reference       Partner    Invoice       State
30.09.2026  1500     INV/2026/0015   ABC Ltd    INV/2026/0015 Matched
30.09.2026   850     INV/2026/0016   XYZ Ltd    —             New
30.09.2026   300     INV/2026/9999   —          —             New
```

Display the following columns:

- Date
- Amount
- Reference
- Partner
- Invoice
- State

Add useful filters:

- New
- Matched
- Ignored
- Date

---

## 5. Import Bank Transactions

Add the **Import Bank Transactions** button to the bank transaction list view.

The button should simulate an external banking API.

The test data can be defined directly in Python, for example:

```python
[
    {
        "date": "2026-09-30",
        "amount": 1500.00,
        "reference": "INV/2026/0015",
    },
    {
        "date": "2026-09-30",
        "amount": 850.00,
        "reference": "INV/2026/0016",
    },
    {
        "date": "2026-09-30",
        "amount": 300.00,
        "reference": "INV/2026/9999",
    },
]
```

For every imported bank transaction, create a separate
`bank.integration.transaction` record.

### Duplicate protection

Repeated imports must not create duplicate transactions.

A transaction should be considered a duplicate when the following values are the same:

- transaction date;
- amount;
- reference.

---

## 6. Automatic Matching

Add the **Auto Match** button to the bank transaction list view.

The button should process transactions with state `new`.

For each transaction, search for a customer invoice using the bank `reference`.

Example:

```text
Bank reference
INV/2026/0015
        ↓
Customer Invoice
INV/2026/0015
        ↓
invoice_id
```

If an invoice is found:

- set `invoice_id`;
- set `partner_id` from the invoice;
- change `state` to `matched`.

If no invoice is found:

- keep the transaction in state `new`;
- do not assign an invoice.

For this task, matching by reference is sufficient. Amount matching is not required.

The automatic matching operation should be able to process multiple transactions at once.

---

## 7. Bank Transaction Form

A separate complex form is not required.

Use a simple form view for opening and editing one bank transaction.

The form should display:

- `transaction_date`;
- `amount`;
- `reference`;
- `partner_id`;
- `invoice_id`;
- `state`.

The form is mainly needed for manual matching of a single transaction.

Example:

```text
Bank Transaction

Date:       30.09.2026
Amount:     850.00
Reference:  INV/2026/0016

Partner:    XYZ Ltd
Invoice:    [Select Invoice]

State:      New

[Match] [Ignore]
```

---

## 8. Manual Matching

A user must be able to open a `bank.integration.transaction` record and manually select an invoice.

The user selects:

- `invoice_id`.

The `partner_id` should then be taken automatically from the selected invoice.

The user should not need to select the partner separately.

Create a **Match** button.

When the button is pressed:

- `invoice_id` must be selected;
- `partner_id` is synchronized with the invoice partner;
- `state` becomes `matched`.

A transaction cannot be moved to `matched` without an invoice.

---

## 9. Ignore Transaction

Add an **Ignore** button to the bank transaction form.

The button should change the transaction state to:

`ignored`

An ignored transaction does not require an invoice.

---

## 10. Business Rules

1. One bank transaction can be matched with one invoice.
2. A transaction in state `matched` must have an `invoice_id`.
3. A transaction cannot be matched without an invoice.
4. Automatic matching searches for customer invoices by `reference`.
5. Manual matching allows the user to select an invoice.
6. When an invoice is selected, `partner_id` must be synchronized with the invoice partner.
7. Re-importing the same bank transaction must not create a duplicate.
8. Auto Match processes only transactions in state `new`.
9. An ignored transaction does not require an invoice.

---

## 11. Technical Requirements

Use standard Odoo models where appropriate:

- `account.move`
- `res.partner`

Customer invoices should be identified using:

```python
move_type == 'out_invoice'
```

Do not modify Odoo core code.

The external bank API should be simulated by a Python method returning hard-coded test data.

Keep the import and matching logic in clear, reusable model methods.

---

## 12. Tests

Add automated tests covering at least:

### Test 1 — Import

Import the test bank transactions and verify that the expected records are created.

### Test 2 — Duplicate Import

Run the import twice and verify that duplicate transactions are not created.

### Test 3 — Automatic Match

Create a customer invoice with a matching reference.

Run `Auto Match` and verify:

- `invoice_id` is set;
- `partner_id` is set;
- state becomes `matched`.

### Test 4 — Invoice Not Found

Create a bank transaction with an unknown reference.

Run `Auto Match` and verify:

- `invoice_id` is empty;
- state remains `new`.

### Test 5 — Manual Match

Open a bank transaction, select an invoice manually, and run `Match`.

Verify:

- `invoice_id` is set;
- `partner_id` is synchronized with the invoice;
- state becomes `matched`.

### Test 6 — Invalid Match

Try to match a transaction without selecting an invoice.

The operation should be rejected with an appropriate Odoo validation error.

### Test 7 — Ignore

Ignore a transaction and verify that its state becomes `ignored`.

### Test 8 — Multiple Transactions

Import several bank transactions and run `Auto Match`.

Verify that each transaction is matched independently with its corresponding invoice.

---

## 13. Expected Workflow

The final workflow should look like this:

```text
                    Bank Transactions
                           │
             ┌─────────────┴─────────────┐
             ↓                           ↓
          Import                      Auto Match
             ↓                           ↓
    Multiple transactions         Process "New"
                                         │
                              ┌──────────┴──────────┐
                              ↓                     ↓
                           Matched                 New
                                                     │
                                                     ↓
                                             Open transaction
                                                     │
                                             Select invoice
                                                     │
                                                   Match
```

Transactions that do not need to be processed can be moved to:

```text
Ignored
```

---

## 14. Out of Scope

The following functionality is intentionally excluded from this task:

- real bank API integration;
- importing CSV/Excel files;
- creating accounting journal entries;
- creating payments;
- full Odoo bank reconciliation;
- automatic reconciliation of partial payments;
- matching one bank transaction with multiple invoices;
- matching by amount and date;
- handling payment differences or residual amounts.
