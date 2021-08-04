from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import date

class AdvancePayments(models.TransientModel):
    _name = 'advance.payments'
    _description = 'Advance Payment'

    amount = fields.Float(string='Amount')
    order_amount = fields.Float(string='Order Amount')
    user_id = fields.Many2one('res.users', string='Sales Person')
    ref = fields.Char(string='Reference')
    payment_date = fields.Date(string='Payment Date', default=date.today())
    memo = fields.Char(string='Memo')
    rec_bank_account = fields.Many2one('res.partner.bank', string='Recipient Bank Account')

    def default_journal_id(self):
        journal = self.env['account.journal'].search([('name', '=', 'Bank')])
        return journal.id

    journal_id = fields.Many2one('account.journal', default=default_journal_id)
    
    
    
    
    def create_data(self):
        model = self.env.context.get('active_model')
        record = self.env[model].browse(self.env.context.get('active_id'))
        for rec in self:
            if rec.amount < rec.order_amount:
                raise UserError(_('Payment cannot be registered less than order amount'))
            else:
                vals = {
                    'journal_id': rec.journal_id.id,
                    'partner_id': record.partner_id.id,
                    'date': datetime.today().date(),
                    'amount': rec.amount,
                    'user_id': rec.user_id.id,
                    'partner_bank_id': rec.rec_bank_account.id,
                    'memo': rec.memo,
                    'state': 'draft',
                }
            payment = self.env['account.payment'].create(vals)
            payment.action_post()
            if record.invoice_ids:
                record.invoice_ids.payment_reference = payment.name
                payment.move_id.invoice_ref =  record.invoice_ids[0]
            record.is_show_payment = True
#             commission = record.user_id.commission_price
            if record.commission_for and record.commission_for.commission_price: 
                commission=record.commission_for.commission_price
            if record.referred_by:
                independent_partner = record.referred_by
                self.create_journal_entry(record , commission ,independent_partner)
                
            else: 
                self.create_journal_entry(record , commission)
                
                
            
    def create_journal_entry(self , rec , commission , inde_part = False):
        
              
        move_lines=[]
        credit_amount =0.0
        commission_debit_account = self.env['account.account'].search([('name','=','Commission expense')])
        commission_credit_account = self.env['account.account'].search([('name','=','Commission payable')])
        misc_journal = self.env['account.journal'].search([('type','=','general')],limit=1)
        
        journal_entry_dict ={
                            'journal_id': misc_journal.id,
                            'move_type': 'entry',
                            'date': self.payment_date,
                            'ref':rec.name,
                            'commission_partner_id':rec.commission_for.id,
                            'state':'draft'
                     }
        for line in rec.order_line:
            if not inde_part:
                debit = (line.price_subtotal * commission)/100
                
            else:
                subtotal = line.comm_extra_price * line.product_uom_qty  
                debit = (subtotal * commission )/100
                
                 
            credit_amount = credit_amount + debit
            debit_line = (0, 0 ,{
                'account_id': commission_debit_account.id,
                'partner_id':rec.partner_id.id,
                'debit':debit,
                'credit': 0.0,
                })
        
            move_lines.append(debit_line)
            
        credit_line = (0, 0 ,{
                'account_id': commission_credit_account.id,
                'partner_id':rec.partner_id.id,
                'debit':0.0,
                'credit': credit_amount,
                })
         
        move_lines.append(credit_line)
        journal_entry_dict['line_ids'] = move_lines
        journal_entry_id = self.env['account.move'].create(journal_entry_dict)
        journal_entry_id.action_post()
        if rec.invoice_ids:
            journal_entry_id.invoice_ref = rec.invoice_ids[0]
            
        #extra journal entry (extra price  - unit price)based on string
        if inde_part:
            ip_move_lines=[]
            ip_credit_amount= 0.0
            ip_je_dict = {
                        'journal_id': misc_journal.id,
                        'move_type': 'entry',
                        'date': self.payment_date,
#                         'commission_partner_id':rec.commission_for.id,
                        'ref':rec.name,
                        'state':'draft'
                    }
            
            for line in rec.order_line:
                debit = (line.price_unit - line.comm_extra_price) * line.product_uom_qty
                ip_credit_amount = ip_credit_amount + debit
                ip_debit_line = (0, 0 ,{
                'account_id': commission_debit_account.id,
                'partner_id':rec.referred_by.id,
                'debit':debit,
                'credit': 0.0,
                })
                ip_move_lines.append(ip_debit_line)
            
            ip_credit_line = (0, 0 ,{
                'account_id': commission_credit_account.id,
                'partner_id':rec.referred_by.id,
                'debit':0.0,
                'credit': ip_credit_amount,
                })
            
            ip_move_lines.append(ip_credit_line)
            
            ip_je_dict['line_ids'] = ip_move_lines
            ip_journal_entry_id = self.env['account.move'].create(ip_je_dict)
            ip_journal_entry_id.action_post() 