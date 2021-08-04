from odoo import models, fields, api,_
from datetime import datetime
from odoo.exceptions import ValidationError , UserError
import json
# from odoo.tools.float_utils import stop


# 
class SaleOrderPartnerCommission(models.Model):
    _inherit = "sale.order"

    referred_by = fields.Many2one("res.partner" , string = "Referred by" ,domain =[('independent_partner','=',True)])

    def _prepare_invoice(self):
        invoice_vals = super(SaleOrderPartnerCommission , self)._prepare_invoice()
        if self.referred_by:
            invoice_vals['referred_by'] = self.referred_by.id
        if self.commission_for:
            invoice_vals['commission_partner_id'] = self.commission_for.id    
        return invoice_vals






class SaleOrderExtraPriceCommission(models.Model):
    _inherit="sale.order.line"

    comm_extra_price = fields.Float(sting= "Unit Price" , readonly=True)
    price_unit = fields.Float('Extra Price', required=True, digits='Product Price', default=0.0)



    def _prepare_invoice_line(self, **optional_values):
        """
        Prepare the dict of values to create the new invoice line for a sales order line.
 
        :param qty: float quantity to invoice
        :param optional_values: any parameter that should be added to the returned invoice line
        """
        self.ensure_one()
        res = {
            'display_type': self.display_type,
            'sequence': self.sequence,
            'name': self.name,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom.id,
            'quantity': self.qty_to_invoice,
            'discount': self.discount,
            'price_unit': self.price_unit,
            'comm_extra_price':self.comm_extra_price,
            'tax_ids': [(6, 0, self.tax_id.ids)],
            'analytic_account_id': self.order_id.analytic_account_id.id,
            'analytic_tag_ids': [(6, 0, self.analytic_tag_ids.ids)],
            'sale_line_ids': [(4, self.id)],
        }
        if optional_values:
            res.update(optional_values)
        if self.display_type:
            res['account_id'] = False
        return res


    @api.onchange('product_uom', 'product_uom_qty')
    def product_uom_change(self):
        pre_price =0.0
        if self.price_unit:
            pre_price = self.price_unit
        super(SaleOrderExtraPriceCommission,self).product_uom_change()
        self.price_unit = pre_price


    #
    #     @api.onchange('product_id')
    #     def product_id_change(self):
    #         super(SaleOrderExtraPriceCommission , self).product_id_change()
    #         if self.product_id:
    # #             if self.product_id.lst_price:
    #             self.comm_extra_price =  self.product_id.sale_extra_price
    #             self.price_unit= self.product_id.lst_price


    @api.onchange('product_id')
    def _onchange_extra_price(self):

        self.comm_extra_price =  self.product_id.lst_price


class AccountInvoiceExtraPrice(models.Model):
    _inherit="account.move.line"

    comm_extra_price = fields.Float(sting= "Price",)


    @api.onchange('product_id')
    def update_custom_unit_price(self):
        if self.product_id:
            self.comm_extra_price = self.product_id.lst_price


class AccountMoveCommissionInh(models.Model):

    _inherit="account.move"

    journal_entry_count = fields.Integer(string = "Journal Entry",compute="get_total_enteries")
    referred_by = fields.Many2one('res.partner',string="Referred by", domain =[('independent_partner','=',True)])
    invoice_ref = fields .Many2one('account.move', string="Invoice Ref")
    commission_partner_id = fields.Many2one("hr.employee", string="Commission for") 
    
    commission_payable_total = fields.Monetary(string='Commission Payable Total', compute='compute_commission_amount', currency_field='company_currency_id' ) 
    
    
    @api.depends(
    
        'line_ids.debit',
        'line_ids.credit',
        )
    def compute_commission_amount(self):
        for rec in self:
            payable_total = 0.0
            if rec.move_type == 'entry':
                com_payable_acc = self.env['account.account'].search([('name','=','Commission payable')])
               
                line_comm_payable = rec.line_ids.filtered(lambda q ,r = com_payable_acc : q.account_id.id == r.id)
                if line_comm_payable:
                    if line_comm_payable.debit > 0.0:
                        payable_total = line_comm_payable.debit
                        rec.commission_payable_total = -1 * payable_total    
                    elif line_comm_payable.credit > 0.0:
                        payable_total = line_comm_payable.credit  
                        rec.commission_payable_total =  payable_total       
                else:    
                    rec.commission_payable_total = payable_total    
          
            else:    
                rec.commission_payable_total = payable_total    
            
            return payable_total
            
    def action_post(self):
        res = super(AccountMoveCommissionInh,self).action_post()
        gen_entries =self.search([('ref','=',self.invoice_origin),('move_type','=','entry')])
        bank_entry = gen_entries.filtered(lambda q : q.journal_id.name =='Bank')
        self.payment_reference = bank_entry.name
        if gen_entries:
            for rec in gen_entries:
                rec.invoice_ref = self


        return res


    def get_total_enteries(self):
        for rec in self:
           
            if rec.invoice_origin:
                if rec.state == 'posted':
                    enteries = rec.env['account.move'].search([('invoice_ref','=',rec.id),('move_type','=','entry')])
                elif rec.state == 'draft':
                    enteries = rec.env['account.move'].search([('ref','=',rec.invoice_origin),('move_type','=','entry')])
                rec.journal_entry_count = len(enteries)
            else:
                rec.journal_entry_count = 0

    def view_journal_entry(self):
        #         self.ensure_one()
        #         action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        #         if self.state == 'posted':
        #             action['domain']=[('ref','=', self.name)]
        #             action['context'] = {'create' : 0}
        #             return action
        if self.invoice_origin != False:
            domain = [('invoice_ref', '=', self.id)] if self.state == 'posted' else [('ref','=',self.invoice_origin)]
            return {
                'type': 'ir.actions.act_window',
                'name': 'Commission journal Entry',
                'view_id': self.env.ref('account.action_move_journal_line', False).id,
                'target': 'current',
                'domain': domain,
                'res_model': 'account.move',
                'views': [[False, 'tree'], [False, 'form']],
            }

#     def action_post(self):
#         res = super(AccountMoveCommissionInh, self).action_post()
# 
#         if self.invoice_origin and 'S' in self.invoice_origin:
#           
# #             if self.amount == inv_rec.amount_total:
#             commission = self.invoice_user_id.commission_price
#             if self.referred_by:
#                 independent_partner = self.referred_by
#                 self.create_journal_entry(self , commission ,independent_partner)
#                  
#             else: 
#                 self.create_journal_entry(self , commission)
#         return res  


# class PaymentWizardInheritJE(models.TransientModel):
#     _inherit = "account.payment.register"
# 
#     def create_journal_entry(self , inv_rec , commission , inde_part = False):
# 
# 
#         move_lines=[]
#         credit_amount =0.0
#         commission_debit_account = self.env['account.account'].search([('name','=','Commission expense')])
#         commission_credit_account = self.env['account.account'].search([('name','=','Commission payable')])
#         misc_journal = self.env['account.journal'].search([('type','=','general')],limit=1)
# 
#         journal_entry_dict ={
#             'journal_id': misc_journal.id,
#             'move_type': 'entry',
#             'date': self.payment_date,
#             'ref':self.communication,
#             'state':'draft'
#         }
#         for line in inv_rec.invoice_line_ids:
#             if not inde_part:
#                 debit = (line.price_subtotal * commission)/100
# 
#             else:
#                 subtotal = line.comm_extra_price * line.quantity
#                 debit = (subtotal * commission )/100
# 
# 
#             credit_amount = credit_amount + debit
#             debit_line = (0, 0 ,{
#                 'account_id': commission_debit_account.id,
#                 'partner_id':inv_rec.partner_id.id,
#                 'debit':debit,
#                 'credit': 0.0,
#             })
# 
#             move_lines.append(debit_line)
# 
#         credit_line = (0, 0 ,{
#             'account_id': commission_credit_account.id,
#             'partner_id':inv_rec.partner_id.id,
#             'debit':0.0,
#             'credit': credit_amount,
#         })
# 
#         move_lines.append(credit_line)
#         journal_entry_dict['line_ids'] = move_lines
#         journal_entry_id = self.env['account.move'].create(journal_entry_dict)
# 
#         #extra journal entry (extra price  - unit price)based on string
#         if inde_part:
#             ip_move_lines=[]
#             ip_credit_amount= 0.0
#             ip_je_dict = {
#                 'journal_id': misc_journal.id,
#                 'move_type': 'entry',
#                 'date': self.payment_date,
#                 'ref':self.communication,
#                 'state':'draft'
#             }
# 
#             for line in inv_rec.invoice_line_ids:
#                 debit = (line.price_unit - line.comm_extra_price) * line.quantity
#                 ip_credit_amount = ip_credit_amount + debit
#                 ip_debit_line = (0, 0 ,{
#                     'account_id': commission_debit_account.id,
#                     'partner_id':inv_rec.referred_by.id,
#                     'debit':debit,
#                     'credit': 0.0,
#                 })
#                 ip_move_lines.append(ip_debit_line)
# 
#             ip_credit_line = (0, 0 ,{
#                 'account_id': commission_credit_account.id,
#                 'partner_id':inv_rec.referred_by.id,
#                 'debit':0.0,
#                 'credit': ip_credit_amount,
#             })
# 
#             ip_move_lines.append(ip_credit_line)
# 
#             ip_je_dict['line_ids'] = ip_move_lines
#             ip_journal_entry_id = self.env['account.move'].create(ip_je_dict)
# 
#         #         return journal_entry_id
# 
# 
#     def _create_payments(self):
#         res = super(PaymentWizardInheritJE , self)._create_payments()
#         if self.env.context.get('active_id'):
# 
#             inv_rec= self.env['account.move'].search([('id','=',self.env.context['active_id'])])
#             if inv_rec:
#                 if inv_rec.invoice_origin and 'S' in inv_rec.invoice_origin:
# 
#                     if self.amount == inv_rec.amount_total:
#                         commission = inv_rec.invoice_user_id.commission_price
#                         if inv_rec.referred_by:
#                             independent_partner = inv_rec.referred_by
#                             self.create_journal_entry(inv_rec , commission ,independent_partner)
# 
#                         else:
#                             self.create_journal_entry(inv_rec , commission)
# 
# 
# 
#         return res
        
class AccountMoveReversalCommisssionInh(models.TransientModel):
    _inherit = 'account.move.reversal'

    def reverse_moves(self):

        if self.move_ids.invoice_ref:
            commission_entries = self.env['account.move'].search([('invoice_ref','=',self.move_ids.invoice_ref.id)])
            if commission_entries:
                self.move_ids = commission_entries
               
        res = super(AccountMoveReversalCommisssionInh , self).reverse_moves()
        return res
        
        
    def _prepare_default_reversal(self, move):
        res = super(AccountMoveReversalCommisssionInh , self)._prepare_default_reversal(move)
        
        if move.journal_id.type == 'general':
            res['journal_id'] =  move.journal_id.id
            
        return res
    
        
    
    @api.model
    def default_get(self, fields):
        res = super(AccountMoveReversalCommisssionInh, self).default_get(fields)
        move_ids = self.env['account.move'].browse(self.env.context['active_ids']) if self.env.context.get('active_model') == 'account.move' else self.env['account.move']
        if 'journal_id' in fields:
            res['journal_id'] = move_ids.journal_id.id 
       
        return res    
    
        
 
    
    
        
        