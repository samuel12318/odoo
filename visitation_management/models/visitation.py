from odoo import models, fields, api



class Visitation(models.Model):
    _name = 'visitation.visitation'
    _description = 'Visitation'

    name = fields.Char(string='Name', compute="_compute_name", store=True)
    title = fields.Selection([('Mr.','Mr.'),('Mrs.','Mrs.'),('Dr.','Dr.'),('Miss','Miss')], string='Title')
    visitor_type = fields.Selection([('individual', 'Individual'), ('group', 'Group')], string='Visitor Type', required=True)
    purpose = fields.Char(string='Purpose', required=True)

    full_name = fields.Char(string='Full Name')
    contact = fields.Char(string='Contact')
    email = fields.Char(string='Email')


    time_in = fields.Datetime(string='Time In', readonly=True)
    time_out = fields.Datetime(string='Time Out', readonly=True)

    visitor_id = fields.Many2one('visitation.visitors', string='Visitor')
    group_visitors = fields.One2many('visitation.visitors', 'visitation_id', string='Group Visitors')
    status = fields.Selection([
        ('signed_in', 'Signed In'),
        ('signed_out', 'Signed Out'),
    ],)
    company_name = fields.Char(string='Company Name')
    auto_signed_out = fields.Boolean(default=False)

    
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
        record.action_sign_in()
        return record

    def action_sign_out(self):
        for record in self:
            if record.visitor_type == 'individual':
                record.status = 'signed_out'
                record.time_out = fields.Datetime.now()
            elif record.visitor_type == 'group':
                last_visitor = self.env['visitation.visitors'].search(
                    [('visitation_id', '=', record.id)], order='time_out DESC', limit=1
                )

                if last_visitor:
                    record.time_out = last_visitor.time_out

    def set_nextcall(self):
        cron = self.env['ir.cron'].search([('cron_name', '=', 'Visitation: Auto SignOut')], limit=1)

    def auto_sign_out(self):
        today = fields.Date.today()  # Get today's date

        records = self.search([])
        for record in records:
            if record.status == 'signed_in':
                print(
                    "\n \n ******************************* There is a record who hasn't signed out yet ********************* \n \n")
                record.status = 'signed_out'
                record.auto_signed_out = True

        # Find the cron job
        cron = self.env['ir.cron'].search([('cron_name', '=', 'Visitation: Auto SignOut')], limit=1)
        if cron:
            # Calculate the next run time
            next_run = fields.Datetime.now().replace(hour=13, minute=50, second=0, microsecond=0)
            print("Next run time:", next_run)

            # Update the cron job
            # cron.sudo().write({'nextcall': next_run})
            print('Auto Sign Out Completed::::::::::::', cron.nextcall)
        else:
            print("Cron job not found!")

        print("Auto Sign Out Completed")

            # cron.sudo().write({'nextcall': (fields.Datetime.now() + relativedelta(days=1)).replace(hour=17, minute=0, second=0)})
            # cron.sudo().write({'nextcall': next_run})fields.Datetime.now() + relativedelta(hour=16, minute=35, second=0)



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

    time_in = fields.Datetime(string='Time In', readonly=True)

    time_out = fields.Datetime(string='Time Out', readonly=True)

    # Link to the Visitation model
    visitation_id = fields.Many2one('visitation.visitation', string='Visitation', ondelete='cascade')
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
            record.status = 'signed_out'
            record.time_out = fields.Datetime.now()





    def group_auto_sign_out(self):

        records = self.search([])
        for record in records:
            if record.status == 'signed_in':
                print(
                    "\n \n ******************************* There is a record who hasn't signed out yet ********************* \n \n")
                record.status = 'signed_out'
                record.auto_signed_out = True

        # Find the cron job
        cron = self.env['ir.cron'].search([('cron_name', '=', 'Visitation: Individuals of a group to SignOut')], limit=1)
        if cron:
            # Calculate the next run time
            next_run = fields.Datetime.now().replace(hour=13, minute=50, second=0, microsecond=0)
            print("Next run time:", next_run)
            print('Auto Sign Out Completed::::::::::::', cron.nextcall)
        else:
            print("Cron job not found!")

        print("Auto Sign Out Completed")
