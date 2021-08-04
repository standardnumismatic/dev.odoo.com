# -*- coding: utf-8 -*-
{
    'name': "Grading Company Vaults",

    'summary': """
       Create a Boolean Field field on locations and generate error on Pickings if barcode isn't available""",

    'description': """
       Create a Boolean Field field on locations and generate error on Pickings if barcode isn't available
    """,

    'author': "Viltco",
    'website': "https://viltco.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'stock',
    'version': '14.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock', 'purchase'],

    # always loaded
    'data': [
        'views/grading_company_vaults_views.xml',
        'views/purchase_grading_views.xml',
    ],

}
