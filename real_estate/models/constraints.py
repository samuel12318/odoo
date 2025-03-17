from odoo import models

def check_cost(self):
    for record in self:
        if record.cost < 0:
            raise models.ValidationError("Cost must be positive")
        if record.cost > 100:
            raise models.ValidationError("Cost must be less than 100")

def validate_money(self):
    for record in self:
        if record.price< 0:
            raise models.ValidationError("Selling price must be positive")
            
def validate_net_worth(self):
    for record in self:
        if  record.net_worth<0:
            raise models.ValidationError("Net worth must be positive")