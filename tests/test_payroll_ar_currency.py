"""
Tests para payroll_ar_currency.

Cobertura:
  1. Un contrato nuevo recibe ARS por defecto.
  2. currency_id del contrato sigue a wage_currency_id.
  3. currency_id del recibo sigue al contrato.
  4. La estructura puede usar un diario en ARS sin error.
  5. La estructura rechaza monedas no declaradas.

Ejecutar desde Odoo.sh o CLI:
  python odoo-bin -d <db> --test-enable -i payroll_ar_currency --stop-after-init
"""
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestPayrollArCurrency(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.usd = cls.env.ref('base.USD')
        cls.ars = cls.env.ref('base.ARS')
        cls.eur = cls.env.ref('base.EUR')

        # Empresa con moneda USD (simula el caso real)
        cls.company = cls.env.company
        cls.company.currency_id = cls.usd

        # Empleado de prueba
        cls.employee = cls.env['hr.employee'].create({
            'name': 'Test Employee',
            'company_id': cls.company.id,
        })

        # Tipo de estructura y estructura mínima
        cls.struct_type = cls.env['hr.payroll.structure.type'].create({
            'name': 'Test UOM',
            'wage_type': 'monthly',
        })

        # Diario en ARS
        cls.journal_ars = cls.env['account.journal'].create({
            'name': 'Salarios ARS Test',
            'code': 'SLARS',
            'type': 'general',
            'currency_id': cls.ars.id,
            'company_id': cls.company.id,
        })

        # Diario en USD (moneda empresa)
        cls.journal_usd = cls.env['account.journal'].create({
            'name': 'Salarios USD Test',
            'code': 'SLUSD',
            'type': 'general',
            'company_id': cls.company.id,
        })

    # ── 1. Contrato nuevo: ARS por defecto ───────────────────────────────────

    def test_01_new_contract_defaults_to_ars(self):
        contract = self.env['hr.contract'].create({
            'name': 'Test Contract ARS',
            'employee_id': self.employee.id,
            'wage': 1_000_000,
            'date_start': '2026-01-01',
            'structure_type_id': self.struct_type.id,
        })
        self.assertEqual(
            contract.wage_currency_id, self.ars,
            'Un contrato nuevo debe tener ARS como moneda de salario por defecto.',
        )

    # ── 2. currency_id sigue a wage_currency_id ─────────────────────────────

    def test_02_currency_id_follows_wage_currency(self):
        contract = self.env['hr.contract'].create({
            'name': 'Test Contract Currency',
            'employee_id': self.employee.id,
            'wage': 500_000,
            'date_start': '2026-01-01',
            'structure_type_id': self.struct_type.id,
            'wage_currency_id': self.ars.id,
        })
        self.assertEqual(
            contract.currency_id, self.ars,
            'currency_id debe ser ARS cuando wage_currency_id = ARS.',
        )

        # Cambiar a EUR
        contract.wage_currency_id = self.eur
        self.assertEqual(
            contract.currency_id, self.eur,
            'currency_id debe actualizarse al cambiar wage_currency_id.',
        )

    # ── 3. Recibo hereda la moneda del contrato ──────────────────────────────

    def test_03_payslip_currency_follows_contract(self):
        contract = self.env['hr.contract'].create({
            'name': 'Test Contract for Payslip',
            'employee_id': self.employee.id,
            'wage': 800_000,
            'date_start': '2026-01-01',
            'structure_type_id': self.struct_type.id,
            'wage_currency_id': self.ars.id,
            'state': 'open',
        })
        struct = self.env['hr.payroll.structure'].search(
            [['type_id', '=', self.struct_type.id]], limit=1
        )
        if not struct:
            self.skipTest('No hay estructura asociada al tipo de prueba')

        payslip = self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'contract_id': contract.id,
            'struct_id': struct.id,
            'date_from': '2026-04-01',
            'date_to': '2026-04-30',
        })
        self.assertEqual(
            payslip.currency_id, self.ars,
            'El recibo debe heredar la moneda ARS del contrato.',
        )

    # ── 4. Estructura acepta diario en ARS (empresa USD) ────────────────────

    def test_04_structure_allows_ars_journal_for_usd_company(self):
        """No debe lanzar ValidationError al asignar journal ARS."""
        try:
            struct = self.env['hr.payroll.structure'].create({
                'name': 'Test Struct ARS Journal',
                'type_id': self.struct_type.id,
                'journal_id': self.journal_ars.id,
            })
            struct.journal_id = self.journal_ars  # trigger constraint
        except ValidationError as e:
            self.fail(
                f'La estructura no debería rechazar un diario ARS para empresa USD.\n'
                f'Error: {e}'
            )

    # ── 5. Estructura rechaza monedas no declaradas ──────────────────────────

    def test_05_structure_rejects_undeclared_currency(self):
        """Debe lanzar ValidationError para monedas no configuradas."""
        # Crear diario en EUR (no está en ALLOWED_WAGE_CURRENCIES para USD)
        journal_eur = self.env['account.journal'].create({
            'name': 'Salarios EUR Test',
            'code': 'SLEUR',
            'type': 'general',
            'currency_id': self.eur.id,
            'company_id': self.company.id,
        })
        with self.assertRaises(ValidationError):
            self.env['hr.payroll.structure'].create({
                'name': 'Test Struct EUR Journal',
                'type_id': self.struct_type.id,
                'journal_id': journal_eur.id,
            })

    # ── 6. Fallback: sin wage_currency_id usa moneda de la empresa ───────────

    def test_06_fallback_to_company_currency(self):
        """Si wage_currency_id queda vacío, currency_id = moneda empresa."""
        contract = self.env['hr.contract'].create({
            'name': 'Test Contract Fallback',
            'employee_id': self.employee.id,
            'wage': 100,
            'date_start': '2026-01-01',
            'structure_type_id': self.struct_type.id,
            'wage_currency_id': self.ars.id,
        })
        # Forzar el campo a False (situación de migración / datos legacy)
        contract.write({'wage_currency_id': False})
        self.assertEqual(
            contract.currency_id, self.company.currency_id,
            'Sin wage_currency_id, currency_id debe ser la moneda de la empresa.',
        )
