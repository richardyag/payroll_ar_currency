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

    # ── Métodos ─────────────────────────────────────────────────────────────

    def _default_wage_currency(self):
        """Retorna ARS si existe, si no la moneda de la empresa actual."""
        ars = self.env.ref('base.ARS', raise_if_not_found=False)
        return ars or self.env.company.currency_id

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        records._force_currency_from_wage()
        return records

    def write(self, vals):
        res = super().write(vals)
        if 'wage_currency_id' in vals:
            self._force_currency_from_wage()
        return res

    def _force_currency_from_wage(self):
        """
        Sincroniza currency_id con wage_currency_id usando SQL directo.

        En Odoo 18 no es posible redefinir un campo `related` almacenado
        mediante herencia sin que el atributo `related` del padre persista
        y bloquee el compute. El enfoque SQL bypasea el ORM (y sus
        restricciones contables) actualizando directamente la columna
        almacenada en la tabla, que es lo que hr.payslip.currency_id lee.

        No afecta la contabilidad: el ORM no recomputa un campo related
        almacenado a menos que cambien sus dependencias declaradas
        (company_id.currency_id), que en este caso no cambia.
        """
        for contract in self:
            target = contract.wage_currency_id or contract.company_id.currency_id
            if target:
                self.env.cr.execute(
                    "UPDATE hr_contract SET currency_id = %s WHERE id = %s",
                    (target.id, contract.id),
                )
        # Limpiar cache para que la próxima lectura venga de la DB
        self.invalidate_recordset(['currency_id'])
