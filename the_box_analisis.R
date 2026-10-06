# ==============================================================================
# THE BOX - OLA Y MONTAÑA S.A.C.
# Script de replicacion de los resultados estadisticos del Trabajo Final
# TFIE 262, ciclo 26-2
#
# Fuente unica: "BD The Box Presentacion 30.08.xlsx"
# Cada bloque imprime el resultado que debe aparecer en el documento.
# Al final del archivo hay una tabla de valores esperados para verificar
# que la replicacion es correcta.
# ==============================================================================

# ---- 0. Paquetes -------------------------------------------------------------
options(repos = c(CRAN = "https://cloud.r-project.org"))
paquetes <- c("readxl", "dplyr", "tidyr", "fixest")
faltan <- paquetes[!paquetes %in% rownames(installed.packages())]
if (length(faltan) > 0) install.packages(faltan, repos = getOption("repos"))
invisible(lapply(paquetes, library, character.only = TRUE))

options(scipen = 999)

# Ajustar a la ruta local. Si el archivo esta en el directorio de trabajo basta
# con el nombre. Verificar con getwd() donde esta parado R.
RUTA <- file.path("C:/Users/ADMIN/Desktop/UP/TRABAJO FINAL INGENIERÍA EMPRESARIAL/TFIE_26_2",
                  "BD The Box Presentacion 30.08.xlsx")

if (!file.exists(RUTA)) stop("No se encuentra el archivo: ", RUTA, ". Directorio actual: ", getwd())

# ---- 1. Carga y normalizacion de nombres -------------------------------------
# Se renombra por POSICION y no por nombre, porque los encabezados originales
# tienen tildes y espacios que R maneja de forma inconsistente segun el sistema.
raw <- read_excel(RUTA, sheet = "BD Venta por hora")
cat("Encabezados originales:\n"); print(names(raw)[1:13])
# Deben ser, en este orden: Anio, Semana, Fecha, InicioSemana, Hora, Categoria,
# Nro Tienda, Tienda, Nombre Tienda, Flujo, Transacciones, Venta, Unds Vendidas
raw <- raw[, 1:13]
names(raw) <- c("anio","semana","fecha","inicio_semana","hora","categoria",
                "nro_tienda","tienda","nombre_tienda","flujo","transacciones",
                "venta","unidades")

raw <- raw %>%
  mutate(across(c(anio, semana, hora, flujo, transacciones, venta, unidades), as.numeric),
         fecha = as.Date(fecha))

cat("Filas totales:", nrow(raw), "\n")           # esperado: 122329
cat("Categorias:", paste(unique(raw$categoria), collapse = ", "), "\n")

tb <- raw %>% filter(categoria == "THE BOX")
cat("Filas THE BOX:", nrow(tb), "\n")            # esperado: 103790

# ==============================================================================
# 2. CALIDAD DE DATOS  (dimension tecnologica del diagnostico)
# ==============================================================================
calidad <- tb %>%
  group_by(anio) %>%
  summarise(
    filas               = n(),
    flujo_total         = sum(flujo),
    trx_total           = sum(transacciones),
    conv_reportada      = sum(transacciones) / sum(flujo),
    filas_flujo_cero    = sum(flujo == 0),
    trx_en_flujo_cero   = sum(transacciones[flujo == 0]),
    pct_trx_flujo_cero  = sum(transacciones[flujo == 0]) / sum(transacciones),
    flujo_hora22        = sum(flujo[hora == 22]),
    trx_hora22          = sum(transacciones[hora == 22]),
    .groups = "drop")
print(as.data.frame(calidad))
# 2026: conv_reportada = 0.06815 ; pct_trx_flujo_cero = 0.0484
# 2025: conv_reportada = 0.06468 ; pct_trx_flujo_cero = 0.0711

# ---- 3. Muestra depurada -----------------------------------------------------
# Criterio: horario comercial efectivo (10:00-21:59), registros internamente
# consistentes (flujo >= transacciones) y flujo positivo.
dep <- tb %>% filter(hora >= 10, hora <= 21, flujo >= transacciones, flujo > 0)
cat("Filas muestra depurada:", nrow(dep), "\n")

dep %>%
  group_by(anio) %>%
  summarise(conv_depurada = sum(transacciones) / sum(flujo), .groups = "drop") %>%
  as.data.frame() %>% print()
# 2026: 0.06467 ; 2025: 0.05973

# ==============================================================================
# 4. COMPARACION INTERANUAL, SEMANAS 2 A 34
#    Descomposicion Venta = Flujo x Conversion x UPT x Precio unitario
# ==============================================================================
comp <- dep %>%
  filter(semana >= 2, semana <= 34) %>%
  group_by(anio) %>%
  summarise(flujo = sum(flujo), trx = sum(transacciones),
            venta = sum(venta), unid = sum(unidades),
            tiendas = n_distinct(nombre_tienda), .groups = "drop") %>%
  mutate(conv = trx / flujo, ticket = venta / trx,
         upt = unid / trx, ppu = venta / unid)
print(as.data.frame(comp))

a <- comp %>% filter(anio == 2025); b <- comp %>% filter(anio == 2026)
dlv <- log(b$venta / a$venta)
cat("\nCrecimiento de venta:", sprintf("%+.1f%%", 100 * (b$venta / a$venta - 1)), "\n")
cat("Aporte flujo:      ", sprintf("%.1f%%", 100 * log(b$flujo / a$flujo) / dlv), "\n")
cat("Aporte conversion: ", sprintf("%.1f%%", 100 * log(b$conv  / a$conv ) / dlv), "\n")
cat("Aporte ticket:     ", sprintf("%.1f%%", 100 * log(b$ticket/ a$ticket) / dlv), "\n")
# Esperado: venta +94.1% ; flujo 35.9% ; conversion 16.5% ; ticket 47.5%

# Mismas tiendas en ambos anios
comunes <- intersect(
  dep %>% filter(anio == 2025, semana >= 2, semana <= 34) %>% pull(nombre_tienda) %>% unique(),
  dep %>% filter(anio == 2026, semana >= 2, semana <= 34) %>% pull(nombre_tienda) %>% unique())
dep %>%
  filter(semana >= 2, semana <= 34, nombre_tienda %in% comunes) %>%
  group_by(anio) %>%
  summarise(venta = sum(venta), conv = sum(transacciones)/sum(flujo), .groups = "drop") %>%
  as.data.frame() %>% print()
# 14 tiendas comparables: venta +75.9%

# ==============================================================================
# 5. VALOR IDEAL: FRONTERA INTERNA DE DESEMPENO DEMOSTRADO
#    Percentil de la distribucion de conversion semanal propia de cada tienda,
#    ponderado por flujo. Es el valor ideal del enunciado del problema.
# ==============================================================================
sw26 <- dep %>%
  filter(anio == 2026, semana >= 2, semana <= 34) %>%
  group_by(nombre_tienda, semana) %>%
  summarise(f = sum(flujo), t = sum(transacciones),
            v = sum(venta), u = sum(unidades), .groups = "drop") %>%
  filter(f >= 100, t >= 10) %>%
  mutate(conv = t / f)

conv_real <- sum(sw26$t) / sum(sw26$f)
cat("\nConversion real (tienda-semana, 2026 sem 2-34):", sprintf("%.4f%%", 100*conv_real), "\n")

frontera <- function(p) {
  sw26 %>%
    group_by(nombre_tienda) %>%
    summarise(q = quantile(conv, p, type = 7), w = sum(f), .groups = "drop") %>%
    summarise(valor = sum(q * w) / sum(w)) %>% pull(valor)
}
for (p in c(0.75, 0.90, 1.00)) {
  v <- frontera(p)
  cat(sprintf("Frontera p%-3d = %.4f%%  ->  brecha = %.4f pp\n",
              p*100, 100*v, 100*(v - conv_real)))
}
# Esperado: p75 = 7.1980% (0.7157 pp) ; p90 = 7.7848% (1.3025 pp) ; max = 8.5843% (2.1020 pp)

# Cuantas semanas-tienda alcanzaron alguna vez el 10%
sw_todas <- dep %>%
  group_by(nombre_tienda, anio, semana) %>%
  summarise(f = sum(flujo), t = sum(transacciones), .groups = "drop") %>%
  filter(f >= 300) %>% mutate(conv = t / f)
sw_todas %>% filter(anio == 2026) %>%
  summarise(n = n(), n_10 = sum(conv >= 0.10), pct = mean(conv >= 0.10)) %>%
  as.data.frame() %>% print()
sw_todas %>% filter(anio == 2026, conv >= 0.10) %>%
  count(nombre_tienda) %>% as.data.frame() %>% print()
# Esperado: 4.1% de las semanas-tienda, concentradas en Cusco y San Isidro

# ==============================================================================
# 6. RELACION TRAFICO - CONVERSION
#    Hallazgo central. Replica Perdikaki, Kesavan y Swaminathan (2012).
# ==============================================================================

# 6.1 Panel tienda-fecha-hora, efectos fijos tienda x hora y fecha
h <- dep %>%
  filter(flujo >= 20) %>%
  mutate(conv = transacciones / flujo,
         lf = log(flujo),
         tienda_hora = paste0(nombre_tienda, "_", hora))
m1 <- feols(conv ~ lf | tienda_hora + fecha, data = h, cluster = ~nombre_tienda)
summary(m1)
cat("\n+10% de flujo horario =>",
    sprintf("%.4f pp de conversion", coef(m1)["lf"] * log(1.1) * 100), "\n")
# Esperado: n = 38866 ; beta = -0.01583 ; ee = 0.00271 ; p < 0.001 ; -0.1509 pp

# 6.2 Panel tienda-semana, efectos fijos de tienda y de semana calendario
swp <- dep %>%
  group_by(nombre_tienda, anio, semana) %>%
  summarise(f = sum(flujo), t = sum(transacciones), .groups = "drop") %>%
  filter(f >= 200) %>%
  mutate(conv = t / f, lf = log(f), periodo = paste0(anio, "_", semana))
m2 <- feols(conv ~ lf | nombre_tienda + periodo, data = swp, cluster = ~nombre_tienda)
summary(m2)
# Esperado: n = 1228 ; beta = -0.04897 ; ee = 0.02559 ; p = 0.056

# 6.3 Corte transversal entre tiendas
# IMPORTANTE: el flujo semanal debe dividirse entre las semanas en que la tienda
# estuvo activa, no entre 33, porque Real Plaza Piura 2 abrio a mitad de anio.
ct <- dep %>%
  filter(anio == 2026, semana >= 2, semana <= 34) %>%
  group_by(nombre_tienda) %>%
  summarise(f = sum(flujo), t = sum(transacciones),
            sem_activas = n_distinct(semana), .groups = "drop") %>%
  mutate(conv = t / f, flujo_sem = f / sem_activas)
print(cor.test(ct$flujo_sem, ct$conv, method = "pearson"))
print(cor.test(ct$flujo_sem, ct$conv, method = "spearman", exact = FALSE))
# Esperado: Pearson = -0.378 (p = 0.149) ; Spearman = -0.615 (p = 0.011)

# Robustez: excluyendo las dos tiendas con ruptura de contador
ct2 <- ct %>% filter(!grepl("SAN ISIDRO|CHIMBOTE", nombre_tienda))
print(cor.test(ct2$flujo_sem, ct2$conv, method = "spearman", exact = FALSE))
# Esperado: Spearman = -0.758 (p = 0.002), la relacion se refuerza

# ==============================================================================
# 7. DESCOMPOSICION DE VARIANZA
#    Sustenta que la oportunidad esta dentro de cada tienda, no entre tiendas.
# ==============================================================================
vr <- sw_todas %>% filter(anio == 2026, semana >= 2, semana <= 34)
r_tienda <- summary(lm(conv ~ factor(nombre_tienda), data = vr))$r.squared
r_semana <- summary(lm(conv ~ factor(semana), data = vr))$r.squared
r_ambos  <- summary(lm(conv ~ factor(nombre_tienda) + factor(semana), data = vr))$r.squared
cat(sprintf("\nR2 tienda = %.4f | R2 semana = %.4f | R2 ambos = %.4f | residual = %.4f\n",
            r_tienda, r_semana, r_ambos, 1 - r_ambos))

sd_entre  <- vr %>% group_by(nombre_tienda) %>%
  summarise(c = sum(t)/sum(f), .groups="drop") %>% pull(c) %>% sd()
sd_dentro <- vr %>% group_by(nombre_tienda) %>%
  summarise(s = sd(conv), .groups="drop") %>% pull(s) %>% mean()
cat(sprintf("Desviacion ENTRE tiendas = %.5f | Desviacion DENTRO de tienda = %.5f\n",
            sd_entre, sd_dentro))
# Esperado: R2 tienda 0.332 ; semana 0.080 ; ambos 0.420 ; sd entre 0.00999 < sd dentro 0.01200

# ==============================================================================
# 8. PATRONES OPERATIVOS: HORA Y DIA
# ==============================================================================
d26 <- dep %>% filter(anio == 2026, semana >= 2, semana <= 34)

por_hora <- d26 %>% group_by(hora) %>%
  summarise(flujo = sum(flujo), trx = sum(transacciones), venta = sum(venta), .groups="drop") %>%
  mutate(share = flujo/sum(flujo), conv = trx/flujo, ticket = venta/trx)
print(as.data.frame(por_hora))
cat("\nConversion 10:00 =", sprintf("%.4f%%", 100*por_hora$conv[por_hora$hora==10]),
    "| resto del dia =", sprintf("%.4f%%",
    100*sum(por_hora$trx[por_hora$hora>10])/sum(por_hora$flujo[por_hora$hora>10])), "\n")
# Esperado: 4.21% contra 6.54%

por_dia <- d26 %>%
  mutate(dow = as.integer(format(fecha, "%u"))) %>%   # 1 = lunes ... 7 = domingo
  group_by(dow) %>%
  summarise(flujo = sum(flujo), trx = sum(transacciones), venta = sum(venta),
            unid = sum(unidades), .groups="drop") %>%
  mutate(share = flujo/sum(flujo), conv = trx/flujo, ticket = venta/trx)
print(as.data.frame(por_dia))
# Esperado: domingo con 22.4% del flujo y conversion 5.86%, la mas baja

# ==============================================================================
# 9. RUPTURAS DE MEDICION EN LOS CONTADORES
# ==============================================================================
si <- dep %>%
  filter(nombre_tienda == "THE BOX SAN ISIDRO", anio == 2026) %>%
  group_by(semana) %>%
  summarise(flujo = sum(flujo), trx = sum(transacciones), venta = sum(venta), .groups="drop") %>%
  mutate(conv = trx/flujo)
print(as.data.frame(si))

si %>% mutate(tramo = ifelse(semana <= 19, "sem 2-19", "sem 22-34")) %>%
  filter(semana <= 19 | semana >= 22) %>%
  group_by(tramo) %>%
  summarise(flujo_sem = mean(flujo), trx_sem = mean(trx), venta_sem = mean(venta),
            conv = sum(trx)/sum(flujo), .groups="drop") %>%
  as.data.frame() %>% print()
# Esperado: flujo de 555 a 938 por semana mientras trx baja de 60 a 44.
# La conversion cae de 10.79% a 4.71% por cambio en el denominador.

# Efecto de excluir las tiendas con ruptura sobre la mejora interanual
for (excl in c(FALSE, TRUE)) {
  d <- dep %>% filter(semana >= 2, semana <= 34, nombre_tienda %in% comunes)
  if (excl) d <- d %>% filter(!grepl("SAN ISIDRO|CHIMBOTE", nombre_tienda))
  r <- d %>% group_by(anio) %>% summarise(c = sum(transacciones)/sum(flujo), .groups="drop")
  cat(ifelse(excl, "Sin rupturas:  ", "Todas:         "),
      sprintf("2025 %.4f%% -> 2026 %.4f%% (%+.2f pp)\n",
              100*r$c[1], 100*r$c[2], 100*(r$c[2]-r$c[1])))
}
# Esperado: todas +0.96 pp ; sin rupturas +1.13 pp

# ==============================================================================
# 10. SISTEMA DE METAS  (dimension organizacional del diagnostico)
# ==============================================================================
# ---- 10. SISTEMA DE METAS ----------------------------------------------------
meta <- read_excel(RUTA, sheet = "BD Cumplimiento de Meta de Vta")
meta <- meta[, 1:10]
names(meta) <- c("anio","mes","semana","categoria","nro_tienda","tienda",
                 "nombre_tienda","meta","venta","cumplimiento")
meta <- meta %>%
  mutate(across(c(anio, semana, meta, venta), as.numeric),
         nombre_tienda = as.character(nombre_tienda),
         categoria     = as.character(categoria)) %>%
  filter(!is.na(anio), !is.na(meta), categoria == "THE BOX", meta > 0) %>%
  mutate(cump = venta / meta)

cat("Filas de metas THE BOX:", nrow(meta), "\n")
print(head(as.data.frame(meta), 3))   # verificar que nombre_tienda sea texto

meta %>% group_by(anio) %>%
  summarise(n = n(), ponderado = sum(venta)/sum(meta),
            pct_sobre_80 = mean(cump >= 0.80),
            pct_sobre_100 = mean(cump >= 1.00), .groups="drop") %>%
  as.data.frame() %>% print()

v25 <- meta %>% filter(anio == 2025, semana >= 2, semana <= 34) %>%
  group_by(nombre_tienda) %>% summarise(v25 = sum(venta), .groups="drop")
v26 <- meta %>% filter(anio == 2026, semana >= 2, semana <= 34) %>%
  group_by(nombre_tienda) %>% summarise(meta26 = sum(meta), v26 = sum(venta), .groups="drop")
exig <- inner_join(v25, v26, by = "nombre_tienda")
cat(sprintf("\nLa meta 2026 exige %+.1f%% sobre la venta 2025. Se logro %+.1f%%. Cumplimiento %.1f%%\n",
            100*(sum(exig$meta26)/sum(exig$v25) - 1),
            100*(sum(exig$v26)/sum(exig$v25) - 1),
            100*sum(exig$v26)/sum(exig$meta26)))

cm <- meta %>% filter(anio == 2026, semana >= 2, semana <= 34) %>%
  group_by(nombre_tienda) %>% summarise(cumpl = sum(venta)/sum(meta), .groups="drop")
jj <- inner_join(ct %>% select(nombre_tienda, conv), cm, by = "nombre_tienda")
cat("Tiendas cruzadas:", nrow(jj), "\n")
print(cor.test(jj$conv, jj$cumpl))

# ==============================================================================
# 11. IMPACTO ECONOMICO DE LA BRECHA
# ==============================================================================
# Factor de estacionalidad: flujo anual 2025 / flujo de sus semanas 2 a 34.
w25 <- tb %>% filter(anio == 2025) %>% group_by(semana) %>%
  summarise(f = sum(flujo), .groups="drop")
factor_est <- sum(w25$f) / sum(w25$f[w25$semana >= 2 & w25$semana <= 34])
cat("\nFactor de estacionalidad:", round(factor_est, 4), "\n")   # esperado: 1.9009

flujo_26 <- dep %>% filter(anio == 2026, semana >= 2, semana <= 34) %>% pull(flujo) %>% sum()
flujo_anual <- flujo_26 * factor_est
ticket <- sum(sw26$v) / sum(sw26$t)
brecha <- frontera(0.90) - conv_real

cat(sprintf("Flujo anual equivalente: %.0f visitas\n", flujo_anual))
cat(sprintf("Ticket promedio: S/%.2f\n", ticket))
cat(sprintf("Brecha: %.4f pp -> %.0f transacciones -> S/%.2f millones al anio\n",
            100*brecha, flujo_anual*brecha, flujo_anual*brecha*ticket/1e6))
# Esperado: flujo anual 1,697,953 ; ticket S/354.90 ; brecha 1.3025 pp ;
#           22,116 transacciones ; S/7.85 millones al anio

# Sensibilidad de un punto porcentual
cat(sprintf("1 pp sin ajuste estacional: S/%.2f MM | con ajuste: S/%.2f MM\n",
            (flujo_26/33*52)*0.01*ticket/1e6, flujo_anual*0.01*ticket/1e6))


