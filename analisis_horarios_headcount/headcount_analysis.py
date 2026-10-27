from __future__ import annotations

import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SCHEDULE_XLSX = ROOT / 'Horarios_Headcount S34-S38.xlsx'
OUT_DIR = Path(__file__).resolve().parent / 'outputs'
TABLAS_DIR = OUT_DIR / 'tablas'
FIG_DIR = OUT_DIR / 'figuras'


def safe_read(sheet):
    return pd.read_excel(SCHEDULE_XLSX, sheet_name=sheet)


def parse_schedule():
    df = safe_read('BD')
    df = df.copy()
    df['Cuenta'] = df['Cuenta'].astype(str).str.strip()
    df['Tienda'] = df['Tienda'].astype(str).str.strip()
    df['Fecha'] = pd.to_datetime(df['Fecha'], errors='coerce')
    df['Semana ISO'] = pd.to_numeric(df['Semana ISO'], errors='coerce')
    df['Horas'] = pd.to_numeric(df['Horas'], errors='coerce')
    df['Ingreso'] = pd.to_datetime(df['Ingreso'], format='mixed', errors='coerce')
    df['Salida'] = pd.to_datetime(df['Salida'], format='mixed', errors='coerce')
    df['Turno largo'] = df['Horas'] >= 11
    return df


def compute_exclusions(df):
    total = len(df)
    included = df['Cuenta'].eq('Si').sum()
    excluded = total - included
    reason_counts = df.loc[df['Cuenta'].eq('No'), 'Motivo de exclusion'].value_counts(dropna=False)
    excl_df = reason_counts.reset_index()
    excl_df.columns = ['Motivo de exclusion', 'Registros']
    return total, included, excluded, excl_df


def compute_summary(df):
    included = df[df['Cuenta'].eq('Si')].copy()
    daily = included.groupby(['Tienda', 'Semana ISO', 'Fecha'], as_index=False)['Colaborador'].nunique()
    daily = daily.rename(columns={'Colaborador': 'personas_dia'})

    weekly = included.groupby(['Tienda', 'Semana ISO'], as_index=False).agg(
        personas_distintas=('Colaborador', 'nunique'),
        horas_programadas=('Horas', 'sum'),
        turnos=('Colaborador', 'size'),
        turno_promedio_horas=('Horas', 'mean'),
        proporcion_turnos_11mas=('Horas', lambda s: (s >= 11).mean()),
    )

    daily_agg = daily.groupby(['Tienda', 'Semana ISO'], as_index=False)['personas_dia'].agg(
        personas_dia_promedio='mean',
        suma_personas_dia='sum',
        max_personas_dia='max',
    )

    weekly = weekly.merge(daily_agg, on=['Tienda', 'Semana ISO'], how='left')
    weekly['categoria'] = weekly['Tienda'].str.startswith('TB').map({True: 'The Box', False: 'Coolbrands'})
    return included, daily, weekly


def save_csv(df, name):
    path = TABLAS_DIR / name
    df.to_csv(path, index=False)
    return path


def plot_long_turn_share(weekly):
    plot_df = weekly.groupby('Semana ISO')['proporcion_turnos_11mas'].mean().reset_index()
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(plot_df['Semana ISO'], plot_df['proporcion_turnos_11mas'], marker='o', linewidth=2)
    ax.set_title('Participación de turnos de 11+ horas por semana')
    ax.set_xlabel('Semana ISO')
    ax.set_ylabel('Proporción de turnos')
    ax.set_ylim(0, 0.5)
    ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'turnos_11mas_por_semana.png', dpi=200)
    plt.close(fig)


def plot_weekly_people(weekly):
    tb = weekly[weekly['categoria'] == 'The Box'].groupby('Semana ISO', as_index=False)['personas_dia_promedio'].mean()
    cb = weekly[weekly['categoria'] == 'Coolbrands'].groupby('Semana ISO', as_index=False)['personas_dia_promedio'].mean()
    merged = tb.merge(cb, on='Semana ISO', how='outer', suffixes=('_TB', '_CB'))
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(merged['Semana ISO'], merged['personas_dia_promedio_TB'], marker='o', label='The Box')
    ax.plot(merged['Semana ISO'], merged['personas_dia_promedio_CB'], marker='s', label='Coolbrands')
    ax.set_title('Promedio diario de personas programadas por semana')
    ax.set_xlabel('Semana ISO')
    ax.set_ylabel('Personas/día promedio')
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'personas_dia_por_semana.png', dpi=200)
    plt.close(fig)


def plot_heatmap_store_week(weekly):
    pivot = weekly.pivot(index='Tienda', columns='Semana ISO', values='personas_dia_promedio')
    tb = pivot[pivot.index.str.startswith('TB')]
    fig, ax = plt.subplots(figsize=(9, 12))
    im = ax.imshow(tb, aspect='auto', cmap='YlOrRd')
    ax.set_xticks(range(tb.shape[1]))
    ax.set_xticklabels(tb.columns.tolist())
    ax.set_yticks(range(tb.shape[0]))
    ax.set_yticklabels(tb.index.tolist())
    ax.set_title('Promedio diario de personas programadas por tienda y semana (The Box)')
    ax.set_xlabel('Semana ISO')
    ax.set_ylabel('Tienda')
    for i in range(tb.shape[0]):
        for j in range(tb.shape[1]):
            ax.text(j, i, f'{tb.iloc[i, j]:.1f}', ha='center', va='center', color='black', fontsize=7)
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.02)
    fig.tight_layout()
    fig.savefig(FIG_DIR / 'heatmap_personas_tienda_semana.png', dpi=200)
    plt.close(fig)


def make_report(summary_stats, exclusions, weekly, daily, included):
    tb = weekly[weekly['categoria'] == 'The Box'].copy()
    cb = weekly[weekly['categoria'] == 'Coolbrands'].copy()
    tb_by_week = tb.groupby('Semana ISO').agg(
        personas_distintas=('personas_distintas', 'mean'),
        personas_dia_promedio=('personas_dia_promedio', 'mean'),
        horas_programadas=('horas_programadas', 'sum'),
        turno_promedio_horas=('turno_promedio_horas', 'mean'),
        proporcion_turnos_11mas=('proporcion_turnos_11mas', 'mean'),
    )
    cb_by_week = cb.groupby('Semana ISO').agg(
        personas_distintas=('personas_distintas', 'mean'),
        personas_dia_promedio=('personas_dia_promedio', 'mean'),
        horas_programadas=('horas_programadas', 'sum'),
        turno_promedio_horas=('turno_promedio_horas', 'mean'),
        proporcion_turnos_11mas=('proporcion_turnos_11mas', 'mean'),
    )

    lines = []
    lines.append('# Análisis de horarios y headcount — The Box y Coolbrands')
    lines.append('')
    lines.append('## Fuentes y alcance')
    lines.append('- Archivo base: `Horarios_Headcount S34-S38.xlsx`')
    lines.append('- Periodo confirmado: semanas ISO 34 a 38 de 2026 (2026-08-17 a 2026-09-20).')
    lines.append('- Unidad de observación: cada turno programado en la hoja `BD`; cada fila representa una persona en una tienda, un día y un turno planificado.')
    lines.append('- El campo `Cuenta` indica si la fila suma al head count. El archivo ya está filtrado a `Cuenta = Si` para la vista principal.')
    lines.append('- Según `Notas`, la base representa horario planificado, no asistencia efectiva; se excluyen descansos, vacaciones, baja médica, ausencias y `TM` por inventario nocturno.')
    lines.append('')
    lines.append('## Calidad de datos y exclusiones')
    lines.append(f'- Registros totales: {summary_stats["total_rows"]}.')
    lines.append(f'- Registros incluidos (`Cuenta = Si`): {summary_stats["included_rows"]}.')
    lines.append(f'- Registros excluidos: {summary_stats["excluded_rows"]}.')
    for _, row in exclusions.iterrows():
        lines.append(f'- {row["Motivo de exclusion"]}: {int(row["Registros"])} filas.')
    lines.append('')
    lines.append('## Estadísticas clave del horario programado')
    lines.append(f'- Personas distintas incluidas: {included["Colaborador"].nunique()} en 5 semanas.')
    lines.append(f'- Turnos con duración >=11 horas: {((included["Horas"] >= 11).mean()*100):.1f}% del total de turnos.')
    lines.append(f'- Horas programadas totales en la muestra: {included["Horas"].sum():,.0f} horas-persona.')
    lines.append(f'- La proporción de turnos largos sube de {((included.loc[included["Semana ISO"].eq(34), "Horas"] >= 11).mean()*100):.1f}% en semana 34 a {((included.loc[included["Semana ISO"].eq(38), "Horas"] >= 11).mean()*100):.1f}% en semana 38.')
    lines.append('')
    lines.append('## Hallazgos relevantes')
    lines.append('- El patrón dominante no es asistencia efectiva ni ventas; es cobertura programada, sin medición directa de presencia real.')
    lines.append('- Las horas antes de las 09:30 se interpretan como apertura/despacho, no atención al público, según `Notas`.')
    lines.append('- Los 28 casos de dobles registros quedaron resueltos con evidencia de ventas o continuidad, por lo que no se imputan de manera automática en la base principal.')
    lines.append('- The Box tiene una estructura de turnos más larga a partir de la semana 36, con una expansión visible en la proporción de turnos de 11+ horas.')
    lines.append('')
    lines.append('## Sugerencia para el paper')
    lines.append('- Usar este análisis como evidencia descriptiva de la programación: la dotación se ajusta por semana, pero la base no permite atribuir causalidad ni déficit de personal sin un cruce con tráfico y una medición de asistencia efectiva.')
    lines.append('- Para la redacción, evitar afirmar que ”la empresa nunca ajusta su programación” o que ”hay déficit de personal” solo por el número programado; lo defensible es que la cobertura varía por tienda y franja y que la proporción de turnos largos cambia de manera sostenida.')
    lines.append('')
    lines.append('## Archivos generados')
    lines.append('- `headcount_analysis.py`')
    lines.append('- `outputs/tablas/headcount_summary.csv`')
    lines.append('- `outputs/tablas/store_week_headcount.csv`')
    lines.append('- `outputs/figuras/turnos_11mas_por_semana.png`')
    lines.append('- `outputs/figuras/personas_dia_por_semana.png`')
    lines.append('- `outputs/figuras/heatmap_personas_tienda_semana.png`')
    lines.append('')
    lines.append('## Reproducibilidad')
    lines.append('```bash')
    lines.append('python analisis_horarios_headcount/headcount_analysis.py')
    lines.append('```')
    lines.append('')
    return '\n'.join(lines)


def main():
    os.makedirs(TABLAS_DIR, exist_ok=True)
    os.makedirs(FIG_DIR, exist_ok=True)

    df = parse_schedule()
    total_rows, included_rows, excluded_rows, exclusions = compute_exclusions(df)
    included, daily, weekly = compute_summary(df)

    summary_stats = {
        'total_rows': total_rows,
        'included_rows': included_rows,
        'excluded_rows': excluded_rows,
        'weeks': sorted(df['Semana ISO'].dropna().unique().tolist()),
        'distinct_people': included['Colaborador'].nunique(),
        'long_turn_share': float((included['Horas'] >= 11).mean()),
        'hours_programmed_total': float(included['Horas'].sum()),
    }

    save_csv(exclusions, 'exclusions_by_reason.csv')
    save_csv(weekly, 'store_week_headcount.csv')
    save_csv(daily, 'daily_headcount_by_store_week.csv')
    save_csv(included[['Tienda', 'Semana ISO', 'Fecha', 'Colaborador', 'Horas', 'Tipo de turno', 'Tipo RMS', 'Ingreso', 'Salida']].copy(), 'included_schedule_rows.csv')

    plot_long_turn_share(weekly)
    plot_weekly_people(weekly)
    plot_heatmap_store_week(weekly)

    report = make_report(summary_stats, exclusions, weekly, daily, included)
    (Path(__file__).resolve().parent / 'headcount_analysis_report.md').write_text(report, encoding='utf-8')

    # Extra compact summary for easy table access
    total_weekly = included.groupby('Semana ISO').agg(
        registros=('Fecha', 'size'),
        personas_distintas=('Colaborador', 'nunique'),
        horas_programadas=('Horas', 'sum'),
        turnos_largos=('Horas', lambda s: int((s >= 11).sum())),
        share_turnos_largos=('Horas', lambda s: float((s >= 11).mean())),
    ).reset_index()
    save_csv(total_weekly, 'weekly_headcount_summary.csv')

    print('Processed rows:', total_rows)
    print('Included rows:', included_rows)
    print('Distinct collaborators:', summary_stats['distinct_people'])
    print('Share long turns:', round(summary_stats['long_turn_share'] * 100, 1), '%')
    print('Report saved to', Path(__file__).resolve().parent / 'headcount_analysis_report.md')


if __name__ == '__main__':
    main()
