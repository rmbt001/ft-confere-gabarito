"""Baixa da Nekt só as saídas da IA de um ou mais CNJs e grava o recorte que o motor de comparação lê.

Diferente do `ingerir.py` do painel, que baixa as tabelas inteiras (cerca de 15 GB), aqui cada tabela é lida
direto do Delta da Nekt com filtro pelos `id_processado` dos CNJs pedidos: uma leitura por tabela para o lote
inteiro (1 CNJ ou 2.000 levam quase o mesmo tempo, alguns minutos).

Grava `.cache/caso_raw__<CNJ>.pkl` no mesmo formato do painel, mais duas tabelas de referência pequenas
(de-para de verbas e catálogo de prompts), atualizadas uma vez por dia.

Uso:
    python baixa_cnj.py 0011628-97.2016.5.15.0093 [outro CNJ ...]
    python baixa_cnj.py --lista cnjs.txt      (um CNJ por linha)
"""
import json
import sys
import time
from pathlib import Path

import pandas as pd
import pyarrow.compute as pc

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI / "codigo" / "src"))
from config_nekt import token_nekt  # noqa: E402

CACHE = AQUI / ".cache"

# mesmas tabelas e apelidos do ingerir.py do painel (o motor de comparação lê por esses apelidos)
RAW = {
    "P1": "ft_lift_tb_resultado_dados_iniciais_ia",
    "DEF": "ft_lift_tb_resultado_infos_decisoes_ia",
    "EDT": "postgres_ft_lift_tb_resultado_editor_decisoes_ia",
    "P10A": "postgres_ft_lift_tb_resultado_calc_principal_mensais_ia",
    "P10B": "postgres_ft_lift_tb_resultado_calc_principal_rescisorias_ia",
    "P9A": "postgres_ft_lift_tb_resultado_calc_quantificador_roteamento_ia",
    "P9B": "postgres_ft_lift_tb_resultado_calc_quantificador_mensais_ia",
    "REFL": "postgres_ft_lift_tb_resultado_calc_reflexos",
    "HOLE": "ft_lift_tb_resultado_hist_salarial_filtro_ia",
    "PROV": "ft_lift_tb_resultado_hist_salarial_proventos_ia",
    "STATUS": "ft_lift_tb_status_processamento",
}
TRUSTED_CNJ = {
    "C10A": "fast_track_calc_principal_mensais_ia_resultados_por_verba_consolidada",
    "C10B": "fast_track_calc_principal_rescisorias_ia_resultados_rescisorias_consolidada",
    "CRAV": "fast_track_calc_reflexos_aviso_previo_consolidada",
    "CRFE": "fast_track_calc_reflexos_ferias_consolidada",
    "CR13": "fast_track_calc_reflexos_decimo_terceiro_consolidada",
    "CRDS": "fast_track_calc_reflexos_dsr_consolidada",
}
REFERENCIA = ["depara_final_verbas_codigo", "ft_lift_tb_agente"]  # tabelas inteiras, pequenas (~3 MB)

_ENG = None


def _dataset(layer, tabela):
    global _ENG
    if _ENG is None:
        import nekt
        nekt.data_access_token = token_nekt(AQUI)
        nekt.engine = "python"
        _ENG = nekt._get_engine()
    from deltalake import DeltaTable
    dp = _ENG._data_provider
    caminho = dp._normalize_path(_ENG._get_table_config(layer, tabela).path)
    return DeltaTable(caminho, storage_options=dp._storage_options).to_pyarrow_dataset()


def _le(layer, tabela, filtro=None):
    for tentativa in (1, 2):  # a Nekt às vezes falha na primeira e passa na segunda
        try:
            ds = _dataset(layer, tabela)
            return (ds.to_table(filter=filtro) if filtro is not None else ds.to_table()).to_pandas()
        except Exception as e:  # noqa: BLE001
            erro = e
            time.sleep(10 * tentativa)
    print(f"[aviso] {layer}/{tabela}: Nekt falhou ({type(erro).__name__}); segue vazio")
    return pd.DataFrame()


def _digitos(c):
    return "".join(ch for ch in str(c) if ch.isdigit())


def _formata(d):
    return f"{d[:7]}-{d[7:9]}.{d[9:13]}.{d[13:14]}.{d[14:16]}.{d[16:20]}"


def referencias():
    CACHE.mkdir(exist_ok=True)
    for t in REFERENCIA:
        fp = CACHE / f"raw__{t}.pkl"
        if fp.exists() and time.time() - fp.stat().st_mtime < 12 * 3600:
            continue
        df = _le("raw", t)
        if len(df):
            df.to_pickle(fp)
    pend = CACHE / "pendentes.json"
    if not pend.exists():
        pend.write_text("[]", encoding="utf-8")


def recorta_lote(cnjs):
    """Lê cada tabela da Nekt UMA vez, filtrada por todos os CNJs do lote, e grava um recorte por CNJ.
    Num lote de 2.000 processos são ~18 leituras filtradas (minutos), e não 2.000 × 18."""
    ds = sorted({_digitos(c) for c in cnjs if len(_digitos(c)) == 20})
    proc = _le("raw", "ft_lift_tb_cnj_processado", pc.field("cnj").isin(ds))
    if not len(proc):
        print("nenhum desses CNJs rodou na esteira")
        return []
    proc = proc.sort_values("criado_em")
    idps = list(proc["id_processado"])
    print(f"{proc['cnj'].nunique()} de {len(ds)} CNJ(s) rodaram na esteira; lendo as tabelas da IA...")
    raw = {a: _le("raw", t, pc.field("id_processado").isin(idps)) for a, t in RAW.items()}
    tru = {a: _le("trusted", t, pc.field("cnj").isin(ds)) for a, t in TRUSTED_CNJ.items()}
    CACHE.mkdir(exist_ok=True)
    feitos = []
    for d in ds:
        m = proc[proc["cnj"].astype(str) == d]
        cnj = _formata(d)
        if not len(m):
            print(f"{cnj}: não rodou na esteira (sem linha na Nekt)")
            continue
        ids = set(m["id_processado"])
        slc = {"cnj": cnj, "cnj_d": d, "idp": m.iloc[-1]["id_processado"], "PROC": m,
               "esteira": {"tipo_calculo": None, "data_validade_calculo": None, "calculo_adequacao": None}}
        for a, df in raw.items():
            slc[a] = df[df["id_processado"].isin(ids)].copy() if "id_processado" in df.columns else pd.DataFrame()
        for a, df in tru.items():  # consolidadas: chave é o cnj; fica só a safra mais recente
            sub = df[df["cnj"].astype(str) == d] if "cnj" in df.columns else pd.DataFrame()
            if len(sub) and "criado_em" in sub.columns:
                sub = sub[sub["criado_em"] == sub["criado_em"].max()]
            slc[a] = sub.copy()
        pd.to_pickle(slc, CACHE / f"caso_raw__{cnj}.pkl")
        feitos.append(cnj)
    print(f"{len(feitos)} recorte(s) gravados em {CACHE}")
    return feitos


def recorta(cnj):
    r = recorta_lote([cnj])
    return r[0] if r else None

def main():
    sys.stdout.reconfigure(encoding="utf-8")
    cnjs = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] != "--lista"]
    if "--lista" in sys.argv:
        cnjs += [l.strip() for l in Path(sys.argv[sys.argv.index("--lista") + 1]).read_text(encoding="utf-8").splitlines() if l.strip()]
    if not cnjs:
        sys.exit(__doc__)
    referencias()
    recorta_lote(cnjs)


if __name__ == "__main__":
    main()
