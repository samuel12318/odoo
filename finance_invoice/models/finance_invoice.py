from odoo import fields, models
from odoo.exception import UserError

class AccountInvoice(models.Model):
    _inherit='finance.transaction'
    