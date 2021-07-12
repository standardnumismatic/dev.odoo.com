# -*- coding: utf-8 -*-
{
    'name': "Off Site Vaults",

    'summary': """
       Create a field on locations and make approvals on  the Pickings""",

    'description': """
       Create a field on locations and make approvals on  the Pickings
    """,

    'author': "Viltco",
    'website': "https://viltco.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '14.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock'],

    # always loaded
    'data': [
        'security/security.xml',
        'views/off_site_vaults_views.xml',
    ],

}
