{
    'name': 'Nómina en Moneda Secundaria (AR)',
    'version': '18.0.1.0.0',
    'summary': 'Permite liquidar sueldos en ARS cuando la empresa opera en USD',
    'description': """
        Extiende hr.contract con el campo wage_currency_id para que la moneda
        del salario sea independiente de la moneda contable de la empresa.

        Caso de uso principal: empresa con libros en USD que paga sueldos en ARS
        (industria metalúrgica argentina, CCT UOM/ASSIMRA).

        Cambios respecto al estándar:
        - hr.contract: nuevo campo wage_currency_id (Many2one res.currency)
        - hr.contract: currency_id pasa de related readonly a computed stored
        - hr.payroll.structure: constraint de moneda de journal relaxada
          para permitir pares conocidos (USD/EUR empresa + ARS sueldos)
    """,
    'author': 'Guvens Consultora',
    'category': 'Payroll',
    'license': 'LGPL-3',
    'depends': ['hr_payroll', 'hr_payroll_account'],
    'data': [
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
    ],
    'post_init_hook': 'post_init_hook',
    'installable': True,
    'auto_install': False,
    'application': False,
}
