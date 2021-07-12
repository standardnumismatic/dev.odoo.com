{
    'name': 'import_logistic Module',
    'version': '0.2',
    'category': 'accouting',
    'license': "AGPL-3",
    'summary': " ",
    'author': 'Itech Reosurces',
    'company': 'ItechResources',
    'depends': [
                'account',
                'purchase',
#                 'obro_workflows',
                ],
    'data': [
            'security/ir.model.access.csv',
            'data/lc_sequence.xml',
            # 'views/account_invoice.xml',
            'views/lc_view.xml',
            ],
    'installable': True,
    'auto_install': False,
}
