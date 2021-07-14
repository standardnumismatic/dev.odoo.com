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


class StockPickingInherit(models.Model):
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


    def button_validated(self):
        if self.location_id.off_site_vaults == True or self.location_dest_id.off_site_vaults == True:
            if self.picking_type_id.code in ['internal', 'incoming', 'outgoing']:
                self.write({
                    'state': 'ceo_approve'
                })
            else:
                res = super(StockPickingInherit, self).button_validate()
                return res
        else:
            res = super(StockPickingInherit, self).button_validate()
            return res

    def ceo_button_approved(self):
        res = super(StockPickingInherit, self).button_validate()
        return res

    def ceo_button_reject(self):
        self.write({
            'state': 'rejected'
        })
