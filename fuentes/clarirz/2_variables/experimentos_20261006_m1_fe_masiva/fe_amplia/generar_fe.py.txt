#!/usr/bin/env python3
"""FE amplia para DMEyF: salidas columnares por partes, memoria acotada."""
from __future__ import annotations
import argparse, csv, hashlib, json, platform, time
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from fe_core import Panel, KEYS, FORBIDDEN, generate_coverage
from fe_semantica import load_catalog
from fe_univariadas import generate_univariate
from fe_relaciones import generate_relations

ROOT = Path(__file__).resolve().parent

def sha256_file(path):
    h = hashlib.sha256()
    with open(path,'rb') as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b''):
            h.update(chunk)
    return h.hexdigest()

def validate_config(config):
    for key, minimum in [('lags',1),('windows',2)]:
        values=config.get(key)
        if not isinstance(values,list) or not values or any(type(x)!=int or x<minimum for x in values):
            raise ValueError(f'{key} debe ser una lista no vacía de enteros >= {minimum}')
        if len(set(values))!=len(values):
            raise ValueError(f'{key}: valores repetidos')
    if config.get('storage_dtype','float64') not in {'float32','float64'}:
        raise ValueError('storage_dtype inválido')
    if not 1 <= config.get('features_per_part',32) <= 128:
        raise ValueError('features_per_part debe estar entre 1 y128')
    if config.get('rank_reference','complete_contemporary_month')!='complete_contemporary_month':
        raise ValueError('Este generador implementa ranks del lote contemporáneo completo')

def iter_features(panel, specs, config, blocks=None):
    blocks = set(blocks or [])
    streams=[generate_coverage(panel,config)]
    streams.extend(generate_univariate(panel,spec,config) for spec in specs)
    if config.get('relations',True):
        streams.append(generate_relations(panel,config))
    for stream in streams:
        for name, values, meta in stream:
            if not blocks or meta['block'] in blocks:
                meta.setdefault('feature_kind','numeric')
                if FORBIDDEN.intersection(meta.get('sources',[])):
                    raise ValueError(f'Feature usa fuente prohibida: {name}')
                yield name,values,meta

def generate(input_path, output_path, config, blocks=None, months=None, max_clients=None, variables=None):
    validate_config(config)
    output=Path(output_path)
    # Nunca mezclar una ejecución anterior ni sobrescribir resultados.
    if output.exists() and any(output.iterdir()):
        raise ValueError('La carpeta de salida debe ser nueva o estar vacía')
    output.mkdir(parents=True,exist_ok=True); (output/'features').mkdir(exist_ok=True)
    start=time.time(); manifest={'status':'running','config':config,'input_sha256':sha256_file(input_path),
        'blocks_requested':blocks or 'all','output_months_requested':months or 'all',
        'versions':{'python':platform.python_version(),'pandas':pd.__version__,'numpy':np.__version__,'pyarrow':pa.__version__},
        'target_used_for_features':False,'rank_population':'complete_contemporary_month' if not max_clients else 'diagnostic_client_subset',
        'diagnostic_max_clients':max_clients,'started_at_utc':pd.Timestamp.now(tz='UTC').isoformat()}
    manifest['code_sha256']={p.name:sha256_file(p) for p in ROOT.glob('*.py')}
    def save_manifest():
        tmp=output/'manifest.tmp'; tmp.write_text(json.dumps(manifest,ensure_ascii=False,indent=2));tmp.replace(output/'manifest.json')
    save_manifest()
    try:
        df=pd.read_parquet(input_path)
        input_rows=len(df)
        if max_clients:
            # Determinista y mantiene toda la historia de cada ID escogido.
            ids=np.sort(df.numero_de_cliente.unique())[:max_clients]
            df=df[df.numero_de_cliente.isin(ids)].copy()
        panel=Panel(df,config);del df
        specs=load_catalog()
        actual=set(panel.columns)-FORBIDDEN
        expected={s['variable'] for s in specs}
        if actual != expected:
            raise ValueError(f'Esquema difiere de152predictores: faltan={sorted(expected-actual)}, extras={sorted(actual-expected)}')
        if variables:
            unknown=set(variables)-expected
            if unknown:raise ValueError(f'Variables desconocidas:{sorted(unknown)}')
            specs=[s for s in specs if s['variable'] in variables]
            # Selección univariada explícita no genera relaciones de otras fuentes.
            config={**config,'relations':False};manifest['config']=config
        row_mask=np.isin(panel.month,months) if months else np.ones(panel.n,bool)
        if not row_mask.any():raise ValueError('No hay filas para los meses de salida')
        if months and not set(months).issubset(set(panel.month)):
            raise ValueError('Algún mes de salida no está en la base')
        keys=panel.df.loc[row_mask,KEYS].reset_index(drop=True)
        keys.to_parquet(output/'claves.parquet',index=False)
        raw=[c for c in panel.df if c not in {'clase_ternaria','clase_binaria'}]
        panel.df.loc[row_mask,raw].to_parquet(output/'raw.parquet',index=False)
        if 'clase_ternaria' in panel.df:
            panel.df.loc[row_mask,KEYS+['clase_ternaria']].to_parquet(output/'etiquetas.parquet',index=False)
        catalog=[];buffer={};buffer_rows=[];seen_names=set();parts=[];part_no=0
        dtype=np.dtype(config.get('storage_dtype','float64'))
        def flush():
            nonlocal part_no
            if not buffer:return
            part_no+=1; rel=f'features/parte_{part_no:04d}.parquet'
            arrays={k:pa.array(keys[k].to_numpy()) for k in KEYS}
            arrays.update({k:pa.array(v,from_pandas=True) for k,v in buffer.items()})
            table=pa.table(arrays)
            tmp=output/(rel+'.tmp');pq.write_table(table,tmp,compression='zstd',compression_level=3,row_group_size=65536)
            tmp.replace(output/rel)
            for idx in buffer_rows:catalog[idx]['file']=rel
            parts.append({'file':rel,'n_features':len(buffer),'rows':len(keys),'bytes':(output/rel).stat().st_size})
            buffer.clear();buffer_rows.clear()
        for name,values,meta in iter_features(panel,specs,config,blocks):
            if name in seen_names:raise ValueError(f'Feature duplicada:{name}')
            seen_names.add(name);values=np.asarray(values,dtype=float)
            if values.shape!=(panel.n,):raise ValueError(f'Longitud incorrecta:{name}')
            arr=values[row_mask]
            if np.isinf(arr).any():raise ValueError(f'Inf en {name}')
            finite=np.isfinite(arr);nobs=int(finite.sum())
            entry={'feature':name,**meta,'sources':json.dumps(meta.get('sources',[]),ensure_ascii=False),
                'n_rows':len(arr),'n_observed':nobs,'missing_fraction':1-nobs/len(arr),
                'minimum':float(arr[finite].min()) if nobs else None,'maximum':float(arr[finite].max()) if nobs else None,
                'status':'generated' if nobs else 'all_missing_in_output','file':''}
            # Se registra toda definición; omitir materializar un vector todo NA ahorra espacio.
            catalog.append(entry)
            if nobs:
                arr=arr.astype(dtype,copy=False)
                if np.isinf(arr).any():raise ValueError(f'Overflow al guardar {name}; usar float64')
                buffer[name]=arr;buffer_rows.append(len(catalog)-1)
            if len(buffer)>=config.get('features_per_part',32):flush()
            if len(catalog)%500==0:
                print(f'{len(catalog)} definiciones; {part_no} partes; {time.time()-start:.1f}s',flush=True)
        flush()
        if not catalog:raise ValueError('La selección no produjo features; revisar nombres de bloque')
        cat=pd.DataFrame(catalog);cat.to_csv(output/'catalogo_features.csv',index=False)
        summary=cat.groupby('block').agg(definidas=('feature','size'),materializadas=('status',lambda x:int(x.eq('generated').sum()))).reset_index()
        summary.to_csv(output/'resumen_bloques.csv',index=False)
        pd.DataFrame(specs).to_csv(output/'variables_transformadas.csv',index=False)
        manifest.update(status='completed',input_rows=input_rows,panel_rows=panel.n,output_rows=len(keys),
            input_months=sorted(map(int,np.unique(panel.month))),output_months=sorted(map(int,keys.foto_mes.unique())),
            source_predictors=len(expected),source_predictors_transformed=len(specs),
            features_defined=len(catalog),features_materialized=int(cat.status.eq('generated').sum()),
            all_missing_features=int(cat.status.eq('all_missing_in_output').sum()),parts=parts,
            output_bytes=sum(p['bytes'] for p in parts),elapsed_seconds=round(time.time()-start,3),
            coverage_note='min_history expresa amplitud retrospectiva solicitada; ventanas parciales se acompañan de nobs. No implica disponibilidad en todos los meses de train.',
            warnings=['No es una selección predictiva ni una prueba de ganancia.','No incorporar etiquetas ni claves como predictores.','Las features de tipo category requieren tratamiento nominal al entrenar.','Ranks calculados con población contemporánea, nunca con futuros BAJA+2.'])
        save_manifest();print(json.dumps({k:manifest[k] for k in ['status','panel_rows','output_rows','features_defined','features_materialized','elapsed_seconds']},ensure_ascii=False),flush=True)
        return manifest
    except Exception as exc:
        manifest.update(status='failed',error=f'{type(exc).__name__}: {exc}',elapsed_seconds=time.time()-start)
        save_manifest();raise

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    p.add_argument('--config',type=Path,default=ROOT/'config_amplia.json')
    p.add_argument('--blocks',nargs='+',help='Bloques exactos; omitir para todos')
    p.add_argument('--months',nargs='+',type=int,help='Sólo filtra salida; historia y ranks usan todas las fotos disponibles')
    p.add_argument('--max-clients',type=int,help='Diagnóstico por subconjunto, no ejecución de producción')
    p.add_argument('--variables',nargs='+',help='Prueba univariada selectiva; desactiva relaciones')
    args=p.parse_args()
    if args.max_clients is not None and args.max_clients<1:p.error('--max-clients debe ser positivo')
    cfg=json.loads(args.config.read_text())
    generate(args.input,args.output,cfg,args.blocks,args.months,args.max_clients,args.variables)

if __name__=='__main__':main()
