from email.policy import default
import logging

from PIL.ImImagePlugin import number

_logger = logging.getLogger(__name__)

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ReceiptFinalSize(models.Model):
    _name = 'receipt.final.size'
    _order = 'create_date desc'
    _description = 'Final Size for Receipts'

    # serial_no = fields.Integer('Serial')
    name = fields.Char('Final size', required=True)
    description = fields.Text('Description')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'The final size name must be unique!'),
    ]

    @api.constrains('name')
    def _check_unique_name(self):
        for record in self:
            if self.search_count([('name', '=', record.name), ('id', '!=', record.id)]) > 0:
                raise ValidationError('The final size name must be unique!')


class ReceiptBookConfiguration(models.Model):
    _name = 'receipt.book.configuration'
    _order = 'create_date desc'
    _rec_name = 'partner_id'
    _description = 'Receipt Book Configuration for Printing Press'

    sequence = fields.Char(string='Memo No', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: ('New'))

    @api.model
    def create(self, vals):
        if vals.get('sequence', 'New') == 'New':
            vals['sequence'] = self.env['ir.sequence'].next_by_code('multi.page.sequence') or 'New'
        return super(ReceiptBookConfiguration, self).create(vals)

    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    partner_tags = fields.Many2many(related='partner_id.category_id', string="Partner Tags")
    selected_partner_tag = fields.Many2one('res.partner.category', string="Tag",
                                           domain="[('id', 'in', partner_tags)]")
    order_date = fields.Date(string='Order Date', default=fields.Date.context_today)
    due_date = fields.Date(string='Due Date', required=True)
    select_item = fields.Selection([
        ('receipt', 'Receipt'), ('bill_book', 'Bill Book'), ('counterfoil', 'Counterfoil')
    ], default='receipt', string='Item', required=True)
    # printing_order_id = fields.Many2one('printing.order', string="Printing Order", required=True)
    number_of_copies = fields.Integer('Copies',
                                      default=2)  # Default 2 copies (e.g., customer,and  vendor)
    number_of_books = fields.Integer('Books', default=10)  # Number of receipt books in the order
    number_of_receipts = fields.Integer('per Book',
                                        default=25)  # Receipts per book (e.g., 25 receipts per book)
    final_size = fields.Many2one('receipt.final.size', string='Size', required=True)

    # Multiple base papers for different copies
    base_paper_1 = fields.Many2one('product.product', string='Paper 1',
                                   domain="[('categ_id', '=', 'Base Papers')]", )
    base_paper_2 = fields.Many2one('product.product', string='Paper 2',
                                   domain="[('categ_id', '=', 'Base Papers')]", )
    base_paper_3 = fields.Many2one('product.product', string='Paper 3',
                                   domain="[('categ_id', '=', 'Base Papers')]", )
    base_paper_4 = fields.Many2one('product.product', string='Paper 4',
                                   domain="[('categ_id', '=', 'Base Papers')]", )

    # Add computed fields for base paper requirements
    base_paper_1_sheets = fields.Integer(string="Paper 1 Count", compute='_compute_base_paper_sheets', store=True)
    base_paper_2_sheets = fields.Integer(string="Paper 2 Count", compute='_compute_base_paper_sheets', store=True)
    base_paper_3_sheets = fields.Integer(string="Paper 3 Count", compute='_compute_base_paper_sheets', store=True)
    base_paper_4_sheets = fields.Integer(string="Paper 4 Count", compute='_compute_base_paper_sheets', store=True)

    @api.depends('number_of_books', 'number_of_receipts', 'number_of_copies', 'final_size', 'base_paper_1',
                 'base_paper_2', 'base_paper_3', 'base_paper_4')
    def _compute_base_paper_sheets(self):
        for record in self:
            # Initialize sheet counts to 0
            record.base_paper_1_sheets = 0
            record.base_paper_2_sheets = 0
            record.base_paper_3_sheets = 0
            record.base_paper_4_sheets = 0

            # Calculate total receipts needed
            total_receipts_needed = record.number_of_books * record.number_of_receipts * record.number_of_copies

            # Calculate sheets for each base paper
            base_papers = [
                (record.base_paper_1, 'base_paper_1_sheets'),
                (record.base_paper_2, 'base_paper_2_sheets'),
                (record.base_paper_3, 'base_paper_3_sheets'),
                (record.base_paper_4, 'base_paper_4_sheets'),
            ]

            for base_paper, sheet_field in base_papers:
                if base_paper:
                    receipts_per_sheet = self._get_receipts_per_sheet(base_paper, record.final_size)
                    if receipts_per_sheet:
                        # Calculate the number of sheets needed for this base paper
                        sheets_needed = total_receipts_needed / (receipts_per_sheet * record.number_of_copies)
                        setattr(record, sheet_field, sheets_needed)

    order_status = fields.Selection([
        ('draft', 'Draft'),
        ('designing', 'Designing'),
        ('printing', 'Printing'),
        ('binding', 'Binding'),
        ('serializing', 'Serializing'),
        ('ready', 'Ready'),
    ], default='draft', string="Order Status")

    # Define a field for designers
    designer_ids = fields.Many2many('res.users', string="Designers", domain="[('is_designer', '=', True)]")
    # cost
    total_cost = fields.Float('Material Cost', compute='_compute_cost')
    designing_cost = fields.Float('Designing Charge', default=500)
    # printing_charge = fields.Float('Printing Charge')
    printing_charge = fields.Float('Printing Charge', compute='_compute_printing_charge', store=True)
    binding_charge = fields.Float('Binding Charge')
    numbering_charge = fields.Float('Serializing Charge')
    # Total Cost
    net_charge = fields.Float('Total Cost', compute='_net_total')

    total_receipts = fields.Float(string="Total Receipts", compute='_compute_total_receipts', store=True)

    def _compute_cost(self):
        for config in self:
            total_cost = 0.0
            total_receipts_needed = config.number_of_books * config.number_of_receipts * config.number_of_copies

            # Calculate cost for each base paper used for different copies
            base_papers = [config.base_paper_1, config.base_paper_2, config.base_paper_3, config.base_paper_4]
            for base_paper in base_papers:
                if base_paper:
                    receipts_per_sheet = self._get_receipts_per_sheet(base_paper, config.final_size)
                    if receipts_per_sheet:
                        # Calculate the number of sheets needed for this base paper
                        sheets_needed = total_receipts_needed / receipts_per_sheet
                        print('total sheet', sheets_needed)

                        total_cost += sheets_needed * base_paper.list_price  # Assuming cost per sheet is the list price

            config.total_cost = total_cost

    @api.depends('total_receipts')
    def _compute_printing_charge(self):
        for record in self:
            pricing_rule = self.env['printing.charge.pricing'].search([
                ('min_receipts', '<=', record.total_receipts),
                ('max_receipts', '>=', record.total_receipts)
            ], limit=1)
            record.printing_charge = pricing_rule.printing_charge if pricing_rule else 0.0

    def _get_receipts_per_sheet(self, base_paper, final_size):
        # Get how many receipts fit per sheet based on the selected base paper product and final size
        receipt_record = self.env['receipt.base.paper'].search([
            ('base_paper_id', '=', base_paper.id),
            ('final_size', '=', final_size.id)
        ], limit=1)

        if receipt_record:
            return receipt_record.receipts_per_sheet

        return None  # Return None if no mapping found

    @api.depends('number_of_books', 'number_of_receipts', 'number_of_copies')
    def _compute_total_receipts(self):
        for config in self:
            config.total_receipts = config.number_of_books * config.number_of_receipts * config.number_of_copies

            # Net Total

    @api.depends('total_cost', 'designing_cost', 'printing_charge', 'binding_charge', 'numbering_charge')
    def _net_total(self):
        for record in self:
            # Calculate the net total as the sum of all charges
            record.net_charge = round(record.total_cost +
                                      record.designing_cost +
                                      record.printing_charge +
                                      record.binding_charge +
                                      record.numbering_charge)

    # Generating Invoices
    def action_generate_invoice(self):
        """Generate invoice and deduct stock for used base papers"""

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_type': 'out_invoice',  # Outgoing invoice (customer)
            'invoice_line_ids': [],
        }

        # Calculate total receipts required for invoice
        total_receipts_needed = self.number_of_books * self.number_of_receipts * self.number_of_copies

        # Loop through base papers (1, 2, 3, 4) to create invoice lines for them
        base_papers = [self.base_paper_1, self.base_paper_2, self.base_paper_3, self.base_paper_4]
        for base_paper in base_papers:
            if base_paper:
                # Check if base_paper has a related product
                if base_paper.product_id:
                    # Get the product related to the base paper (ensure it has a valid product_id)
                    product = base_paper.product_id

                    # Proceed with the rest of the logic for base paper
                    receipts_per_sheet = self._get_receipts_per_sheet(base_paper, self.final_size)
                    if receipts_per_sheet:
                        # Calculate the number of sheets needed for this base paper
                        sheets_needed = total_receipts_needed / receipts_per_sheet

                        # Calculate the total price for the base paper (based on the cost per sheet)
                        total_price = sheets_needed * product.list_price  # Adjust if necessary

                        # Add line for the base paper to the invoice
                        invoice_vals['invoice_line_ids'].append((0, 0, {
                            # 'product_id': product.id,
                            'name': f'Base Paper {base_paper.name}',
                            'quantity': sheets_needed,
                            'price_unit': product.list_price,
                            'account_id': product.product_tmpl_id.property_account_income_id.id,
                        }))

                        # Deduct stock for the base paper
                        self.env['stock.move'].create({
                            # 'product_id': product.id,
                            'quantity_done': sheets_needed,
                            'location_id': self.env.ref('stock.stock_location_stock').id,  # Source location (stock)
                            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
                            # Destination (customer)
                            'move_type': 'direct',  # Direct transfer
                        })

        # Add other costs to the invoice (Designing, Printing, Binding, Serialization)

        # Material cost
        if self.total_cost:
            material_product = self.env['product.product'].search([('name', '=', 'Material Cost')], limit=1)
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': material_product.id,
                'name': 'Material Cost',
                'quantity': 1,
                'price_unit': self.total_cost,
                'account_id': self.env.ref('account.data_account_type_expenses').id,
            }))

        # Designing cost
        if self.designing_cost:
            designing_product = self.env['product.product'].search([('name', '=', 'Designing Charge')], limit=1)
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': designing_product.id,
                'name': 'Designing Charge',
                'quantity': 1,
                'price_unit': self.designing_cost,
                'account_id': self.env.ref('account.data_account_type_expenses').id,
            }))

        # Printing cost
        if self.printing_charge:
            printing_product = self.env['product.product'].search([('name', '=', 'Printing Charge')], limit=1)
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': printing_product.id,
                'name': 'Printing Charge',
                'quantity': 1,
                'price_unit': self.printing_charge,
                'account_id': self.env.ref('account.data_account_type_expenses').id,
            }))

        # Binding charge
        if self.binding_charge:
            binding_product = self.env['product.product'].search([('name', '=', 'Binding Charge')], limit=1)
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': binding_product.id,
                'name': 'Binding Charge',
                'quantity': 1,
                'price_unit': self.binding_charge,
                'account_id': self.env.ref('account.data_account_type_expenses').id,
            }))

        # Serialization charge
        if self.numbering_charge:
            numbering_product = self.env['product.product'].search([('name', '=', 'Serialization Charge')], limit=1)
            invoice_vals['invoice_line_ids'].append((0, 0, {
                'product_id': numbering_product.id,
                'name': 'Serialization Charge',
                'quantity': 1,
                'price_unit': self.numbering_charge,
                'account_id': self.env.ref('account.data_account_type_expenses').id,
            }))

        # Create the invoice
        invoice = self.env['account.move'].create(invoice_vals)

        # Confirm the invoice (making it official)
        invoice.action_post()

        # Optionally, update the partner's credit balance
        self.partner_id.write({'credit': self.partner_id.credit + self.total_cost})

    # Dynamic costs
    @api.depends('number_of_copies')
    def _compute_dynamic_cost(self):
        for record in self:
            # Get the relevant pricing range based on the number of copies
            pricing_ranges = self.env['pricing.range'].search([
                ('lower_limit', '<=', record.number_of_copies),
                ('upper_limit', '>=', record.number_of_copies)
            ])

            if pricing_ranges:
                # Assuming you want to apply the cost from the first matching range
                range = pricing_ranges[0]
                record.binding_charge = range.binding_cost
                record.printing_charge = range.printing_cost
                record.numbering_charge = range.serializing_cost

    assigned_designer_id = fields.Many2one('res.users', string="Designer",
                                           domain="[('is_designer', '=', True)]", required=True)
    design_start_date = fields.Datetime(string="Design Start Date")
    design_end_date = fields.Datetime(string="Design End Date")
    design_status = fields.Selection([
        ('pending', 'Pending'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ], default='pending', string="Design Status")

    def action_assign_designer(self):
        """Manually assign a designer to the receipt book configuration."""
        for record in self:
            if not record.assigned_designer_id:
                raise ValidationError("Please select at least one designer to assign work.")

            # Explicitly assign designer and update order status when button is clicked
            record.write({
                'design_status': 'pending',
                'design_start_date': fields.Datetime.today(),
                'order_status': 'designing',  # Move to designing state
            })

    def action_start_designing(self):
        # Mark the printing as ongoing.
        for record in self:
            if not record.assigned_designer_id:
                raise ValidationError("No designer is assigned to this work.")
            record.write({
                'design_status': 'ongoing',
                'design_start_date': fields.Datetime.now(),
            })

    def action_mark_design_completed(self):
        """Mark the design as completed."""
        for record in self:
            if not record.assigned_designer_id:
                raise ValidationError("No designer is assigned to this work.")
            record.write({
                'design_status': 'completed',
                'design_end_date': fields.Datetime.today(),
                'order_status': 'printing',  # Move to printing stage
            })

    def action_reassign_designer(self):
        """Reassign the work to another designer."""
        for record in self:
            if not record.designer_ids:
                raise ValidationError("Please select at least one designer to reassign work.")
            record.write({
                'assigned_designer_id': False,
                'design_status': 'pending',
                'design_start_date': False,
                'design_end_date': False,
                'order_status': 'assigning',  # Set to assigning state
            })

    def action_print_service_memo(self):
        _logger.info("Printing Service Memo for Record: %s", self)
        return self.env.ref('press_management.action_service_memo_report').report_action(self)

    def _get_report_values(self, docids, data=None):
        docs = self.browse(docids)  # Ensure you are fetching the correct records
        _logger.info(f"Fetched docids: {docids}")
        _logger.info(f"Fetched docs: {docs}")
        return {
            'doc_ids': docids,
            'doc_model': self._name,
            'docs': docs,
        }


class BasePaperReceipt(models.Model):
    _name = 'receipt.base.paper'
    _description = 'Base Paper Receipt Size Mapping'

    base_paper_id = fields.Many2one('product.product', string="Base Paper", domain="[('categ_id', '=', 'Base Papers')]")
    final_size = fields.Many2one('receipt.final.size', string='Final Size', required=True, )
    receipts_per_sheet = fields.Integer('Receipts per Sheet', required=True)

    _sql_constraints = [
        ('unique_base_paper_final_size', 'unique(base_paper_id, final_size)',
         'This combination of base paper and final size already exists.')
    ]


class PrintingChargePricing(models.Model):
    _name = 'printing.charge.pricing'
    _description = 'Printing Charge Pricing Rules'

    min_receipts = fields.Integer(string="Minimum Receipts", required=True)
    max_receipts = fields.Integer(string="Maximum Receipts", required=True)
    printing_charge = fields.Float(string="Printing Charge", required=True)

    _sql_constraints = [
        ('no_overlapping_ranges', 'CHECK(min_receipts < max_receipts)',
         'The minimum receipts must be less than the maximum receipts.'),
        ('unique_range', 'UNIQUE(min_receipts, max_receipts)', 'This range already exists.'),
    ]


class BasePaper(models.Model):
    _name = 'base.paper.receipt'
