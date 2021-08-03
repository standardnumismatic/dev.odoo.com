# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, Warning
from datetime import datetime
from datetime import date


class PurchaseGradingCompany(models.Model):
    _inherit = "purchase.order"

    reference_out_id = fields.Many2many('stock.picking', 'partner_id', 'location_id', string='Transfer Ref Out')

    reference_out_ids = fields.Many2many(
        'stock.picking',
        string='Pickings',
        copy=False,
        compute='compute_reference_out_ids'
    )

    @api.depends('reference_out_id')
    def compute_reference_out_ids(self):
        picking = self.env['stock.picking'].search([('picking_type_id.code', '=', 'internal'),('location_dest_id.grading_company_vaults', '=', True)])
        self.reference_out_ids = picking.ids

# ------------ start in ref ------------------

    reference_in_id = fields.Many2many('stock.picking', 'location_id', string='Transfer Ref In')

    reference_in_ids = fields.Many2many(
        'stock.picking',
        string='Pickings',
        copy=False,
        compute='compute_reference_in_ids'
    )

    @api.depends('reference_in_id')
    def compute_reference_in_ids(self):
        picking = self.env['stock.picking'].search([('picking_type_id.code', '=', 'internal'),('location_id.grading_company_vaults', '=', True)])
        self.reference_in_ids = picking.ids

    def action_create_invoice(self):
        res = super(PurchaseGradingCompany, self).action_create_invoice()
        ref_in =[]
        ref_out =[]
        for ref_outs in self.reference_out_id:
            ref_out.append(ref_outs.name)
        data_out = ','.join(ref_out)
        for ref_ins in self.reference_in_id:
            ref_in.append(ref_ins.name)
        data_in = ','.join(ref_in)
        bills = self.env['account.move'].search([('invoice_origin', '=', self.name)])
        print(bills)
        for bill in bills:
            bill.write({
                'reference_out': data_out,
                'reference_in': data_in,
            })
        return res


class StockPickingInhe(models.Model):
    _inherit = "stock.picking"

    location_id = fields.Many2one('stock.location', string='Source Locations')
    location_ids = fields.Many2many('stock.location', string='Locations', compute='compute_location_ids')

    @api.depends('location_id')
    def compute_location_ids(self):
        picking_type = self.env['stock.location'].search([('grading_company_vaults', '=', True)])
        self.location_ids = picking_type.ids

    def button_validate(self):
        if self.location_id.grading_company_vaults:
            if self.picking_type_id.code == 'internal':
                for rec in self.move_ids_without_package:
                    if not rec.barcode:
                        raise UserError(_('Barcode on product must be filled'))
                    rec.product_id.write({
                        'barcode': rec.barcode,
                    })
        res = super(StockPickingInhe, self).button_validate()
        return res


class AccountMoveInh(models.Model):
    _inherit = "account.move"

    reference_out = fields.Char(string='Reference Out')
    reference_in = fields.Char(string='Reference In')
