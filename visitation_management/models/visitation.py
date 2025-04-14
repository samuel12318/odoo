from odoo import models, fields, api
from odoo.exceptions import UserError




class Visitation(models.Model):
    _name = 'visitation.visitation'
    _description = 'Visitation'

    name = fields.Char(string='Name', compute="_compute_name", store=True)
    title = fields.Char(string='Role')

    visitor_type = fields.Selection([('individual', 'Individual'), ('group', 'Group')], string='Visitor Type', required=True)
    purpose = fields.Char(string='Purpose', required=True)

    full_name = fields.Char(string='Full Name')
    contact = fields.Char(string='Contact')
    email = fields.Char(string='Email')


    time_in = fields.Datetime(string='Check In', readonly=True)
    time_out = fields.Datetime(string='Check Out', readonly=True)

    visitor_id = fields.Many2one('visitation.visitors', string='Visitor')
    group_visitors = fields.One2many('visitation.visitors', 'visitation_id', string='Group Visitors')
    status = fields.Selection([
        ('signed_in', 'Signed In'),
        ('signed_out', 'Signed Out'),
    ],)
    company_name = fields.Char(string='Company Name')
    auto_signed_out = fields.Boolean(default=False)
    check = fields.Integer(default=0,compute="_compute_check")


    def send_mail(self):
        try:

            mail_values = {
                "subject": f"Visitation Letter: {self.name}",
                "body_html": f"""
                    <p>Dear {self.name},</p>

                    <p>I hope this message finds you well.</p>

                    <p>Please find attached the visitation letter for <strong>{self.name}</strong>. Kindly review the document at your earliest convenience.</p>

                    <p>Should you have any questions or require further assistance, feel free to reach out.</p>
                    <br><br><br

                    <p>Best regards,</p>
                    <p>{self.env.user.name}</p>
                    <p>The Quantum Group LTD.</p>
                """,
                "email_to": self.email,
            }

            mail = self.env["mail.mail"].create(mail_values)
            mail.send()

        except Exception as e:
            print(e)
        return True


    @api.depends('visitor_type', 'title', 'full_name', 'company_name')
    def _compute_name(self):
        for record in self:
            if record.visitor_type == 'individual':
                title = record.title or ''
                full_name= record.full_name if record.id else ''

                record.name = f"{title} {full_name} ".strip()
            elif record.visitor_type == 'group':
                record.name = record.company_name or ''

    def action_sign_in(self):
        for record in self:
            if id:
                if record.visitor_type == 'individual':
                    record.status = 'signed_in'
                    record.time_in = fields.Datetime.now()

                elif record.visitor_type == 'group':
                    first_visitor = self.env['visitation.visitors'].search(
                        [('visitation_id', '=', record.id)], order='create_date ASC', limit=1
                    )

                    if first_visitor:
                        record.time_in = first_visitor.time_in
                    record.status = 'signed_in'

    @api.model
    def create(self, vals):
        record = super(Visitation,self).create(vals)
        if record.status=='signed_out':
            raise UserError("Cannot create a new record after group has signed out")
        record.action_sign_in()
        return record

    def action_sign_out(self):
        timeout = fields.Datetime.now()
        for record in self:
            if record.visitor_type == 'individual':
                record.status = 'signed_out'
                record.time_out = fields.Datetime.now()
                record.send_mail()



            elif record.visitor_type == 'group':
                visitors = self.env['visitation.visitors'].search([('visitation_id', '=', record.id)])

                for item in visitors:
                    if not item.time_out:
                        item.time_out = timeout
                        item.status = 'signed_out'

                last_visitor = self.env['visitation.visitors'].search(
                    [('visitation_id', '=', record.id)], order='time_out DESC', limit=1
                )
                if last_visitor:
                    record.time_out = last_visitor.time_out

                record.status='signed_out'





    def set_nextcall(self):
        cron = self.env['ir.cron'].search([('cron_name', '=', 'Visitation: Auto SignOut')], limit=1)


    def auto_sign_out(self):
        today = fields.Date.today()  # Get today's date

        records = self.search([])
        for record in records:
            if record.status == 'signed_in':
                print(
                    "\n ***\nThere is a record in a group visit who hasn't signed out yet\n*** \n")
                record.status = 'signed_out'
                record.auto_signed_out = True
                record.send_mail()
                record.time_out = fields.Datetime.now().replace(hour=17, minute=00, second=0, microsecond=0)


class Visitors(models.Model):
    _name = 'visitation.visitors'
    _description = 'Visitors'

    # Fields for visitor details
    role = fields.Char(string='Role', required=True)
    full_name = fields.Char(string='Full Name', required=True)
    contact = fields.Char(string='Contact', required=True)
    email = fields.Char(string='Email')
    auto_signed_out = fields.Boolean(default=False)

    status = fields.Selection([
        ('signed_in', 'Signed In'),
        ('signed_out', 'Signed Out'),
    ])

    time_in = fields.Datetime(string='Check In', readonly=True)
    time_out = fields.Datetime(string='Check Out', readonly=True)

    # Link to the Visitation model
    visitation_id = fields.Many2one('visitation.visitation', string='Visitation', ondelete='cascade')

    @api.model
    def create(self, vals):
        for record in self:
            if record.visitation_id.status == 'signed_out':
                raise UserError("Cannot create a new record while a 'signed_in' record exists!")
            return super().create(vals)


    def send_group_mail(self):
        try:

            mail_values = {
                "subject": f"Visitation Letter: {self.full_name} :{self.role}. ",
                "body_html": f"""
                    <p>Dear {self.full_name},</p>

                    <p>I hope this message finds you well.</p>

                    <p>Please find attached the visitation letter for <strong>{self.full_name}</strong>. Kindly review the document at your earliest convenience.</p>

                    <p>Should you have any questions or require further assistance, feel free to reach out.</p>
                    <br><br><br

                    <p>Best regards,</p>
                    <p>{self.env.user.name}</p>
                    <p>The Quantum Group LTD.</p>
                """,
                "email_to": self.email,
            }

            mail = self.env["mail.mail"].create(mail_values)
            mail.send()

        except Exception as e:
            print(e)
        return True


    def action_sign_in(self):
        for record in self:
            record.status = 'signed_in'
            record.time_in = fields.Datetime.now()

    @api.model
    def create(self, vals):
        record = super(Visitors,self).create(vals)
        record.action_sign_in()
        return record



    def action_sign_out(self):
        for record in self:
            if not record.time_out:
                record.status = 'signed_out'
                record.time_out = fields.Datetime.now()
                record.send_group_mail()

            records = self.search([('status', '=', 'signed_in')])
            if not records and record.visitation_id:
                record.visitation_id.status = 'signed_out'
                record.visitation_id.time_out = fields.Datetime.now()


    def group_auto_sign_out(self):

        records = self.search([])
        for record in records:
            if record.status == 'signed_in':
                print(
                    "\n ***\nThere is a record in a group visit who hasn't signed out yet\n*** \n")

                record.status = 'signed_out'
                record.visitation_id.status = 'signed_out'
                record.auto_signed_out = True
                record.send_group_mail()
                record.time_out = fields.Datetime.now().replace(hour=17, minute=00, second=0, microsecond=0)




    #title=fields.Selection(selection='title_selection')
    # def title_selection(self):
    #     return [('Mr.', 'Mr.'), ('Mrs.', 'Mrs.'), ('Dr.', 'Dr.'), ('Miss', 'Miss')]
