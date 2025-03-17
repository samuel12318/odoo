from odoo import fields, models,api
from . import constraints


class EstateProperty(models.Model):
    _name = "estate.property"
    _description = "Real Estate Property"
    _order = "price desc"

    name = fields.Char(string="Name of Property", required=True,help="Name of the property,Enter captial letters")
    price = fields.Float(string="Selling Price", default=0.0)
    sequence = fields.Integer('Sequence', default=1, help="Used to order stages. Lower is better.")

    location = fields.Char(string="Location", default="Amasaman",required=True)
    description = fields.Text(string="Description")
    bedrooms = fields.Selection([('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5')], string="Bedrooms")
    status = fields.Selection([('pending','Pending'),('accepted','Accepted'),('sold','Sold')], default='pending')

    estate_user_id=fields.Many2one(comodel_name='estate.user',string="Estate User")


    @api.ondelete(at_uninstall=False)
    def _unlink_check(self):
        for record in self:
            if record.status in ('pending', 'accepted'):
                raise models.UserError("But why you dey want del something wey dey Pending or Accepted")

    def unlink(self):
        self._unlink_check()
        return super(EstateProperty, self).unlink()


    @api.constrains('price')
    def _check_price(self):
        constraints.validate_money(self)
                                
                            

class User(models.Model):
    _name = "estate.user"
    _description = "Real Estate Client"
    _rec_name = "first_name"
    
    title=fields.Char(string="Title", default="Mr./Mrs.", readonly=True, compute="_compute_title")
    first_name = fields.Char(string="First Name")
    last_name = fields.Char(string="Last Name")
    gender = fields.Selection([('male','Male'),('female','Female'),('other','Other')],string="Gender")
    is_active = fields.Boolean(default=True,string="Active")

    net_worth = fields.Float()
    net_worth_plus_25 = fields.Float(compute="_compute_25",inverse="_inverse_25",store=True)

    estate_property_id = fields.One2many(comodel_name='estate.property',inverse_name='estate_user_id',string="Property Name")


    def action_reset_net_worth(self):
        for record in self:
            record.net_worth=0.0
            record.is_active=False
        return True

    @api.depends('net_worth')
    def _compute_25(self):
        for record in self:
            record.net_worth_plus_25=1.25*record.net_worth 

    @api.depends('net_worth_plus_25')
    def _inverse_25(self):
        for record in self:
            record.net_worth=record.net_worth_plus_25/1.25

    @api.depends('gender')
    def _compute_title(self):
        for record in self:
            if record.gender == 'male':
                record.title = 'Mr.'
            elif record.gender == 'female':
                record.title = 'Mrs.'
            else:
                record.title = 'Gyimii.'

    @api.constrains('net_worth')
    def _check_net_worth(self):
        constraints.validate_net_worth(self)


class ResUsers(models.Model):
    _inherit='estate.user'

    property_ids=fields.One2many('estate.property','estate_user_id',string='Property',domain=[('status','!=','sold')])
