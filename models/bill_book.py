from email.policy import default

from odoo import models, fields, api
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class BillBookPage(models.Model):
    _name = 'printing.bill.book.page'
    _description = 'Bill Book Page'

    customer_id = fields.Many2one('res.partner', string="Customer", required=True)
    num_copies = fields.Integer(string="Number of Copies", required=True, default=2)
    number_of_books = fields.Integer(string='Number of Books', required=True)
    receipts_per_book = fields.Integer(string='Receipts Per Book', required=True)
    designing_charge = fields.Float(string="Designing Charge", required=True)
    printing_charge = fields.Float(string="Printing Charge", required=True)
    binding_charge = fields.Float(string="Binding Charge", required=True)
    numbering_charge = fields.Float(string="Numbering Charge", required=True)
    material_cost = fields.Float(string='Material Cost', compute='_compute_material_cost', store=True)
    total_cost = fields.Float(string='Total Cost', compute='_compute_total_cost', store=True)
    order_date = fields.Date(string='Order Date', default=fields.Date.context_today)
    due_date = fields.Date(string='Due Date', required=True)

    first_paper = fields.Many2one('printing.paper',string='First paper')
    second_paper = fields.Many2one('printing.paper',string='Second paper')
    third_paper = fields.Many2one('printing.paper', string='Third paper')
    fourth_paper = fields.Many2one('printing.paper', string='Fourth paper')


    receipt_size_id = fields.Many2one('printing.paper.size', string="Receipt Size", required=True,
                                     default=lambda self: self._get_default_paper_size())

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancel', 'Cancelled'),
    ], string='Status', default='draft', track_visibility='onchange')

    @api.model
    def _get_default_paper_size(self):
        paper_size = self.env['printing.paper.size'].search([('name', '=', 'A4')], limit=1)
        if paper_size:
            return paper_size.id
        return False

    @api.depends('num_copies', 'number_of_books', 'receipts_per_book', 'first_paper', 'second_paper', 'third_paper',
                 'fourth_paper', 'receipt_size_id')
    def _compute_material_cost(self):
        """
        Compute the material cost based on the number of copies, books, and paper used.
        This uses PaperOutputCalculator to determine how many receipts fit on a sheet of paper.
        """
        for record in self:
            material_cost = 0.0

            # Calculate total receipts (total number of receipts across all copies)
            total_receipts = record.number_of_books * record.receipts_per_book * record.num_copies

            # Function to calculate material cost for each paper type (first, second, third, fourth)
            def calculate_paper_cost(paper, receipts_needed):
                """
                Helper function to calculate material cost for a given paper type.
                :param paper: The paper (first, second, etc.)
                :param receipts_needed: The total number of receipts that need to be printed.
                :return: The calculated material cost for this paper.
                """
                if paper and record.receipt_size_id:
                    # Search for the PaperOutputCalculator record for the paper and receipt size
                    output_calculator = self.env['paper.output.calculator'].search([
                        ('paper_id', '=', paper.id),
                        ('output_size_id', '=', record.receipt_size_id.id)
                    ], limit=1)

                    print(output_calculator)
                    if output_calculator:
                        # Get the output quantity (how many receipts per sheet)
                        receipts_per_sheet = output_calculator.output_quantity
                        # Get the price per sheet for the paper
                        price_per_sheet = paper.price_per_sheet

                        # Calculate the number of sheets needed
                        sheets_needed = receipts_needed / receipts_per_sheet
                        # Calculate material cost for this paper
                        return sheets_needed * price_per_sheet
                return 0.0

            # Calculate material cost for first paper
            material_cost += calculate_paper_cost(record.first_paper, total_receipts // record.num_copies)

            # Calculate material cost for second paper
            material_cost += calculate_paper_cost(record.second_paper, total_receipts // record.num_copies)

            # Calculate material cost for third paper (if exists)
            if record.third_paper:
                material_cost += calculate_paper_cost(record.third_paper, total_receipts // record.num_copies)

            # Calculate material cost for fourth paper (if exists)
            if record.fourth_paper:
                material_cost += calculate_paper_cost(record.fourth_paper, total_receipts // record.num_copies)

            # Store the calculated material cost
            record.material_cost = material_cost

    @api.depends('material_cost', 'designing_charge', 'printing_charge', 'binding_charge', 'numbering_charge')
    def _compute_total_cost(self):
        # Compute the total cost including material, designing, printing, binding, and numbering charges.
        for record in self:
            record.total_cost = (
                    record.material_cost
                    + record.designing_charge
                    + record.printing_charge
                    + record.binding_charge
                    + record.numbering_charge
            )

    @api.constrains('num_copies', 'number_of_books', 'receipts_per_book')
    def _check_positive_values(self):
        # Ensure critical fields have positive values.
        for record in self:
            if record.num_copies <= 0:
                raise ValidationError("Number of Copies must be greater than zero.")
            if record.number_of_books <= 0:
                raise ValidationError("Number of Books must be greater than zero.")
            if record.receipts_per_book <= 0:
                raise ValidationError("Receipts Per Book must be greater than zero.")

    def generate_invoice(self):
        """
        Confirms the printing order and creates an invoice linked to the partner.
        """
        for order in self:
            # Change state to confirmed
            order.state = 'confirmed'

            # Create an invoice
            invoice_vals = {
                'type': 'out_invoice',  # Customer invoice
                'partner_id': order.customer_id.id,
                'invoice_date': fields.Date.context_today(order),
                'invoice_line_ids': [(0, 0, {
                    'name': f'Printing Order {order.name}',
                    'quantity': 1,
                    'price_unit': order.total_cost,
                })],
            }
            invoice = self.env['account.move'].create(invoice_vals)

            # Link the invoice to the order
            order.invoice_id = invoice.id

            # Optionally, post the invoice immediately
            invoice.action_post()

            # Log the invoice creation in partner chatter
            if order.customer_id:
                message = f"An invoice has been created for Printing Order {order.name}."
                order.customer_id.message_post(body=message)
