# Conclusiones -- The Box (OLA y Montana S.A.C.)
## TFIE 26-2 -- Analisis de Conversion

*Generado automaticamente desde resultados del notebook. Cifras reproducibles ejecutando `analisis_the_box.ipynb` desde kernel limpio.*

---

## Resumen ejecutivo

En las semanas comparables 2-34, la conversion de The Box subio de **5.56%** (2025) a **6.48%** (2026), mejora de 0.92 pp.
La frontera p90 ponderada es **7.7848%**, dejando una brecha de **1.3025 pp**.
Bajo los supuestos del modelo, esto equivale a **S/7.85M** anuales adicionales.

**No se detecta asociacion lineal** entre conversion y cumplimiento de metas (r=-0.015, p=0.9571).

---

## Metodologia y muestras

| Muestra | Definicion |
|---|---|
| `raw` | Todo el Excel THE BOX sin filtro |
| `dep` | hora 10-21, flujo>0, flujo>=trx, semana!=35 |
| `sw26/sw25` | dep + sem 2-34 + f>=100 + t>=10 por tienda-semana |
| `comunes` | 14 tiendas en dep de 2025 Y 2026, sem 2-34 |

Semana 35 excluida: solo cubre 2026-08-24 (1 dia, flujo=156).

---

## Resultados por bloque

### Bloque 2 -- Calidad y depuracion
- Conv. reportada (raw): 2025=6.4680%, 2026=6.8147%
- Conv. depurada (dep, sem 2-34): **2025=5.5610%, 2026=6.4815%**
- Sin duplicados tienda-fecha-hora ni valores negativos.
- Tablas: `outputs/tablas/calidad_datos.csv`, `exclusiones_depuracion.csv`

### Bloque 3 -- Evolucion 2025-2026

| Ano | Tiendas | Venta (S/) | Conv dep sem 2-34 |
|---|---|---|---|
| 2025 | 14 | 10,140,566 | 5.5610% |
| 2026 | 16 | 20,546,688 | 6.4815% |

- Crecimiento total cadena: **+102.6%** (mix distinto: 2026 tiene 2 tiendas nuevas)
- Crecimiento tiendas comunes (14): **+85.2%**
- Descomposicion: flujo 33.8%, conv 21.7%, ticket 44.5% (contable, no causal)
- Discrepancia con comentarios R (94.1% total, 75.9% comunes): **pendiente de verificacion ejecutando R**
- Grafico: `outputs/figuras/evolucion_descomposicion.png`

### Bloque 4 -- Frontera interna

| Percentil | Frontera | Brecha vs conv real |
|---|---|---|
| p75 | 7.1980% | 0.7157 pp |
| p90 | 7.7848% | 1.3025 pp |
| p100 | 8.5843% | 2.1020 pp |

El p90 es desempeno propio observado -- no una meta sostenible garantizada.
- Grafico: `outputs/figuras/frontera_conversion.png`

### Bloque 5 -- Modelos trafico-conversion

| Modelo | n | beta | SE | p |
|---|---|---|---|---|
| Panel hora (FE tienda_hora+fecha) | 38,461 | -0.01585 | 0.00264 | 1.86e-09 |
| Panel semana (FE tienda+periodo)  | 1,214 | -0.04902 | 0.02478 | 0.0482 |

Spearman entre tiendas: r=-0.615. Asociacion observacional -- NO implica causalidad.
Diferencia p-valor M2 (Python 0.0482 vs R 0.056): distinta correccion de GL en varianza agrupada.

### Bloque 6 -- Varianza
- R2 tienda=0.332 | R2 semana=0.080 | R2 ambos=0.420
- SD dentro (0.01200) > SD entre (0.00999)
- La variacion temporal dentro supera la diferencia entre locales. No implica que el residual sea controlable.

### Bloque 7 -- Patrones horarios
- Hora 10: 4.21% vs 6.54% resto del dia (descriptivo, no causal)
- Domingo: mayor flujo (~22%), conversion mas baja (~5.86%)
- Graficos: `outputs/figuras/patron_hora.png`, `patron_dia.png`, `heatmap_hora_dia.png`, `heatmap_tienda_hora.png`

### Bloque 8 -- Sensibilidad a problemas de medicion

San Isidro: cambio abrupto de flujo entre semanas 19-22 (indicio, no confirmacion de falla de contador).

| Escenario | Conv real | p90 | Brecha | Impacto S/M |
|---|---|---|---|---|
| Todas las tiendas | 6.4823% | 7.7848% | 1.3025pp | 7.85 |
| Sin San Isidro | 6.4567% | 7.6323% | 1.1756pp | 6.90 |
| Sin Chimbote | 6.5160% | 7.7700% | 1.2540pp | 7.31 |
| Sin San Isidro ni Chimbote | 6.4905% | 7.6119% | 1.1214pp | 6.36 |

### Bloque 9 -- Metas
- **No se detecta asociacion lineal** entre conversion y cumplimiento: r=-0.015, p=0.9571
- Meta 2026 exige +158.0% sobre venta 2025 (sem 2-34)
- Logro real 2026 vs venta 2025: +89.0%

### Bloque 10 -- Impacto economico
Factor estacional: 1.9009 | Flujo anual: 1,697,953 | Ticket: S/354.90

| Escenario | Brecha | Trx extra | Venta adicional |
|---|---|---|---|
| p75 | 0.7157 pp | 12,153 | S/4.31M |
| p90 | 1.3025 pp | 22,116 | S/7.85M |
| maximo | 2.1020 pp | 35,692 | S/12.67M |

- Grafico: `outputs/figuras/impacto_escenarios.png`

---

## Supuestos del impacto economico
1. Estacionalidad 2026 ~ 2025 (factor=1.9009).
2. Ticket (S/354.90) permanece constante.
3. Frontera p90: desempeno propio historico observado -- no meta garantizada.
4. El flujo total no cambia al mejorar la conversion.
5. Estimaciones referenciales -- **no representan utilidad garantizada**.

---

## Limitaciones
- Correlacion no implica causalidad.
- Los efectos fijos no eliminan todos los factores de confusion.
- El p90 es desempeno observado, no meta externa ni garantia de sostenibilidad.
- Los cambios bruscos de flujo son indicios, no confirmacion de falla de contador.
- La discrepancia en crecimiento de venta vs comentarios del script R queda **pendiente de verificacion**.

---

## Verificacion vs valores esperados del script R

Tabla completa: `outputs/tablas/verificacion_vs_r.csv`

- **Replican exactamente** (diferencia < tolerancia): conv_reportada, frontera p75/p90/max,
  m1_beta, pearson_r, spearman_r, r2_tienda, r2_semana, factor_estacional, ticket.
- **Discrepancia pendiente de verificacion (ejecutar R):**
  crecimiento total (Python +102.6% vs R_ref +94.1%)
  y tiendas comunes (Python +85.2% vs R_ref +75.9%).
  Los valores R son comentarios en el script, no resultados verificados de ejecucion.

---

## Proximos pasos
1. Ejecutar `the_box_analisis.R` para resolver discrepancias de crecimiento interanual.
2. Auditar contadores de San Isidro y Chimbote con el proveedor del sensor.
3. Recopilar datos de dotacion por hora y tienda.
4. Encuesta de tipo de visitante (proposito de visita).
5. Disenar pilotos controlados en tiendas con mayor brecha respecto a su p90.