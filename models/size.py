from odoo import models, fields,api


class PaperSize(models.Model):
    _name = 'printing.paper.size'
    _description = 'Paper Size'

    name = fields.Char(string="Out Type", required=True)
    width = fields.Float(string='Width (mm)', required=True)
    height = fields.Float(string='Height (mm)', required=True)


