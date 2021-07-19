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
    
class CommissionSaleEmployee(models.Model):
    _inherit = "sale.order" 
    commission_for = fields.Many2one("hr.employee", string="Commission for",required = True)        
    
#     @api.model
#     def create(self, vals):
#         if vals['commission_for'] ==  False:
#             raise UserError(_('please select commissioned employee'))
#         res= super(CommissionSaleEmployee,self).create(vals)
#         return res