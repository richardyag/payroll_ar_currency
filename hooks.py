import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Al instalar el módulo: asigna ARS como moneda de salario en todos
    los contratos existentes que aún no tienen wage_currency_id configurado.

    hr.payslip.currency_id es un campo computed no almacenado que lee
    contract_id.wage_currency_id en tiempo real — no requiere migración.
    """
    ars = env.ref('base.ARS', raise_if_not_found=False)
    if not ars:
        _logger.warning(
            'payroll_ar_currency: moneda ARS no encontrada. '
            'Contratos no actualizados.'
        )
        return

    env.cr.execute(
        "UPDATE hr_contract SET wage_currency_id = %s WHERE wage_currency_id IS NULL",
        (ars.id,),
    )
    _logger.info(
        'payroll_ar_currency: wage_currency_id = ARS asignado en %d contratos.',
        env.cr.rowcount,
    )
