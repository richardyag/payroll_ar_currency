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

    # 2. Recibos: currency_id = currency del contrato asociado
    cr.execute("""
        UPDATE hr_payslip hp
        SET    currency_id = c.wage_currency_id
        FROM   hr_contract c
        WHERE  hp.contract_id = c.id
          AND  c.wage_currency_id IS NOT NULL
          AND  hp.currency_id IS DISTINCT FROM c.wage_currency_id
    """)
    _logger.info("payroll_ar_currency: actualizados %d recibos (currency_id → ARS)", cr.rowcount)
