# -*- coding: utf-8 -*-
{
    'name': "commission",

    'summary': """
        Short (1 phrase/line) summary of the module's purpose, used as
        subtitle on modules listing or apps.openerp.com""",

    'description': """
        Long description of module's purpose
    """,

    'author': "Erum Asghar",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base','sale','account','product','stock','hr','sale_management'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/commission.xml',
        'views/commission_partner.xml',
        #'report/report_sale_order.xml',
        #'report/report_invoice.xml'
    ],
    # only loaded in demonstration mode
    'demo': [
        
    ],
}
