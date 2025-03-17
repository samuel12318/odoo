from odoo import models,api,fields
from odoo.exceptions import UserError,ValidationError
from datetime import date
import smtplib,time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class FinanceTracker(models.Model):
    _name = 'finance.tracker'
    _description = 'Finance Tracker'

    name = fields.Char(string="Account Type", required=True)
    account_number = fields.Char(string="Account Number", required=True)
    balance = fields.Float(default=0.0)
    email = fields.Char(required=True)

    goal_id = fields.One2many('finance.goals', 'account_id', string="Goals")
    transaction_id = fields.One2many('finance.transaction', 'tracker_id', string="Transaction")
    _last_balance_change = {}


    def send_email(self):
        self.ensure_one()  # Ensure we're working with a single record

        mail_server = self.env['ir.mail_server'].search([], limit=1)
        if not mail_server:
            raise UserError(_("No Mail server configured"))

        if self.email:
            # Create a multipart message
            message = MIMEMultipart()
            message['From'] = mail_server.smtp_user
            message['To'] = self.email
            message['Subject'] = _("Balance Update - %s") % self.name # Use _() for translation
            
            # Email body (HTML or plain text)
            body = _("""
                Hello,

                Your account "%s" (Account Number: %s) has been updated.
                Your new balance is: %s.

                Thank you!
            """) % (self.name, self.account_number, self.balance)
            message.attach(MIMEText(body, 'plain')) 

            try:
                mail_server.sendmail(mail_server.smtp_user, self.email, message.as_string())  #Use sendmail
                self.message_post(body=_("Email sent successfully!"))
            except smtplib.SMTPException as e:
                raise UserError(_("Email sending failed: %s") % e)

    @api.onchange('balance')
    def _onchange_balance(self):
        self.ensure_one()
        record_id = self.id  # Get the id of the current record
        current_time = time.time()

        if record_id not in self._last_balance_change or current_time - self._last_balance_change[record_id] > 60:  # 60 seconds debounce
            if self.balance < 0:
                raise models.UserError(_("Balance cannot be negative!"))
            self.send_email()
            self._last_balance_change[record_id] = current_time
        else:
            print("Balance change debounced")
            

class FinanceTransaction(models.Model):
    _name="finance.transaction"
    _description="Finance Transaction"
    # _inherit="account"

    name=fields.Char(compute="_compute_name")
    date=fields.Datetime(string="Transaction Date",default=fields.Datetime.now,readonly=True)
    amount=fields.Float(required=True)
    amount_format=fields.Char(compute="_format_amount",store=True)
    account_balance=fields.Float(default=0.0,required=True)
    transaction_type=fields.Selection([
        ('income','Income'),('expense','Expense')
        ],required=True, compute="_set_expense",store=True,search=True,index=True,readonly=False)
    send_money_button=fields.Boolean(string="Send Money", compute="_switch_radio", readonly=False)
    default_button=fields.Boolean(string="Transaction")
    recipient_number=fields.Char(required=True)
    status=fields.Selection([('pending','Pending'),('sent','Sent')], default="pending",readonly=True,required=True)
    category_id=fields.Many2one('finance.category',string="Category",required=True)
    tracker_id=fields.Many2one('finance.tracker',string="Transaction",required=True)
    # invoice_id=fields.Many2one('account.move',string="Invoice")





    @api.constrains('amount')
    def _check_amount(self):
        for record in self:
            if record.amount < 0:
                raise ValidationError("Amount cannot")


    @api.model
    def create(self, vals):
        record = super().create(vals)

        if record.amount < 0:
            raise models.UserError("Invalid amount, check the amount...")
        else:
            if record.transaction_type == 'income':
                record.tracker_id.balance += record.amount
            elif record.transaction_type == 'expense':
                if record.amount>record.tracker_id.balance:
                    raise exceptions.ValidationError("Insufficient funds to perform this transaction")
                record.tracker_id.balance -= record.amount
                record.category_id.amount += record.amount
            record.status='sent'
            return record
         
    @api.depends('send_money_button')
    def _set_expense(self):
        for record in self:
            if record.send_money_button == True:
                record.transaction_type='expense'

    @api.depends('default_button')
    def _switch_radio(self):
        for record in self:
            record.send_money_button = not record.default_button

    @api.onchange('send_money_button')
    def _toggle_default_button(self):
        if self.send_money_button:
            self.default_button = False

    @api.onchange('default_button')
    def _toggle_send_money_button(self):
        if self.default_button:
            self.send_money_button = False

    @api.depends('date','transaction_type')
    def _compute_name(self):
        for record in self:
            if not record.name:     
                record.name = "Transaction pending"
                if record.send_money_button==True:
                    record.name=f"Cash sent on {record.date}"

                else:
                    if record.transaction_type=='income':
                        record.name=f"Deposit on {record.date}"
                    elif record.transaction_type=='expense':
                        record.name=f"Withdrawal on {record.date}"
        
    
    @api.depends('amount','transaction_type')
    def _format_amount(self):
        for record in self:
            if record.transaction_type=='income':
                record.amount_format=f" + GHC {record.amount}"
            elif record.transaction_type=='expense':
                record.amount_format=f" - GHC {record.amount}"





    








class FinanceCategory(models.Model):
    _name="finance.category"
    _description="Finance Category"

    name=fields.Char(string="Category")
    amount=fields.Float()
    transaction_id=fields.One2many('finance.transaction','category_id',string="Transaction")

class FinanceGoals(models.Model):
    _name="finance.goals"
    _description="Finance Goals"

    name=fields.Char(string="Name")
    current_amount=fields.Float(string="Current Amount")
    target=fields.Float(string="Target Amount")
    transfer_in=fields.Float(string="Deposit")

    frequency=fields.Selection([('day','Day'),('week',"Week"),('month','Month'),('year','Year')], string="Per")
    progress=fields.Float(string="Progress", readonly=True, default=0.00, compute="_compute_progress")
    status=fields.Boolean(string="Completed", store=True, compute="_compute_status")
    date=fields.Date(default=fields.Date.context_today)
    account_id=fields.Many2one('finance.tracker',string="Account")
    next_run_date=fields.Date(readonly=True, compute="_compute_next_run_date")


    @staticmethod
    def get_next_run_date(frequency: str):
        run_date = date.today()
        if frequency == 'day':
            return run_date
        elif frequency == 'week':
            return run_date.replace(day=run_date.day + 7)
        elif frequency == 'month':
            if run_date.month == 12:
                return run_date.replace(year=run_date.year + 1, month=1)
            else:
                return run_date.replace(month=run_date.month + 1)
        elif frequency == 'year':
            return run_date.replace(year=run_date.year + 1)
        else:
            return run_date

    @api.depends('frequency')
    def _compute_next_run_date(self):
        for record in self:
            record.next_run_date = self.get_next_run_date(record.frequency)

    @api.depends('current_amount','target')
    def _compute_progress(self):
        for record in self:
            record.progress=100*record.current_amount/record.target

    @api.depends('current_amount','target')
    def _compute_status(self):
        for record in self:
            record.status=record.current_amount==record.target
        

    def run_compute_amount(self):
        goals = self.search([])
        for record in goals:
            if record.next_run_date == date.today(): 
                if record.account_id.balance >= record.transfer_in and record.current_amount<record.target:
                    self.env['finance.transaction'].create({
                        'name': f"Goal deposit on {record.next_run_date}",
                        'date': record.next_run_date,
                        'amount': record.transfer_in,
                        'account_balance': record.account_id.balance - record.transfer_in,
                        'transaction_type': 'expense',
                        'tracker_id': record.account_id.id,
                        'status': 'sent'
                    })
                    record.current_amount += record.transfer_in
                    record.next_run_date = self.get_next_run_date(record.frequency)
        return True
    
