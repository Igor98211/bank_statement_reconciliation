from odoo import Command
from odoo.exceptions import ValidationError
from odoo.tests.common import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestBankIntegrationTransaction(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        company = cls.env.company
        if not company.chart_template:
            cls.env['account.chart.template'].try_loading(
                'generic_coa', company, install_demo=False,
            )
        cls.partner_abc = cls.env['res.partner'].create({'name': 'ABC Ltd'})
        cls.partner_xyz = cls.env['res.partner'].create({'name': 'XYZ Ltd'})
        cls.income_account = cls.env['account.account'].search([
            *cls.env['account.account']._check_company_domain(company),
            ('account_type', '=', 'income'),
        ], limit=1)

    def _transactions(self):
        return self.env['bank.integration.transaction']

    def _import(self):
        return self._transactions()._import_bank_transactions()

    def _create_customer_invoice(self, partner, move_name, amount):
        return self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
            'invoice_date': '2026-09-30',
            'name': move_name,
            'invoice_line_ids': [Command.create({
                'name': 'Service',
                'quantity': 1.0,
                'price_unit': amount,
                'account_id': self.income_account.id,
            })],
        })

    def test_import_creates_transactions(self):
        created = self._import()

        self.assertEqual(len(created), 3)
        by_reference = {transaction.reference: transaction for transaction in created}
        self.assertEqual(by_reference['INV/2026/0015'].amount, 1500.00)
        self.assertEqual(by_reference['INV/2026/0016'].amount, 850.00)
        self.assertEqual(by_reference['INV/2026/9999'].amount, 300.00)
        self.assertTrue(all(
            transaction.transaction_date.isoformat() == '2026-09-30'
            for transaction in created
        ))
        self.assertEqual(set(created.mapped('state')), {'new'})
        self.assertFalse(created.invoice_id)

    def test_duplicate_import_is_skipped(self):
        first = self._import()
        second = self._import()

        self.assertEqual(len(first), 3)
        self.assertFalse(second)
        self.assertEqual(
            self._transactions().search_count([
                ('reference', 'in', ['INV/2026/0015', 'INV/2026/0016', 'INV/2026/9999']),
            ]),
            3,
        )

    def test_auto_match_sets_invoice_partner_and_state(self):
        invoice = self._create_customer_invoice(self.partner_abc, 'INV/TEST/0001', 1500.00)
        transaction = self._transactions().create({
            'transaction_date': '2026-09-30',
            'amount': 1500.00,
            'reference': invoice.name,
        })

        self._transactions().action_auto_match()

        self.assertEqual(transaction.invoice_id, invoice)
        self.assertEqual(transaction.partner_id, invoice.partner_id)
        self.assertEqual(transaction.state, 'matched')

    def test_auto_match_keeps_new_when_invoice_is_missing(self):
        transaction = self._transactions().create({
            'transaction_date': '2026-09-30',
            'amount': 300.00,
            'reference': 'INV/DOES/NOT/EXIST',
        })

        self._transactions().action_auto_match()

        self.assertFalse(transaction.invoice_id)
        self.assertEqual(transaction.state, 'new')

    def test_manual_match_synchronizes_partner(self):
        invoice = self._create_customer_invoice(self.partner_xyz, 'INV/TEST/0002', 850.00)
        transaction = self._transactions().create({
            'transaction_date': '2026-09-30',
            'amount': 850.00,
            'reference': 'BANK/MANUAL/0002',
        })
        transaction.invoice_id = invoice

        transaction.action_match()

        self.assertEqual(transaction.invoice_id, invoice)
        self.assertEqual(transaction.partner_id, invoice.partner_id)
        self.assertEqual(transaction.state, 'matched')

    def test_match_without_invoice_is_rejected(self):
        transaction = self._transactions().create({
            'transaction_date': '2026-09-30',
            'amount': 100.00,
            'reference': 'BANK/INVALID/0001',
        })

        with self.assertRaises(ValidationError):
            transaction.action_match()
        self.assertEqual(transaction.state, 'new')

    def test_ignore_sets_state(self):
        transaction = self._transactions().create({
            'transaction_date': '2026-09-30',
            'amount': 100.00,
            'reference': 'BANK/IGNORE/0001',
        })

        transaction.action_ignore()

        self.assertEqual(transaction.state, 'ignored')
        self.assertFalse(transaction.invoice_id)

    def test_auto_match_matches_each_transaction_independently(self):
        invoice_abc = self._create_customer_invoice(self.partner_abc, 'INV/2026/0015', 1500.00)
        invoice_xyz = self._create_customer_invoice(self.partner_xyz, 'INV/2026/0016', 850.00)

        self._import()
        self._transactions().action_auto_match()

        transaction_abc = self._transactions().search([('reference', '=', 'INV/2026/0015')], limit=1)
        transaction_xyz = self._transactions().search([('reference', '=', 'INV/2026/0016')], limit=1)
        transaction_unknown = self._transactions().search([('reference', '=', 'INV/2026/9999')], limit=1)

        self.assertEqual(transaction_abc.invoice_id, invoice_abc)
        self.assertEqual(transaction_abc.partner_id, self.partner_abc)
        self.assertEqual(transaction_abc.state, 'matched')

        self.assertEqual(transaction_xyz.invoice_id, invoice_xyz)
        self.assertEqual(transaction_xyz.partner_id, self.partner_xyz)
        self.assertEqual(transaction_xyz.state, 'matched')

        self.assertFalse(transaction_unknown.invoice_id)
        self.assertEqual(transaction_unknown.state, 'new')
