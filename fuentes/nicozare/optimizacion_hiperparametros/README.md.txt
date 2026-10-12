# Optimización de hiperparámetros

Los valores de `modelos/mejores_hiperparametros.json` (los que usa
`scripts/02_entrenar_ensamble.py` del pipeline de entrega) no se buscan
dentro del pipeline final: salen de esta búsqueda, ya corrida de antemano.
Esta carpeta documenta esa búsqueda para que se pueda revisar o repetir.

## Contenido

- `optimizacion_lgbm.db`: base de datos SQLite de Optuna con los 30 trials
  ya completados (estudio `lgbm_drift_aguinaldo`).
- `buscar_hiperparametros.py`: el script que generó esos 30 trials.
- `resultado_busqueda.json`: se genera al correr el script (no viene
  incluido; ver más abajo cómo verificarlo sin correrlo).

## Método

Optuna (TPE), 30 iteraciones, sobre 5 hiperparámetros de LightGBM
(`num_leaves`, `learning_rate`, `min_data_in_leaf`, `feature_fraction`,
`bagging_fraction`). Cada trial se mide con `lgb.cv` en 5 particiones
(`StratifiedShuffleSplit`, 30% de test), entrenando con todos los meses de
clase conocida excepto el más reciente (ese se reserva para la medición
real del pipeline principal, nunca se usa acá). La métrica de cada trial es
la ganancia real del negocio sobre las probabilidades que superan el umbral
de equilibrio económico, no AUC ni logloss.

## Cómo verificar el resultado sin volver a correr la búsqueda

```bash
uv run --with optuna python -c "
import optuna
st = optuna.load_study(study_name='lgbm_drift_aguinaldo', storage='sqlite:///optimizacion_lgbm.db')
print(st.best_trial.number, st.best_value, st.best_trial.params, st.best_trial.user_attrs)
"
```

El mejor trial (número 26, ganancia CV $1.193.298.333) coincide exactamente
con los valores de `../modelos/mejores_hiperparametros.json`.

## Cómo reproducir la búsqueda desde cero

Requiere haber corrido antes `scripts/01_feature_engineering.py` (necesita
`data/dataset_features.csv`).

```bash
uv run --with duckdb --with lightgbm --with numpy --with optuna --with pandas --with scikit-learn python buscar_hiperparametros.py
```

Como usa `load_if_exists=True` sobre la misma base, si se corre de nuevo
sigue agregando trials al mismo estudio en vez de empezar otro. Para una
búsqueda completamente nueva, borrar o renombrar `optimizacion_lgbm.db`
antes de correrlo.
