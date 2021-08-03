# -*- coding: utf-8 -*-


from odoo.exceptions import AccessError, UserError, AccessDenied
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError, AccessError, MissingError, AccessDenied
from datetime import timedelta
from datetime import datetime
from datetime import date


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

    # def action_transfer_independent(self):
    #     picking_record = self.search([])
    #     for record in picking_record:
    #         if record.picking_type_id.sequence_code == 'INT':
    #             if record.date_deadlines:
    #                 if record.state == 'done' and record.date_deadlines <= datetime.now() and record.check_internal == False:
    #                     print('Working')
    #                     vals = {
    #                             'location_id': record.location_dest_id.id,
    #                             'location_dest_id': record.location_id.id,
    #                             'partner_id': record.partner_id.id,
    #                             'picking_type_id': record.picking_type_id.id,
    #                             'origin': record.name,
    #                         }
    #                     picking = self.env['stock.picking'].create(vals)
    #                     for line in record.move_line_ids_without_package:
    #                         location_record = self.env['stock.quant'].search([('product_id', '=', line.product_id.id), ('location_id', '=', line.location_dest_id.id), ('lot_id', '=', line.lot_id.id)])
    #                         lines = {
    #                             'picking_id': picking.id,
    #                             'product_id': line.product_id.id,
    #                             # 'lot_ids': [line.lot_id.id],
    #                             'name': line.product_id.name,
    #                             'product_uom': line.product_id.uom_id.id,
    #                             'location_id': record.location_dest_id.id,
    #                             'location_dest_id': record.location_id.id,
    #                             'product_uom_qty': location_record.available_quantity,
    #                             'quantity_done': location_record.available_quantity,
    #                         }
    #                         stock_move = self.env['stock.move'].create(lines)
    #                     if picking:
    #                         record.check_internal = True
    #                         picking.action_confirm()
    #                         picking.action_assign()
    #                         picking.button_validate()

                            # moves = {
                            #     'move_id': stock_move.id,
                            #     'product_id': line.product_id.id,
                            #     'lot_id': line.lot_id.id,
                            #     'location_id': record.location_id.id,
                            #     'location_dest_id': record.location_dest_id.id,
                            #     'product_uom_id': line.product_id.uom_id.id,
                            #     'product_uom_qty': location_record.available_quantity,
                            #     'qty_done': location_record.available_quantity,
                            # }
                            # stock_move_line_id = self.env['stock.move.line'].create(moves)

    def action_transfer_independent(self):
        picking_record = self.search([])
        for record in picking_record:
            if record.picking_type_id.sequence_code == 'INT':
                if record.date_deadlines:
                    if record.state == 'done' and record.date_deadlines <= datetime.now() and record.check_internal == False:
                        print('Working')
                        line_val = []
                        for line in record.move_line_ids_without_package:
                            location_record = self.env['stock.quant'].search([('product_id', '=', line.product_id.id), ('location_id', '=', line.location_dest_id.id), ('lot_id', '=', line.lot_id.id)])
                            print(location_record.available_quantity)
                            line_val.append((0, 0, {
                                'product_id': line.product_id.id,
                                'name': line.product_id.name,
                                'lot_ids': [line.lot_id.id],
                                'product_uom_qty': location_record.available_quantity,
                                'product_uom': line.product_id.uom_id.id,
                                'location_id': record.location_dest_id.id,
                                'location_dest_id': record.location_id.id,
                                'reserved_availability': location_record.available_quantity,
                                'quantity_done': location_record.available_quantity,
                            }))
                        rec = self.env['stock.picking'].create({
                            'check_internal': True,
                            'partner_id': record.partner_id.id,
                            'picking_type_id': record.picking_type_id.id,
                            'location_id': record.location_dest_id.id,
                            'location_dest_id': record.location_id.id,
                            'origin': record.name,
                            'move_ids_without_package': line_val,
                        })
                        rec.action_confirm()
                        rec.action_assign()
                        rec.button_validate()
                        if rec:
                            record.check_internal = True

