# -*- coding: utf-8 -*-
{
    'name': "Transfer For Independent Partner",

    'summary': """
       Generate Internal Transfer Note As Locations Interchanged""",

    'description': """
    Generate Internal Transfer Note As Locations Interchanged in Operations Stock Picking
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
        'views/transfer_independent_partner_views.xml',
    ],

}
