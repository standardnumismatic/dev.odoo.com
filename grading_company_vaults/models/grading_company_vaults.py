# -*- coding: utf-8 -*-


import datetime
from lxml import etree
from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime

from odoo.tools import float_compare


class StockLocationsInherit(models.Model):
    _inherit = 'stock.location'

    grading_company_vaults = fields.Boolean(string='Grading Company Vaults', default=False)


class StockPickingsInherit(models.Model):
    _inherit = 'stock.picking'

    # @api.model
    # def create(self, vals):
    #     res = super(StockPickingsInherit, self).create(vals)
    #     if res.location_id.grading_company_vaults:
    #         if res.picking_type_id.code == 'internal':
    #             for rec in res.move_ids_without_package:
    #                 if not rec.barcode:
    #                     raise UserError(_('Barcode on product must be filled'))
    #                 rec.product_id.write({
    #                     'barcode': rec.barcode,
    #                 })
    #     return res
    #
    # def write(self, vals):
    #     if self.location_id.grading_company_vaults:
    #         if self.picking_type_id.code == 'internal':
    #             for rec in self.move_ids_without_package:
    #                 if not rec.barcode:
    #                     raise UserError(_('Barcode on product must be filled'))
    #                 rec.product_id.write({
    #                     'barcode': rec.barcode,
    #                 })
    #     res = super(StockPickingsInherit, self).write(vals)
    #     return res


class StockMoveInherit(models.Model):
    _inherit = 'stock.move'

    barcode = fields.Char(related='product_id.barcode', string='Barcode', readonly=False)
