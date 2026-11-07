"""De-para PJC -> glossário: o código BTxxx de uma verba do PJC pelo nome.

Antes vivia dentro do gerar_telas; saiu para cá (16/10/2026) para a tabela do PJC
(tabela_pjc.py) e o painel usarem a mesma regra.

A tabela de de-para vem do lake (raw.depara_final_verbas_codigo, baixada pelo ingerir
para .cache/). Casa a verba do PJC pelo nome/descrição (coluna `chave`) a um código,
permitindo o casamento PJC × IA por CÓDIGO, não só por nome parecido. `comparavel`=N
marca verbas que não são comparáveis no FT (ex.: reflexo não calculado).
"""
import re
import unicodedata
from pathlib import Path

import pandas as pd

CACHE_DIR = Path(".cache")


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return " ".join(s.upper().replace("'", " ").split())


# Correções locais sobre a tabela de de-para (que é fonte de terceiro, no lake).
# "8ª e 44ª" é a hora extra que excede a jornada normal (8h diárias / 44h
# semanais) = BT089; o de-para manda essas chaves para BT081, que é a 7ª e 8ª
# hora do bancário — outra verba. Todas as chaves irmãs ("ALÉM DA 8ª/44ª",
# "EXCEDENTES DA 8ª", "ACIMA DA 8/44") já apontam BT089 na própria tabela, então
# são estas seis linhas que destoam. Confirmado pela Raíra (set/2026).
# Corrigir na origem (raw.depara_final_verbas_codigo) torna este bloco inócuo,
# e ele pode sair quando a tabela subir corrigida.
DEPARA_FIX = {k: "BT089" for k in [
    "HORAS EXTRAS - 8ª E 44ª",
    "HORAS EXTRAS 8ª E 44ª",
    "HORAS EXTRAS 8ª E 44ª - FIXO",
    "HORAS EXTRAS 8ª E 44ª - VARIAVEL",
    "HORAS EXTRAS 8ª E 44ª - FIXO E REPOUSO SEMANAL REMUNERADO E FERIADO - POS 20/03",
    "HORAS EXTRAS 8ª E 44ª - VARIAVEL E REPOUSO SEMANAL REMUNERADO E FERIADO - POS 20/03",
]}


def _codigo(v):
    s = "" if v is None or (isinstance(v, float) and v != v) else str(v).strip()
    return s if s and s.lower() != "nan" else None


def carregar(cache_dir=None):
    """Lê a tabela do lake e aplica as correções locais. Devolve {chave normalizada: {codigo, comparavel, confianca}}."""
    fp = Path(cache_dir or CACHE_DIR) / "raw__depara_final_verbas_codigo.pkl"
    dep = {}
    if fp.exists():
        try:
            for _, r in pd.read_pickle(fp).iterrows():
                dep[norm(r["chave"])] = {
                    "codigo": _codigo(r.get("codigo_bt")),
                    "comparavel": str(r.get("comparavel") or "S").strip().upper() != "N",
                    "confianca": r.get("confianca"),
                }
        except Exception:
            print("[aviso] de-para não pôde ser lido; matching cai só no fuzzy de nome.")
    n_fix = 0
    for k, cod in DEPARA_FIX.items():
        kn = norm(k)
        e = dep.get(kn)
        if e is None:
            dep[kn] = {"codigo": cod, "comparavel": True, "confianca": "Alta (correção local)"}
            n_fix += 1
        elif e["codigo"] != cod:
            e["codigo"] = cod
            e["confianca"] = "Alta (correção local)"
            n_fix += 1
    if n_fix:
        print(f"[de-para] {n_fix} chave(s) de 'HE 8ª e 44ª' corrigidas p/ BT089 (tabela do lake diz BT081)")
    return dep


DEPARA = carregar()

# Numeração que o calculista põe na frente da verba ("01 - ", "03) ", "1. ").
# Exige o separador, senão comeria o "13" de "13º SALÁRIO".
PREFIXO_NUM = re.compile(r"^\(?\d{1,3}\s*[.)\-–:]+\s*")

# Nomes do PJC que não estão no de-para (ou estão sem código) e cujo código sai
# do próprio nome sem ambiguidade. Revisado pela Raíra em 15/10/2026 (só as de
# confiança alta). Ficam de fora de propósito: "HORAS EXTRAS 50%" e afins sem
# dizer a hora (podem ser BT089, BT081 ou BT001) e as estabilidades (BT069 ×
# BT070 depende do caso). Ancoradas no começo do nome: não pegam reflexo.
REGRAS_NOME = [
    (re.compile(r"^(VERBAS )?RESCISORIAS?\W+AVISO PREVIO$"), "BT041"),
    (re.compile(r"^(VERBAS )?RESCISORIAS?\W+FERIAS \+ 1/3$"), "BT044"),
    (re.compile(r"^(VERBAS )?RESCISORIAS?\W+13º SALARIO$"), "BT038"),
    (re.compile(r"^(VERBAS )?RESCISORIAS?\W+SALDO DE SALARIO$"), "BT058"),
    (re.compile(r"^(ADICIONAL DE )?HORAS? EXTRAS?\b.*\bALEM (DA )?(6ª\W*(E\W+)?)?30ª"), "BT001"),
    (re.compile(r"^(ADICIONAL DE )?HORAS? EXTRAS?\b.*(\bALEM (DA )?8ª|\b07:20ª E 44ª)"), "BT089"),
    (re.compile(r"^(HORAS?( EXTRAS?)?( 50%)?|INTERVALO)\W*(ART\.?|ARTIGO) 384\b"), "BT003"),
    # hora extra em feriado ou domingo é BT011 (Raíra, 16/10/2026: "02. HORAS EXTRAS FERIADO")
    (re.compile(r"^(ADICIONAL DE )?HORAS? EXTRAS?\b.*\b(FERIADOS?|DOMINGOS?)\b"), "BT011"),
    (re.compile(r"^AUX(ILIO)?\.? REFEICAO$"), "BT076"),
    (re.compile(r"^AUX(ILIO)?\.? CESTA ALIMENTACAO$"), "BT078"),
    (re.compile(r"^PLR\b(?!.*\bSOBRE\b)"), "BT028"),
    (re.compile(r"^PPR\b(?!.*\bSOBRE\b)"), "BT029"),
    (re.compile(r"^DOBRA D(AS|E) FERIAS\b"), "BT044"),
]


def pjc_info(nome, depara=None):
    """Info do de-para p/ a verba PJC. Ordem: nome EXATO com código; o mesmo nome
    sem a numeração da frente; regra de nome (REGRAS_NOME). O que não resolver
    devolve a linha exata (pode vir sem código) e cai no fuzzy.
    Retorna {codigo, comparavel, confianca} ou None."""
    dep = DEPARA if depara is None else depara
    k = norm(nome)
    e = dep.get(k)
    if e and (e["codigo"] or not e["comparavel"]):
        return e
    b = PREFIXO_NUM.sub("", k)
    if b != k:
        eb = dep.get(b)
        if eb and eb["codigo"]:
            return eb
    for rx, cod in REGRAS_NOME:
        if rx.search(b):
            return {"codigo": cod, "comparavel": True, "confianca": "Alta (regra de nome)"}
    return e
