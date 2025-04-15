from odoo import models, fields, api

class Visitation(models.Model):
    _inherit = 'visitation.visitation'

    remarks = fields.Text(string='Visitor Remarks')