from odoo import models, fields, api,_
from odoo.exceptions import ValidationError , UserError


class CommissionPartner(models.Model):
    _inherit = "res.partner"
    
    independent_partner = fields.Boolean(string = "Independent partner", default = False)
#     wealth_manager = fields.Boolean(string = "Wealth manager", default = False)
    
    
class CommissionUser(models.Model):
    _inherit = "res.users" 
    commission_price = fields.Float('Commission %')
 
 
class CommissionEmployee(models.Model):
    _inherit = "hr.employee" 
    commission_price = fields.Float('Commission %')
    total_commission =fields.Float(string= 'Commission', compute="get_emp_commission")
     
     
    def get_emp_commission(self):
        for rec in self:
            amount = 0.0
            enteries = rec.env['account.move'].search([('commission_partner_id','=',rec.id),('move_type','=','entry')])  
            for record in enteries:
                amount= amount + record.commission_payable_total
            rec.total_commission =amount
                
    def view_emp_journal_entry(self):
        #         self.ensure_one()
        #         action = self.env["ir.actions.actions"]._for_xml_id("account.action_move_journal_line")
        #         if self.state == 'posted':
        #             action['domain']=[('ref','=', self.name)]
        #             action['context'] = {'create' : 0}
        #             return action
      
        if self:
#             action = self.env["ir.actions.actions"]._for_xml_id("commission.action_commission_emp_journal_entry_type")
#             action['domain']= [('commission_partner_id', '=', self.id),('journal_id.type','=','general')]
#             action['context'] = {'create' : 0}
#             
#             return action 
            custom_action = {
                'type': 'ir.actions.act_window',
                'name': 'Employee Commission journal Entry',
#                 'view_id': self.env.ref('account.action_move_journal_line', False).id,
                'view_id': self.env.ref('commission.view_tree_emplyee_je', False).id,
                'target': 'current',
                'context':{'create' : 0},
                'domain': [('commission_partner_id', '=', self.id),('journal_id.type','=','general')],
                'res_model': 'account.move',
#                 'view_mode' : 'tree',
                 'views': [[False, 'tree'],[False, 'form']],
            }
 
            return custom_action
    
    
    
    
    
    
class CommissionSaleEmployee(models.Model):
    _inherit = "sale.order" 
    commission_for = fields.Many2one("hr.employee", string="Commission for")        
    
#     @api.model
#     def create(self, vals):
#         if vals['commission_for'] ==  False:
#             raise UserError(_('please select commissioned employee'))
#         res= super(CommissionSaleEmployee,self).create(vals)
#         return res