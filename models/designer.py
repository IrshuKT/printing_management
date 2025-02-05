from email.policy import default

from odoo import models,fields,api
from odoo.exceptions import ValidationError


class ResUsers(models.Model):
    _inherit = 'res.users'


    is_designer = fields.Boolean(string='Is Designer',default=False)
    is_printing = fields.Boolean(string='Printing' ,default=False)

class ReceiptBookConfiguration(models.Model):
    _inherit = 'receipt.book.configuration'

    printing_status = fields.Selection([
        ('pending', 'Pending'),
        ('ongoing', 'Ongoing'),
        ('completed', 'Completed'),
    ], default='pending', string="Printing Status")

    assigned_printer_id = fields.Many2one('res.users', string="Assigned Printer",
                                          domain="[('is_printing', '=', True)]")
    printing_start_date = fields.Datetime(string="Printing Start Date")
    printing_end_date = fields.Datetime(string="Printing End Date")
    binding_status = fields.Selection([('not_started', 'Not Started'),
                                       ('in_progress', 'In Progress'),
                                       ('completed', 'Completed')], string="Binding Status")
    serialization_status = fields.Selection([('not_started', 'Not Started'),
                                             ('in_progress', 'In Progress'),
                                             ('completed', 'Completed')], string="Serialization Status")
    binding_start_date = fields.Datetime()
    binding_end_date = fields.Datetime()
    serialization_start_date = fields.Datetime()
    serialization_end_date = fields.Datetime()

    # Methods to handle binding and serialization processes
    def action_start_binding(self):
        self.write({'binding_status': 'in_progress', 'binding_start_date': fields.Datetime.now()})

    def action_mark_binding_completed(self):
        self.write({'binding_status': 'completed', 'binding_end_date': fields.Datetime.now()})
        self.write({'order_status': 'serializing'})

    def action_start_serialization(self):
        self.write({'serialization_status': 'in_progress', 'serialization_start_date': fields.Datetime.now()})

    def action_mark_serialization_completed(self):
        self.write({'serialization_status': 'completed', 'serialization_end_date': fields.Datetime.now()})
        self.write({'order_status': 'ready'})


    def action_assign_printer(self):
        # Manually assign a printer to the receipt book configuration
        for record in self:
            if not record.assigned_printer_id:
                raise ValidationError("Please select at least one printer to assign work.")
            if not record.assigned_printer_id:
                raise ValidationError("Please manually select a printer from the list of available printers.")
            # Update printing status and order status
            record.printing_status = 'pending'
            record.order_status = 'printing'

    def action_start_printing(self):
        # Mark the printing as ongoing.
        for record in self:
            if not record.assigned_printer_id:
                raise ValidationError("No printer is assigned to this work.")
            record.printing_status = 'ongoing'
            record.printing_start_date = fields.Datetime.now()

    def action_mark_printing_completed(self):
        # Mark the printing as completed.
        for record in self:
            if not record.assigned_printer_id:
                raise ValidationError("No printer is assigned to this work.")
            record.printing_status = 'completed'
            record.printing_end_date = fields.Datetime.now()
            record.order_status = 'binding'  # Move to the next stage
