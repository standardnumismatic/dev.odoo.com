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
            record.is_show_payment = True
