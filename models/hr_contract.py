from odoo import models, fields


class HrContract(models.Model):
    _inherit = 'hr.contract'

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

    def _default_wage_currency(self):
        """Retorna ARS si existe, si no la moneda de la empresa actual."""
        ars = self.env.ref('base.ARS', raise_if_not_found=False)
        return ars or self.env.company.currency_id
