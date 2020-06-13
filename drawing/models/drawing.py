from odoo import fields, models, api, _
from datetime import datetime


class ConstructionDrawing (models.Model):
    _name = 'construction.drawing'
    _description = 'Items Records for Projects'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name_seq'

    project_id = fields.Many2one('project.project', string='Project', required=True)
    pricing_id = fields.Many2one('construction.pricing', string='Pricing', required=True)
    item_ids = fields.One2many('item.number', 'drawing_id', string='Item Code', copy=True)
    Division = fields.Selection([('GRC', 'GRC'),('GRP', 'GRP'),('GRG','GRG'),('MOULD', 'MOULD'),('STEEL', 'STEEL')],)
    Building = fields.Char(String='Building')
    name_seq = fields.Char(string='Drawing No', required=True, copy=False, readonly=True, index=True,
                           default=lambda self: _('New'))
    create_date = fields.Datetime(string="Create Date", default=datetime.now())
    close_date = fields.Datetime(string="Close Date", default=datetime.now())
    create_by_id = fields.Many2one('res.users', 'Created By')
    confirmed_by_id = fields.Many2one('res.users', string="Confirmed By", copy=False)
    department_manager_id = fields.Many2one('res.users', string="Department Manager", copy=False)
    approved_by_id = fields.Many2one('res.users', string="Approved By", copy=False)
    rejected_by = fields.Many2one('res.users', string="Rejected By", copy=False)
    confirmed_date = fields.Date(string="Confirmed Date", readonly=True, copy=False)
    department_approval_date = fields.Date(string="Department Approval Date", readonly=True, copy=False)
    approved_date = fields.Date(string="Approved Date", readonly=True, copy=False)
    rejected_date = fields.Date(string="Rejected Date", readonly=True, copy=False)
    reason_for_requisition = fields.Text(string="Reason For Requisition")
    state = fields.Selection([
        ('new', 'New'),
        ('department_approval', 'Waiting Department Approval'),
        ('ir_approve', 'Waiting User Approved'),
        ('approved', 'Approved'),
        ('cancel', 'Cancel')], string='Stage', copy=False, default="new")
    active = fields.Boolean(default=True, help="If the active field is set to False")
    total_cost = fields.Float(String='Total Cost', compute='_compute_total_cost', required=True)
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    total_prod = fields.Float(String='Amount Production', compute='_compute_total_prod')
    total_deli = fields.Float(String='Amount Delivery', compute='_compute_total_deli')
    total_erec = fields.Float(String='Amount Erection', compute='_compute_total_erec')

    @api.multi
    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id.id

    @api.multi
    def print_quotation(self):
        return self.env.ref('drawing.report_boq').report_action(self)

    @api.multi
    def confirm_drawing(self):
        res = self.write({
            'state': 'department_approval',
            'confirmed_by_id': self.env.user.id,
            'confirmed_date': datetime.now()
        })
        return res

    @api.multi
    def department_approve(self):
        res = self.write({
            'state': 'ir_approve',
            'department_manager_id': self.env.user.id,
            'department_approval_date': datetime.now()
        })
        return res

    @api.multi
    def action_cancel(self):
        res = self.write({
            'state': 'cancel',
        })
        return res

    @api.multi
    def action_reject(self):
        res = self.write({
            'state': 'cancel',
            'rejected_date': datetime.now(),
            'rejected_by': self.env.user.id
        })
        return res

    @api.multi
    def action_reset_draft(self):
        res = self.write({
            'state': 'new',
        })
        return res

    @api.multi
    def action_approve(self):
        res = self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approved_date': datetime.now()
        })
        return res

    @api.model
    def create(self, vals):
        if vals.get('name_seq', _('New')) == _('New'):
            vals['name_seq'] = self.env['ir.sequence'].next_by_code('construction.drawing') or _('New')
        result = super(ConstructionDrawing, self).create(vals)
        return result

    @api.multi
    def pricing(self):
        self.ensure_one()
        return {
            'name': _('Pricing'),
            'domain': [('drawing_id', '=', self.id)],
            'res_model': 'construction.pricing',
            'type': 'ir.actions.act_window',
            'view_id': False,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'limit': 80,
            'context': "{'default_project_id': %d,'default_drawing_id': %d}" % (self.project_id.id, self.id)
        }

    @api.multi
    def _compute_total_cost(self):
        total = 0.0
        for line in self.item_ids:
            total += line.Amount_total
        self.total_cost = total

    @api.multi
    def _compute_total_prod(self):
        total = 0.0
        for line in self.item_ids:
            total += line.Amount_prod
        self.total_prod = total

    @api.multi
    def _compute_total_deli(self):
        total = 0.0
        for line in self.item_ids:
            total += line.Amount_deli
        self.total_deli = total

    @api.multi
    def _compute_total_erec(self):
        total = 0.0
        for line in self.item_ids:
            total += line.Amount_erec
        self.total_erec = total


class ItemNumber (models.Model):
    _name = 'item.number'
    _description = 'Items Records for Projects Lines'
    _rec_name = 'title'

    title = fields.Char('Item No', required=True)
    drawing_id = fields.Many2one('construction.drawing', 'Drawing')
    Type = fields.Char('Type')
    Type_of_finish = fields.Char('Type of finish')
    Length = fields.Float('Length', required=True)
    Width = fields.Float('Width', required=True)
    Height = fields.Float('Height', required=True)
    Thick = fields.Float('Thick', required=True)
    Quantity = fields.Integer('Quantity', required=True)
    Volume = fields.Integer('Volume', compute='_compute_total', required=True)
    Unit = fields.Many2one('uom.uom', 'Unit Of Measure')
    UR_production = fields.Float(String='UR Production')
    UR_delivery = fields.Float(String='UR Delivery')
    UR_erection = fields.Float(String='UR Erection')
    Amount_prod = fields.Float(String='Amount Production', compute='_compute_total_production', required=True)
    Amount_deli = fields.Float(String='Amount Delivery', compute='_compute_total_delivery', required=True)
    Amount_erec = fields.Float(String='Amount Erection', compute='_compute_total_erection', required=True)
    UR_total = fields.Float(String='Unit Rate Total', compute='_compute_total_UR', required=True)
    Amount_total = fields.Float(String='Amount Total', compute='_compute_total_amount', required=True)
    Amount_cost_t = fields.Float(String='Total Amount', compute='_compute_amount_total', required=True)
    pricing_id = fields.Many2one('construction.pricing', String='Pricing',
                                 default=lambda self: self.env.context.get('drawing_id'))
    currency_id = fields.Many2one("res.currency", compute='get_currency_id', string="Currency")
    volume_prod = fields.Float(String='Unit Production', compute='_compute_unit_production', required=True)
    volume_deli = fields.Float(String='Unit Delivery', compute='_compute_unit_delivery', required=True)
    volume_erec = fields.Float(String='Unit Erection', compute='_compute_unit_erection', required=True)

    @api.multi
    def _compute_amount_total(self):
        total = 0.0
        for line in self.items:
            total += line.subtotal
        self.total_labour_cost = total

    @api.multi
    def open_bom(self):
        self.ensure_one()
        return {
            'name': _('Details'),
            'domain': [('item_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'item.code',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
            'context': "{'default_item_id': %d}" % (self.id)

        }

    @api.multi
    @api.depends('Length', 'Width', 'Height')
    def _compute_total(self):
        for rec in self:
            rec.Volume = rec.Length * rec.Width * rec.Height

    @api.multi
    @api.depends('UR_production', 'UR_delivery', 'UR_erection')
    def _compute_total_UR(self):
        for rec in self:
            rec.UR_total = rec.UR_production + rec.UR_delivery + rec.UR_erection

    @api.multi
    @api.depends('Amount_prod', 'Amount_deli', 'Amount_erec')
    def _compute_total_amount(self):
        for rec in self:
            rec.Amount_total = rec.Amount_prod + rec.Amount_deli + rec.Amount_erec

    @api.multi
    @api.depends('Quantity', 'volume_prod')
    def _compute_total_production(self):
        for rec in self:
            rec.Amount_prod = rec.Quantity * rec.volume_prod

    @api.multi
    @api.depends('volume_deli', 'Quantity')
    def _compute_total_delivery(self):
        for rec in self:
            rec.Amount_deli = rec.Quantity * rec.volume_deli

    @api.multi
    @api.depends('volume_erec', 'Quantity')
    def _compute_total_erection(self):
        for rec in self:
            rec.Amount_erec = rec.Quantity * rec.volume_erec

    @api.multi
    @api.depends('UR_production', 'Volume')
    def _compute_unit_production(self):
        for rec in self:
            rec.volume_prod = rec.UR_production * rec.Volume

    @api.multi
    @api.depends('UR_delivery', 'Volume')
    def _compute_unit_delivery(self):
        for rec in self:
            rec.volume_deli = rec.UR_delivery * rec.Volume

    @api.multi
    @api.depends('UR_erection', 'Volume')
    def _compute_unit_erection(self):
        for rec in self:
            rec.volume_erec = rec.UR_erection * rec.Volume

    @api.multi
    def get_currency_id(self):
        user_id = self.env.uid
        res_user_id = self.env['res.users'].browse(user_id)
        for line in self:
            line.currency_id = res_user_id.company_id.currency_id.id

    @api.multi
    @api.onchange('pricing_id')
    def onchange_pricing_id(self):
        res = {}
        if not self.pricing_id:
            return res
        self.UR_production = self.pricing_id.UR_production
        self.UR_delivery = self.pricing_id.UR_delivery
        self.UR_erection = self.pricing_id.UR_erection



    class ItemCode(models.Model):
        _name = 'item.code'
        _description = 'Item Code'
        _inherit = ['mail.thread', 'mail.activity.mixin']
        _rec_name = 'title'
        _order = 'sequence,id'

        item_id = fields.Many2one('item.number', string='Item No',
                                  required=True, default=lambda self: self.env.context.get('item_id'))
        title = fields.Char('Item Code', required=True)
        Image = fields.Binary(String='image')
        sequence = fields.Integer('Item Code number', default=10)
        description = fields.Html('Description', translate=True, oldname="note",
                                  help="An introductory text to your page")
        sub_ids = fields.One2many('item.sub', 'code_id', string='Item Subs', copy=True)
        Type = fields.Char('Type')
        Type_of_finish = fields.Char('Type of finish')
        Length = fields.Char('Length', required=True)
        Width = fields.Char('Width', required=True)
        Height = fields.Char('Height', required=True)
        Thick = fields.Char('Thick', required=True)
        Quantity = fields.Char('Quantity', required=True)
        Unit = fields.Many2one('uom.uom','Unit Of Measure')

    class ItemSub(models.Model):
        _name = 'item.sub'
        _description = 'Item Sub'
        _rec_name = 'title'
        _order = 'sequence,id'

        # Model fields #
        title = fields.Char('Item Sub', required=True, translate=True)
        code_id = fields.Many2one('item.code', string='Item Code', required=True,
                                  default=lambda self: self.env.context.get('code_id'))
        sequence = fields.Integer('Sequence', default=10)
        Image = fields.Binary(String='image')
        Length = fields.Char('Length', required=True)
        Width = fields.Char('Width', required=True)
        Height = fields.Char('Height', required=True)
        Thick = fields.Char('Thick', required=True)
        Quantity = fields.Char('Quantity', required=True)
        Unit = fields.Many2one('uom.uom', 'Unit Of Measure')

