# -*- coding: utf-8 -*-
{
    'name': "Purchase Approved Limits",

    'summary': """
       Create an Approval on PO to approve the PO""",

    'description': """
       Create an Approval on PO to approve the PO
    """,

    'author': "Viltco",
    'website': "https://viltco.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'purchase',
    'version': '14.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'purchase'],

    # always loaded
    'data': [
        'security/security.xml',
        'views/purchase_approved_limits_views.xml',
    ],

}
