from odoo import models, fields, api


class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    # En Odoo 18, _inherit + campo related no puede ser sobreescrito con
    # compute porque _complete_related() sobrescribe _depends con la cadena
    # del related (contract_id.currency_id), ignorando nuestro @api.depends.
    # Solución: definimos el campo Y lo parchamos en _setup_complete, que corre
    # después de que Odoo termina el setup y antes de que el registry esté listo.
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        compute='_compute_payslip_currency',
        store=False,
    )

    @classmethod
    def _setup_complete(cls):
        super()._setup_complete()
        field = cls._fields.get('currency_id')
        if field and getattr(field, 'related', None):
            # Limpiar el related para que _compute_related no interfiera
            field.related = None
            field.compute = '_compute_payslip_currency'
            field._depends = frozenset({
                'contract_id.wage_currency_id',
                'contract_id.company_id.currency_id',
                'company_id.currency_id',
            })

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
