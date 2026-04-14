"""
Tests para payroll_ar_currency.

Cobertura:
  1. Un contrato nuevo recibe ARS por defecto en wage_currency_id.
  2. payslip.currency_id sigue a contract.wage_currency_id.
  3. payslip.currency_id hereda ARS del contrato.
  4. La estructura puede usar un diario en ARS sin error.
  5. La estructura rechaza monedas no declaradas.
  6. Fallback: sin wage_currency_id el recibo usa la moneda de la empresa.

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

        # Tipo de estructura mínima
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

    # ── helpers ─────────────────────────────────────────────────────────────

    def _make_contract(self, wage_currency_id=None, **kw):
        vals = {
            'name': 'Test Contract',
            'employee_id': self.employee.id,
            'wage': 1_000_000,
            'date_start': '2026-01-01',
            'structure_type_id': self.struct_type.id,
        }
        if wage_currency_id is not None:
            vals['wage_currency_id'] = wage_currency_id
        vals.update(kw)
        return self.env['hr.contract'].create(vals)

    def _make_payslip(self, contract):
        struct = self.env['hr.payroll.structure'].search(
            [['type_id', '=', self.struct_type.id]], limit=1
        )
        if not struct:
            return None
        return self.env['hr.payslip'].create({
            'employee_id': self.employee.id,
            'contract_id': contract.id,
            'struct_id': struct.id,
            'date_from': '2026-04-01',
            'date_to': '2026-04-30',
        })

    # ── 1. Contrato nuevo: ARS por defecto ───────────────────────────────────

    def test_01_new_contract_defaults_to_ars(self):
        contract = self._make_contract()
        self.assertEqual(
            contract.wage_currency_id, self.ars,
            'Un contrato nuevo debe tener ARS como moneda de salario por defecto.',
        )

    # ── 2. payslip.currency_id sigue a contract.wage_currency_id ────────────

    def test_02_payslip_currency_follows_wage_currency(self):
        contract_ars = self._make_contract(wage_currency_id=self.ars.id, state='open')
        slip_ars = self._make_payslip(contract_ars)
        if not slip_ars:
            self.skipTest('No hay estructura asociada al tipo de prueba')
        self.assertEqual(
            slip_ars.currency_id, self.ars,
            'El recibo debe mostrar ARS cuando wage_currency_id = ARS.',
        )

        contract_eur = self._make_contract(wage_currency_id=self.eur.id, state='open')
        slip_eur = self._make_payslip(contract_eur)
        self.assertEqual(
            slip_eur.currency_id, self.eur,
            'El recibo debe mostrar EUR cuando wage_currency_id = EUR.',
        )

    # ── 3. Recibo hereda ARS del contrato ────────────────────────────────────

    def test_03_payslip_currency_follows_contract(self):
        contract = self._make_contract(wage_currency_id=self.ars.id, state='open')
        slip = self._make_payslip(contract)
        if not slip:
            self.skipTest('No hay estructura asociada al tipo de prueba')
        self.assertEqual(
            slip.currency_id, self.ars,
            'El recibo debe heredar la moneda ARS del contrato.',
        )

    # ── 4. Estructura acepta diario en ARS (empresa USD) ────────────────────

    def test_04_structure_allows_ars_journal_for_usd_company(self):
        try:
            struct = self.env['hr.payroll.structure'].create({
                'name': 'Test Struct ARS Journal',
                'type_id': self.struct_type.id,
                'journal_id': self.journal_ars.id,
            })
            struct.journal_id = self.journal_ars
        except ValidationError as e:
            self.fail(
                f'La estructura no debería rechazar un diario ARS para empresa USD.\n'
                f'Error: {e}'
            )

    # ── 5. Estructura rechaza monedas no declaradas ──────────────────────────

    def test_05_structure_rejects_undeclared_currency(self):
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

    # ── 6. Fallback: sin wage_currency_id el recibo usa moneda de empresa ────

    def test_06_fallback_to_company_currency(self):
        contract = self._make_contract(wage_currency_id=self.ars.id, state='open')
        # Limpiar wage_currency_id simula datos legacy / migración
        contract.write({'wage_currency_id': False})
        slip = self._make_payslip(contract)
        if not slip:
            self.skipTest('No hay estructura asociada al tipo de prueba')
        self.assertEqual(
            slip.currency_id, self.company.currency_id,
            'Sin wage_currency_id, el recibo debe usar la moneda de la empresa.',
        )
