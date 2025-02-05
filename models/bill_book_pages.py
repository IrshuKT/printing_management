from odoo import models,fields,api


class BillBookPageLine(models.Model):
    _name = 'printing.bill.book.page.line'
    _description = 'Bill Book Page Line'

    bill_book_page_id = fields.Many2one('printing.bill.book.page', string="Bill Book Page", required=True, ondelete='cascade')
    paper_size_id = fields.Many2one('printing.paper.size', string="Paper Size", required=True)
    gsm = fields.Float(string="GSM", required=True)  # GSM for this page
    number_of_pages = fields.Integer(string="Number of Pages", required=True)
