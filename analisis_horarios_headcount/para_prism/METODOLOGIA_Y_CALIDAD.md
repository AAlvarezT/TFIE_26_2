# Metodología y calidad

## Fuentes
- Horarios: `Horarios_Headcount S34-S38.xlsx` (hojas BD, Notas, Dobles, Revisar).
- Comercial: `BD The Box Presentacion 30.08.xlsx` (hojas BD Venta por hora y BD NPS).
## Unidades de observación
- Horarios: cada fila representa un turno programado para un colaborador en una tienda y fecha.
- Venta: cada fila representa un registro de flujo por tienda, fecha y hora.
- Encuesta: cada fila representa una respuesta voluntaria.
## Inclusión/exclusión
- Se usan solo registros con Cuenta = Si.
- Se excluyen descanso, vacaciones, descanso médico, faltas e inventario nocturno según Notas.
- Los casos de dobles registros fueron revisados y descontados cuando había evidencia.
## Cruce
- Se cruza por tienda, fecha y hora.
- Se reconstruye la dotación solapada por hora para cada turno.
- El análisis principal del cruce se limita a la semana 34, porque el 24 de agosto aparece incompleto.
## Calidad
- El porcentaje de turnos largos se calcula como `turnos largos / total de turnos incluidos` del archivo BD.
- No se interpreta la programación como asistencia efectiva ni como presencia real.
- La encuesta se presenta como descriptiva y no generalizable a todos los visitantes.
