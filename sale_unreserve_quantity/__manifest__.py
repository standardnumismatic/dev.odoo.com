# -*- coding: utf-8 -*-
{
    'name': "Sale Unreserve Quantity",

    'summary': """
       Calculate Days and Unreserve Quantity On Sale Order""",

    'description': """
    Calculate Days and Unreserve Quantity On Sale Order Delivery and Invoice
    """,

    'author': "Viltco",
    'website': "https://viltco.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'sale',
    'version': '14.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale','sale_management'],

    # always loaded
    'data': [
        'wizards/advance_payment_wizard.xml',
        'security/ir.model.access.csv',
        'reports/report_templates.xml',
        'views/sale_unreserve_quantity_views.xml',
    ],

}
