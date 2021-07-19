from odoo import models, fields

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    input_url = fields.Char(string='URL')
