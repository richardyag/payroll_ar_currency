from odoo import models, fields, api


class HrContract(models.Model):
    _inherit = 'hr.contract'

    # ── Campo nuevo ─────────────────────────────────────────────────────────
    wage_currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda del salario',
        required=True,
        default=lambda self: self._default_wage_currency(),
        tracking=True,
        help=(
            'Moneda en que se expresa el salario del empleado. '
            'Permite liquidar en ARS cuando la empresa opera en USD. '
            'Por defecto: ARS (Peso Argentino).'
        ),
    )

    # ── Override del campo relacionado de Odoo ──────────────────────────────
    #
    # En Odoo estándar:
    #   currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)
    #
    # Lo reemplazamos por un campo computed+stored para que tome el valor de
    # wage_currency_id en lugar de la moneda de la empresa.
    # Al estar stored=True, hr.payslip.currency_id (related: contract_id.currency_id)
    # lo lee correctamente sin cambios adicionales en el modelo de recibos.
    #
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Moneda',
        compute='_compute_currency_id',
        store=True,
        precompute=True,
        readonly=False,
    )

    # ── Métodos ─────────────────────────────────────────────────────────────

    def _default_wage_currency(self):
        """Retorna ARS si existe, si no la moneda de la empresa actual."""
        ars = self.env.ref('base.ARS', raise_if_not_found=False)
        return ars or self.env.company.currency_id

    @api.depends('wage_currency_id', 'company_id.currency_id')
    def _compute_currency_id(self):
        """
        currency_id sigue a wage_currency_id.
        Fallback: moneda de la empresa (comportamiento estándar de Odoo).
        """
        for contract in self:
            contract.currency_id = (
                contract.wage_currency_id
                or contract.company_id.currency_id
            )
