from __future__ import annotations

import re
import shutil
import unicodedata
from pathlib import Path
from typing import Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ANALYSIS_DIR = Path(__file__).resolve().parent
OUT = ANALYSIS_DIR / "outputs"
TABLAS_DIR = OUT / "tablas"
FIG_DIR = OUT / "figuras"
SCHEDULE_XLSX = ROOT / "Horarios_Headcount S34-S38.xlsx"
COMMERCIAL_XLSX = ROOT / "BD The Box Presentacion 30.08.xlsx"
PRISM_DIR = ANALYSIS_DIR / "para_prism"
PRISM_TABLAS = PRISM_DIR / "tablas"
PRISM_FIGS = PRISM_DIR / "figuras"

SPANISH_DAY_MAP = {
    0: "L",
    1: "M",
    2: "X",
    3: "J",
    4: "V",
    5: "S",
    6: "D",
}


def save_csv(df: pd.DataFrame, path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def read_excel_sheet(path: Path, sheet_name: str) -> pd.DataFrame:
    df = pd.read_excel(path, sheet_name=sheet_name)
    df.columns = [str(c).strip() for c in df.columns]
    return df


def normalize_text(value: str) -> str:
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.strip().lower()


def find_column(df: pd.DataFrame, include: list[str], exclude: list[str] | None = None) -> str:
    exclude = exclude or []
    for col in df.columns:
        ncol = normalize_text(col)
        if all(token in ncol for token in include) and not any(token in ncol for token in exclude):
            return col
    raise ValueError(f"No se encontró columna con include={include}, exclude={exclude}")


def find_exact_column(df: pd.DataFrame, normalized_name: str) -> str:
    for col in df.columns:
        if normalize_text(col) == normalized_name:
            return col
    raise ValueError(f"No se encontró columna exacta '{normalized_name}'")


def parse_schedule_base() -> tuple[pd.DataFrame, pd.DataFrame]:
    bd = read_excel_sheet(SCHEDULE_XLSX, "BD").copy()
    bd["Cuenta"] = bd["Cuenta"].astype(str).str.strip()
    bd["Tienda"] = bd["Tienda"].astype(str).str.strip()
    bd["Colaborador"] = bd["Colaborador"].astype(str).str.strip()
    bd["Fecha"] = pd.to_datetime(bd["Fecha"], errors="coerce")
    bd["Semana ISO"] = pd.to_numeric(bd["Semana ISO"], errors="coerce")
    bd["Horas"] = pd.to_numeric(bd["Horas"], errors="coerce")
    bd["Categoria"] = np.where(bd["Tienda"].str.startswith("TB"), "The Box", "Coolbrands")
    included = bd[bd["Cuenta"].eq("Si")].copy()
    excluded = bd[bd["Cuenta"].eq("No")].copy()
    included["shift_id"] = np.arange(len(included))
    return included, excluded


def parse_shift_datetimes(included: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    records: list[dict] = []
    questionable: list[dict] = []

    for _, row in included.iterrows():
        fecha = row["Fecha"]
        ingreso_raw = row["Ingreso"]
        salida_raw = row["Salida"]
        horas_reportadas = row["Horas"]

        issue_flags: list[str] = []
        include_shift = True

        if pd.isna(fecha):
            include_shift = False
            issue_flags.append("fecha_invalida")
            start_dt = pd.NaT
            end_dt = pd.NaT
        else:
            start_dt = pd.to_datetime(f"{fecha.date()} {ingreso_raw}", format="mixed", errors="coerce")
            end_dt = pd.to_datetime(f"{fecha.date()} {salida_raw}", format="mixed", errors="coerce")
            if pd.isna(start_dt) or pd.isna(end_dt):
                include_shift = False
                issue_flags.append("hora_invalida")

        crossed_midnight = False
        duration_hours = np.nan
        if include_shift:
            if end_dt <= start_dt:
                end_dt = end_dt + pd.Timedelta(days=1)
                crossed_midnight = True
                issue_flags.append("cruza_medianoche")

            duration_hours = (end_dt - start_dt).total_seconds() / 3600
            if duration_hours <= 0:
                include_shift = False
                issue_flags.append("duracion_no_positiva")
            elif duration_hours > 16:
                include_shift = False
                issue_flags.append("duracion_mayor_16h")

            if pd.notna(horas_reportadas) and np.isfinite(duration_hours):
                if abs(float(horas_reportadas) - float(duration_hours)) > 1.5:
                    issue_flags.append("difiere_de_horas_reportadas")

        item = {
            "shift_id": row["shift_id"],
            "Tienda": row["Tienda"],
            "Colaborador": row["Colaborador"],
            "Semana ISO": row["Semana ISO"],
            "Fecha": fecha,
            "Ingreso": ingreso_raw,
            "Salida": salida_raw,
            "Horas_reportadas": horas_reportadas,
            "start_dt": start_dt,
            "end_dt": end_dt,
            "duracion_reconstruida_h": duration_hours,
            "include_shift": include_shift,
            "crossed_midnight": crossed_midnight,
            "flags": "|".join(issue_flags) if issue_flags else "",
        }
        records.append(item)
        if issue_flags:
            questionable.append(item)

    parsed = pd.DataFrame(records)
    questionable_df = pd.DataFrame(questionable)
    return parsed, questionable_df


def expand_shift_hourly(parsed_shifts: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    valid = parsed_shifts[parsed_shifts["include_shift"]].copy()

    for _, row in valid.iterrows():
        start_dt = row["start_dt"]
        end_dt = row["end_dt"]
        cursor = start_dt.floor("h")
        while cursor < end_dt:
            bin_start = cursor
            bin_end = cursor + pd.Timedelta(hours=1)
            overlap_start = max(start_dt, bin_start)
            overlap_end = min(end_dt, bin_end)
            overlap_hours = max((overlap_end - overlap_start).total_seconds() / 3600, 0.0)

            if overlap_hours > 0:
                rows.append(
                    {
                        "shift_id": row["shift_id"],
                        "Tienda": row["Tienda"],
                        "Colaborador": row["Colaborador"],
                        "Semana ISO": row["Semana ISO"],
                        "Fecha_hora_bin": bin_start,
                        "Fecha": pd.Timestamp(bin_start.date()),
                        "Dia": SPANISH_DAY_MAP[bin_start.dayofweek],
                        "Hora": int(bin_start.hour),
                        "horas_solapadas": overlap_hours,
                    }
                )
            cursor = bin_end

    if not rows:
        return pd.DataFrame(
            columns=[
                "Tienda",
                "Semana ISO",
                "Fecha",
                "Dia",
                "Hora",
                "personas_solapan_hora",
                "horas_persona_programadas",
                "turnos_aportantes",
            ]
        )

    hourly = pd.DataFrame(rows)
    grouped = (
        hourly.groupby(["Tienda", "Semana ISO", "Fecha", "Dia", "Hora"], as_index=False)
        .agg(
            personas_solapan_hora=("Colaborador", "nunique"),
            horas_persona_programadas=("horas_solapadas", "sum"),
            turnos_aportantes=("shift_id", "nunique"),
        )
        .sort_values(["Tienda", "Semana ISO", "Fecha", "Hora"])
    )
    return grouped


def run_overlap_unit_tests() -> pd.DataFrame:
    cases = [
        {
            "name": "10-19_exclusive_end",
            "start": pd.Timestamp("2026-08-17 10:00:00"),
            "end": pd.Timestamp("2026-08-17 19:00:00"),
            "expected_hours": {10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 1},
            "not_expected_hours": [9, 19],
        },
        {
            "name": "09_30_18_30_partial_edges",
            "start": pd.Timestamp("2026-08-17 09:30:00"),
            "end": pd.Timestamp("2026-08-17 18:30:00"),
            "expected_hours": {9: 0.5, 10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 1, 16: 1, 17: 1, 18: 0.5},
            "not_expected_hours": [8, 19],
        },
        {
            "name": "23-05_cross_midnight",
            "start": pd.Timestamp("2026-08-19 23:00:00"),
            "end": pd.Timestamp("2026-08-20 05:00:00"),
            "expected_hours": {23: 1, 0: 1, 1: 1, 2: 1, 3: 1, 4: 1},
            "not_expected_hours": [5, 22],
        },
    ]

    records: list[dict] = []
    for case in cases:
        cursor = case["start"].floor("h")
        observed: dict[int, float] = {}
        while cursor < case["end"]:
            bin_start = cursor
            bin_end = cursor + pd.Timedelta(hours=1)
            overlap_hours = max((min(case["end"], bin_end) - max(case["start"], bin_start)).total_seconds() / 3600, 0.0)
            if overlap_hours > 0:
                observed[int(bin_start.hour)] = observed.get(int(bin_start.hour), 0.0) + overlap_hours
            cursor = bin_end

        ok = True
        for hour, expected in case["expected_hours"].items():
            if not np.isclose(observed.get(hour, 0.0), expected):
                ok = False
        for hour in case["not_expected_hours"]:
            if observed.get(hour, 0.0) > 0:
                ok = False

        records.append(
            {
                "caso": case["name"],
                "horas_observadas": str(observed),
                "resultado": "ok" if ok else "fail",
            }
        )
        if not ok:
            raise AssertionError(f"Falló prueba de solapamiento: {case['name']}")

    return pd.DataFrame(records)


def compare_with_por_hora(hourly_staffing: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    por_hora = read_excel_sheet(SCHEDULE_XLSX, "Por hora")
    hour_cols = [c for c in por_hora.columns if re.match(r"^\d{2}:00$", str(c))]
    por_long = por_hora.melt(
        id_vars=["Tienda", "Semana ISO", "Dia"],
        value_vars=hour_cols,
        var_name="hora_col",
        value_name="personas_por_hora_hoja",
    )
    por_long["Hora"] = por_long["hora_col"].str.slice(0, 2).astype(int)
    por_long["personas_por_hora_hoja"] = pd.to_numeric(por_long["personas_por_hora_hoja"], errors="coerce").fillna(0)
    por_long = por_long.drop(columns=["hora_col"])

    ours = (
        hourly_staffing.groupby(["Tienda", "Semana ISO", "Dia", "Hora"], as_index=False)["personas_solapan_hora"]
        .sum()
        .rename(columns={"personas_solapan_hora": "personas_reconstruidas"})
    )
    comp = por_long.merge(ours, on=["Tienda", "Semana ISO", "Dia", "Hora"], how="left")
    comp["personas_reconstruidas"] = comp["personas_reconstruidas"].fillna(0)
    comp["diferencia"] = comp["personas_reconstruidas"] - comp["personas_por_hora_hoja"]
    comp["abs_diferencia"] = comp["diferencia"].abs()
    summary = pd.DataFrame(
        [
            {
                "filas_comparadas": len(comp),
                "filas_con_diferencia": int(comp["diferencia"].ne(0).sum()),
                "diferencia_media_absoluta": comp["abs_diferencia"].mean(),
                "diferencia_maxima_absoluta": comp["abs_diferencia"].max(),
            }
        ]
    )
    top_diff = comp.sort_values("abs_diferencia", ascending=False).head(120)
    return summary, top_diff


def compute_long_shift_tables(included: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    all_chain = included.groupby("Semana ISO", as_index=False).agg(
        tiendas=("Tienda", "nunique"),
        turnos_incluidos=("Colaborador", "size"),
        turnos_largos=("Horas", lambda s: int((s >= 11).sum())),
        horas_programadas=("Horas", "sum"),
    )
    all_chain["pct_turnos_largos"] = all_chain["turnos_largos"] / all_chain["turnos_incluidos"]

    the_box = included[included["Tienda"].str.startswith("TB")].groupby("Semana ISO", as_index=False).agg(
        tiendas=("Tienda", "nunique"),
        turnos_incluidos=("Colaborador", "size"),
        turnos_largos=("Horas", lambda s: int((s >= 11).sum())),
        horas_programadas=("Horas", "sum"),
    )
    the_box["pct_turnos_largos"] = the_box["turnos_largos"] / the_box["turnos_incluidos"]
    return all_chain, the_box


def build_cruce_s34(included: pd.DataFrame, parsed_shifts: pd.DataFrame, hourly_staffing: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sales = read_excel_sheet(COMMERCIAL_XLSX, "BD Venta por hora")
    col_year = find_column(sales, include=["ano"])
    col_week = find_column(sales, include=["semana"])
    col_date = find_column(sales, include=["fecha"])
    col_hour = find_column(sales, include=["hora"])
    col_cat = find_column(sales, include=["categoria"])
    col_store = find_exact_column(sales, "tienda")
    col_flow = find_column(sales, include=["flujo"])
    col_tx = find_column(sales, include=["transacciones"])
    col_sale = find_column(sales, include=["venta"], exclude=["meta"])

    sales = sales.rename(
        columns={
            col_year: "Anio",
            col_week: "Semana",
            col_date: "Fecha",
            col_hour: "Hora",
            col_cat: "Categoria",
            col_store: "Tienda",
            col_flow: "Flujo",
            col_tx: "Transacciones",
            col_sale: "Venta",
        }
    )
    sales["Fecha"] = pd.to_datetime(sales["Fecha"], errors="coerce")
    sales["Hora"] = pd.to_numeric(sales["Hora"], errors="coerce")
    sales["Flujo"] = pd.to_numeric(sales["Flujo"], errors="coerce")
    sales["Transacciones"] = pd.to_numeric(sales["Transacciones"], errors="coerce")
    sales["Venta"] = pd.to_numeric(sales["Venta"], errors="coerce")
    sales = sales[sales["Categoria"].astype(str).str.strip().str.upper().eq("THE BOX")].copy()
    sales_w34 = sales[(sales["Anio"] == 2026) & (sales["Semana"] == 34)].copy()
    sales_w34 = sales_w34[["Tienda", "Fecha", "Hora", "Flujo", "Transacciones", "Venta"]].copy()

    staffing = hourly_staffing[
        (hourly_staffing["Semana ISO"] == 34) & hourly_staffing["Tienda"].astype(str).str.startswith("TB")
    ][["Tienda", "Fecha", "Hora", "personas_solapan_hora", "horas_persona_programadas"]].copy()

    schedule_day = included[
        (included["Semana ISO"] == 34) & included["Tienda"].astype(str).str.startswith("TB")
    ].groupby(["Tienda", "Fecha"], as_index=False).size().rename(columns={"size": "filas_horario"})
    valid_shift_day = parsed_shifts[
        (parsed_shifts["Semana ISO"] == 34)
        & parsed_shifts["Tienda"].astype(str).str.startswith("TB")
        & parsed_shifts["include_shift"]
    ].groupby(["Tienda", "Fecha"], as_index=False).size().rename(columns={"size": "turnos_validos"})
    day_status = schedule_day.merge(valid_shift_day, on=["Tienda", "Fecha"], how="left")
    day_status["turnos_validos"] = day_status["turnos_validos"].fillna(0).astype(int)

    matched = sales_w34.merge(staffing, on=["Tienda", "Fecha", "Hora"], how="left")
    matched = matched.merge(day_status, on=["Tienda", "Fecha"], how="left")
    matched["has_schedule_day"] = matched["filas_horario"].notna()
    matched["has_valid_shift_day"] = matched["turnos_validos"].fillna(0).gt(0)
    matched["has_hourly_match"] = matched["personas_solapan_hora"].notna()

    matched["estado_emparejamiento"] = np.select(
        [
            matched["has_hourly_match"],
            (~matched["has_hourly_match"]) & (~matched["has_schedule_day"]),
            (~matched["has_hourly_match"]) & (matched["has_schedule_day"]) & (~matched["has_valid_shift_day"]),
            (~matched["has_hourly_match"]) & (matched["has_schedule_day"]) & (matched["has_valid_shift_day"]),
        ],
        [
            "coincidencia_encontrada",
            "registro_horario_ausente",
            "registro_horario_dudoso_no_emparejado",
            "cero_confirmado",
        ],
        default="no_clasificado",
    )

    matched["personas_confirmadas_analisis"] = np.where(
        matched["estado_emparejamiento"].eq("cero_confirmado"),
        0,
        matched["personas_solapan_hora"],
    )
    matched["horas_persona_confirmadas_analisis"] = np.where(
        matched["estado_emparejamiento"].eq("cero_confirmado"),
        0,
        matched["horas_persona_programadas"],
    )
    matched["conversion"] = matched["Transacciones"] / matched["Flujo"].replace(0, np.nan)

    audit = pd.DataFrame(
        [
            {
                "periodo_ventas": f"{sales_w34['Fecha'].min().date()} a {sales_w34['Fecha'].max().date()}",
                "filas_ventas": len(sales_w34),
                "tiendas_ventas": sales_w34["Tienda"].nunique(),
                "filas_coincidencia": int(matched["estado_emparejamiento"].eq("coincidencia_encontrada").sum()),
                "filas_cero_confirmado": int(matched["estado_emparejamiento"].eq("cero_confirmado").sum()),
                "filas_horario_ausente": int(matched["estado_emparejamiento"].eq("registro_horario_ausente").sum()),
                "filas_dudosas_no_emparejadas": int(
                    matched["estado_emparejamiento"].eq("registro_horario_dudoso_no_emparejado").sum()
                ),
                "flujo_cero": int(matched["Flujo"].eq(0).sum()),
                "transacciones_gt_flujo": int(matched["Transacciones"].gt(matched["Flujo"]).sum()),
                "fecha_min_horarios_tb": str(included[included["Tienda"].str.startswith("TB")]["Fecha"].min().date()),
                "fecha_max_horarios_tb": str(included[included["Tienda"].str.startswith("TB")]["Fecha"].max().date()),
            }
        ]
    )
    return matched, audit


def build_survey_outputs() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    nps = read_excel_sheet(COMMERCIAL_XLSX, "BD NPS")

    score_col = find_column(
        nps,
        include=["escala", "0", "10", "atencion"],
        exclude=["puntos:", "comentarios:"],
    )
    comment_col = find_column(
        nps,
        include=["que fue lo que mas te gusto o que podriamos mejorar"],
        exclude=["puntos:", "comentarios:"],
    )

    score = pd.to_numeric(nps[score_col], errors="coerce")
    score_valid = score[(score >= 0) & (score <= 10)]
    comments = nps[comment_col].astype(str).str.strip()
    comments = comments[~comments.str.lower().isin(["", "nan", "none", "anónimo", "anonimo"])]

    score_table = (
        pd.DataFrame({"calificacion": range(0, 11)})
        .merge(score_valid.value_counts().rename_axis("calificacion").reset_index(name="frecuencia"), on="calificacion", how="left")
        .fillna({"frecuencia": 0})
    )
    score_table["frecuencia"] = score_table["frecuencia"].astype(int)
    score_table["porcentaje"] = np.where(len(score_valid) > 0, score_table["frecuencia"] / len(score_valid) * 100, 0.0)
    score_table["denominador"] = len(score_valid)
    score_table["media"] = float(score_valid.mean()) if len(score_valid) else np.nan
    score_table["mediana"] = float(score_valid.median()) if len(score_valid) else np.nan

    topic_keywords = {
        "atencion_servicio": ["atencion", "trato", "asesor", "vendedor", "servicio", "amable"],
        "precio_promociones": ["precio", "promocion", "descuento", "oferta", "caro", "barato"],
        "stock_variedad_tallas": ["stock", "variedad", "talla", "modelo", "inventario"],
        "tiempos_fila_caja": ["fila", "espera", "caja", "demora", "rapido", "lento"],
        "tienda_ambiente_layout": ["tienda", "orden", "limpio", "ambiente", "espacio"],
    }
    valence_keywords = {
        "positivo": ["bueno", "excelente", "amable", "rápido", "rapido", "bien", "genial"],
        "negativo": ["malo", "caro", "lento", "demora", "falta", "pésimo", "pesimo", "mejorar"],
    }

    topic_rows: list[dict] = []
    sample_review: list[dict] = []
    for idx, text in comments.items():
        norm = normalize_text(text)
        topics = [topic for topic, kws in topic_keywords.items() if any(kw in norm for kw in kws)]
        if not topics:
            topics = ["sin_tema_dominante"]

        if any(kw in norm for kw in valence_keywords["positivo"]) and any(kw in norm for kw in valence_keywords["negativo"]):
            valence = "mixto"
        elif any(kw in norm for kw in valence_keywords["positivo"]):
            valence = "positivo"
        elif any(kw in norm for kw in valence_keywords["negativo"]):
            valence = "negativo"
        else:
            valence = "no_explicito"

        sample_review.append({"id_respuesta": int(idx), "temas": "|".join(topics), "valoracion_textual": valence})
        for topic in topics:
            topic_rows.append({"tema": topic, "valoracion_textual": valence})

    if topic_rows:
        topic_df = pd.DataFrame(topic_rows)
        theme_summary = (
            topic_df.groupby(["tema", "valoracion_textual"], as_index=False)
            .size()
            .rename(columns={"size": "n_comentarios"})
            .sort_values(["n_comentarios", "tema"], ascending=[False, True])
        )
        theme_summary["porcentaje_sobre_comentarios"] = np.where(
            len(comments) > 0, theme_summary["n_comentarios"] / len(comments) * 100, 0.0
        )
    else:
        theme_summary = pd.DataFrame(columns=["tema", "valoracion_textual", "n_comentarios", "porcentaje_sobre_comentarios"])

    selected_cols_audit = pd.DataFrame(
        [
            {
                "columna_calificacion": score_col,
                "columna_comentario": comment_col,
                "registros_nps_totales": len(nps),
                "calificaciones_validas_0_10": int(len(score_valid)),
                "comentarios_no_vacios": int(len(comments)),
            }
        ]
    )
    sample_df = pd.DataFrame(sample_review).head(20)
    return score_table, theme_summary, selected_cols_audit.merge(sample_df, how="cross")


def plot_turnos_largos_the_box(the_box_weekly: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(8, 4.5))
    ax.plot(the_box_weekly["Semana ISO"], the_box_weekly["pct_turnos_largos"], marker="o", linewidth=2, color="#1f77b4")
    ax.set_title("Turnos de 11+ horas en The Box, por semana")
    ax.set_xlabel("Semana ISO")
    ax.set_ylabel("Turnos largos / turnos incluidos")
    ax.set_ylim(0, 0.45)
    ax.grid(True, alpha=0.25)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "turnos_largos_the_box.png", dpi=220)
    fig.savefig(FIG_DIR / "turnos_largos_the_box.svg", format="svg")
    plt.close(fig)


def plot_dotacion_rbsb(hourly_staffing: pd.DataFrame) -> None:
    subset = hourly_staffing[
        (hourly_staffing["Tienda"] == "TB RBSB")
        & (hourly_staffing["Semana ISO"] == 34)
        & (hourly_staffing["Hora"].between(7, 22))
    ].copy()
    if subset.empty:
        return
    pivot = subset.pivot_table(index="Hora", columns="Fecha", values="personas_solapan_hora", aggfunc="sum").sort_index()
    fig, ax = plt.subplots(figsize=(10, 4))
    im = ax.imshow(pivot.values, aspect="auto", cmap="YlOrRd")
    ax.set_yticks(range(len(pivot.index)))
    ax.set_yticklabels(pivot.index.tolist())
    ax.set_xticks(range(len(pivot.columns)))
    ax.set_xticklabels([d.strftime("%a %d-%b") for d in pivot.columns], rotation=45, ha="right")
    ax.set_title("Dotación programada por hora (personas) — TB RBSB, semana 34")
    ax.set_xlabel("Fecha")
    ax.set_ylabel("Hora")
    fig.colorbar(im, ax=ax, fraction=0.03, pad=0.04)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "dotacion_por_hora_tbrbsb_s34.png", dpi=220)
    plt.close(fig)


def write_prism_docs(
    all_chain_weekly: pd.DataFrame,
    the_box_weekly: pd.DataFrame,
    overlap_test_results: pd.DataFrame,
    por_hora_summary: pd.DataFrame,
    survey_audit_for_docs: pd.DataFrame,
    cross_audit: pd.DataFrame,
) -> None:
    s34_all = all_chain_weekly[all_chain_weekly["Semana ISO"] == 34].iloc[0]
    s38_all = all_chain_weekly[all_chain_weekly["Semana ISO"] == 38].iloc[0]
    s34_tb = the_box_weekly[the_box_weekly["Semana ISO"] == 34].iloc[0]
    s38_tb = the_box_weekly[the_box_weekly["Semana ISO"] == 38].iloc[0]
    survey_info = survey_audit_for_docs.iloc[0]
    overlap_info = por_hora_summary.iloc[0]
    cross_info = cross_audit.iloc[0]

    report_text = f"""# Hallazgos para paper

## Resumen ejecutivo (resultados calculados)
- Fuente de horarios: `Horarios_Headcount S34-S38.xlsx`, hoja `BD`, con inclusión `Cuenta = Si`.
- Cobertura temporal horarios: semanas ISO 34 a 38 de 2026.
- Cobertura The Box para turnos largos: 16 tiendas.
- Cobertura total cadena para turnos largos: 19 tiendas (The Box + Coolbrands).
- Turnos largos (>=11h) en **The Box**:
  - Semana 34: {int(s34_tb['turnos_largos'])}/{int(s34_tb['turnos_incluidos'])} = {s34_tb['pct_turnos_largos']*100:.2f}%.
  - Semana 38: {int(s38_tb['turnos_largos'])}/{int(s38_tb['turnos_incluidos'])} = {s38_tb['pct_turnos_largos']*100:.2f}%.
- Turnos largos (>=11h) en **cadena total (19 tiendas)**:
  - Semana 34: {int(s34_all['turnos_largos'])}/{int(s34_all['turnos_incluidos'])} = {s34_all['pct_turnos_largos']*100:.2f}%.
  - Semana 38: {int(s38_all['turnos_largos'])}/{int(s38_all['turnos_incluidos'])} = {s38_all['pct_turnos_largos']*100:.2f}%.
- La reconstrucción por hora usa solapamiento semiabierto: turno `[ingreso, salida)` y franja `[hora, hora+1)`.
- El cruce comercial-horarios se limita a semana ISO 34 de 2026 para mantener un periodo común y auditable.

## Cruce con comercial (semana 34, The Box)
- Filas de ventas en población del cruce: {int(cross_info['filas_ventas'])}.
- Coincidencia encontrada: {int(cross_info['filas_coincidencia'])}.
- Cero confirmado (solo con respaldo horario del día): {int(cross_info['filas_cero_confirmado'])}.
- Registro horario ausente: {int(cross_info['filas_horario_ausente'])}.
- Registro horario dudoso/no emparejado: {int(cross_info['filas_dudosas_no_emparejadas'])}.
- Anomalías de consistencia comercial: `transacciones > flujo` = {int(cross_info['transacciones_gt_flujo'])}; `flujo = 0` = {int(cross_info['flujo_cero'])}.
- Advertencia metodológica: dotación programada no equivale a asistencia efectiva.

## Encuesta (BD NPS)
- Columna de calificación seleccionada explícitamente: `{survey_info['columna_calificacion']}`.
- Columna de comentario abierto seleccionada explícitamente: `{survey_info['columna_comentario']}`.
- Registros NPS totales: {int(survey_info['registros_nps_totales'])}.
- Calificaciones válidas (0-10): {int(survey_info['calificaciones_validas_0_10'])}.
- Comentarios no vacíos: {int(survey_info['comentarios_no_vacios'])}.
- La clasificación separa **tema** y **valoración textual**. Una mención de precio/atención no se interpreta automáticamente como negativa.

## Qué sí y qué no interpretar
- Sí: cambios descriptivos en estructura de turnos y dotación programada por tienda/semana/franja.
- No: causalidad sobre conversión o satisfacción a partir de este paquete descriptivo.
- No: inferir asistencia efectiva de colaboradores ni opinión de toda la población de clientes.

## Párrafos propuestos para el paper
1. "En las semanas ISO 34-38 de 2026, la proporción de turnos de 11 o más horas en The Box (16 tiendas) aumentó de {s34_tb['pct_turnos_largos']*100:.2f}% ({int(s34_tb['turnos_largos'])}/{int(s34_tb['turnos_incluidos'])}) a {s38_tb['pct_turnos_largos']*100:.2f}% ({int(s38_tb['turnos_largos'])}/{int(s38_tb['turnos_incluidos'])}), medido sobre turnos programados con `Cuenta = Si`."
2. "En la cadena total (19 tiendas), los valores equivalentes fueron {s34_all['pct_turnos_largos']*100:.2f}% en semana 34 y {s38_all['pct_turnos_largos']*100:.2f}% en semana 38, por lo que cualquier comparación de marcas debe explicitar la población usada."
3. "El cruce horario-comercial de la semana 34 clasifica explícitamente coincidencias, ausencia de registro y ceros confirmados; por diseño, no interpreta dotación programada como presencia efectiva ni prueba causal de desempeño."
"""

    method_text = f"""# Metodología y calidad

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
- Resultado: {", ".join(overlap_test_results['resultado'].tolist())}.

## Comparación con hoja "Por hora"
- Filas comparadas: {int(overlap_info['filas_comparadas'])}.
- Filas con diferencia: {int(overlap_info['filas_con_diferencia'])}.
- Diferencia media absoluta: {overlap_info['diferencia_media_absoluta']:.3f}.
- Diferencia máxima absoluta: {overlap_info['diferencia_maxima_absoluta']:.3f}.
- Las discrepancias se reportan para revisión; no se ocultan ni se fuerzan a cero.

## Límites del cruce comercial
- Ventana de análisis: {cross_info['periodo_ventas']} (semana ISO 34 de 2026).
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
"""

    readme_text = """# README_PARA_PRISM

Paquete listo para Prism (sin modificar Excel fuente ni paper).

## Contenido
- INFORME_HALLAZGOS_PARA_PAPER.md
- METODOLOGIA_Y_CALIDAD.md
- tablas/turnos_largos_por_semana_the_box.csv
- tablas/turnos_largos_por_semana_cadena_19_tiendas.csv
- tablas/dotacion_por_tienda_y_semana.csv
- tablas/auditoria_cruce_horarios_ventas.csv
- tablas/resultados_cruce_s34_detallado.csv
- tablas/encuesta_calificacion_atencion.csv
- tablas/encuesta_temas_comentarios.csv
- tablas/auditoria_columnas_nps_y_muestra_revision.csv
- tablas/auditoria_reconstruccion_por_hora.csv
- tablas/discrepancias_muestra_vs_por_hora.csv
- tablas/pruebas_solapamiento_intervalos.csv
- figuras/turnos_largos_the_box.png
- figuras/turnos_largos_the_box.svg
- figuras/dotacion_por_hora_tbrbsb_s34.png
"""

    (PRISM_DIR / "INFORME_HALLAZGOS_PARA_PAPER.md").write_text(report_text, encoding="utf-8")
    (PRISM_DIR / "METODOLOGIA_Y_CALIDAD.md").write_text(method_text, encoding="utf-8")
    (PRISM_DIR / "README_PARA_PRISM.md").write_text(readme_text, encoding="utf-8")


def copy_outputs_to_prism(files: Iterable[Path]) -> None:
    PRISM_DIR.mkdir(parents=True, exist_ok=True)
    PRISM_TABLAS.mkdir(parents=True, exist_ok=True)
    PRISM_FIGS.mkdir(parents=True, exist_ok=True)
    for src in files:
        if src.suffix.lower() in {".png", ".svg"}:
            shutil.copy2(src, PRISM_FIGS / src.name)
        else:
            shutil.copy2(src, PRISM_TABLAS / src.name)


def main() -> None:
    TABLAS_DIR.mkdir(parents=True, exist_ok=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    overlap_tests = run_overlap_unit_tests()
    save_csv(overlap_tests, TABLAS_DIR / "pruebas_solapamiento_intervalos.csv")

    included, excluded = parse_schedule_base()
    parsed_shifts, questionable = parse_shift_datetimes(included)
    hourly_staffing = expand_shift_hourly(parsed_shifts)
    por_hora_summary, por_hora_top_diff = compare_with_por_hora(hourly_staffing)

    all_chain_weekly, the_box_weekly = compute_long_shift_tables(included)

    week_store = included.groupby(["Tienda", "Semana ISO"], as_index=False).agg(
        turnos_incluidos=("Colaborador", "size"),
        personas_distintas=("Colaborador", "nunique"),
        horas_programadas=("Horas", "sum"),
        turnos_largos=("Horas", lambda s: int((s >= 11).sum())),
    )
    week_store["pct_turnos_largos"] = week_store["turnos_largos"] / week_store["turnos_incluidos"]
    week_store["Categoria"] = np.where(week_store["Tienda"].str.startswith("TB"), "The Box", "Coolbrands")

    exclusion_summary = excluded["Motivo de exclusion"].value_counts(dropna=False).reset_index()
    exclusion_summary.columns = ["Motivo de exclusion", "Registros"]

    matched_cross, cross_audit = build_cruce_s34(included, parsed_shifts, hourly_staffing)
    survey_score, survey_themes, survey_audit_and_sample = build_survey_outputs()

    out_files = [
        save_csv(all_chain_weekly, TABLAS_DIR / "turnos_largos_por_semana_cadena_19_tiendas.csv"),
        save_csv(the_box_weekly, TABLAS_DIR / "turnos_largos_por_semana_the_box.csv"),
        save_csv(week_store[week_store["Categoria"].eq("The Box")], TABLAS_DIR / "dotacion_por_tienda_y_semana.csv"),
        save_csv(exclusion_summary, TABLAS_DIR / "exclusions_by_reason.csv"),
        save_csv(questionable, TABLAS_DIR / "auditoria_turnos_dudosos.csv"),
        save_csv(hourly_staffing, TABLAS_DIR / "dotacion_horaria_reconstruida.csv"),
        save_csv(por_hora_summary, TABLAS_DIR / "auditoria_reconstruccion_por_hora.csv"),
        save_csv(por_hora_top_diff, TABLAS_DIR / "discrepancias_muestra_vs_por_hora.csv"),
        save_csv(cross_audit, TABLAS_DIR / "auditoria_cruce_horarios_ventas.csv"),
        save_csv(matched_cross, TABLAS_DIR / "resultados_cruce_s34_detallado.csv"),
        save_csv(survey_score, TABLAS_DIR / "encuesta_calificacion_atencion.csv"),
        save_csv(survey_themes, TABLAS_DIR / "encuesta_temas_comentarios.csv"),
        save_csv(survey_audit_and_sample, TABLAS_DIR / "auditoria_columnas_nps_y_muestra_revision.csv"),
        save_csv(overlap_tests, TABLAS_DIR / "pruebas_solapamiento_intervalos.csv"),
    ]

    plot_turnos_largos_the_box(the_box_weekly)
    plot_dotacion_rbsb(hourly_staffing)

    fig_files = [
        FIG_DIR / "turnos_largos_the_box.png",
        FIG_DIR / "turnos_largos_the_box.svg",
        FIG_DIR / "dotacion_por_hora_tbrbsb_s34.png",
    ]

    copy_outputs_to_prism([*out_files, *fig_files])
    write_prism_docs(
        all_chain_weekly=all_chain_weekly,
        the_box_weekly=the_box_weekly,
        overlap_test_results=overlap_tests,
        por_hora_summary=por_hora_summary,
        survey_audit_for_docs=survey_audit_and_sample[["columna_calificacion", "columna_comentario", "registros_nps_totales", "calificaciones_validas_0_10", "comentarios_no_vacios"]].drop_duplicates(),
        cross_audit=cross_audit,
    )

    print("done")


if __name__ == "__main__":
    main()
