# -*- coding: utf-8 -*-


import datetime
from lxml import etree
from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from datetime import datetime
# from odoo.addons.purchase.models.purchase import PurchaseOrder as Purchase

from odoo.tools import float_compare


class PurchaseOrderInherit(models.Model):
    _inherit = 'purchase.order'


    payment_term_id = fields.Many2one('account.payment.term', 'Payment Terms', domain="['|', ('company_id', '=', False), ('company_id', '=', company_id)]")
    carriage_method = fields.Selection([
        ('by_land', 'By Land'),
        ('by_sea', 'By Sea'),
        ('by_air', 'By Air')
    ], string='Carriage Method')

    state = fields.Selection([
        ('draft', 'RFQ'),
        ('sent', 'RFQ Sent'),
        ('hos_approve', 'Approval For MD'),
        ('md_approve', 'Approval For CEO'),
        ('to approve', 'To Approve'),
        ('purchase', 'Purchase Order'),
        ('done', 'Locked'),
        ('reject', 'Reject'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', tracking=True)

    is_receipt_done = fields.Boolean(
        string='Receipt Done',
        default=False,
        compute='compute_is_receipt_done'
    )

    @api.model
    def _default_picking_type(self):
        return self._get_picking_type(self.env.context.get('company_id') or self.env.company.id)

    picking_type_id = fields.Many2one('stock.picking.type', 'Deliver To', required=True, default=_default_picking_type, domain="['|', ('warehouse_id', '=', False), ('warehouse_id.company_id', '=', company_id)]",
        help="This will determine operation type of incoming shipment")

    incoterm_id = fields.Many2one('account.incoterms', 'Incoterm', states={'done': [('readonly', True)]}, invisible=1, readonly=True, help="International Commercial Terms are a series of predefined commercial terms used in international transactions.")

    warehouse_id = fields.Many2one(
        'stock.warehouse', string='Warehouse',
        required=True, readonly=True, states={'draft': [('readonly', False)]}, check_company=True)

    def compute_is_receipt_done(self):
        flag = True
        picking_record = self.env['stock.picking'].search([('origin', '=', self.name)])
        for picking_rec in picking_record:
            if picking_rec.state != 'done':
                flag = False
        if flag:
            self.is_receipt_done = True
        else:
            self.is_receipt_done = False

    # @api.onchange('payment_term_id')
    # def onchange_payment_term_id(self):
    #     if self.env.user.has_group('purchase_approved_limits.group_hos_approval'):
    #         if self.state == 'purchase':
    #             if self.amount_total > 1000:
    #                 self.write({
    #                     'state': 'revised_md_approve'
    #                 })
    #     else:
    #         if self.state == 'purchase':
    #             if self.amount_total <= 1000:
    #                 self.write({
    #                     'state': 'revised_om_approve'
    #                 })
    #             elif self.amount_total > 1000 and self.amount_total <= 5000:
    #                 self.write({
    #                     'state': 'revised_hos_approve'
    #                 })
    #             else:
    #                 self.write({
    #                     'state': 'revised_md_approve'
    #                 })
        # self.is_payment_term_change = True

    def button_confirm(self):
        if self.amount_total > 1000 and self.amount_total <= 5000:
            self.write({
                'state': 'hos_approve'
            })
        if self.amount_total > 5000:
            self.write({
                'state': 'md_approve'
            })
        else:
            for order in self:
                if order.state not in ['draft', 'sent']:
                    continue
                order._add_supplier_to_product()
                # Deal with double validation process
                if order.company_id.po_double_validation == 'one_step'\
                        or (order.company_id.po_double_validation == 'two_step'\
                            and order.amount_total < self.env.company.currency_id._convert(
                                order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                        or order.user_has_groups('purchase.group_purchase_manager'):
                    order.button_approve()
                else:
                    order.write({'state': 'to approve'})
            return True



    # def om_button_approved(self):
    #     for order in self:
    #         if order.state not in ['draft', 'sent','om_approve']:
    #             continue
    #         order._add_supplier_to_product()
    #         # Deal with double validation process
    #         if order.company_id.po_double_validation == 'one_step'\
    #                 or (order.company_id.po_double_validation == 'two_step'\
    #                     and order.amount_total < self.env.company.currency_id._convert(
    #                         order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
    #                 or order.user_has_groups('purchase.group_purchase_manager'):
    #             order.button_approve()
    #         else:
    #             order.write({'state': 'to approve'})
    #     return True

    def hos_button_approved(self):
        for order in self:
            if order.state not in ['draft', 'sent','hos_approve']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True


    def md_button_approved(self):
        for order in self:
            if order.state not in ['draft', 'sent','md_approve']:
                continue
            order._add_supplier_to_product()
            # Deal with double validation process
            if order.company_id.po_double_validation == 'one_step'\
                    or (order.company_id.po_double_validation == 'two_step'\
                        and order.amount_total < self.env.company.currency_id._convert(
                            order.company_id.po_double_validation_amount, order.currency_id, order.company_id, order.date_order or fields.Date.today()))\
                    or order.user_has_groups('purchase.group_purchase_manager'):
                order.button_approve()
            else:
                order.write({'state': 'to approve'})
        return True

    def hos_button_reject(self):
        self.write({
            'state': 'reject'
        })

    def md_button_reject(self):
        self.write({
            'state': 'reject'
        })


class StockPickingInh(models.Model):
    _inherit = 'stock.picking'

# states={'draft,confirmed': [('readonly', False)]}

    location_dest_id = fields.Many2one(
        'stock.location', "Destination Location",
        default=lambda self: self.env['stock.picking.type'].browse(self._context.get('default_picking_type_id')).default_location_dest_id,
        check_company=True, required=True, readonly=False,
        )

# states={'draft': [('readonly', False)]}
    warehouse_domain_id = fields.Many2many('stock.location', compute='onchange_get_locations')

    @api.depends('location_dest_id')
    def onchange_get_locations(self):
        if self.origin:
            locations = self.env['stock.location'].search([('location_id', '=', self.purchase_id.warehouse_id.code)])
            self.warehouse_domain_id = locations.ids
        else:
            locations = self.env['stock.location'].search([])
            self.warehouse_domain_id = locations.ids
