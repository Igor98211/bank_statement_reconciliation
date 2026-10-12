# from odoo import http


# class BankStatementReconciliation(http.Controller):
#     @http.route('/bank_statement_reconciliation/bank_statement_reconciliation', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/bank_statement_reconciliation/bank_statement_reconciliation/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('bank_statement_reconciliation.listing', {
#             'root': '/bank_statement_reconciliation/bank_statement_reconciliation',
#             'objects': http.request.env['bank_statement_reconciliation.bank_statement_reconciliation'].search([]),
#         })

#     @http.route('/bank_statement_reconciliation/bank_statement_reconciliation/objects/<model("bank_statement_reconciliation.bank_statement_reconciliation"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('bank_statement_reconciliation.object', {
#             'object': obj
#         })

