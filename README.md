# The Box — Análisis de Conversión (TFIE 26-2)

## Entregables

| Archivo | Descripción |
|---|---|
| `analisis_the_box.ipynb` | Notebook Python con 12 bloques (35 celdas, ejecutado completo) |
| `conclusiones_the_box.md` | Informe generado automáticamente desde los resultados calculados |
| `outputs/figuras/` | 13 gráficos exportados |
| `outputs/tablas/` | 18 tablas CSV con resultados |
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

```bash
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.timeout=600 analisis_the_box.ipynb
```

O abrir en VS Code/Jupyter y ejecutar `Kernel → Restart & Run All`.

El notebook usa rutas relativas (`Path().resolve()`) y guarda figuras en `outputs/figuras/` y tablas en `outputs/tablas/`.

## Notas de replicación

- Todos los valores se calculan desde el Excel; los comentados en `the_box_analisis.R` son referencias para contrastar, **no resultados verificados de ejecución**.
- **Semana 35 excluida:** solo cubre 2026-08-24 (1 día, flujo=156).
- **Discrepancia pendiente de verificación:** crecimiento de venta total (Python +102.6% vs R comentario +94.1%) y tiendas comunes (+85.2% vs +75.9%). La diferencia en total se explica en parte por el distinto mix de tiendas (14 en 2025 vs 16 en 2026); la diferencia en comunes requiere ejecutar R para resolver.
- **Interpretación corregida:** no se detecta asociación lineal entre conversión y cumplimiento de metas (r≈0, p=0.96).
- Modelos de efectos fijos: `linearmodels.PanelOLS` (Python) vs `fixest` (R). Diferencia de p-valor en M2 (0.048 vs 0.056) se debe a distinta corrección de grados de libertad en varianza agrupada.
