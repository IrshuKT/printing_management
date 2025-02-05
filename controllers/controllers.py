# -*- coding: utf-8 -*-
# from odoo import http


# class PressManagement(http.Controller):
#     @http.route('/press_management/press_management/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/press_management/press_management/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('press_management.listing', {
#             'root': '/press_management/press_management',
#             'objects': http.request.env['press_management.press_management'].search([]),
#         })

#     @http.route('/press_management/press_management/objects/<model("press_management.press_management"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('press_management.object', {
#             'object': obj
#         })
