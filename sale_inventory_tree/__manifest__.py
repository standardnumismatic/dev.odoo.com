# -*- coding: utf-8 -*-
{
    'name': "Sale Inventory Tree",

    'summary': """
       Create a Menu on Sale and This will acts to show product varients""",

    'description': """
       Create a Menu on Sale and This will acts to show product varients
    """,

    'author': "Viltco",
    'website': "https://viltco.com",
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/14.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'sale',
    'version': '14.0.0.0',

    # any module necessary for this one to work correctly
    'depends': ['base', 'sale',],

    # always loaded
    'data': [
        # 'security/security.xml',
        'views/sale_inventory_tree_views.xml',
        'views/inventory_product_url_views.xml',
    ],

}
