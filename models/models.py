from odoo import models, fields, api


class PrintingOrder(models.Model):
    _name = 'printing.order'
    _description = 'Printing Order'

    sequence = fields.Char(string='Memo No', required=True, copy=False, readonly=True, default=lambda self: ('New'))
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    order_date = fields.Date(string='Order Date', default=fields.Date.context_today)
    due_date = fields.Date(string='Due Date', required=True)
    out_product = fields.Selection([
        ('notice', 'Notice'), ('table_sheet', 'Table Sheet')
    ], string='Select Product')

    base_paper = fields.Many2one('product.product', string='Base Paper', domain="[('categ_id', '=', 'Base Papers')]")
    final_size = fields.Many2one('receipt.final.size', string='Final size', required=True)
    total_count = fields.Integer('Total Qty',default=500)
    designing_cost = fields.Float('Designing Charge', default=350)
    printing_charge = fields.Float('Printing Charge', compute='_compute_printing_charge', store=True)
    material_cost = fields.Float('Material Cost', compute='_compute_material_cost', store=True)
    total_cost = fields.Float('Total Cost', compute='_compute_total_cost', store=True)


    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Order Status', default='draft', track_visibility='onchange')

    def action_confirm(self):
        self.state = 'confirmed'

    def action_done(self):
        self.state = 'done'

    def action_cancel(self):
        self.state = 'cancel'

    #Material cost
    @api.depends('base_paper', 'final_size', 'total_count')
    def _compute_material_cost(self):
        for order in self:
            if order.base_paper and order.final_size and order.total_count:
                # Fetch qty_per_sheet from receipt.base.paper
                base_paper_record = self.env['receipt.base.paper'].search([
                    ('base_paper_id', '=', order.base_paper.id),
                    ('final_size', '=', order.final_size.id)
                ], limit=1)
                print(base_paper_record)
                if base_paper_record and base_paper_record.receipts_per_sheet:
                    qty_per_sheet = base_paper_record.receipts_per_sheet  # How many final sizes fit on one base paper sheet

                    # Calculate required sheets
                    required_sheets = order.total_count / qty_per_sheet
                    required_sheets = round(required_sheets)  # Round up if necessary
                    print('number of sheet is ',required_sheets)
                    # Get cost per sheet from base paper (product)
                    cost_per_sheet = order.base_paper.list_price
                    print('cost of sheet ',cost_per_sheet)
                    print('Base Paper:', order.base_paper.name)
                    if cost_per_sheet:
                        # Calculate material cost
                        order.material_cost = round(required_sheets * cost_per_sheet)
                    else:
                        order.material_cost = 0
                else:
                    order.material_cost = 0
            else:
                order.material_cost = 0

    #  Total cost
    @api.depends('material_cost', 'designing_cost', 'printing_charge')
    def _compute_total_cost(self):
        for order in self:
            order.total_cost = order.material_cost + order.designing_cost + order.printing_charge

    @api.depends('total_count')
    def _compute_printing_charge(self):
        for record in self:
            pricing_rule = self.env['printing.charge.pricing'].search([
                ('min_receipts', '<=', record.total_count),
                ('max_receipts', '>=', record.total_count)
            ], limit=1)
            record.printing_charge = pricing_rule.printing_charge if pricing_rule else 0.0

