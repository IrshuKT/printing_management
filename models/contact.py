from odoo import models,fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    total_printing_orders = fields.Integer(
        string="Total Printing Orders",
        compute='_compute_total_printing_orders'
    )

    def _compute_total_printing_orders(self):
        for partner in self:
            partner.total_printing_orders = len(partner.printing_order_ids)



