from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # En Odoo 18, hr.payslip.currency_id es un campo related no almacenado
    # (related='contract_id.currency_id', store=False). Al proveer un compute
    # explícito, Odoo usa nuestra función en vez de _compute_related, sin
    # necesidad de sobreescribir la definición del campo en hr.contract.
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        compute='_compute_payslip_currency',
        store=False,
    )

    @api.depends(
        'contract_id.wage_currency_id',
        'contract_id.company_id.currency_id',
        'company_id.currency_id',
    )
    def _compute_payslip_currency(self):
        for slip in self:
            contract = slip.contract_id
            slip.currency_id = (
                contract.wage_currency_id
                or contract.company_id.currency_id
                or slip.company_id.currency_id
            )
