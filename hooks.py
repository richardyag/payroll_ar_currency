import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Al instalar el módulo: asigna ARS como moneda de salario en todos
    los contratos existentes que aún no tienen wage_currency_id configurado.

    Los contratos nuevos reciben ARS por defecto (ver hr_contract.py).
    """
    ars = env.ref('base.ARS', raise_if_not_found=False)
    if not ars:
        _logger.warning(
            'payroll_ar_currency: moneda ARS no encontrada en la base de datos. '
            'Los contratos existentes no fueron actualizados.'
        )
        return

    contracts = env['hr.contract'].search([('wage_currency_id', '=', False)])
    if contracts:
        contracts.write({'wage_currency_id': ars.id})
        _logger.info(
            'payroll_ar_currency: %d contratos actualizados con moneda ARS.',
            len(contracts),
        )
    else:
        _logger.info('payroll_ar_currency: no hay contratos a actualizar.')
