from odoo import models,api,fields
import base64

class NewResPartner(models.Model):
    _inherit="res.partner"

    region=fields.Selection([
        ('accra','Greater Accra'),
        ('eastern','Eastern'),
        ('central','Central'),
        ('northern','Northern'),
        ('west','Western'),
        ('u-west','Upper West'),
        ('u-east','Upper East'),
        ])
    
    tribe = fields.Char()
    festival = fields.Char()
    
    def action_download_form(self):  
        # Generate PDF  
        pdf_content, _ = self.env.ref('your_module.report_partners').render_qweb_pdf(self.ids)  
        
        # Create an attachment  
        attachment = self.env['ir.attachment'].create({  
            'name': f"Partner_{self.id}.pdf",  
            'type': 'binary',  
            'datas': base64.b64encode(pdf_content),  
            'datas_fname': f"Partner_{self.id}.pdf",  
            'res_model': 'res.partner',  
            'res_id': self.id,  
        })  

        return {  
            'type': 'ir.actions.act_url',  
            'url': f'/web/content/{attachment.id}?download=true',  
            'target': 'self',  
        }