from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    s_for = fields.Selection([('local', 'LOCAL'), ('import', 'IMPORT')], string="Select For", required=True,
                             default='local',
                             readonly=True, states={'draft': [('readonly', False)]})

    is_lc = fields.Boolean('LC')
    is_tt = fields.Boolean('TT')

    lc_ref = fields.Char('Ref Number')
    tt_ref = fields.Char('TT Ref Number')

    lc_account = fields.Many2one('account.account', string='LC Account', readonly=True,
                                 states={'draft': [('readonly', False)]})
    lc_ids = fields.One2many('lc.tt', 'lc_id', string="LC and TT Field")

    fx_rate = fields.Float('FX Rate')
    # start
    lc_ref_no = fields.Char('Contract No.')
    bank_name = fields.Many2one('account.journal', string="Bank Name")
    condition = fields.Many2one('lc.condition', "Condition")

    # end

    # this field show in LC notebook

    _sql_constraints = [
        ('uniq_lc_ref',
         'unique(lc_ref)',
         'The reference must be unique'),
    ]

    @api.model
    def create(self, vals):
        if 'lc_ref' not in vals or vals['lc_ref'] == False and vals['is_lc'] == True:
            sequence = self.env.ref('import_logistic.seq_lc_auto')
            vals['lc_ref'] = sequence.next_by_id()

        if 'tt_ref' not in vals or vals['tt_ref'] == False and vals['is_tt'] == True:
            sequence = self.env.ref('import_logistic.seq_tt_auto')
            vals['tt_ref'] = sequence.next_by_id()
        return super(PurchaseOrder, self).create(vals)

    def compute(self):
        total_tt = 0.0
        total_lc = 0.0
        for lc in self.lc_ids:
            total_lc += lc.amount

        for line in self.order_line:
            line.sub_total_fc = line.sub_total_lp = line.sub_total_lp = 0.0
            line.sub_total_fc = line.product_qty * line.unit_pricefc
            line.sub_total_lp = line.sub_total_fc * self.fx_rate

        totalunit_pricefc = 0.0
        num_of_product = 0
        for line in self.order_line:
            num_of_product += 1
            totalunit_pricefc += line.unit_pricefc

        #         here other charges mean sum of all charges which created in LC and TT notebook
        lc_othercharges = 0.0

        for lc_id in self.lc_ids:
            lc_othercharges += lc_id.amount

        for line in self.order_line:
            line.lc_cost = ((total_lc / totalunit_pricefc) * line.unit_pricefc)

            if line.qty_received > 0:
                line.price_unit = (line.lc_cost + line.sub_total_lp) / line.qty_received

            elif line.product_qty != 0:
                line.price_unit = (line.lc_cost + line.sub_total_lp) / line.product_qty


class PurchaseOrderLine(models.Model):
    _inherit = "purchase.order.line"
    unit_pricefc = fields.Float('Unit Price FC')
    sub_total_fc = fields.Float('Subtotal FC')
    sub_total_lp = fields.Float('Subtotal LP')
    lc_cost = fields.Float('LC Cost')
    s_for = fields.Selection([('local', 'LOCAL'), ('import', 'IMPORT')], string="Select For", related='order_id.s_for')

    @api.depends('product_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:

            taxes = line.taxes_id.compute_all(line.price_unit, line.order_id.currency_id, line.product_qty,
                                              product=line.product_id, partner=line.order_id.partner_id)
            if line.s_for != 'import':
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal': taxes['total_excluded'],
                })
            else:
                line.update({
                    'price_tax': taxes['total_included'] - taxes['total_excluded'],
                    'price_total': taxes['total_included'],
                    'price_subtotal': line.lc_cost + line.sub_total_lp,
                })
                line.price_subtotal = line.lc_cost + line.sub_total_lp
                if line.qty_received > 0:
                    line.price_unit = line.price_subtotal / line.qty_received
                else:
                    line.price_unit = line.price_subtotal / line.product_qty

                line.price_subtotal = line.lc_cost + line.sub_total_lp


#                     if line.qty_received > 0:
#                         line.price_unit = line.price_subtotal/line.qty_received
#                     elif line.product_qty !=0:
#                         line.price_unit = line.price_subtotal/line.product_qty
#         self.env['purchase.order'].compute()

class LcCharges(models.Model):
    _name = "lc.tt"

    lc_id = fields.Many2one('purchase.order')
    name = fields.Many2one('lc.tt.name', String='Name')
    amount = fields.Float('Amount')


class LcTtName(models.Model):
    _name = "lc.tt.name"

    name = fields.Char('Name')


class LcCondition(models.Model):
    _name = "lc.condition"

    name = fields.Char('Name')


class AccountMove(models.Model):
    _inherit = "account.move"

    lc_ref_po = fields.Many2one('purchase.order', string='PO Ref of LC OR TT')

    lc_insurance = fields.Float('Insurance')
    lc_clearing = fields.Float('Clearing Charges')
    lc_ref = fields.Char('LC Ref Number', related="lc_ref_po.lc_ref")
    tt_ref = fields.Char('TT Ref Number', related="lc_ref_po.tt_ref")

    is_lc_jour_entr = fields.Boolean('Is LC', related="journal_id.is_lc_jour")
    is_tt_jour_entr = fields.Boolean('Is LT', related="journal_id.is_tt_jour")

    @api.onchange('lc_ref_po')
    def add_account(self):
        if self.lc_ref_po.id != False:
            lc_line_ids = []
            r = ({
                'account_id': self.lc_ref_po.lc_account.id,
                #                     'date_maturity': '03-01-2018',
                'name': str(self.lc_ref_po.lc_account.name),
            })
            lc_line_ids.append(r)

            lc_lines = self.line_ids.browse([])

            for r in lc_line_ids:
                lc_lines += lc_lines.new(r)
            self.line_ids = lc_lines

    def button_cancel(self):
        res = super(AccountMove, self).button_cancel()
        # for lc in  self.lc_ref_po.lc_ids:
        #     self.lc_ref_po.write({'lc_ids':[(1, lc.id,{
        #                                                 'amount':0.0})]})
        lc_line = []
        if self.journal_id.is_lc_jour == True and self.lc_ref_po != ' ' or self.journal_id.is_tt_jour == True and self.lc_ref_po != ' ':
            for lc_move in self.line_ids:
                vals = {
                    'po_ref': self.lc_ref_po,
                    'chrg_name': lc_move.lc_charges,
                    'chrg_debit': lc_move.debit,
                    'chrg_credit': lc_move.credit,
                }
                lc_line.append(vals)
        for line in lc_line:
            flag = 0
            for lc in self.lc_ref_po.lc_ids:
                if lc.name == line['chrg_name']:
                    flag = 1
                    prv_amount = lc.amount

                    if line['chrg_debit']:
                        curr_amount = prv_amount - line['chrg_debit']
                        if curr_amount < 0:
                            curr_amount = 0
                    else:
                        curr_amount = prv_amount + line['chrg_credit']
                        if curr_amount > 0:
                            curr_amount = 0
                    self.lc_ref_po.write({'lc_ids': [(1, lc.id, {
                        'amount': curr_amount})]})
            if flag == 0 and line['chrg_name'].id != False:

                if line['chrg_debit']:
                    curr_amount1 = line['chrg_debit']
                    if curr_amount1 < 0:
                        curr_amount1 = 0
                    self.lc_ref_po.write({'lc_ids': [(0, 0, {
                        'name': line['chrg_name'].id,
                        'amount': curr_amount1})]})
                else:
                    curr_amount1 = -line['chrg_credit']
                    if curr_amount1 > 0:
                        curr_amount1 = 0
                    self.lc_ref_po.write({'lc_ids': [(0, 0, {
                        'name': line['chrg_name'].id,
                        'amount': curr_amount1})]})
        return res

    def post(self):
        res = super(AccountMove, self).post()

        lc_line = []
        if self.journal_id.is_lc_jour == True and self.lc_ref_po != ' ' or self.journal_id.is_tt_jour == True and self.lc_ref_po != ' ':
            for lc_move in self.line_ids:
                vals = {
                    'po_ref': self.lc_ref_po,
                    'chrg_name': lc_move.lc_charges,
                    'chrg_debit': lc_move.debit,
                    'chrg_credit': lc_move.credit,
                }
                lc_line.append(vals)
        for line in lc_line:
            flag = 0
            for lc in self.lc_ref_po.lc_ids:
                if lc.name == line['chrg_name']:
                    flag = 1
                    prv_amount = lc.amount

                    if line['chrg_debit']:
                        curr_amount = prv_amount + line['chrg_debit']
                    else:
                        curr_amount = prv_amount - line['chrg_credit']
                    self.lc_ref_po.write({'lc_ids': [(1, lc.id, {
                        'amount': curr_amount})]})
            if flag == 0 and line['chrg_name'].id != False:

                if line['chrg_debit']:
                    curr_amount1 = line['chrg_debit']
                    self.lc_ref_po.write({'lc_ids': [(0, 0, {
                        'name': line['chrg_name'].id,
                        'amount': curr_amount1})]})
                else:
                    curr_amount1 = -line['chrg_credit']
                    self.lc_ref_po.write({'lc_ids': [(0, 0, {
                        'name': line['chrg_name'].id,
                        'amount': curr_amount1})]})
        return res


class AccountMoveLine(models.Model):
    _inherit = "account.move.line"
    lc_charges = fields.Many2one('lc.tt.name', string="Charges")
    is_lc_jour_entr = fields.Char('Is LC', compute="get_lctt")  # related="move_id.lc_ref")
    is_tt_jour_entr = fields.Char('Is LT', compute="get_lc")

    #     is_lc_jour_entr = fields.Boolean('Is LC',related="move_id.is_lc_jour_entr")
    #     is_tt_jour_entr = fields.Boolean('Is LT',related="move_id.is_tt_jour_entr")

    @api.depends('account_id')
    def get_lctt(self):
        for lc in self:
            lc.is_lc_jour_entr = lc.move_id.lc_ref

    @api.depends('account_id')
    def get_lc(self):
        for lc in self:
            lc.is_tt_jour_entr = lc.move_id.tt_ref


class AccountJournal(models.Model):
    _inherit = "account.journal"
    is_lc_jour = fields.Boolean('Is LC')
    is_tt_jour = fields.Boolean('Is TT')
