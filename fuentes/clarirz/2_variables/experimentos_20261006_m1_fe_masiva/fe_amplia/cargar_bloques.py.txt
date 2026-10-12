"""Carga selectiva para ablaciones; NO construye un dataframe gigante por defecto."""
from pathlib import Path
import json
import pandas as pd
from fe_semantica import load_catalog

def cargar_bloques(carpeta,bloques=None,meses=None,incluir_raw=True,features=None):
    root=Path(carpeta);manifest=json.loads((root/'manifest.json').read_text())
    if manifest['status']!='completed':raise ValueError('Ejecución incompleta')
    cat=pd.read_csv(root/'catalogo_features.csv')
    wanted=set(bloques or [])
    if not wanted and not features:raise ValueError('Elegir bloques o features explícitamente')
    unknown=wanted-set(cat.block)
    if unknown:raise ValueError(f'Bloques inexistentes:{sorted(unknown)}')
    sel=cat[cat.block.isin(wanted)] if wanted else cat
    if features is not None:
        unknown_features=set(features)-set(cat.feature)
        if unknown_features:raise ValueError(f'Features inexistentes:{sorted(unknown_features)}')
        sel=sel[sel.feature.isin(features)]
    rawpath=root/('raw.parquet' if incluir_raw else 'claves.parquet')
    df=pd.read_parquet(rawpath)
    mask=df.foto_mes.isin(meses) if meses else pd.Series(True,index=df.index)
    base=df.loc[mask].reset_index(drop=True)
    pieces=[base]
    for rel,features in sel[sel.status.eq('generated')].groupby('file',sort=False):
        part=pd.read_parquet(root/rel,columns=['numero_de_cliente','foto_mes']+features.feature.tolist())
        if not part[['numero_de_cliente','foto_mes']].equals(df[['numero_de_cliente','foto_mes']]):
            raise ValueError(f'Claves desalineadas en {rel}')
        pieces.append(part.loc[mask,features.feature.tolist()].reset_index(drop=True))
    absent=sel.loc[sel.status.eq('all_missing_in_output'),'feature'].tolist()
    if absent:pieces.append(pd.DataFrame(float('nan'),index=base.index,columns=absent))
    result=pd.concat(pieces,axis=1)
    # Orden de schema estable aunque cambie qué columnas son totalmente NA.
    result=result[base.columns.tolist()+sel.feature.tolist()]
    cats=([s['variable'] for s in load_catalog() if s['kind']=='category' and s['variable'] in base] +
          sel.loc[sel.feature_kind.eq('category'),'feature'].tolist())
    # Devuelve claves y tipos; el usuario separa X de claves e y antes de entrenar.
    return result, cats
