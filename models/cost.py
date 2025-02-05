from odoo import models,fields,api

class PrintingCostRange(models.Model):
    _name = 'printing.cost.range'
    _description = 'Cost Range for Binding and Serial Numbering'

    name = fields.Char(string="Name", required=True)
    min_quantity = fields.Integer(string="Min Quantity", required=True)
    max_quantity = fields.Integer(string="Max Quantity", required=True)
    binding_cost = fields.Float(string="Binding Cost", required=True)
    serial_number_cost = fields.Float(string="Serial Numbering Cost", required=True)

    _sql_constraints = [
        ('min_max_quantity_unique', 'unique(min_quantity, max_quantity)', 'The quantity range should be unique.')
    ]
