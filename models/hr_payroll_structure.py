from odoo import models, api, _
from odoo.exceptions import ValidationError


# Pares (moneda de empresa → monedas de salario permitidas) que este módulo habilita.
# Extender este dict si en el futuro se agregan otras combinaciones.
ALLOWED_WAGE_CURRENCIES = {
    'USD': {'ARS'},   # empresa en dólares, sueldos en pesos
    'EUR': {'ARS'},   # filiales europeas con empleados en Argentina
}


class HrPayrollStructure(models.Model):
    _inherit = 'hr.payroll.structure'

    # ── Override del constraint de moneda del diario ─────────────────────────
    #
    # Odoo estándar tiene en hr.payroll.structure un @api.constrains('journal_id')
    # que impide usar un diario con moneda distinta a la empresa.
    # Método más probable en Odoo 18: _check_journal_type
    #
    # Al redefinir el método con el mismo nombre, Python MRO garantiza que
    # se ejecuta nuestra versión en lugar de la original.
    #
    # IMPORTANTE PARA UPGRADES:
    #   Si tras una actualización de Odoo el constraint vuelve a dispararse,
    #   buscar el nombre real del método en el stack trace y actualizar este
    #   archivo. Buscar en:
    #   odoo/addons/hr_payroll/models/hr_payroll_structure.py
    #   la línea con @api.constrains('journal_id')
    #
    @api.constrains('journal_id')
    def _check_journal_type(self):
        """
        Versión extendida del constraint de moneda del diario de sueldos.

        Permite usar diarios en ARS (u otras monedas configuradas en
        ALLOWED_WAGE_CURRENCIES) cuando la empresa opera en USD/EUR.
        Rechaza cualquier otra combinación no declarada explícitamente.
        """
        for struct in self:
            journal = struct.journal_id
            if not journal or not journal.currency_id:
                # Sin moneda explícita en el diario: hereda la de la empresa → ok
                continue

            company_cur = struct.company_id.currency_id.name
            journal_cur = journal.currency_id.name

            if journal_cur == company_cur:
                continue  # misma moneda → ok

            allowed = ALLOWED_WAGE_CURRENCIES.get(company_cur, set())
            if journal_cur in allowed:
                continue  # par explícitamente permitido → ok

            raise ValidationError(_(
                'El diario "%(journal)s" tiene moneda %(jcur)s, '
                'que no está permitida para la moneda de la empresa (%(ccur)s).\n\n'
                'Si necesita agregar este par de monedas, edite el diccionario '
                'ALLOWED_WAGE_CURRENCIES en el módulo payroll_ar_currency.',
                journal=journal.name,
                jcur=journal_cur,
                ccur=company_cur,
            ))
