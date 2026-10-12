# ENTRENAMIENTO Y PREDICCIONES FINALES 
#  
# ============================================================
# LIBRERÍAS
# ============================================================

import pandas as pd
import numpy as np
from pathlib import Path
import lightgbm as lgb

import os
import re

# ============================================================
# CONFIGURACIÓN
# ============================================================

# DEFINICIONES
semilla = 42
np.random.seed(semilla)
semillas = np.random.choice(1000000, size=50, replace=False).tolist()

# PENDIENTE: confirmar ambos valores antes de la entrega.
# Actualmente se utilizan las primeras 16 semillas generadas con np.random.seed(42).
N_SEMILLAS_FINAL = 16 # TO DO: confirmar si quedan 16 o se completan las 20
N_ENVIOS_FINAL = 10500  # TODO: confirmar el número definitivo de clientes
if not isinstance(N_SEMILLAS_FINAL, int) or not 1 <= N_SEMILLAS_FINAL <= len(semillas):
    raise ValueError(f"N_SEMILLAS_FINAL debe estar entre 1 y {len(semillas)}")
semillas_envio = semillas[:N_SEMILLAS_FINAL]

# Parámetros de guardado/carga
RUN_ID = "modelo_final"
base_path = Path.cwd()
dataset_path = str(base_path / "data") + "/"
resultados_path = str(base_path / "resultados") + "/"
os.makedirs(resultados_path, exist_ok=True)

# ============================================================
# CARGA Y PROCESAMIENTO DE DATA
# ============================================================

# CARGA DATA
dataset_file = 'competencia_01_fev4.parquet'  
data = pd.read_parquet(dataset_path + dataset_file)

# PROCESAMIENTO DE DATA
# Creo target binario
data['clase_binaria12'] = np.where(data['clase_ternaria'].isin(['BAJA+1', 'BAJA+2']), 1, 0)  # continua vs resto
data['clase_binaria2'] = np.where(data['clase_ternaria'].isin(['BAJA+2']), 1, 0)  # baja+2 vs resto

# Rankings con cero fijo y normalización
modo = "sustituir"  # "sustituir" o "anadir"
m_cols = [c for c in data.columns if c.startswith("m")
          and pd.api.types.is_numeric_dtype(data[c])]
 
for col in m_cols:
    valores = data[col]
    max_abs_mes = valores.abs().groupby(data["foto_mes"]).transform("max")
    min_mes = valores.groupby(data["foto_mes"]).transform("min")
    max_mes = valores.groupby(data["foto_mes"]).transform("max")
    divisor = max_abs_mes.where(min_mes < 0, max_mes)
    divisor = divisor.replace(0, np.nan)
    escalada = valores.div(divisor).where(divisor.notna(), valores)
    nombre = f"{col}_norm0"
    if modo == "sustituir":
        data[col] = escalada.astype("float32")
    else:
        data[nombre] = escalada.astype("float32")
if modo == "sustituir":
    data.rename(columns={c: f"{c}_norm0" for c in m_cols}, inplace=True)

print(f"Variables originales procesadas: {len(m_cols)}")
print(f"Modo: {modo} | Columnas finales: {data.shape[1]}")

# Separación entre sub-modelos/sub-datasets
cols_fijas = [
    "numero_de_cliente",
    "foto_mes",
    "clase_ternaria",
    "clase_binaria12",
    "clase_binaria2"
]

# Identificar TODAS las variables históricas
mask_hist = data.columns.str.contains(
    r"(lag|delta)",
    case=False,
    regex=True
)
cols_hist_todas = data.columns[mask_hist].tolist()

# HIST1: quedarse solamente con lag1 y delta1
cols_hist1 = [
    c for c in cols_hist_todas
    if __import__("re").search(r"(lag|delta)1(?!\d)", c, flags=__import__("re").IGNORECASE)
]
data_hist1 = data[cols_fijas + cols_hist1].copy()

# HIST2: quedarse solamente con lag2 y delta2
cols_hist2 = [
    c for c in cols_hist_todas
    if __import__("re").search(r"(lag|delta)2(?!\d)", c, flags=__import__("re").IGNORECASE)
]
data_hist2 = data[cols_fijas + cols_hist2].copy()

# CURRENT: eliminar TODAS las variables históricas
cols_current = [
    c for c in data.columns
    if c not in cols_hist_todas
    and c not in cols_fijas 
]
data_current = data[cols_fijas + cols_current].copy()

print("Original :", data.shape)
print("HIST 1   :", data_hist1.shape)
print("HIST 2   :", data_hist2.shape)
print("CURRENT  :", data_current.shape)

# borro prestamos personales x sugerencia de la cátedra
data_hist1 = data_hist1.loc[
    :,
    ~data_hist1.columns.str.contains("prestamos_personales", case=False)
].copy()
data_hist2 = data_hist2.loc[
    :,
    ~data_hist2.columns.str.contains("prestamos_personales", case=False)
].copy()
data_current = data_current.loc[
    :,
    ~data_current.columns.str.contains("prestamos_personales", case=False)
].copy()

# Separo train/test
mes_train_current = [202103, 202104, 202105]
mes_test_current = 202106
train_data_current = data_current[data_current['foto_mes'].isin(mes_train_current)]
test_data_current = data_current[data_current['foto_mes'] == mes_test_current]

mes_train_hist1 = [202104, 202105] # NO Incluimos marzo porque son puros NANS
mes_test_hist1 = 202106
train_data_hist1 = data_hist1[data_hist1['foto_mes'].isin(mes_train_hist1)]
test_data_hist1 = data_hist1[data_hist1['foto_mes'] == mes_test_hist1]

mes_train_hist2 = [202105] # NO Incluimos ni marzo ni abril porque son puros NANS
mes_test_hist2 = 202106
train_data_hist2 = data_hist2[data_hist2['foto_mes'].isin(mes_train_hist2)]
test_data_hist2 = data_hist2[data_hist2['foto_mes'] == mes_test_hist2]

# Tiro cols 
cols_target = ['clase_ternaria', 'clase_binaria12', 'clase_binaria2']
cols_inutiles = ['foto_mes', 'numero_de_cliente']
cols_a_drop = cols_target + cols_inutiles

# Undersampling + separación X e y + lgb data

# current
df_bajas_current = train_data_current[train_data_current["clase_ternaria"] != "CONTINUA"]
df_continua_current = train_data_current[train_data_current["clase_ternaria"] == "CONTINUA"].sample(
    frac=0.20, random_state=semilla)
train_under_current = pd.concat([df_bajas_current, df_continua_current])

X_train_current = train_under_current.drop(cols_a_drop, axis=1)
y_train_current = train_under_current['clase_binaria12']
 
X_test_current = test_data_current.drop(cols_a_drop, axis=1)
y_test_true_current = np.where(test_data_current['clase_ternaria'] == "BAJA+2", 1, 0) # deberia ser idem de arriba # dejo igual para legibilidad


train_data_lgb_current = lgb.Dataset(X_train_current, label= y_train_current)

# hist 1

df_bajas_hist1 = train_data_hist1[train_data_hist1["clase_ternaria"] != "CONTINUA"]
df_continua_hist1 = train_data_hist1[train_data_hist1["clase_ternaria"] == "CONTINUA"].sample(
    frac=0.20, random_state=semilla)
train_under_hist1 = pd.concat([df_bajas_hist1, df_continua_hist1])

X_train_hist1 = train_under_hist1.drop(cols_a_drop, axis=1)
y_train_hist1 = train_under_hist1['clase_binaria12']

X_test_hist1 = test_data_hist1.drop(cols_a_drop, axis=1)

train_data_lgb_hist1 = lgb.Dataset(X_train_hist1, label= y_train_hist1)

# hist 2
df_bajas_hist2 = train_data_hist2[train_data_hist2["clase_ternaria"] != "CONTINUA"]
df_continua_hist2 = train_data_hist2[train_data_hist2["clase_ternaria"] == "CONTINUA"].sample(
    frac=0.20, random_state=semilla)
train_under_hist2 = pd.concat([df_bajas_hist2, df_continua_hist2])

X_train_hist2 = train_under_hist2.drop(cols_a_drop, axis=1)
y_train_hist2 = train_under_hist2['clase_binaria12']
 
X_test_hist2 = test_data_hist2.drop(cols_a_drop, axis=1)

train_data_lgb_hist2 = lgb.Dataset(X_train_hist2, label= y_train_hist2)

# Funcion de ganancia / elementos de negocio

ganancia_nominal = 2_200_000
efectividad = 0.5
costo_estimulo = 27_500 
ganancia_acierto = ganancia_nominal * efectividad - costo_estimulo 

def ganancia_por_envios(y_pred, y_true, cant_envios): # para optimizar alpha abajo
    orden = np.argsort(y_pred)[::-1]
    y_ordenado = np.asarray(y_true)[orden]
    enviados = y_ordenado[:cant_envios]
    ganancia = np.where(
        enviados == 1,
        ganancia_acierto,
        -costo_estimulo
    )
    return ganancia.sum()

# PARAMETROS OPTIMIZADOS

FIXED_PARAMS = {
        'objective': 'binary',
        'metric': 'custom',
        'boosting_type': 'gbdt',  
        'first_metric_only': True,  
        'boost_from_average': True, 
        'feature_pre_filter': False,  
        'max_bin': 31,  
        'seed': semillas[0],
        'verbose': -1
}
OPT_PARAMS = {'num_leaves': 18,
 'learning_rate': 0.00625238,
 'min_data_in_leaf': 1748,
 'feature_fraction': 0.939774,
 'bagging_fraction': 0.376689,
 'bagging_freq': 1}

PARAMS = {
    **FIXED_PARAMS,
    **OPT_PARAMS,
    "metric": "auc",
}

NUM_ROUNDS = 4928 

# ENTRENAMIENTO SOBRE CONJUNTO DE ENTRENAMIENTO

# CURRENT 
model_current = lgb.train(
    PARAMS,
    train_data_lgb_current,
    num_boost_round=NUM_ROUNDS
)

y_pred_current = model_current.predict(X_test_current)

# HIST 1 
model_hist1 = lgb.train(
    PARAMS,
    train_data_lgb_hist1,
    num_boost_round=NUM_ROUNDS
)
y_pred_hist1 = model_hist1.predict(X_test_hist1)

# HIST 2
model_hist2 = lgb.train(
    PARAMS,
    train_data_lgb_hist2,
    num_boost_round=NUM_ROUNDS
)

y_pred_hist2 = model_hist2.predict(X_test_hist2)


# OPTIMIZACION DE ENSAMBLE Y PUNTOS DE CORTE
# ==========================================
# OPTIMIZAR ENSEMBLE - JUNIO
# ==========================================

pesos = np.arange(0, 1.01, 0.05)
cant_envios = range(8000, 15001, 1000)
resultados_ensemble = []

# Rankings de cada modelo
rank_current = pd.Series(y_pred_current).rank(pct=True).values
rank_hist1 = pd.Series(y_pred_hist1).rank(pct=True).values
rank_hist2 = pd.Series(y_pred_hist2).rank(pct=True).values
for w_current in pesos:
    for w_hist1 in pesos:
        w_hist2 = 1 - w_current - w_hist1
        # solo combinaciones válidas
        if w_hist2 < -1e-10 or w_hist2 > 1 + 1e-10:
            continue
        # --------------------------
        # Ensemble de probabilidades
        # --------------------------
        score_proba = (
            w_current * y_pred_current
            + w_hist1 * y_pred_hist1
            + w_hist2 * y_pred_hist2
        )
        # --------------------------
        # Ensemble de rankings
        # --------------------------
        score_rank = (
            w_current * rank_current
            + w_hist1 * rank_hist1
            + w_hist2 * rank_hist2
        )
        for n in cant_envios:
            ganancia_proba = ganancia_por_envios(
                score_proba,
                y_test_true_current,
                n
            )
            resultados_ensemble.append({
                "tipo": "probas",
                "w_current": w_current,
                "w_hist1": w_hist1,
                "w_hist2": w_hist2,
                "cant_envios": n,
                "ganancia": ganancia_proba
            })
            ganancia_rank = ganancia_por_envios(
                score_rank,
                y_test_true_current,
                n
            )
            resultados_ensemble.append({
                "tipo": "rankings",
                "w_current": w_current,
                "w_hist1": w_hist1,
                "w_hist2": w_hist2,
                "cant_envios": n,
                "ganancia": ganancia_rank
            })
df_ensemble = pd.DataFrame(resultados_ensemble)

# ==========================================
# MEJOR ENSEMBLE
# ==========================================

mejor_proba = df_ensemble[
    df_ensemble["tipo"] == "probas"
].loc[
    lambda x: x["ganancia"].idxmax()
]
mejor_rank = df_ensemble[
    df_ensemble["tipo"] == "rankings"
].loc[
    lambda x: x["ganancia"].idxmax()
]
print("MEJOR ENSEMBLE PROBAS")
print(mejor_proba)
print("\nMEJOR ENSEMBLE RANKINGS")
print(mejor_rank)

# ==========================================
# Pesos del mejor ensemble de 3 modelos
# ==========================================

w_current_proba = mejor_proba["w_current"]
w_hist1_proba = mejor_proba["w_hist1"]
w_hist2_proba = mejor_proba["w_hist2"]
w_current_rank = mejor_rank["w_current"]
w_hist1_rank = mejor_rank["w_hist1"]
w_hist2_rank = mejor_rank["w_hist2"]


# ==========================================
# Entrenamiento completo y creación de archivos para la entrega
# ==========================================

# ==========================================
# Data para entrega   
# ==========================================
# CURRENT

train_data_marzo_junio_current = data_current[data_current['foto_mes'].isin([202103, 202104, 202105, 202106])]
test_data_agosto_current = data_current[data_current['foto_mes'] == 202108]
X_train_marzo_junio_current = train_data_marzo_junio_current.drop(cols_a_drop, axis=1)
y_train_marzo_junio_current = train_data_marzo_junio_current['clase_binaria12']
train_data_lgb_current_final = lgb.Dataset(X_train_marzo_junio_current, label=y_train_marzo_junio_current)
X_agosto_current = test_data_agosto_current.drop(cols_a_drop, axis=1)
numero_cliente_agosto_current = test_data_agosto_current["numero_de_cliente"]

# HIST 1
train_data_abril_junio_hist1 = data_hist1[data_hist1['foto_mes'].isin([202104, 202105, 202106])]
test_data_agosto_hist1 = data_hist1[data_hist1['foto_mes'] == 202108]
X_train_abril_junio_hist1 = train_data_abril_junio_hist1.drop(cols_a_drop, axis=1)
y_train_abril_junio_hist1 = train_data_abril_junio_hist1['clase_binaria12']
train_data_lgb_hist_final1 = lgb.Dataset(X_train_abril_junio_hist1, label=y_train_abril_junio_hist1)
X_agosto_hist1 = test_data_agosto_hist1.drop(cols_a_drop, axis=1)
numero_cliente_agosto_hist1 = test_data_agosto_hist1["numero_de_cliente"]

# HIST 2
train_data_mayo_junio_hist2 = data_hist2[data_hist2['foto_mes'].isin([202105, 202106])]
test_data_agosto_hist2 = data_hist2[data_hist2['foto_mes'] == 202108]
X_train_mayo_junio_hist2 = train_data_mayo_junio_hist2.drop(cols_a_drop, axis=1)
y_train_mayo_junio_hist2 = train_data_mayo_junio_hist2['clase_binaria12']
train_data_lgb_hist_final2 = lgb.Dataset(X_train_mayo_junio_hist2, label=y_train_mayo_junio_hist2)
X_agosto_hist2 = test_data_agosto_hist2.drop(cols_a_drop, axis=1)
numero_cliente_agosto_hist2 = test_data_agosto_hist2["numero_de_cliente"]

# ============================================================
# CHEQUEO: LOS CLIENTES DE AGOSTO COINCIDEN
# ============================================================
assert np.array_equal(
    numero_cliente_agosto_current.values,
    numero_cliente_agosto_hist1.values
), "ERROR: CURRENT y HIST1 no tienen los mismos clientes en el mismo orden."
assert np.array_equal(
    numero_cliente_agosto_current.values,
    numero_cliente_agosto_hist2.values
), "ERROR: CURRENT y HIST2 no tienen los mismos clientes en el mismo orden."
print(
    f"Clientes agosto: {len(numero_cliente_agosto_current)}"
)


# Los envíos se guardan en resultados/ (sin subcarpetas).
# ============================================================
# PARAMETROS
# ============================================================
base_params_current = model_current.params.copy()
model_best_iter_current = model_current.current_iteration()
base_params_hist1 = model_hist1.params.copy()
model_best_iter_hist1 = model_hist1.current_iteration()
base_params_hist2 = model_hist2.params.copy()
model_best_iter_hist2 = model_hist2.current_iteration()

# ============================================================
# LOOP DE SEMILLAS
# ============================================================
# Control de avance: una semilla completa no se repite.
# Se guardan rankings Parquet por semilla; los CSV se generan solo al final. 
checkpoint_path = os.path.join(resultados_path, f"{RUN_ID}_semillas_completadas.txt")
semillas_completadas = set()

if os.path.exists(checkpoint_path):
    with open(checkpoint_path, "r", encoding="utf-8") as f:
        semillas_completadas = {int(x.strip()) for x in f if x.strip()}
for seed in semillas_envio:
    if seed in semillas_completadas:
        archivos_semilla = [
            Path(resultados_path) / f"{RUN_ID}_{tipo}_seed_{seed}.parquet"
            for tipo in ("current", "hist1", "hist2", "ensemble_proba", "ensemble_rank")
        ]
        if all(ruta.exists() for ruta in archivos_semilla):
            print(f"Semilla {seed}: ya completada, se omite")
            continue
        print(f"Semilla {seed}: checkpoint incompleto, se vuelve a ejecutar")

    print(f"\n========== SEMILLA {seed} ==========")

    params_current = base_params_current.copy()
    params_current["seed"] = seed
    params_hist1 = base_params_hist1.copy()
    params_hist1["seed"] = seed
    params_hist2 = base_params_hist2.copy()
    params_hist2["seed"] = seed

    # --------------------------------------------------------
    # CURRENT
    # --------------------------------------------------------

    modelo_current = lgb.train(
        params_current,
        train_data_lgb_current_final,
        num_boost_round=model_best_iter_current
    )
    proba_current = modelo_current.predict(X_agosto_current)
    
    # --------------------------------------------------------
    # HIST 1
    # --------------------------------------------------------
    
    modelo_hist1 = lgb.train(
        params_hist1,
        train_data_lgb_hist_final1,
        num_boost_round=model_best_iter_hist1
    )
    proba_hist1 = modelo_hist1.predict(X_agosto_hist1)
    
    # --------------------------------------------------------
    # HIST 2
    # --------------------------------------------------------
    
    modelo_hist2 = lgb.train(
        params_hist2,
        train_data_lgb_hist_final2,
        num_boost_round=model_best_iter_hist2
    )
    proba_hist2 = modelo_hist2.predict(X_agosto_hist2)
    
    # --------------------------------------------------------
    # ENSEMBLE PROBABILIDADES
    # --------------------------------------------------------
    
    score_ensemble_proba = (
        w_current_proba * proba_current
        + w_hist1_proba * proba_hist1
        + w_hist2_proba * proba_hist2
    )
    
    # --------------------------------------------------------
    # ENSEMBLE RANKINGS
    # --------------------------------------------------------
    
    rank_current = (
        pd.Series(proba_current)
        .rank(pct=True)
        .values
    )
    rank_hist1 = (
        pd.Series(proba_hist1)
        .rank(pct=True)
        .values
    )
    rank_hist2 = (
        pd.Series(proba_hist2)
        .rank(pct=True)
        .values
    )
    score_ensemble_rank = (
        w_current_rank * rank_current
        + w_hist1_rank * rank_hist1
        + w_hist2_rank * rank_hist2
    )
    
    # ========================================================
    # RANKINGS
    # ========================================================
    
    ranking_current = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_current.values,
        "proba": proba_current
    }).sort_values(
        "proba",
        ascending=False
    )
    ranking_hist1 = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_hist1.values,
        "proba": proba_hist1
    }).sort_values(
        "proba",
        ascending=False
    )
    ranking_hist2 = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_hist2.values,
        "proba": proba_hist2
    }).sort_values(
        "proba",
        ascending=False
    )
    ranking_proba = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_current.values,
        "score": score_ensemble_proba
    }).sort_values(
        "score",
        ascending=False
    )
    ranking_rank = pd.DataFrame({
        "numero_de_cliente": numero_cliente_agosto_current.values,
        "score": score_ensemble_rank
    }).sort_values(
        "score",
        ascending=False
    )
    # ========================================================
    # GUARDAR RANKINGS
    # ========================================================
    
    ranking_current.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_current_seed_{seed}.parquet"
        ),
        index=False
    )
    ranking_hist1.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_hist1_seed_{seed}.parquet"
        ),
        index=False
    )
    ranking_hist2.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_hist2_seed_{seed}.parquet"
        ),
        index=False
    )
    ranking_proba.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_ensemble_proba_seed_{seed}.parquet"
        ),
        index=False
    )
    ranking_rank.to_parquet(
        os.path.join(
            resultados_path,
            f"{RUN_ID}_ensemble_rank_seed_{seed}.parquet"
        ),
        index=False
    )
    
    # No se generan CSV individuales: los rankings Parquet se combinan al final.

    # Registrar solamente después de guardar todos los resultados de la semilla.
    with open(checkpoint_path, "a", encoding="utf-8") as f:
        f.write(f"{seed}\n")
        f.flush()
        os.fsync(f.fileno())
    print("OK")


# ============================================================
# ENSAMBLE MULTISEMILLA FINAL
# ============================================================
# Los archivos por semilla se generan arriba y se recuperan por su nombre exacto.
# La combinación es el promedio de los rankings percentiles por semilla,
# siguiendo el criterio del bloque de ensamble multisemilla original.

def ejecutar_ensemble_semillas():
    if N_ENVIOS_FINAL is None:
        print("PENDIENTE: definir N_ENVIOS_FINAL; no se generan CSVs finales.")
        return
    if not isinstance(N_ENVIOS_FINAL, int) or isinstance(N_ENVIOS_FINAL, bool) or N_ENVIOS_FINAL <= 0:
        raise ValueError("N_ENVIOS_FINAL debe ser un entero positivo")

    for metodo in ("proba", "rank"):
        partes = []
        for seed in semillas_envio:
            ruta = Path(resultados_path) / (
                f"{RUN_ID}_ensemble_{metodo}_seed_{seed}.parquet"
            )
            if not ruta.exists():
                raise FileNotFoundError(
                    f"Falta la predicción de la semilla {seed}: {ruta}. "
                    "No se generará un ensamble con menos semillas que las configuradas."
                )
            df = pd.read_parquet(ruta)
            if not {"numero_de_cliente", "score"}.issubset(df.columns):
                raise ValueError(f"Faltan columnas en {ruta}")
            if df["numero_de_cliente"].duplicated().any():
                raise ValueError(f"Clientes duplicados en {ruta}")
            partes.append(
                df[["numero_de_cliente"]].assign(
                    **{f"s{seed}": df["score"].rank(pct=True)}
                )
            )

        combinado = partes[0]
        for parte in partes[1:]:
            combinado = combinado.merge(
                parte, on="numero_de_cliente", how="inner", validate="one_to_one"
            )
        if len(combinado) != len(partes[0]) or any(
            len(combinado) != len(parte) for parte in partes
        ):
            raise ValueError("Las semillas no contienen exactamente los mismos clientes")

        columnas_semillas = [f"s{seed}" for seed in semillas_envio]
        combinado["score"] = combinado[columnas_semillas].mean(axis=1)
        ranking = combinado.sort_values(
            ["score", "numero_de_cliente"], ascending=[False, True]
        )
        if N_ENVIOS_FINAL > len(ranking):
            raise ValueError("N_ENVIOS_FINAL excede la cantidad de clientes")

        salida = Path(resultados_path) / (
            f"multisemilla_ensemble_{metodo}_{N_ENVIOS_FINAL}_nsemillas_{len(partes)}.csv"
        )
        ranking["numero_de_cliente"].head(N_ENVIOS_FINAL).astype("int64").to_csv(
            salida, index=False, header=False
        )
        print("Generado:", salida)


ejecutar_ensemble_semillas()
