# -*- coding: utf-8 -*-

from odoo import models, fields, api, _

class ProductTemplateInherit(models.Model):
    _inherit = 'product.template'

    capex = fields.Boolean(string='Capex')
    non_capex = fields.Boolean(string='Non Capex')

    @api.onchange('capex')
    def onchange_capex(self):
        if self.capex == True:
            self.non_capex = False
        elif self.capex == False:
            self.non_capex = True

    @api.onchange('non_capex')
    def onchange_non_capex(self):
        if self.non_capex == True:
            self.capex = False
        elif self.non_capex == False:
            self.capex = True
