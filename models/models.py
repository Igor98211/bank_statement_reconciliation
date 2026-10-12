from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.float_utils import float_compare


class BankIntegrationTransaction(models.Model):
    _name = 'bank.integration.transaction'
    _description = 'Bank Transaction'
    _order = 'transaction_date desc, id desc'
    _rec_name = 'reference'

    name = fields.Char(string='Description')
    transaction_date = fields.Date(string='Date', required=True)
    amount = fields.Float(string='Amount', required=True, digits=(16, 2))
    partner_id = fields.Many2one('res.partner', string='Partner')
    reference = fields.Char(string='Reference', required=True)
    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        domain=[('move_type', '=', 'out_invoice')],
    )
    state = fields.Selection(
        selection=[
            ('new', 'New'),
            ('matched', 'Matched'),
            ('ignored', 'Ignored'),
        ],
        string='State',
        default='new',
        required=True,
    )

    @api.constrains('state', 'invoice_id')
    def _check_matched_invoice(self):
        for transaction in self:
            if transaction.state == 'matched' and not transaction.invoice_id:
                raise ValidationError(_("A transaction cannot be matched without an invoice."))

    @api.onchange('invoice_id')
    def _onchange_invoice_id(self):
        """Show the invoice customer immediately, before the form is saved."""
        if self.invoice_id:
            self.partner_id = self.invoice_id.partner_id

    @api.model_create_multi
    def create(self, vals_list):
        vals_list = [self._values_with_invoice_partner(vals) for vals in vals_list]
        return super().create(vals_list)

    def write(self, vals):
        vals = self._values_with_invoice_partner(vals)
        return super().write(vals)

    @api.model
    def _values_with_invoice_partner(self, vals):
        invoice_id = vals.get('invoice_id')
        if not invoice_id:
            return vals
        invoice = self.env['account.move'].browse(invoice_id)
        return {**vals, 'partner_id': invoice.partner_id.id}

    @api.model
    def _get_bank_api_transactions(self):
        """Stand-in for an external banking API. Returns fixed test data."""
        return [
            {
                'date': '2026-09-30',
                'amount': 1500.00,
                'reference': 'INV/2026/0015',
            },
            {
                'date': '2026-09-30',
                'amount': 850.00,
                'reference': 'INV/2026/0016',
            },
            {
                'date': '2026-09-30',
                'amount': 300.00,
                'reference': 'INV/2026/9999',
            },
        ]

    @api.model
    def _find_duplicate(self, transaction_date, amount, reference):
        candidates = self.search([
            ('transaction_date', '=', transaction_date),
            ('reference', '=', reference),
        ])
        return candidates.filtered(
            lambda transaction: float_compare(transaction.amount, amount, precision_digits=2) == 0
        )[:1]

    @api.model
    def _import_bank_transactions(self):
        """Create one record per bank transaction. Skip rows already imported."""
        created = self.browse()
        for data in self._get_bank_api_transactions():
            transaction_date = fields.Date.to_date(data['date'])
            amount = data['amount']
            reference = data['reference']
            if self._find_duplicate(transaction_date, amount, reference):
                continue
            created |= self.create({
                'name': reference,
                'transaction_date': transaction_date,
                'amount': amount,
                'reference': reference,
            })
        return created

    def action_import_bank_transactions(self):
        self._import_bank_transactions()

    def _find_customer_invoice(self, reference):
        if not reference:
            return self.env['account.move']
        return self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('name', '=', reference),
        ], limit=1)

    def _auto_match(self):
        for transaction in self.filtered(lambda record: record.state == 'new'):
            invoice = transaction._find_customer_invoice(transaction.reference)
            if not invoice:
                continue
            transaction.write({
                'invoice_id': invoice.id,
                'state': 'matched',
            })

    def action_auto_match(self):
        """Match every new transaction. The list button may be called with no selection."""
        self.search([('state', '=', 'new')])._auto_match()

    def action_match(self):
        for transaction in self:
            if not transaction.invoice_id:
                raise ValidationError(_("A transaction cannot be matched without an invoice."))
            transaction.write({
                'partner_id': transaction.invoice_id.partner_id.id,
                'state': 'matched',
            })

    def action_ignore(self):
        self.write({'state': 'ignored'})
