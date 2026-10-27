# Metodología y calidad

## Fuentes y reproducibilidad
- Horarios: `Horarios_Headcount S34-S38.xlsx` (`BD`, `Por hora`, `Notas`).
- Comercial y encuesta: `BD The Box Presentacion 30.08.xlsx` (`BD Venta por hora`, `BD NPS`).
- Script: `analisis_horarios_headcount/prism_package_builder.py`.
- Comando de reproducción:

```bash
python analisis_horarios_headcount/prism_package_builder.py
```

## Criterios de limpieza y reconstrucción
1. Inclusión principal: `Cuenta = Si`.
2. Reconstrucción horaria por solapamiento semiabierto:
   - turno: `[ingreso, salida)`;
   - franja: `[hora, hora + 1)`;
   - métricas por franja: `personas_solapan_hora` y `horas_persona_programadas`.
3. Cruce de medianoche:
   - si `salida <= ingreso`, se suma 1 día a `salida`;
   - se asigna cada franja a su fecha real de calendario.
4. Registros dudosos:
   - hora inválida o duración no positiva / >16h se marcan como no aptos para reconstrucción;
   - se documentan en tabla de auditoría.

## Validación de límites de entrada/salida (pruebas)
- Casos probados: 10:00-19:00 (excluye 19:00), 09:30-18:30 (incluye parcial 09:00 y 18:00), 23:00-05:00 (cruza medianoche).
- Resultado: ok, ok, ok.

## Comparación con hoja "Por hora"
- Filas comparadas: 10640.
- Filas con diferencia: 0.
- Diferencia media absoluta: 0.000.
- Diferencia máxima absoluta: 0.000.
- Las discrepancias se reportan para revisión; no se ocultan ni se fuerzan a cero.

## Límites del cruce comercial
- Ventana de análisis: 2026-08-17 a 2026-08-23 (semana ISO 34 de 2026).
- Claves de cruce: `Tienda`, `Fecha`, `Hora`.
- Estados de emparejamiento: coincidencia encontrada, registro horario ausente, registro dudoso no emparejado, cero confirmado.
- Se reportan anomalías (`flujo=0`, `transacciones>flujo`) y se evita interpretación causal.

## Encuesta: selección de columnas y anonimización
- Se seleccionan explícitamente las columnas sustantivas, excluyendo prefijos `Puntos:` y `Comentarios:`.
- No se exportan nombres, correos ni textos completos de comentarios.
- Se publica solo agregado por tema y valoración textual.

## Tablas/figuras utilizables en Prism
- `turnos_largos_por_semana_the_box.csv`
- `turnos_largos_por_semana_cadena_19_tiendas.csv`
- `auditoria_cruce_horarios_ventas.csv`
- `resultados_cruce_s34_detallado.csv`
- `encuesta_calificacion_atencion.csv`
- `encuesta_temas_comentarios.csv`
- `auditoria_reconstruccion_por_hora.csv`
- `discrepancias_muestra_vs_por_hora.csv`
- `turnos_largos_the_box.png`
- `dotacion_por_hora_tbrbsb_s34.png`
