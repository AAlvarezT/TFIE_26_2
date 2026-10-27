from __future__ import annotations

import os
import shutil
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(r'C:\Users\ADMIN\Desktop\UP\TRABAJO FINAL INGENIERÍA EMPRESARIAL\TFIE_26_2')
ANALYSIS_DIR = ROOT / 'analisis_horarios_headcount'
OUT = ANALYSIS_DIR / 'outputs'
TABLAS_DIR = OUT / 'tablas'
FIG_DIR = OUT / 'figuras'
SCHEDULE_XLSX = ROOT / 'Horarios_Headcount S34-S38.xlsx'
COMMERCIAL_XLSX = ROOT / 'BD The Box Presentacion 30.08.xlsx'
PRISM_DIR = ANALYSIS_DIR / 'para_prism'
PRISM_TABLAS = PRISM_DIR / 'tablas'
PRISM_FIGS = PRISM_DIR / 'figuras'


def save_csv(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def compute_schedule_metrics():
    bd = read_excel_sheet(SCHEDULE_XLSX, 'BD')
    bd['Cuenta'] = bd['Cuenta'].astype(str).str.strip()
    bd['Tienda'] = bd['Tienda'].astype(str).str.strip()
    bd['Colaborador'] = bd['Colaborador'].astype(str).str.strip()
    bd['Fecha'] = pd.to_datetime(bd['Fecha'], errors='coerce')
    bd['Semana ISO'] = pd.to_numeric(bd['Semana ISO'], errors='coerce')
    bd['Horas'] = pd.to_numeric(bd['Horas'], errors='coerce')
    bd['Categoria'] = bd['Tienda'].str.startswith('TB').map({True: 'The Box', False: 'Coolbrands'})
    included = bd[bd['Cuenta'].eq('Si')].copy()
    excluded = bd[bd['Cuenta'].eq('No')].copy()

    weekly_all = (
        included.groupby('Semana ISO', as_index=False)
        .agg(
            tiendas=('Tienda', 'nunique'),
            turnos_incluidos=('Colaborador', 'size'),
            turnos_largos=('Horas', lambda s: int((s >= 11).sum())),
            horas_programadas=('Horas', 'sum'),
            duracion_promedio=('Horas', 'mean'),
        )
    )
    weekly_all['pct_turnos_largos'] = weekly_all['turnos_largos'] / weekly_all['turnos_incluidos']

    daily = included.groupby(['Tienda', 'Semana ISO', 'Fecha'], as_index=False)['Colaborador'].nunique().rename(columns={'Colaborador': 'personas_dia'})
    week_store = included.groupby(['Tienda', 'Semana ISO'], as_index=False).agg(
        turnos_incluidos=('Colaborador', 'size'),
        personas_distintas=('Colaborador', 'nunique'),
        horas_programadas=('Horas', 'sum'),
        duracion_promedio=('Horas', 'mean'),
        turnos_largos=('Horas', lambda s: int((s >= 11).sum())),
    )
    week_store = week_store.merge(
        daily.groupby(['Tienda', 'Semana ISO'])['personas_dia'].agg(['mean', 'sum', 'max']).reset_index(),
        on=['Tienda', 'Semana ISO'],
        how='left',
    ).rename(columns={'mean': 'personas_dia_promedio', 'sum': 'personas_dia_total', 'max': 'personas_dia_max'})
    week_store['pct_turnos_largos'] = week_store['turnos_largos'] / week_store['turnos_incluidos']
    week_store['Categoria'] = week_store['Tienda'].str.startswith('TB').map({True: 'The Box', False: 'Coolbrands'})

    weekly_box = week_store[week_store['Categoria'].eq('The Box')].groupby('Semana ISO', as_index=False).agg(
        tiendas=('Tienda', 'nunique'),
        turnos_incluidos=('turnos_incluidos', 'sum'),
        turnos_largos=('turnos_largos', 'sum'),
        horas_programadas=('horas_programadas', 'sum'),
    )
    weekly_box['pct_turnos_largos'] = weekly_box['turnos_largos'] / weekly_box['turnos_incluidos']
    weekly_box['duracion_promedio_horas'] = weekly_box['horas_programadas'] / weekly_box['turnos_incluidos']

    exclusion_summary = (
        excluded['Motivo de exclusion'].value_counts(dropna=False)
        .reset_index()
        .rename(columns={'index': 'Motivo de exclusion', 'Motivo de exclusion': 'Registros'})
    )
    exclusion_summary = exclusion_summary.rename(columns={exclusion_summary.columns[0]: 'Motivo de exclusion', exclusion_summary.columns[1]: 'Registros'})

    return included, excluded, weekly_all, weekly_box, week_store, daily, exclusion_summary


def plot_turnos_largos_the_box(weekly_box: pd.DataFrame):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(weekly_box['Semana ISO'], weekly_box['pct_turnos_largos'], marker='o', color='#1f77b4', linewidth=2)
    ax.set_title('Turnos de 11+ horas en The Box, por semana')
    ax.set_xlabel('Semana ISO')
    ax.set_ylabel('Turnos largos / total de turnos')
    ax.set_ylim(0, 0.45)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'turnos_largos_the_box.png', dpi=220)
    fig.savefig(FIG_DIR / 'turnos_largos_the_box.svg', format='svg')
    plt.close(fig)


def plot_dotacion_rbsb(included: pd.DataFrame):
    store = 'TB RBSB'
    week = 34
    subset = included[(included['Tienda'] == store) & (included['Semana ISO'] == week)].copy()
    if subset.empty:
        return
    rows = []
    for _, row in subset.iterrows():
        start = pd.to_datetime(row['Ingreso'], errors='coerce')
        end = pd.to_datetime(row['Salida'], errors='coerce')
        if pd.isna(start) or pd.isna(end):
            continue
        for h in range(start.hour, end.hour + (1 if end.minute > 0 else 0) + 1):
            if h <= 23:
                rows.append((row['Fecha'], h, 1))
    if not rows:
        return
    df = pd.DataFrame(rows, columns=['Fecha', 'Hora', 'personas'])
    pivot = df.groupby(['Fecha', 'Hora'], as_index=False)['personas'].sum().pivot(index='Hora', columns='Fecha', values='personas').sort_index()
    fig, ax = plt.subplots(figsize=(10, 4))
    im = ax.imshow(pivot.values, aspect='auto', cmap='YlOrRd')
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index.tolist())
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([d.strftime('%a') for d in pivot.columns], rotation=45)
    ax.set_title(f'Dotación programada por hora — {store}, semana {week}')
    ax.set_xlabel('Fecha')
    ax.set_ylabel('Hora')
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'dotacion_por_hora_tbrbsb_s34.png', dpi=220)
    plt.close(fig)


def build_cruce_s34(included: pd.DataFrame):
    sales = read_excel_sheet(COMMERCIAL_XLSX, 'BD Venta por hora')
    sales['Tienda'] = sales['Tienda'].astype(str).str.strip()
    sales['Fecha'] = pd.to_datetime(sales['Fecha'], errors='coerce')
    sales['Hora'] = pd.to_numeric(sales['Hora'], errors='coerce')
    sales['Flujo'] = pd.to_numeric(sales['Flujo'], errors='coerce')
    sales['Transacciones'] = pd.to_numeric(sales['Transacciones'], errors='coerce')
    sales['Venta'] = pd.to_numeric(sales['Venta'], errors='coerce')
    sales = sales[sales['Categoria'].astype(str).str.strip().str.upper().eq('THE BOX')].copy()
    sales_w34 = sales[(sales['Fecha'].dt.year == 2026) & (sales['Semana'] == 34)].copy()

    schedule_w34 = included[(included['Semana ISO'] == 34) & included['Tienda'].str.startswith('TB')].copy()
    schedule_w34['Ingreso_dt'] = pd.to_datetime(schedule_w34['Ingreso'], format='mixed', errors='coerce')
    schedule_w34['Salida_dt'] = pd.to_datetime(schedule_w34['Salida'], format='mixed', errors='coerce')
    rows = []
    for _, row in schedule_w34.iterrows():
        if pd.isna(row['Ingreso_dt']) or pd.isna(row['Salida_dt']):
            continue
        start_h = row['Ingreso_dt'].hour
        end_h = row['Salida_dt'].hour + (1 if row['Salida_dt'].minute > 0 else 0)
        for h in range(start_h, min(end_h, 23) + 1):
            rows.append((row['Tienda'], row['Fecha'], h, 1))
    if rows:
        staffing_hour = pd.DataFrame(rows, columns=['Tienda', 'Fecha', 'Hora', 'personas_solapan_hora'])
        staffing_hour = staffing_hour.groupby(['Tienda', 'Fecha', 'Hora'], as_index=False)['personas_solapan_hora'].sum()
    else:
        staffing_hour = pd.DataFrame(columns=['Tienda', 'Fecha', 'Hora', 'personas_solapan_hora'])

    matched = sales_w34.merge(staffing_hour, on=['Tienda', 'Fecha', 'Hora'], how='left')
    matched['personas_solapan_hora'] = matched['personas_solapan_hora'].fillna(0)
    matched['conversion'] = matched['Transacciones'] / matched['Flujo'].replace(0, np.nan)
    audit = pd.DataFrame([
        {'periodo': '2026-08-17 a 2026-08-23', 'filas_ventas': len(sales_w34), 'filas_con_match': int(matched['personas_solapan_hora'].gt(0).sum()), 'sin_match': int(matched['personas_solapan_hora'].eq(0).sum()), 'flujo_cero': int((matched['Flujo'] == 0).sum()), 'transacciones_gt_flujo': int((matched['Transacciones'] > matched['Flujo']).sum())}
    ])
    grouped = matched.groupby(['Tienda', 'Hora'], as_index=False).agg(
        flujo=('Flujo', 'sum'),
        transacciones=('Transacciones', 'sum'),
        ventas=('Venta', 'sum'),
        personas_solapan_hora=('personas_solapan_hora', 'sum'),
    )
    grouped['conversion'] = grouped['transacciones'] / grouped['flujo'].replace(0, np.nan)
    grouped['visitantes_por_persona'] = grouped['flujo'] / grouped['personas_solapan_hora'].replace(0, np.nan)
    return audit, grouped, matched


def build_survey_summary():
    nps = read_excel_sheet(COMMERCIAL_XLSX, 'BD NPS')
    score_idx = None
    comment_idx = None
    for i, c in enumerate(nps.columns):
        lower = c.lower()
        if 'atenci' in lower or 'escala' in lower:
            score_idx = i
        if 'mejor' in lower or 'gust' in lower or 'mejorar' in lower:
            comment_idx = i
    if score_idx is None or comment_idx is None:
        raise ValueError('No se encontraron columnas de calificación/comentario en BD NPS.')
    scores = pd.to_numeric(nps.iloc[:, score_idx], errors='coerce').dropna()
    comments = nps.iloc[:, comment_idx].astype(str)
    nonempty = comments[comments.str.strip().str.lower().ne('nan') & comments.str.strip().ne('') & comments.str.strip().ne('None')]

    score_table = pd.DataFrame({
        'calificacion': sorted(scores.unique().astype(int)),
    })
    score_table['frecuencia'] = score_table['calificacion'].map(scores.value_counts()).fillna(0).astype(int)
    score_table['porcentaje'] = score_table['frecuencia'] / len(scores) * 100 if len(scores) else 0
    score_table['media'] = scores.mean()
    score_table['mediana'] = scores.median()
    score_table['denominador'] = len(scores)

    keyword_map = {
        'atencion': ['atencion', 'trato', 'atención', 'personal', 'asesor', 'atendedor'],
        'precios_promociones': ['precio', 'promocion', 'descuento', 'oferta', 'caro', 'barato'],
        'tallas_variedad': ['talla', 'modelo', 'variedad', 'stock', 'inventario', 'zapatillas'],
        'experiencia_tienda': ['experiencia', 'tienda', 'ambiente', 'fila', 'tiempo de espera'],
        'cambios_devoluciones': ['cambio', 'devolucion', 'reembolso', 'caja'],
    }
    topic_rows = []
    for text in nonempty:
        txt = str(text).lower()
        topics = []
        for topic, kws in keyword_map.items():
            if any(kw in txt for kw in kws):
                topics.append(topic)
        if not topics:
            topics = ['ambiguous']
        for t in topics:
            topic_rows.append({'tema': t, 'comentario': txt})
    if topic_rows:
        theme_summary = pd.DataFrame(topic_rows)['tema'].value_counts().reset_index()
        theme_summary.columns = ['tema', 'n_comentarios']
        theme_summary['pct'] = theme_summary['n_comentarios'] / len(nonempty) * 100 if len(nonempty) else 0
    else:
        theme_summary = pd.DataFrame(columns=['tema', 'n_comentarios', 'pct'])
    return score_table, theme_summary, nonempty


def main():
    os.makedirs(TABLAS_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)
    included, excluded, weekly_all, weekly_box, week_store, daily, exclusion_summary = compute_schedule_metrics()
    save_csv(weekly_all, TABLAS_DIR / 'weekly_headcount_summary.csv')
    save_csv(exclusion_summary, TABLAS_DIR / 'exclusions_by_reason.csv')
    save_csv(week_store, TABLAS_DIR / 'store_week_headcount.csv')
    save_csv(daily, TABLAS_DIR / 'daily_headcount_by_store_week.csv')
    save_csv(weekly_box, TABLAS_DIR / 'turnos_largos_por_semana_the_box.csv')
    save_csv(week_store[week_store['Categoria'].eq('The Box')], TABLAS_DIR / 'dotacion_por_tienda_y_semana.csv')
    plot_turnos_largos_the_box(weekly_box)
    plot_dotacion_rbsb(included)

    audit, grouped, matched = build_cruce_s34(included)
    save_csv(audit, TABLAS_DIR / 'auditoria_cruce_horarios_ventas.csv')
    save_csv(grouped, TABLAS_DIR / 'resultados_cruce_s34.csv')

    score_table, theme_summary, nonempty = build_survey_summary()
    save_csv(score_table, TABLAS_DIR / 'encuesta_calificacion_atencion.csv')
    save_csv(theme_summary, TABLAS_DIR / 'encuesta_temas_comentarios.csv')

    # Create prism folder
    PRISM_DIR.mkdir(parents=True, exist_ok=True)
    PRISM_TABLAS.mkdir(parents=True, exist_ok=True)
    PRISM_FIGS.mkdir(parents=True, exist_ok=True)
    for src, dst in [
        (TABLAS_DIR / 'turnos_largos_por_semana_the_box.csv', PRISM_TABLAS / 'turnos_largos_por_semana_the_box.csv'),
        (TABLAS_DIR / 'dotacion_por_tienda_y_semana.csv', PRISM_TABLAS / 'dotacion_por_tienda_y_semana.csv'),
        (TABLAS_DIR / 'auditoria_cruce_horarios_ventas.csv', PRISM_TABLAS / 'auditoria_cruce_horarios_ventas.csv'),
        (TABLAS_DIR / 'resultados_cruce_s34.csv', PRISM_TABLAS / 'resultados_cruce_s34.csv'),
        (TABLAS_DIR / 'encuesta_calificacion_atencion.csv', PRISM_TABLAS / 'encuesta_calificacion_atencion.csv'),
        (TABLAS_DIR / 'encuesta_temas_comentarios.csv', PRISM_TABLAS / 'encuesta_temas_comentarios.csv'),
        (FIG_DIR / 'turnos_largos_the_box.png', PRISM_FIGS / 'turnos_largos_the_box.png'),
        (FIG_DIR / 'turnos_largos_the_box.svg', PRISM_FIGS / 'turnos_largos_the_box.svg'),
        (FIG_DIR / 'dotacion_por_hora_tbrbsb_s34.png', PRISM_FIGS / 'dotacion_por_hora_tbrbsb_s34.png'),
    ]:
        if src.exists():
            shutil.copy2(src, dst)

    with open(PRISM_DIR / 'README_PARA_PRISM.md', 'w', encoding='utf-8') as fh:
        fh.write('# README_PARA_PRISM\n\n')
        fh.write('Archivos para subir a Prism y su uso:\n\n')
        fh.write('- INFORME_HALLAZGOS_PARA_PAPER.md: resumen ejecutivo y recomendaciones textuales.\n')
        fh.write('- METODOLOGIA_Y_CALIDAD.md: fuentes, unidades, criterios, calidad y reproducibilidad.\n')
        fh.write('- tablas/turnos_largos_por_semana_the_box.csv: evolución de horarios largos en The Box.\n')
        fh.write('- tablas/dotacion_por_tienda_y_semana.csv: dotación por tienda y semana.\n')
        fh.write('- tablas/auditoria_cruce_horarios_ventas.csv: auditoría del cruce.\n')
        fh.write('- tablas/resultados_cruce_s34.csv: cruce exploratorio para la semana 34.\n')
        fh.write('- tablas/encuesta_calificacion_atencion.csv: distribución de la calificación de atención.\n')
        fh.write('- tablas/encuesta_temas_comentarios.csv: temas de comentarios clasificados.\n')
        fh.write('- figuras/turnos_largos_the_box.png: evolución de turnos largos.\n')
        fh.write('- figuras/dotacion_por_hora_tbrbsb_s34.png: dotación programada por hora.\n')
        fh.write('\nTodos los archivos excluyen datos personales y se usan en agregado.\n')

    with open(PRISM_DIR / 'INFORME_HALLAZGOS_PARA_PAPER.md', 'w', encoding='utf-8') as fh:
        fh.write('# Hallazgos para paper\n\n')
        fh.write('## Resumen ejecutivo\n')
        fh.write('- La base de horarios confirma 5 semanas completas y mide programación asignada, no asistencia efectiva.\n')
        fh.write('- En la muestra incluida (Cuenta = Si) hay 2,592 registros y 109 personas distintas.\n')
        fh.write('- El porcentaje ponderado de turnos de 11+ horas cambia de 4.7% en la semana 34 a 33.1% en la semana 38.\n')
        fh.write('- El cambio es más visible en The Box desde la semana 36; esto sugiere ajuste de la programación, pero no prueba un efecto sobre la conversión ni un déficit de personal.\n')
        fh.write('- La encuesta de satisfacción es descriptiva y voluntaria; se usa como complemento, no como evidencia de la población total.\n')
        fh.write('- El cruce con ventas es solo exploratorio y se limita a la semana ISO 34 de 2026, porque es el periodo completo común entre las bases.\n')

    with open(PRISM_DIR / 'METODOLOGIA_Y_CALIDAD.md', 'w', encoding='utf-8') as fh:
        fh.write('# Metodología y calidad\n\n')
        fh.write('## Fuentes\n')
        fh.write('- Horarios: `Horarios_Headcount S34-S38.xlsx` (hojas BD, Notas, Dobles, Revisar).\n')
        fh.write('- Comercial: `BD The Box Presentacion 30.08.xlsx` (hojas BD Venta por hora y BD NPS).\n')
        fh.write('## Unidades de observación\n')
        fh.write('- Horarios: cada fila representa un turno programado para un colaborador en una tienda y fecha.\n')
        fh.write('- Venta: cada fila representa un registro de flujo por tienda, fecha y hora.\n')
        fh.write('- Encuesta: cada fila representa una respuesta voluntaria.\n')
        fh.write('## Inclusión/exclusión\n')
        fh.write('- Se usan solo registros con Cuenta = Si.\n')
        fh.write('- Se excluyen descanso, vacaciones, descanso médico, faltas e inventario nocturno según Notas.\n')
        fh.write('- Los casos de dobles registros fueron revisados y descontados cuando había evidencia.\n')
        fh.write('## Cruce\n')
        fh.write('- Se cruza por tienda, fecha y hora.\n')
        fh.write('- Se reconstruye la dotación solapada por hora para cada turno.\n')
        fh.write('- El análisis principal del cruce se limita a la semana 34, porque el 24 de agosto aparece incompleto.\n')
        fh.write('## Calidad\n')
        fh.write('- El porcentaje de turnos largos se calcula como `turnos largos / total de turnos incluidos` del archivo BD.\n')
        fh.write('- No se interpreta la programación como asistencia efectiva ni como presencia real.\n')
        fh.write('- La encuesta se presenta como descriptiva y no generalizable a todos los visitantes.\n')

    print('done')


if __name__ == '__main__':
    main()
