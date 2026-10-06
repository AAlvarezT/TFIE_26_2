# The Box — Análisis de Conversión (TFIE 26-2)

## Entregables

| Archivo | Descripción |
|---|---|
| `analisis_the_box.ipynb` | Notebook principal con 11 bloques de análisis |
| `conclusiones_the_box.md` | Informe autocontenido con metodología, resultados y limitaciones |
| `outputs/figuras/` | 13 gráficos exportados |
| `outputs/tablas/` | 8 tablas CSV con resultados |
| `the_box_analisis.R` | Script R original de referencia (no modificar) |
| `BD The Box Presentacion 30.08.xlsx` | Fuente de datos única (no modificar) |

## Requisitos

```
pandas>=2.0
numpy>=1.24
matplotlib>=3.7
seaborn>=0.12
openpyxl>=3.1
scipy>=1.10
statsmodels>=0.14
linearmodels>=6.0
```

Instalar con:

```bash
pip install -r requirements.txt
```

## Ejecutar el notebook

Abrir `analisis_the_box.ipynb` en VS Code o Jupyter y ejecutar todas las celdas en orden desde un kernel limpio (`Kernel → Restart & Run All`).

El notebook guarda automáticamente las figuras en `outputs/figuras/` y las tablas en `outputs/tablas/`.

## Notas de replicación

- Todos los valores se calculan directamente desde el Excel; los comentados en `the_box_analisis.R` son referencias para contrastar.
- La discrepancia en crecimiento de venta total (+102.6% Python vs +94.1% R) es metodológicamente esperada: 2026 tiene 2 tiendas nuevas. Ver `outputs/tablas/verificacion_vs_r.csv` para el detalle completo.
- Los modelos de efectos fijos usan `linearmodels.PanelOLS` (Python) en lugar de `fixest` (R); los resultados son prácticamente idénticos.
