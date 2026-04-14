"""
Migración 18.0.1.0.0 → 18.0.1.0.1

El campo currency_id en hr.contract tenía el atributo `related` del padre
activo aunque redefiníamos `compute`. Esto impedía que el compute actualizara
el valor almacenado. Corrección: `related=None` en la definición del campo.

Esta migración sincroniza los datos existentes vía SQL directo para evitar
las validaciones del ORM que bloquean el cambio de moneda cuando existen
asientos contables.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    # 1. Contratos: currency_id = wage_currency_id
    cr.execute("""
        UPDATE hr_contract
        SET    currency_id = wage_currency_id
        WHERE  wage_currency_id IS NOT NULL
          AND  currency_id IS DISTINCT FROM wage_currency_id
    """)
    _logger.info("payroll_ar_currency: actualizados %d contratos (currency_id → ARS)", cr.rowcount)

    # hr_payslip.currency_id es un campo related sin store en Odoo 18 —
    # no existe como columna en la tabla, se calcula desde el contrato.
