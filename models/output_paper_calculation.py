from odoo import models, fields, api
from odoo.exceptions import ValidationError


class PaperOutputCalculator(models.Model):
    _name = 'paper.output.calculator'
    _description = 'Paper Output Calculator'

    paper_id = fields.Many2one('printing.paper', string="Input Paper", required=True)
    output_size_id = fields.Many2one('printing.paper.size', string="Output Paper", required=True)
    output_quantity = fields.Integer(string="Output Qty", required=True)
    gsm = fields.Float(string="GSM", store=True)

    _sql_constraints = [
        ('unique_paper_output_size', 'unique(paper_id, output_size_id)',
         'Each paper and output size combination must be unique.'),
    ]

    def get_output_quantity(self, paper_id, size_id):
        """Get the number of output sheets that can be derived from a paper type for a given size."""

        # Ensure paper_id and size_id are valid (saved)
        if not paper_id.id:
            raise ValidationError(f"Paper '{paper_id.name}' is not saved yet. Please save it before proceeding.")

        if not size_id.id:
            raise ValidationError(f"Size '{size_id.name}' is not saved yet. Please save it before proceeding.")

        # Search for an existing conversion
        conversion = self.env['paper.size.conversion'].search([
            ('paper_id', '=', paper_id.id),
            ('size_id', '=', size_id.id)
        ], limit=1)

        # If no conversion is found, create a default one
        if not conversion:
            conversion = self.env['paper.size.conversion'].create({
                'paper_id': paper_id.id,
                'size_id': size_id.id,
                'output_quantity': 8  # Default or calculated output quantity
            })
            return conversion.output_quantity
        else:
            return conversion.output_quantity

    @api.onchange('paper_id')
    def _onchange_paper_id(self):
        if self.paper_id:
            self.gsm = self.paper_id.gsm  # Automatically updates gsm based on selected paper
        else:
            self.gsm = 0.0

    @api.constrains('output_quantity')
    def _check_output_quantity(self):
        for record in self:
            if record.output_quantity <= 0:
                raise ValidationError('Output quantity must be greater than zero.')

