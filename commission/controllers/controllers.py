# -*- coding: utf-8 -*-
# from odoo import http


# class Commission(http.Controller):
#     @http.route('/commission/commission/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/commission/commission/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('commission.listing', {
#             'root': '/commission/commission',
#             'objects': http.request.env['commission.commission'].search([]),
#         })

#     @http.route('/commission/commission/objects/<model("commission.commission"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('commission.object', {
#             'object': obj
#         })
