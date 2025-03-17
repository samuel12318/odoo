from odoo import models

class Invoice(models.Model):
    _inherit="account.move"


    def action_generate_invoice(self):
        self.ensure_one()  # Ensure it's called on a single record

        if self.transaction_type != 'expense':
            raise UserError(_("Invoices can only be generated for expenses."))

        invoice_vals = {
            'partner_id': self.tracker_id.partner_id.id, # Get the partner from the tracker
            'type': 'out_invoice',  # Expense invoice
            'invoice_date': self.date.date(),  # Use the transaction date
            'reference': self.name or _("Transaction %s") % self.id, # Use transaction name or ID
            'invoice_line_ids': [(0, 0, {
                'name': self.category_id.name,  # Use category name as description
                'quantity': 1,  # Assuming one transaction per line
                'price_unit': self.amount,
                'account_id': self.category_id.account_id.id, # Set the correct account
            })],
        }

        invoice = self.env['account.move'].create(invoice_vals)

        # Optionally open the invoice
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }