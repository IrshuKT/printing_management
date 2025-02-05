from odoo import models,api,fields


class PrintingPaper(models.Model):
    _name = 'printing.paper'
    _description = 'Printing Paper'

    name = fields.Char(string='Paper Name', required=True)
    gsm = fields.Float(string='Thickness (GSM)', required=True)
    width = fields.Float(string='Width (mm)', required=True)
    height = fields.Float(string='Height (mm)', required=True)
    price_per_sheet = fields.Float(string='Price per Sheet', required=True)
    active = fields.Boolean('Active',default=True)
