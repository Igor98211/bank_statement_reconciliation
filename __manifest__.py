{
    'name': 'Bank Transaction Import',
    'summary': 'Import bank transactions and match them with customer invoices',
    'description': """
Simulates a bank feed and matches each transaction with one customer invoice.
    """,
    'author': 'My Company',
    'website': 'https://www.yourcompany.com',
    'category': 'Accounting',
    'version': '19.0.1.0.0',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
