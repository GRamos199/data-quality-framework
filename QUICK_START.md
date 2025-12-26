# Quick Start Guide - Data Quality Framework

## 🚀 Ejecutar Todo Rápidamente

### Paso 1: Activar el ambiente virtual
```bash
cd /home/george/data-quality-framework
source venv/bin/activate
```

### Paso 2: Ejecutar las pruebas (21 tests)
```bash
pytest tests/ -v
```

**Salida esperada:**
```
test_validators.py::TestNullCheckValidator::test_valid_no_nulls PASSED
test_validators.py::TestNullCheckValidator::test_invalid_with_nulls PASSED
...
===================== 21 passed in 0.43s =====================
```

### Paso 3: Ejecutar ejemplos del framework
```bash
python examples/openweather_examples.py
```

**Salida esperada:**
```
======================================================================
EXAMPLE 1: Valid Raw OpenWeather Data
======================================================================
✓ All quality checks passed for openweather (raw)
...
EXAMPLE 6: Clean Data with Duplicate Records
======================================================================
✗ Quality checks failed for openweather (raw): ['Unique City-Date']
```

### Paso 4: Ejecutar la integración completa ETL
```bash
python examples/lakehouse_integration_example.py
```

**Salida esperada:**
```
[EXTRACT] Fetching data from OpenWeather API...
✓ Extracted 3 records from API

[LOAD RAW] Validating data before loading to raw layer...
✓ Raw layer validation passed

[TRANSFORM] Cleaning and transforming raw data...
✓ Transformed 3 records

[LOAD CLEAN] Validating transformed data before loading...
✓ Clean layer validation passed

[PUBLISH] Loading to Analytics layer...
✓ Published 3 records to Analytics

✓ PIPELINE COMPLETED SUCCESSFULLY
```

---

## 📊 Cómo Usar tu Archivo JSON del Proyecto Anterior

### Paso 1: Crear script para leer tu JSON

```python
# test_your_data.py
import pandas as pd
import json
from data_quality_framework import (
    NullCheckValidator,
    RangeValidator,
    SchemaValidator,
)
from data_quality_framework.orchestrator import QualityCheckOrchestrator

# Leer tu JSON
with open('tu_archivo.json', 'r') as f:
    data_dict = json.load(f)

# Convertir a DataFrame (ajusta según tu estructura)
df = pd.DataFrame(data_dict)

# Crear validadores personalizados para tu datos
validators = [
    NullCheckValidator("campos_obligatorios", ["campo1", "campo2"]),
    RangeValidator("rangos_validos", {
        "temperatura": {"min": -60, "max": 65},
        "humedad": {"min": 0, "max": 100},
    }),
]

# Ejecutar validación
orchestrator = QualityCheckOrchestrator()
result = orchestrator.run_checks(
    df,
    validators,
    dataset_name="mi_dataset",
    layer="raw",
    stop_on_failure=False,
)

# Ver resultados
if result.passed:
    print("✓ Datos válidos!")
else:
    print("✗ Datos inválidos:")
    for validator, errors in result.errors.items():
        print(f"  {validator}: {errors}")
```

### Paso 2: Dónde poner tu archivo JSON

**Opción A: En la raíz**
```bash
/home/george/data-quality-framework/
├── tu_archivo.json    ← Aquí
├── test_your_data.py
└── ...
```

**Opción B: En carpeta `data/`** (recomendado)
```bash
/home/george/data-quality-framework/
├── data/
│   └── tu_archivo.json    ← Aquí
├── test_your_data.py
└── ...
```

### Paso 3: Ejecutar tu test
```bash
python test_your_data.py
```

---

## 🎯 Estructura del JSON Esperada

### Si tu JSON tiene datos meteorológicos:
```json
{
  "id": 1,
  "city": "Buenos Aires",
  "dt": "2025-12-26T10:30:00",
  "temperature": 28.5,
  "humidity": 65,
  "pressure": 1013
}
```

### Si es un array:
```json
[
  {
    "id": 1,
    "city": "Buenos Aires",
    "temperature": 28.5
  },
  {
    "id": 2,
    "city": "Madrid",
    "temperature": 15.2
  }
]
```

---

## 📁 Configuración con YAML

También puedes crear una configuración YAML para validar automáticamente:

```yaml
# config/mi_dataset_validation.yaml
dataset: "mi_dataset"
layer: "raw"

rules:
  - type: "null_check"
    name: "campos_obligatorios"
    columns: ["city", "temperature"]
    enabled: true

  - type: "range"
    name: "temperaturas_validas"
    columns:
      temperature:
        min: -60
        max: 65
      humidity:
        min: 0
        max: 100
    enabled: true

on_failure: "log_and_stop"
```

Luego usarla:
```python
from data_quality_framework import ConfigLoader

config = ConfigLoader.load_yaml("config/mi_dataset_validation.yaml")
print(config)
```

---

## 🧪 Tipos de Validadores Disponibles

| Validador | Uso | Ejemplo |
|-----------|-----|---------|
| **NullCheckValidator** | Verificar campos obligatorios | `NullCheckValidator("nulls", ["city", "temperature"])` |
| **RangeValidator** | Valores dentro de rangos | `RangeValidator("ranges", {"temp": {"min": -60, "max": 65}})` |
| **UniquenessValidator** | Claves únicas | `UniquenessValidator("unique", ["city", "date"])` |
| **SchemaValidator** | Tipos de datos | `SchemaValidator("schema", {"id": "int64", "city": "string"})` |
| **FreshnessValidator** | Datos recientes | `FreshnessValidator("fresh", "timestamp", max_age_hours=1)` |
| **CustomValidator** | Lógica personalizada | `CustomValidator("custom", lambda df: custom_logic(df))` |

---

## 🔍 Debuguear Errores

Si hay errores, mira el resultado detallado:

```python
result = orchestrator.run_checks(df, validators, ...)

# Ver detalles
print(f"Pasó: {result.passed}")
print(f"Validadores ejecutados: {result.validators_run}")
print(f"Validadores fallidos: {result.failed_validators}")
print(f"Errores: {result.errors}")

# Ver reporte completo
report = orchestrator.generate_report()
print(report)
```

---

## 📚 Archivos Importantes

| Archivo | Propósito |
|---------|-----------|
| [README.md](README.md) | Documentación completa |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Arquitectura del sistema |
| [docs/INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) | Cómo integrar con Airflow |
| [examples/openweather_examples.py](examples/openweather_examples.py) | Ejemplos de validadores |
| [examples/lakehouse_integration_example.py](examples/lakehouse_integration_example.py) | ETL completo |
| [src/data_quality_framework/validators.py](src/data_quality_framework/validators.py) | Código de validadores |

---

## ✅ Checklist de Ejecución

- [ ] `source venv/bin/activate` - Ambiente activado
- [ ] `pytest tests/ -v` - 21 tests pasando
- [ ] `python examples/openweather_examples.py` - Ejemplos funcionando
- [ ] `python examples/lakehouse_integration_example.py` - ETL completo
- [ ] Tu archivo JSON copiado a `/data/` o raíz
- [ ] Tu script `test_your_data.py` creado
- [ ] Tu script ejecutando exitosamente

---

## 🆘 Problemas Comunes

### "ModuleNotFoundError: No module named 'data_quality_framework'"
```bash
pip install -e .
```

### "Validator failed: Column not found"
Asegúrate que el nombre de columna existe (case-sensitive):
```python
# Verificar columnas disponibles
print(df.columns.tolist())
```

### "Tests failing after changes"
```bash
pytest tests/ -v --tb=short
```

---

¡Listo! Ahora estás listos para ejecutar todo. 🚀
