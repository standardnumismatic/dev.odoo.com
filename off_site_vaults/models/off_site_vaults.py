# -*- coding: utf-8 -*-


import datetime
from lxml import etree
from odoo import models, fields, api, _
from datetime import timedelta
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

from odoo.tools import float_compare


class StockLocationInherit(models.Model):
    _inherit = 'stock.location'

    off_site_vaults = fields.Boolean(string='Off Site Vaults', default=False)


class StockPickingInherites(models.Model):
    _inherit = 'stock.picking'


    state = fields.Selection([
        ('draft', 'Draft'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting'),
        ('assigned', 'Ready'),
        ('ceo_approve', 'Waiting For Approval'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
        ('rejected', 'Rejected'),
    ], string='Status', compute='_compute_state',
        copy=False, index=True, readonly=True, store=True, tracking=True,
        help=" * Draft: The transfer is not confirmed yet. Reservation doesn't apply.\n"
             " * Waiting another operation: This transfer is waiting for another operation before being ready.\n"
             " * Waiting: The transfer is waiting for the availability of some products.\n(a) The shipping policy is \"As soon as possible\": no product could be reserved.\n(b) The shipping policy is \"When all products are ready\": not all the products could be reserved.\n"
             " * Ready: The transfer is ready to be processed.\n(a) The shipping policy is \"As soon as possible\": at least one product has been reserved.\n(b) The shipping policy is \"When all products are ready\": all product have been reserved.\n"
             " * Done: The transfer has been processed.\n"
             " * Cancelled: The transfer has been cancelled.")

    def button_validate(self):
        if self.location_id.off_site_vaults == True or self.location_dest_id.off_site_vaults == True:
            if self.picking_type_id.code in ['internal', 'incoming', 'outgoing']:
                self.write({
                    'state': 'ceo_approve'
                })
            else:
                res = super(StockPickingInherites, self).button_validate()
                return res
        else:
            res = super(StockPickingInherites, self).button_validate()
            return res

    def ceo_button_approved(self):
        res = super(StockPickingInherites, self).button_validate()
        return res

    def ceo_button_reject(self):
        self.write({
            'state': 'rejected'
        })


class StockImmediateTransferInh(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.immediate_transfer_line_ids:
            if line.to_immediate is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        for picking in pickings_to_do:
            # If still in draft => confirm and assign
            if picking.state == 'draft':
                picking.action_confirm()
                if picking.state != 'assigned':
                    picking.action_assign()
                    if picking.state != 'assigned':
                        raise UserError(_("Could not reserve all requested products. Please use the \'Mark as Todo\' button to handle the reservation manually."))
            for move in picking.move_lines.filtered(lambda m: m.state not in ['done', 'cancel']):
                for move_line in move.move_line_ids:
                    move_line.qty_done = move_line.product_uom_qty

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate)
            pickings_to_validate = pickings_to_validate - pickings_not_to_do
            return pickings_to_validate.with_context(skip_immediate=True).ceo_button_approved()
        return True


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    def process(self):
        pickings_to_do = self.env['stock.picking']
        pickings_not_to_do = self.env['stock.picking']
        for line in self.backorder_confirmation_line_ids:
            if line.to_backorder is True:
                pickings_to_do |= line.picking_id
            else:
                pickings_not_to_do |= line.picking_id

        for pick_id in pickings_not_to_do:
            moves_to_log = {}
            for move in pick_id.move_lines:
                if float_compare(move.product_uom_qty,
                                 move.quantity_done,
                                 precision_rounding=move.product_uom.rounding) > 0:
                    moves_to_log[move] = (move.quantity_done, move.product_uom_qty)
            pick_id._log_less_quantities_than_expected(moves_to_log)

        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            pickings_to_validate = self.env['stock.picking'].browse(pickings_to_validate).with_context(skip_backorder=True)
            if pickings_not_to_do:
                pickings_to_validate = pickings_to_validate.with_context(picking_ids_not_to_backorder=pickings_not_to_do.ids)
            return pickings_to_validate.ceo_button_approved()
        return True

    def process_cancel_backorder(self):
        pickings_to_validate = self.env.context.get('button_validate_picking_ids')
        if pickings_to_validate:
            return self.env['stock.picking']\
                .browse(pickings_to_validate)\
                .with_context(skip_backorder=True, picking_ids_not_to_backorder=self.pick_ids.ids)\
                .ceo_button_approved()
        return True
