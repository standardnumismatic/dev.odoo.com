# -*- coding: utf-8 -*-


from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError, MissingError, AccessDenied
from datetime import timedelta
from datetime import datetime
from datetime import date
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class StockPickingInhs(models.Model):
    _inherit = 'stock.picking'

    date_deadlines = fields.Datetime(string='Deadline')
    is_internal = fields.Boolean(string='Check Internal', default=False)
    check_internal = fields.Boolean(string='Internal Available', default=False)

    @api.onchange('picking_type_id')
    def compute_is_internal(self):
        if self.picking_type_id.sequence_code == 'INT':
            self.is_internal = True
        else:
            self.is_internal = False

    def action_transfer_independent(self):
        quant_in = 0
        a = 0
        quant_out = 0
        b = 0
        print('working')
        picking_record = self.search([])
        # print(picking_record)
        for record in picking_record:
            if record.picking_type_id.sequence_code == 'INT':
                if record.date_deadlines:
                    if record.state == 'done' and record.date_deadlines <= datetime.now() and record.check_internal == False:
                        rec = self.env['stock.picking'].create({
                            'partner_id': record.partner_id.id,
                            'picking_type_id': record.picking_type_id.id,
                            'location_id': record.location_dest_id.id,
                            'location_dest_id': record.location_id.id,
                            'origin': record.name,
                        })
                        for line in record.move_line_ids_without_package:
                            # location_record = self.env['stock.quant'].search([('product_id', '=', line.product_id.id), ('location_id', '=', line.location_dest_id.id)])
                            move_record = self.env['stock.move.line'].search([('product_id', '=', line.product_id.id), ('location_id', '=', line.location_id.id), ('location_dest_id', '=', line.location_dest_id.id), ('lot_id', '=', line.lot_id.id)])
                            for move in move_record:
                                if record.create_date < move.date:
                                    a = a + move.qty_done
                                    move.picking_id.check_internal = True
                            quant_in = a
                            print(quant_in)
                            move_recs = self.env['stock.move.line'].search([('product_id', '=', line.product_id.id), ('location_id', '=', line.location_dest_id.id), ('lot_id', '=', line.lot_id.id)])
                            for moves in move_recs:
                                if record.create_date < moves.date:
                                    b= b + moves.qty_done
                            quant_out = b
                            print(quant_out)
                            total_qty = quant_in - quant_out
                            if total_qty > 0:
                                line1 = self.env['stock.move.line'].create({
                                    'product_id': move_record.product_id.id,
                                    'lot_id': move_record.lot_id.id,
                                    # 'product_uom_qty': move_record.qty_done,
                                    'product_uom_qty': total_qty,
                                    'product_uom_id': move_record.product_id.uom_id.id,
                                    'location_id': move_record.location_dest_id.id,
                                    'location_dest_id': move_record.location_id.id,
                                    # 'qty_done': move_record.qty_done,
                                    'qty_done': total_qty,
                                    'picking_id': rec.id,
                                })
                        print(rec)
                        rec.action_confirm()
                        rec.action_assign()
                        rec.button_validate()
                        if rec:
                            record.check_internal = True


class stockQuantAutoUpdate(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def _update_reserved_quantity(self, product_id, location_id, quantity, lot_id=None, package_id=None, owner_id=None, strict=False):   
        """ Increase the reserved quantity, i.e. increase `reserved_quantity` for the set of quants
        sharing the combination of `product_id, location_id` if `strict` is set to False or sharing
        the *exact same characteristics* otherwise. Typically, this method is called when reserving
        a move or updating a reserved move line. When reserving a chained move, the strict flag
        should be enabled (to reserve exactly what was brought). When the move is MTS,it could take
        anything from the stock, so we disable the flag. When editing a move line, we naturally
        enable the flag, to reflect the reservation according to the edition.

        :return: a list of tuples (quant, quantity_reserved) showing on which quant the reservation
            was done and how much the system was able to reserve on it
        """
        self = self.sudo()
        rounding = product_id.uom_id.rounding

        quants = self._gather(product_id, location_id, lot_id=lot_id, package_id=package_id, owner_id=owner_id, strict=strict)

        if 'button_validate_picking_ids' in self.env.context:
            pic_id = self.env['stock.picking'].search([('id','=',self.env.context['button_validate_picking_ids'][0])])
            reserve_quant= self.update_reserve_quant_forcefully(pic_id.id , quants)

        reserved_quants = []

        if float_compare(quantity, 0, precision_rounding=rounding) > 0:
            # if we want to reserve
            available_quantity = sum(quants.filtered(lambda q: float_compare(q.quantity, 0, precision_rounding=rounding) > 0).mapped('quantity')) - sum(quants.mapped('reserved_quantity'))
            if float_compare(quantity, available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to reserve more products of %s than you have in stock.', product_id.display_name))
        elif float_compare(quantity, 0, precision_rounding=rounding) < 0:
            # if we want to unreserve
            available_quantity = sum(quants.mapped('reserved_quantity'))
           
            if float_compare(abs(quantity), available_quantity, precision_rounding=rounding) > 0:
                raise UserError(_('It is not possible to unreserve more products of %s than you have in stock.', product_id.display_name))
        else:
            return reserved_quants

        for quant in quants:
            if float_compare(quantity, 0, precision_rounding=rounding) > 0:
                max_quantity_on_quant = quant.quantity - quant.reserved_quantity
                if float_compare(max_quantity_on_quant, 0, precision_rounding=rounding) <= 0:
                    continue
                max_quantity_on_quant = min(max_quantity_on_quant, quantity)
                quant.reserved_quantity += max_quantity_on_quant
                reserved_quants.append((quant, max_quantity_on_quant))
                quantity -= max_quantity_on_quant
                available_quantity -= max_quantity_on_quant
            else:
                max_quantity_on_quant = min(quant.reserved_quantity, abs(quantity))
                quant.reserved_quantity -= max_quantity_on_quant
                reserved_quants.append((quant, -max_quantity_on_quant))
                quantity += max_quantity_on_quant
                available_quantity += max_quantity_on_quant

            if float_is_zero(quantity, precision_rounding=rounding) or float_is_zero(available_quantity, precision_rounding=rounding):
                break
        return reserved_quants

    def update_reserve_quant_forcefully(self ,picking_id, quants):
        pick_rec = self.env['stock.picking'].search([('id','=', picking_id)])
        if pick_rec.move_line_ids:
            for rec in pick_rec.move_line_ids:
                if rec.product_id.stock_quant_ids:
                    stock_quant_rec = rec.product_id.stock_quant_ids.filtered(lambda r , q_id = quants.id: r.id == q_id)
                    if stock_quant_rec:
                        stock_quant_rec.reserved_quantity =  rec.product_qty
                        break
