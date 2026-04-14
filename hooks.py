import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """
    Al instalar el módulo:
    1. Asigna ARS como moneda de salario en contratos sin wage_currency_id.
    2. Sincroniza currency_id = wage_currency_id vía SQL directo para
       evitar el bloqueo del ORM cuando ya existen asientos contables.
    """
    ars = env.ref('base.ARS', raise_if_not_found=False)
    if not ars:
        _logger.warning(
            'payroll_ar_currency: moneda ARS no encontrada. '
            'Contratos no actualizados.'
        )
        return

    # Paso 1: wage_currency_id en contratos que no lo tienen
    env.cr.execute(
        "UPDATE hr_contract SET wage_currency_id = %s WHERE wage_currency_id IS NULL",
        (ars.id,),
    )
    _logger.info('payroll_ar_currency: wage_currency_id = ARS en %d contratos.', env.cr.rowcount)

    # Paso 2: currency_id = wage_currency_id (SQL directo, sin pasar por ORM)
    env.cr.execute(
        """
        UPDATE hr_contract
        SET    currency_id = wage_currency_id
        WHERE  wage_currency_id IS NOT NULL
          AND  currency_id IS DISTINCT FROM wage_currency_id
        """
    )
    _logger.info('payroll_ar_currency: currency_id sincronizado en %d contratos.', env.cr.rowcount)

    env['hr.contract'].invalidate_model(['currency_id'])
