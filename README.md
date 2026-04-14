# payroll_ar_currency

**Odoo 18 · Nómina en moneda secundaria para Argentina**

Permite liquidar sueldos en **pesos argentinos (ARS)** cuando la empresa tiene su contabilidad en **dólares estadounidenses (USD)**.

---

## Problema que resuelve

En Odoo estándar, la moneda de los contratos y recibos de sueldo está ligada a la moneda de la empresa mediante campos `related` de solo lectura:

```
hr.payslip.currency_id  →  related: contract_id.currency_id
hr.contract.currency_id →  related: company_id.currency_id  ← origen
```

Esto impide que una empresa con libros en USD liquide sueldos en ARS sin modificar el código. Este módulo resuelve esa limitación de forma mínima e invasiva.

---

## Caso de uso

Empresas industriales argentinas (típicamente bajo CCT UOM / ASSIMRA) que:

- Facturan y llevan su contabilidad comercial en **USD**
- Pagan sueldos y cargas sociales en **ARS** según escalas paritarias
- Usan Odoo 18 con `l10n_ar` y el módulo de Nómina

---

## Qué cambia en el estándar

| Modelo | Campo | Antes | Después |
|--------|-------|-------|---------|
| `hr.contract` | `wage_currency_id` | No existe | Nuevo campo `Many2one res.currency`, default **ARS** |
| `hr.contract` | `currency_id` | `related: company_id.currency_id` (readonly) | `compute` stored, sigue a `wage_currency_id` |
| `hr.payroll.structure` | constraint `_check_journal_type` | Bloquea diarios con moneda ≠ empresa | Permite pares declarados (USD→ARS, EUR→ARS) |

`hr.payslip.currency_id` **no se toca** — hereda ARS automáticamente desde el contrato.

---

## Instalación

### Requisitos

- Odoo 18 (Community o Enterprise)
- Módulos: `hr_payroll`, `hr_payroll_account`
- Moneda ARS activa en la base (`Contabilidad → Configuración → Monedas`)

### Pasos

1. Copiar el módulo en el directorio de addons del servidor (o en el repo de Odoo.sh)
2. Actualizar lista de aplicaciones
3. Instalar **"Nómina en Moneda Secundaria (AR)"**

El `post_init_hook` asigna automáticamente ARS como moneda de salario a todos los contratos existentes.

### Post-instalación

1. Ir al diario `Salarios` (`Contabilidad → Configuración → Diarios`)
   → Establecer **Moneda: ARS**
2. En cada estructura salarial (`Nómina → Configuración → Estructuras Salariales`)
   → Verificar que el campo **Diario de sueldos** apunta al diario en ARS
3. Contratos existentes: `wage_currency_id` ya fue seteado a ARS por el hook.
   Verificar en `Nómina → Contratos` si algún contrato requiere otra moneda.

---

## Uso

### Contrato nuevo

El campo **"Moneda del salario"** aparece en el formulario de contratos, justo antes del campo **Salario**. Por defecto es ARS. Se puede cambiar por empleado si hubiera casos en otra moneda.

![Formulario de contrato con campo Moneda del salario](docs/contract_form.png)

### Recibo de sueldo

El encabezado del recibo muestra el campo **Moneda** (ARS). Los importes de todas las líneas se expresan en ARS.

### Contabilidad multi-moneda

Cuando el diario de sueldos tiene moneda ARS y la empresa opera en USD, Odoo genera el asiento con:

- `amount_currency` = importe en ARS (ej: `1.216.077`)
- `debit / credit` = equivalente en USD al tipo de cambio del día (ej: `878`)

El cierre por diferencia de cambio es automático y usa el mecanismo nativo de Odoo.

---

## Agregar otros pares de monedas

Editar el diccionario `ALLOWED_WAGE_CURRENCIES` en `models/hr_payroll_structure.py`:

```python
ALLOWED_WAGE_CURRENCIES = {
    'USD': {'ARS'},        # empresa en dólares, sueldos en pesos
    'EUR': {'ARS'},        # filiales europeas con empleados en Argentina
    # 'USD': {'ARS', 'CLP'},  # ejemplo: agregar peso chileno
}
```

---

## Tests

```bash
# Desde CLI de Odoo
python odoo-bin -d <nombre_db> \
    --test-enable \
    -i payroll_ar_currency \
    --stop-after-init

# Desde Odoo.sh: los tests se ejecutan automáticamente en el build
```

Casos cubiertos:

| Test | Descripción |
|------|-------------|
| `test_01` | Contrato nuevo recibe ARS por defecto |
| `test_02` | `currency_id` sigue a `wage_currency_id` al cambiar |
| `test_03` | Recibo hereda la moneda del contrato |
| `test_04` | Estructura acepta diario ARS para empresa USD |
| `test_05` | Estructura rechaza monedas no declaradas (EUR en empresa USD) |
| `test_06` | Fallback a moneda de la empresa si `wage_currency_id` queda vacío |

---

## Nota sobre upgrades de Odoo

El punto más frágil del módulo es el override del constraint `_check_journal_type`
en `hr.payroll.structure`. Si tras una actualización de Odoo el constraint vuelve
a dispararse, el nombre del método cambió en el core.

**Para diagnosticar:**
```bash
grep -r "misma moneda\|same currency\|journal.*currency" \
    /ruta/odoo/addons/hr_payroll/models/
```
Actualizar el nombre del método en `models/hr_payroll_structure.py` y reinstalar el módulo.

---

## Estructura del módulo

```
payroll_ar_currency/
├── __init__.py
├── __manifest__.py
├── hooks.py                          post_init_hook
├── models/
│   ├── __init__.py
│   ├── hr_contract.py                wage_currency_id + override currency_id
│   └── hr_payroll_structure.py       override constraint diario
├── tests/
│   ├── __init__.py
│   └── test_payroll_ar_currency.py   6 tests unitarios
└── views/
    ├── hr_contract_views.xml         campo en formulario de contrato
    └── hr_payslip_views.xml          moneda en encabezado de recibo
```

---

## Licencia

LGPL-3 · [Guvens Consultora](https://github.com/GuvensConsultora)

## Autor

Ricardo — [richardyag](https://github.com/richardyag)
