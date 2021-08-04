# -*- coding: utf-8 -*-


from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError, MissingError, AccessDenied
from datetime import timedelta
from datetime import datetime
from datetime import date



class SaleOrderInherites(models.Model):
    _inherit = 'sale.order'

    rem_days = fields.Float(string='Remaining Days', compute='check_rem_days')
    expiry_date = fields.Date(string='Expiry Date')
    payment_count = fields.Integer(compute='compute_payments')
    is_show_payment = fields.Boolean(string='Show Payment Button', default=False)
    # is_show_create_invoice = fields.Boolean(string='Show Invoice Button', default=False, compute='compute_show_create_invoice')
    #
    #
    # def compute_show_create_invoice(self):
    #     for rec in self:
    #         pickings = self.env['stock.picking'].search([('origin', '=', rec.name)])
    #         if pickings:
    #             for picking in pickings:
    #                 if picking.state == 'done':
    #                     rec.is_show_create_invoice = True
    #                 else:
    #                     rec.is_show_create_invoice = False


    def compute_payments(self):
        for rec in self:
            count = self.env['account.payment'].search_count([('ref', '=', rec.name)])
            rec.payment_count = count


    def action_register_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Register Payments',
            'view_id': self.env.ref('sale_unreserve_quantity.advance_payments_wizard_form_view', False).id,
            'context': {'default_ref': self.name, 'default_order_amount': self.amount_total, 'default_user_id': self.user_id.id, 'default_amount': self.amount_total},
            'target': 'new',
            'res_model': 'advance.payments',
            'view_mode': 'form',
        }


    def action_show_payments(self):
        return {
            'type': 'ir.actions.act_window',
            'name': 'Register Payments',
            'view_id': self.env.ref('account.view_account_payment_tree', False).id,
            'target': 'current',
            'domain': [('ref', '=', self.name)],
            'res_model': 'account.payment',
            'views': [[False, 'tree'], [False, 'form']],
        }


    def check_rem_days(self):
        if self.date_order:
            o_date = self.date_order
            future = o_date.date() + timedelta(days=7)
            self.expiry_date = future
            delta = future - (datetime.now()).date()
            new = delta.days
        self.rem_days = new


    def action_change_state(self):
        sale_record = self.search([])
        for record in sale_record:
            if record.expiry_date:
                if (datetime.now()).date() >= record.expiry_date:
                    picking_rec = self.env['stock.picking'].search([('sale_id', '=', record.id)])
                    if picking_rec:
                        for rec in picking_rec:
                            if rec.state == 'assigned' and rec.picking_type_id.code == 'outgoing':
                                rec.do_unreserve()



class StockPickingInhs(models.Model):
    _inherit = 'stock.picking'

    rem_days = fields.Float(related='sale_id.rem_days', string='Remaining Days')
    expiry_date = fields.Date(related='sale_id.expiry_date', string='Expiry Date')
    is_show_validate = fields.Boolean(string='Show Validate Button', default=False, compute='compute_show_validate')
    location_id = fields.Many2one(
        'stock.location', "Source Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_src_id,
        check_company=True, required=True)
# states={'draft,confirmed': [('readonly', False)]}

    warehouse_domain_id = fields.Many2many('stock.location', compute='onchange_get_locations')

    @api.depends('location_id')
    def onchange_get_locations(self):
        if self.origin:
            print('if')
            locations = self.env['stock.location'].search([('location_id', '=', self.sale_id.warehouse_id.code)])
            self.warehouse_domain_id = locations.ids
        else:
            print('else')
            locations = self.env['stock.location'].search([])
            self.warehouse_domain_id = locations.ids

    def compute_show_validate(self):
        if self.picking_type_id.sequence_code in ['OUT', 'PICK', 'PACK']:
            print('abc')
            payments = self.env['account.payment'].search([('ref', '=', self.origin)])
            if payments:
                self.is_show_validate = True
            else:
                self.is_show_validate = False
        else:
            self.is_show_validate = True

class AccountMoveInhs(models.Model):
    _inherit = 'account.move'

    rem_days = fields.Float( string='Remaining Days', compute='check_fields')
    expiry_date = fields.Date( string='Expiry Date')
    is_check_payment_registered = fields.Boolean(string='Check Payment Registration', default=False, compute='check_payment_registered')

    def check_payment_registered(self):
        for record in self:
            sale_record = self.env['sale.order'].search([('name', '=', record.invoice_origin)])
            if sale_record:
                if sale_record.payment_count != False:
                    record.is_check_payment_registered = True
                else:
                    record.is_check_payment_registered = False    
            else:
                record.is_check_payment_registered = True


    def check_fields(self):
        for record in self:
            sale_rec = self.env['sale.order'].search([('name', '=', record.invoice_origin)])
            self.write({
            'rem_days': sale_rec.rem_days,
            'expiry_date': sale_rec.expiry_date
        })

class AccountPaymentInhs(models.Model):
    _inherit = 'account.payment'

    user_id = fields.Many2one('res.users', string='Sales Person')
    memo = fields.Char(string='Memo')
    reverse_move_id = fields.Many2one('account.move', string="Reverse Entry", compute="get_reverse_entry_id")
    is_entry_reversed =  fields.Boolean("Is Entry Reversed" ,default= False ,compute="get_reverse_entry_id")
    
    def get_reverse_entry_id(self):
        for rec in self:
            if rec.reversal_move_id:
                rec.reverse_move_id = rec.reversal_move_id.id
                rec.is_entry_reversed = True
            else:    
                rec.reverse_move_id = False
                rec.is_entry_reversed = False
    
