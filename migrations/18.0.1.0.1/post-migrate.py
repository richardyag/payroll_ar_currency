"""
Migración 18.0.1.0.0 → 18.0.1.0.1

Limpieza: la arquitectura cambió de sobreescribir hr.contract.currency_id
(campo related almacenado que el ORM revierte) a sobreescribir
hr.payslip.currency_id como campo computed no almacenado.

No se requiere migración de datos: hr.payslip.currency_id lee
contract_id.wage_currency_id en tiempo real.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    _logger.info('payroll_ar_currency: migración 18.0.1.0.1 — sin cambios de datos requeridos.')
