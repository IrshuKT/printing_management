from odoo import models,fields,api


class PrintingProduct(models.Model):
    _name = 'printing.product'
    _description = 'Printing Product'

    name = fields.Char(string='Product Name', required=True)
    default_size = fields.Char(string='Default Size (e.g., A4, A5)', required=True)
    default_copies = fields.Integer(string='Default Copies', default=1)
    has_binding = fields.Boolean(string='Requires Binding?')
    has_serial_number = fields.Boolean(string='Requires Serial Number?')
    base_price = fields.Float(string='Base Price', required=True, help="Default price without additional charges")
