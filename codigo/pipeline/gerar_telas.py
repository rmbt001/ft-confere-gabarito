"""Gera o app HTML de validação (LIFT x PJC), com abas por CNJ.

Uso: python gerar_telas.py [CNJ ...]
Saída: saidas/validacao_calculos.html
"""
import ast
import calendar
import json
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from datetime import date
from pathlib import Path

import pandas as pd

sys.path.append("codigo/src")
from comparar import score, normaliza  # noqa: E402
from parse_pjc import parse_pjc, parse_cabecalho_only, parse_resumo_only  # noqa: E402
from parse_pjc_xml import parse_pjc_xml   # noqa: E402
# As tres medidas de acuracia vivem em src/medidas.py, nao mais soltas aqui.
# Neste commit o import existe e nenhuma chamada foi trocada ainda, de proposito:
# assim ele prova que o modulo carrega pelo mesmo caminho dos outros parsers, e o
# JSON regerado sai byte-a-byte igual ao de antes. A troca das contas vem no
# commit seguinte, isolada, para que um numero diferente tenha uma causa so.
from medidas import assertividade, acuracia_global, acuracia_verba, compensacao  # noqa: E402,F401
from confianca import score_confianca  # noqa: E402

_norm = normaliza
_toks_mod = lambda n: {t for t in normaliza(n).split() if len(t) >= 4}

# Regra de status do Fast-Track (doc "Classificação de status do Fast-Track", 14/10/2026;
# adotada nos painéis de homologação e produção em 15/10/2026 a pedido da Raíra). A antiga
# lista fixa de 19-20 códigos inelegíveis deixou de existir.
# Cálculo crítico: bloqueia SEMPRE (FT-NaoAptoVerba), com a verba calculada ou não.
INELEGIVEIS = {"BT012", "BT013", "BT022", "BT045", "BT048", "BT059"}
# Não relevantes: sem valor, não bloqueiam (no FT, calculadas também ficam fora do total).
NAO_RELEVANTES = {"BT043", "BT062", "BT071", "BT079"}
# BT063 (honorários do advogado do reclamante) tem etapa própria de cálculo que o painel
# não lê; como na simulação do doc, é tratado como calculado e não bloqueia.
NAO_BLOQUEIA_SEM_VALOR = NAO_RELEVANTES | {"BT063"}

# Curadoria: casos cujo PJC de referência apurou HE por CARTÃO DE PONTO com
# oscilação extrema mês a mês (CV >= 0,50, >= 6 meses e >= 5 valores de horas
# distintos — descarta degrau de jornada fixa). O automatizado não reproduz
# cartão com confiança, então saem de "apto" para a categoria própria "Provável
# apuração via cartão". Evidência em saidas/analises/he_cartao_pjc.csv. Chave = só dígitos.
CARTAO_PROVAVEL = {"".join(ch for ch in c if ch.isdigit()) for c in (
    "0100640-65.2024.5.01.0018",
    "0010633-04.2020.5.15.0042",
    "0000002-54.2015.5.05.0462",
    "1000464-51.2021.5.02.0402",
    "0100902-09.2022.5.01.0075",
    "0010001-52.2019.5.03.0072",
    "0024666-24.2021.5.24.0006",
)}

# Curadoria: gabarito com o CÁLCULO errado. O processo tem mais de um cálculo no
# PJe-Calc e o que subiu para casos/<CNJ>/ não é o de referência. Chave = CNJ,
# valor = id do cálculo CERTO (raiz <Calculo><id> do .pjc). Enquanto o arquivo
# local tiver outro id, o caso sai da régua como "gabarito a corrigir"; quando o
# .pjc certo subir, o id bate e o caso volta sozinho. (O PJC de OUTRO processo
# é pego sem curadoria: o CNJ do .pjc não bate com o do caso.)
GABARITO_ID_CALCULO = {
    "0012750-14.2020.5.15.0059": "551",   # subiu o 514 (Raíra, 13/10/2026)
}

# Curadoria: .pjc e PDF da pasta são cálculos diferentes e o PDF foi conferido como o
# gabarito (o .pjc era parcial). Nesses vale o PDF; nos demais casos com os dois ids
# diferentes, o caso sai da régua como "gabarito a corrigir" (Raíra, 28/10/2026).
GABARITO_PDF_CONFIRMADO = {
    "1000166-88.2021.5.02.0263",   # .pjc 3997 só "dez dias de férias"; PDF 2166 completo
    "0000230-08.2018.5.09.0011",
    "0020106-92.2024.5.04.0102",
    "0000347-35.2024.5.11.0010",   # 30/10: .pjc 744 antigo; PDF 1396 (13/08/2026) enviado pela Raíra
    # 30/10: PDFs achados pela Raíra para a alta < 50% sem PDF
    "1001419-63.2024.5.02.0342", "0000045-68.2021.5.09.0009", "0000774-06.2019.5.05.0194", "0020486-56.2022.5.04.0791",
}

# De-para código de glossário (BT) -> nome canônico da verba. Carregado do
# glossario_bt.json (fonte oficial do de-para PJC↔IA); usado para (1) resolver
# nome quando o P4 devolve o código cru (ex.: "BT052") e (2) exibir o código na
# comparação verba a verba. Fallback mínimo embutido se o arquivo não estiver lá.
def _carrega_glossario():
    for p in (Path("../gerador_pjc/referencia/glossario_bt.json"),  # fonte canônica
              Path("codigo/referencia/glossario_bt.json"),                 # cópia do pacote
              Path("gerador_pjc/referencia/glossario_bt.json")):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            return {k: v for k, v in d.items() if not k.startswith("_")}
        except Exception:
            continue
    # Antes caía num fallback de UMA verba (contra as ~90 do arquivo) e seguia
    # em silêncio: o painel inteiro saía com nome e código de verba errados, sem
    # nada na tela indicando isso. Numa máquina sem o gerador_pjc ao lado (é o
    # caso de qualquer instalação nova) essa era a falha mais provável de todas.
    raise SystemExit(
        "[ERRO] glossario_bt.json não encontrado.\n"
        "  Procurei em ../gerador_pjc/referencia/ e em referencia/.\n"
        "  Sem ele os nomes e códigos das verbas saem errados no painel inteiro,\n"
        "  então paro aqui em vez de gerar um relatório enganoso."
    )


GLOSSARIO_NOME = _carrega_glossario()

# Teto de indenização por dano no Fast Track: R$5.000. Usado só na COMPARAÇÃO —
# quando a IA aplicou o teto, o PJC (que traz o valor cheio do juiz) é capado
# no mesmo teto p/ a acurácia não cair por divergência de política. Mesmas verbas
# da esteira (TetoDanosMoraisStrategy, CODIGOS_VERBA_TETO_DANOS): dano moral,
# assédio moral e acidente do trabalho.
TETO_DANO_MORAL = 5000.0
CODIGOS_TETO_DANO = ("BT052", "BT050", "BT040")


def _he_grupo(n):
    """Classifica uma verba de horas extras pelo 'tipo' de HE, p/ não fundir linhas
    distintas. O art. 384 é pago a 100% — então PJC 'HE C/ 100%' é o par do 384 da
    IA, não da HE 50% regular. Devolve '384_100' | '50' | 'he' (genérica) | None."""
    if "hora" not in n or "extra" not in n:
        return None
    if "384" in n or "100" in n or "cem por cento" in n:
        return "384_100"          # 384 vem antes: a verba 384 da IA tb tem '50' no nome
    if "50" in n or "cinquenta" in n:
        return "50"
    return "he"


# nome genérico de HE no PJC (já normalizado): por regra de negócio é o BT089, BT081 se não houver
_GENERICO_HE = {"horas extras 50", "horas extras", "adicional de horas extras 50",
                "horas extras 60", "horas extras 70", "hora extra 50", "hora extra"}


def _incompat(a, b):
    """Veta match entre verbas que compartilham tokens mas são conceitos distintos:
    - intrajornada × interjornada (só diferem numa letra);
    - horas extras 50% regular × 384/100% (o PJC chama o art. 384 de 'HE C/ 100%';
      sem isso o matcher funde as duas linhas de HE numa verba só)."""
    na, nb = normaliza(a or ""), normaliza(b or "")
    intra = lambda s: "intrajornada" in s
    inter = lambda s: "interjornada" in s or "entrejornada" in s
    if (intra(na) and inter(nb)) or (inter(na) and intra(nb)):
        return True
    ga, gb = _he_grupo(na), _he_grupo(nb)
    if ga and gb and {ga, gb} == {"50", "384_100"}:
        return True   # HE 50% regular × HE 100%/384 → verbas distintas
    if _natureza_conflita(a, b):
        return True   # dano moral × dano material etc.: indenizações distintas
    # 07/11/2026 (Raíra): vetos de família que o fuzzy atravessava pelo token comum
    # ("horas extras", "salario", "multa"); 15 processos com par trocado no painel 03/11.
    # - intervalo × hora extra que não fala de intervalo (0100275-60: "Horas Extras -
    #   intervalo intrajornada" da IA casava "HORAS EXTRAS 50%" do PJC); o art. 384 nos
    #   dois lados não veta ("Intervalo do Artigo 384" × "HORAS EXTRAS ART. 384").
    iv = lambda s: any(k in s for k in ("intervalo", "intrajornada", "interjornada", "entrejornada"))
    if iv(na) != iv(nb) and (ga or gb) and not ("384" in na and "384" in nb):
        return True
    # - multa do art. 467 × art. 477
    arts = lambda s: set(re.findall(r"\b(467|477)\b", s))
    if arts(na) and arts(nb) and not (arts(na) & arts(nb)):
        return True
    # - saldo de salário × 13º (0001049-11: o saldo da IA casava "13º SALÁRIO PROPORCIONAL")
    d13 = lambda s: bool(re.search(r"\b13\b|13o|decimo|natalin", s))
    sal = lambda s: "saldo" in s or "retido" in s
    if (sal(na) and d13(nb) and not sal(nb)) or (sal(nb) and d13(na) and not sal(na)):
        return True
    # - salário por fora × saldo, retido, 13º, férias, aviso (0100275-60: casava pelo token "salario")
    pf = lambda s: bool(_RE_POR_FORA.search(s))
    rs = lambda s: sal(s) or d13(s) or bool(re.search(r"\b(ferias|aviso)\b", s))
    if (pf(na) and rs(nb) and not pf(nb)) or (pf(nb) and rs(na) and not pf(na)):
        return True
    return False


# ---- natureza das indenizações (dano moral × material × acidente) ----------
# O PJC nomeia a indenização do seu jeito ("02. DANO MORAL", "INDENIZAÇÃO POR
# DANO MORAL") e o matcher por token não casava com "Indenização por Danos
# Morais" (danos/morais × dano/moral) — a IA ficava "só IA" com R$ 5.000 e o PJC
# "só PJC" com o valor cheio, sem o teto. E o contrário: o token "indenização",
# comum a todas, casava dano moral com DANO MATERIAL (0001517: R$ 189 mil de erro
# só de pareamento). A natureza lida do nome resolve as duas coisas: casa quem
# tem a mesma e veta quem tem natureza diferente.
def _natureza(nome):
    """Conjunto de naturezas de indenização que o nome indica (vazio = nenhuma)."""
    n = normaliza(nome or "")
    t = set()
    if re.search(r"\bdanos? materia(?:l|is)\b|lucros? cessantes|pensao|pensionamento", n):
        t.add("material")
    if re.search(r"\bdanos? morai?s?\b|\bmoral\b|\bmorais\b", n) and "assedio" not in n:
        t.add("moral")
    if "assedio" in n:
        t.add("assedio")
    if re.search(r"\bestetic", n):
        t.add("estetico")
    # doença do trabalho/ocupacional é equiparada a acidente; a ESTABILIDADE
    # acidentária (BT070, "indenização estabilitária") é outra verba
    if re.search(r"\bacidente|\bdoenca (?:do trabalho|ocupacional|profissional)", n) and "estabil" not in n:
        t.add("acidente")
    return t


def _natureza_conflita(a, b):
    """Os dois nomes indicam indenizações de natureza diferente? Só veta quando os
    DOIS lados têm natureza lida e elas não se cruzam — nome sem natureza não veta."""
    na, nb = _natureza(a), _natureza(b)
    return bool(na and nb and not (na & nb))


# natureza que cada código de teto aceita, em ordem de preferência: a 1ª é a
# própria; a 2ª é a vizinha (assédio moral é dano moral; o PJC às vezes lança o
# acidente como "dano moral decorrente de acidente").
_NAT_TETO = {"BT052": ("moral", "assedio"), "BT050": ("assedio", "moral"), "BT040": ("acidente",)}


def _erro_execucao(idp):
    """A execução `idp` parou com ERRO antes do cálculo? Devolve {etapa, motivo,
    quando} ou None.

    Sem isto, o caso cuja execução morreu (ex.: CARTAO_PONTO "Jornada mista
    documental e fixada não é apurável", ou erro do provedor de LLM no
    INFOS_DECISOES) não tinha P10 e aparecia como APTO com total IA = 0 e 0% de
    assertividade, puxando a mediana para baixo por um cálculo que não existiu.
    Dispara quando a execução NÃO tem P10a/P10b e tem trilha de status. Se a última
    linha é ERRO, devolve o erro; se não é (execução parada ou ainda em andamento,
    sem P10), também conta como FT Travado (Raíra, 15/10/2026: 0000387-97.2025.5.07.0008,
    parado no GLOSSARIO sem erro, aparecia como apto com IA = 0)."""
    if any(len(df) and len(_linhas(df, "id_processado", idp)) for df in (P10A, P10B)):
        return None
    if not len(STATUS) or not {"id_processado", "status", "criado_em"} <= set(STATUS.columns):
        return None
    sub = _linhas(STATUS, "id_processado", idp).sort_values("criado_em")
    if not len(sub):
        return None
    r = sub.iloc[-1]
    mot = r.get("motivo")
    mot = None if (mot is None or (isinstance(mot, float) and mot != mot)) else str(mot)
    if str(r.get("status")).upper() != "ERRO":
        mot = f"sem P10 e sem erro registrado (última etapa {str(r.get('status')).lower()})"
    return {"etapa": str(r.get("etapa") or "?"), "motivo": mot,
            "quando": str(r.get("criado_em"))[:19]}

def _descobre_casos():
    base = Path("casos")
    if not base.exists():
        return []
    # caso vale se tem .pjc nativo OU o PDF (a fonte é resolvida por caso)
    return sorted(d.name for d in base.iterdir()
                  if (d / "pjc.pjc").exists() or (d / "pjc.pdf").exists())


def _descobre_pendentes():
    """Casos que rodaram (chegaram ao P10) e ainda NÃO têm cálculo de referência —
    a lista que o ingerir.py computou em `.cache/pendentes.json`. Inclui os de
    total ZERO/NEGATIVO (`zerado=True`), que a tela separa num bloco próprio:
    mesma origem, problema diferente — ali o cálculo não respondeu, não é o
    gabarito que falta.

    Eles entram no painel mesmo sem PJC: o lado LIFT (verbas, aptidão, P4/P9/P10)
    é analisável sozinho; o que não existe é o gabarito — então os campos do PJC
    e a acurácia ficam VAZIOS, e o caso fica fora de todas as médias.

    Dois filtros: só quem já tem recorte no cache (senão o run só imprimiria aviso
    de faltante) e só quem NÃO tem referência nenhuma — a lista é montada pelo PDF
    (para o auto_pjc baixá-lo), então pode trazer caso que já tem o .pjc nativo."""
    fp = Path(".cache/pendentes.json")
    if not fp.exists():
        return []
    try:
        pend = json.loads(fp.read_text(encoding="utf-8"))
    except Exception:
        return []
    com_ref = set(_descobre_casos())
    return [p["cnj"] for p in pend
            if p.get("cnj") and p["cnj"] not in com_ref
            and Path(f".cache/caso_raw__{p['cnj']}.pkl").exists()]


# "@arquivo" = um CNJ por linha: listas de centenas de processos estouram o limite
# da linha de comando do Windows (WinError 206, painel de 23/10, 28/10/2026)
sys.argv[1:] = [c for a in sys.argv[1:]
                for c in (Path(a[1:]).read_text(encoding="utf-8").split() if a.startswith("@") else [a])]

# Sem argumentos: casos com cálculo de referência (.pjc ou PDF) + os pendentes de PJC.
CNJS = ([a for a in sys.argv[1:] if not a.startswith("--")]
        or (_descobre_casos() + _descobre_pendentes())
        or ["0012965-92.2016.5.15.0135"])


def _parse(v):
    if isinstance(v, float) and v != v:
        return None   # célula vazia (NaN) em linha incompleta
    if not isinstance(v, str):
        return v
    try:
        return json.loads(v)
    except Exception:
        return ast.literal_eval(v)


def _comp(c):
    if not isinstance(c, str):   # competência vazia (NaN, float) em linha incompleta
        return None
    if not c:
        return None
    if "/" in c:
        m, a = c.split("/")
        return f"{a}-{m}"
    return c


def _rotulo_pjc(nome):
    u = nome.upper()
    if "VARI" in u:
        return "Variável"
    if "FIXA" in u:
        return "Fixa"
    return nome.split(" - ")[0].title()


def _prox(a, b, tol=0.01):
    if a is None or b is None:
        return None
    m = max(abs(a), abs(b)) or 1
    return abs(a - b) / m < tol


def _brl(x):
    if x is None:
        return "—"
    return "R$ " + f"{x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _p4_de(deferidas, vid):
    """Entrada de deferimento (P4) da verba, pelo índice posicional verba_0N."""
    try:
        d = deferidas[int(vid.split("_")[1]) - 1]
    except (ValueError, IndexError):
        return None
    # o deferimento não traz campo "criterio"; o critério vinculante vive em "jornada_especifica"
    crit = d.get("criterio") or d.get("jornada_especifica")
    crit = crit if isinstance(crit, str) else " ".join(crit or [])
    dn = d.get("dados_necessarios_calculo")
    dn = dn if isinstance(dn, str) else " ".join(dn or [])
    blob = f"{crit} {d.get('contexto') or ''} {d.get('explicacao') or ''}".lower()
    return {"contexto": d.get("contexto"), "criterio": crit,
            "explicacao": d.get("explicacao"), "fonte_documento": d.get("fonte_documento"),
            "codigo_glossario": d.get("codigo_glossario"), "dados_necessarios": dn,
            "menciona_variavel": ("variável" in blob or "variavel" in blob),
            "menciona_s340": ("súmula 340" in blob or "sumula 340" in blob or "súm. 340" in blob),
            "depende_documento": any(t in dn.lower() for t in ["cartão de ponto", "cartao de ponto", "ficha financeira", "holerite", "documento"]),
            "_raw": d}  # saída integral do P4 (deferimento / infos_decisoes), crua e sem edição — exibida na tela


def _p4_por_cod(deferidas, cod):
    """Deferimento (P4) da verba pelo CÓDIGO de glossário — p/ rescisórias/valor-fixo,
    que não têm id_verba posicional (verba_0N). Casa o 1º deferido de mesmo código;
    assim o bloco do P4 aparece nessas verbas também (o mínimo p/ ver o que o juiz decidiu)."""
    if not cod:
        return None
    for i, d in enumerate(deferidas):
        if d.get("codigo_glossario") == cod:
            return _p4_de(deferidas, f"verba_{i + 1}")
    return None


# ---- cache local (PJC parseado por caso) -----------------------------------
_CACHE_DIR = Path(".cache")


# versão do formato devolvido pelos parsers do PJC (bump a cada campo novo)
_PJC_SCHEMA = "v11"  # v11: .pjc de outro cálculo que o PDF -> fora da régua, salvo PDF conferido; v10: .pjc de outro cálculo que o PDF -> vale o PDF; id do cálculo no .pjc novo; fora do principal no PDF (28/10); v9: volta a opção "zerar valor negativo" de cada verba, como o PDF (16/10); v8: todos os blocos de multas (16/10); v7: verbas aninhadas no .pjc (15/10); v6: sem "zerar valor negativo" (15/10); v5: bloco de multas + id do cálculo; v4: fora do principal


def _parse_pjc_cached(cnj):
    """Cálculo de referência do caso, parseado e cacheado (por mtime -> invalida
    sozinho se o arquivo for re-baixado).

    FONTE PRIMÁRIA = .pjc nativo (parse_pjc_xml): estruturado, exato, imune a
    layout — resgata casos que o PDF perde e corrige a duplicação do PDF. Cai pro
    PDF (parse_pjc) só quando não há .pjc. Header híbrido: quando o .pjc é a
    fonte mas tem campos de cabeçalho nulos, completa com o cabeçalho do PDF.
    Marca a fonte usada em `_fonte` ('pjc'/'pdf'/None).

    Sem NENHUMA das duas fontes (PJC ainda não subiu) devolve o esqueleto vazio
    marcado com `_sem_pjc`: o caso segue analisável pelo lado LIFT e todo campo
    de referência sai vazio — nada é inventado nem comparado."""
    _CACHE_DIR.mkdir(exist_ok=True)
    fpjc, fpdf = Path(f"casos/{cnj}/pjc.pjc"), Path(f"casos/{cnj}/pjc.pdf")
    if not fpjc.exists() and not fpdf.exists():
        return {"cabecalho": {}, "verbas": [], "resumo": [], "historico_salarial": {},
                "dias_ferias_mes": {}, "rubricas_base": [], "_fonte": None, "_sem_pjc": True}
    usa_pjc = fpjc.exists()
    alvo = fpjc if usa_pjc else fpdf
    # `_PJC_SCHEMA` entra na chave: mudou o formato do parse (campo novo), o cache
    # antigo é ignorado sem precisar limpar o .cache na mão (o mtime não muda).
    # Com os dois arquivos, o mtime do PDF também entra: é ele que decide a fonte.
    _mt = f"{int(alvo.stat().st_mtime)}" + (f"_{int(fpdf.stat().st_mtime)}" if usa_pjc and fpdf.exists() else "")
    fp = _CACHE_DIR / f"pjc__{cnj}__{_PJC_SCHEMA}{'x' if usa_pjc else 'p'}{_mt}.pkl"
    if fp.exists():
        try:
            return pd.read_pickle(fp)
        except Exception:
            pass
    cab_pdf = None
    if usa_pjc and fpdf.exists():
        try:
            cab_pdf = parse_cabecalho_only(fpdf)
        except Exception:
            cab_pdf = None
    if usa_pjc:
        r = parse_pjc_xml(alvo)
        r["_fonte"] = "pjc"
        # .pjc e PDF de cálculos DIFERENTES (o robô baixa os dois como documentos
        # separados do Zeev): 182 casos em 28/10/2026. Sem saber qual é o gabarito, o
        # caso sai da régua ("gabarito a corrigir"); só vale o PDF onde ele foi conferido
        # (GABARITO_PDF_CONFIRMADO, ou o id do PDF é o da curadoria GABARITO_ID_CALCULO).
        id_x, id_p = r["cabecalho"].get("id_calculo"), (cab_pdf or {}).get("id_calculo")
        if id_x and id_p and id_x != id_p:
            r["_outro_calculo"] = {"id_pjc": id_x, "id_pdf": id_p, "usado": "pjc"}
            if cnj in GABARITO_PDF_CONFIRMADO or GABARITO_ID_CALCULO.get(cnj) == id_p:
                try:
                    rp = parse_pjc(fpdf)
                except Exception:
                    rp = None
                if rp and rp.get("verbas"):
                    r = rp
                    r["_fonte"] = "pdf"
                    r["_outro_calculo"] = {"id_pjc": id_x, "id_pdf": id_p, "usado": "pdf"}
        # Resumo do Cálculo do PDF companheiro: única fonte de JUROS por verba
        # (o .pjc dá o fator de correção por ocorrência, não os juros). Best-effort:
        # sem PDF, a camada pós-juros do PJC fica vazia em vez de inventada.
        if fpdf.exists():
            try:
                r["resumo_pdf"] = parse_resumo_only(fpdf)
            except Exception:
                r["resumo_pdf"] = None
        # header híbrido: completa campos nulos do .pjc com o cabeçalho do PDF
        faltam = [k for k in ("periodo_calculo", "admissao", "demissao", "data_ajuizamento")
                  if not r["cabecalho"].get(k)]
        if faltam and cab_pdf:
            try:
                for k in faltam:
                    if cab_pdf.get(k):
                        r["cabecalho"][k] = cab_pdf[k]
            except Exception:
                pass
    else:
        r = parse_pjc(alvo)
        r["_fonte"] = "pdf"
    try:
        pd.to_pickle(r, fp)
    except Exception:
        pass
    return r


# ---- recortes por caso (materializados pelo ingerir.py) --------------------
# gerar_telas NÃO baixa da Nekt: lê os recortes .cache/caso_raw__<CNJ>.pkl que o
# ingerir.py já gravou (só as linhas do id_processado de cada caso). Assim rodar
# um caso custa segundos e não toca a Nekt. Falta recorte -> rode o ingerir.py.
def _carrega_recortes(cnjs):
    faltando, slices = [], []
    for cnj in cnjs:
        fp = _CACHE_DIR / f"caso_raw__{cnj}.pkl"
        if not fp.exists():
            faltando.append(cnj)
            continue
        try:
            slices.append(pd.read_pickle(fp))
        except Exception:
            faltando.append(cnj)
    if faltando:
        print(f"[aviso] sem recorte p/ {len(faltando)} caso(s) — rode antes:")
        print("  python ingerir.py " + " ".join(faltando))
    return slices


_SLICES = _carrega_recortes(CNJS)

# ---- cortes do painel (Raíra, 15/10/2026): o que não vale o tempo de gerar ------
# - caso cuja execução mais recente é anterior a 03/08/2026 sai do painel;
# - pendente de PJC (sem gabarito) com execução de mais de 30 dias sai: dificilmente
#   ainda vai ganhar PJC.
# Só na geração completa: quem pede CNJs na linha de comando recebe exatamente esses.
CORTE_EXECUCAO = "2026-08-03"
PENDENTE_MAX_DIAS = 30


def _ult_execucao(s):
    p = s.get("PROC")
    if isinstance(p, pd.DataFrame) and len(p) and "criado_em" in p.columns:
        return str(p["criado_em"].max())[:10]
    return None


if not [a for a in sys.argv[1:] if not a.startswith("--")]:
    from datetime import timedelta
    _pend = set(_descobre_pendentes())
    _lim_pend = (date.today() - timedelta(days=PENDENTE_MAX_DIAS)).isoformat()
    _fora_antigo, _fora_pend = set(), set()
    for _s in _SLICES:
        _d, _k = _ult_execucao(_s), _s.get("cnj")
        if _d and _d < CORTE_EXECUCAO:
            _fora_antigo.add(_k)
        elif _k in _pend and _d and _d < _lim_pend:
            _fora_pend.add(_k)
    _fora = _fora_antigo | _fora_pend
    _SLICES = [s for s in _SLICES if s.get("cnj") not in _fora]
    CNJS = [c for c in CNJS if c not in _fora]
    print(f"[cortes] fora do painel: {len(_fora_antigo)} com execução antes de {CORTE_EXECUCAO}, "
          f"{len(_fora_pend)} pendentes de PJC com mais de {PENDENTE_MAX_DIAS} dias | ficam {len(CNJS)}")


def _concat(chave):
    """Concatena a fatia `chave` de todos os casos carregados (equivale à tabela
    inteira, mas só com as linhas dos casos pedidos)."""
    dfs = [s[chave] for s in _SLICES if isinstance(s.get(chave), pd.DataFrame) and len(s[chave])]
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


PROC = _concat("PROC")
P1 = _concat("P1")                                                                   # dados iniciais (partes/datas)
# consolidadas (layer trusted): trazem a ATUALIZAÇÃO MONETÁRIA por verba, que as
# tabelas raw não expõem. Chave = cnj (só dígitos). Semântica confirmada nos dados:
#   mensais   : valor_final_competencia (nominal) -> ..._valor_principal_corrigido
#               (× fator do índice) -> ..._valor_atualizado (× (1 + SELIC acumulada))
#   reflexos  : valor_final_* (nominal) -> *_corrigido (índice) -> *_bruto (com juros;
#               nome enganoso: `_juros` é só o MONTANTE de juros, e corrigido+juros=bruto)
#   rescisória: só verba punitiva (BT073) tem correção; nas outras
#               total_verba_atualizado guarda o valor COM JUROS, não o corrigido
C10A = _concat("C10A")                                                               # principais mensais
C10B = _concat("C10B")                                                               # rescisórias
CRAV = _concat("CRAV")                                                               # reflexo aviso prévio
CRFE = _concat("CRFE")                                                               # reflexo férias
CR13 = _concat("CR13")                                                               # reflexo 13º
CRDS = _concat("CRDS")                                                               # reflexo DSR
DEF = _concat("DEF")                                                                 # P4
EDT = _concat("EDT")                                                                 # P4 editor (dono do id_verba)
P10A = _concat("P10A")                                                               # principal
P10B = _concat("P10B")                                                               # rescisórias
P9A = _concat("P9A")                                                                 # P9a (roteamento/mapa_execucao)
P9B = _concat("P9B")                                                                 # P9b (apuração mensal)
REFL = _concat("REFL")                                                               # reflexos
HOLE = _concat("HOLE")
PROV = _concat("PROV")
# trilha de status da execução (status/etapa/motivo por id_processado): é ela que
# diz que uma execução parou com ERRO antes do cálculo — ver `_erro_execucao`.
STATUS = _concat("STATUS")

# ---- busca indexada: não varrer a tabela inteira a cada caso --------------
# As tabelas acima juntam os recortes de TODOS os casos. O filtro `df[df[col] == x]`
# feito caso a caso custava O(total) por chamada e deixava o painel quadrático
# (medido em 15/10/2026: 44 casos = 20 s, 300 = 12,6 min, ~1.500 = 1h40). Aqui cada
# tabela é agrupada UMA vez por coluna e o filtro vira busca no dicionário. Devolve as
# mesmas linhas, na mesma ordem original; a ordenação por criado_em segue no chamador.
_IDX = {}


def _indice(df, col, digitos=False):
    """{valor da coluna (texto): posições das linhas, na ordem original}, montado uma vez."""
    k = (id(df), col, digitos)
    ent = _IDX.get(k)
    if ent is None or ent[0] is not df:       # `is` evita reaproveitar id() de outra tabela
        s = df[col].astype(str)
        if digitos:
            s = s.str.replace(r"\D", "", regex=True)
        ent = (df, s.groupby(s.values, sort=False).indices)
        _IDX[k] = ent
    return ent[1]


def _vazio(chave):
    return chave is None or (isinstance(chave, float) and chave != chave)


def _linhas(df, col, chave, digitos=False):
    """Equivale a `df[df[col].astype(str) == str(chave)]` (com `digitos`, comparando só os
    dígitos da coluna), sem varrer a tabela."""
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    if not len(df) or col not in df.columns or _vazio(chave):
        return df.iloc[0:0]
    pos = _indice(df, col, digitos).get(str(chave))
    return df.iloc[pos] if pos is not None else df.iloc[0:0]


def _linhas_de(df, col, chaves):
    """Equivale a `df[df[col].isin(chaves)]`, na ordem original das linhas."""
    if not isinstance(df, pd.DataFrame):
        return pd.DataFrame()
    if not len(df) or col not in df.columns:
        return df.iloc[0:0]
    idx = _indice(df, col)
    pos = [idx[str(c)] for c in chaves if not _vazio(c) and str(c) in idx]
    if not pos:
        return df.iloc[0:0]
    import numpy as np
    return df.iloc[np.sort(np.concatenate(pos))]

# Esteira pré-compra (Zeev): tipo de cálculo por processo, já resolvido por caso
# no ingerir.py. Reconstrói o índice cnj->info a partir dos recortes (lookup O(1)).
_ESTEIRA_IDX = {s["cnj_d"]: (s.get("esteira") or {}) for s in _SLICES if s.get("cnj_d")}


def _esteira_info(cnj_d):
    """tipo_calculo/validade/flag-adequação do registro mais recente (lookup O(1))."""
    return _ESTEIRA_IDX.get(cnj_d, {"tipo_calculo": None, "data_validade_calculo": None, "calculo_adequacao": None})


def _ultimo(df, idp, col):
    if df is None or "id_processado" not in df.columns or col not in df.columns:
        return None  # tabela degradada (Nekt instável) -> sem dado, não quebra
    sub = _linhas(df, "id_processado", idp).sort_values("criado_em")
    if not len(sub):
        return None
    v = _parse(sub.iloc[-1][col])
    # célula vazia na Nekt chega como NaN, que é truthy: passaria pelo `or []`
    # dos chamadores e quebraria na iteração (0011148-31.2023.5.03.0054, 14/10)
    return None if isinstance(v, float) and v != v else v


# reflexos: tipo -> (rótulo, palavras-chave para casar com a linha do PJC)
_REFLEXO_TIPOS = {
    "decimo_terceiro": ("13º Salário", {"13", "salario", "decimo", "terceiro"}),
    "ferias": ("Férias + 1/3", {"ferias"}),
    "aviso_previo": ("Aviso Prévio", {"aviso", "previo"}),
    "dsr": ("DSR / Repouso", {"dsr", "repouso", "rsr", "repousos", "feriado"}),
}


def _total_reflexo(tipo, item):
    if tipo == "aviso_previo":
        return item.get("valor_final_aviso_previo_por_verba") or 0
    if tipo == "ferias":
        return sum(p.get("valor_final_ferias_periodo") or 0 for p in item.get("calculo_por_periodo_aquisitivo", []))
    if tipo == "decimo_terceiro":
        return sum(a.get("valor_final_decimo_terceiro_por_ano") or 0 for a in item.get("valores_anuais", []))
    if tipo == "dsr":
        return item.get("total_geral_dsr") or 0
    return 0


def _pjc_reflexo_tipo(nome):
    """Classifica uma linha de reflexo do PJC pelo tipo (13º/Férias/Aviso/DSR)."""
    toks = set(re.split(r"\s+", _norm(nome)))
    for tipo, (_, kw) in _REFLEXO_TIPOS.items():
        if kw & toks:
            return tipo
    return None


def _apos_sobre(nome):
    n = _norm(nome)
    return n.split(" sobre ", 1)[1] if " sobre " in n else n


# Salário pago por fora: o PJC chama de "EXTRAFOLHA", "SALÁRIO EXTRA-FOLHA", "SALÁRIO POR FORA";
# a IA, de "Integração de Comissões Pagas por Fora" (BT054). Sem palavra em comum, o reflexo não
# casava e virava sobra dos dois lados (0000642-51.2023.5.10.0005, Raíra 26/10/2026).
_RE_POR_FORA = re.compile(r"extra\s*-?\s*folha|por fora|marginal")


def _marca_por_fora(nome, toks):
    return toks | {"__por_fora__"} if _RE_POR_FORA.search(_norm(nome)) else toks


def _base_apos_sobre(nome):
    """Tokens (>=4 letras) da verba-base, i.e. o que vem depois de 'SOBRE'."""
    return _marca_por_fora(_apos_sobre(nome), {t for t in _apos_sobre(nome).split() if len(t) >= 4})


# O PJC fatia a MESMA verba em blocos de período ("... 20% - 11/2017 A 11/2020" e
# "... 20% - 10/2021"), tanto na principal quanto no reflexo. O loop das principais
# já soma as fatias; o dos reflexos pegava só uma e a outra virava "só PJC" — o que
# derrubava a acurácia do reflexo por PAREAMENTO, não por cálculo (ex.: 13º sobre
# insalubridade, IA 781,79 × PJC 201,67 = 25,8%, quando o PJC soma 779,47 = 99,7%).
_RE_PER_NORM = re.compile(r"\s+\d{1,2}\s+\d{4}(?:\s+a\s+\d{1,2}\s+\d{4})?\s*$")


def _base_canon(nome):
    """Verba-base do reflexo sem o sufixo de período — a chave para somar as fatias
    que o PJC criou da mesma verba (já normalizado: '-' e '/' viram espaço)."""
    return _RE_PER_NORM.sub("", _apos_sobre(nome)).strip()


def _perc_base(nome):
    """Percentuais citados na verba-base do reflexo ('...SOBRE HORAS EXTRAS 50%' -> {'50'}).

    Tokens de <4 letras ficam fora de `_base_apos_sobre`, então '50%', '75%' e
    '100%' eram invisíveis ao matcher: 'DSR sobre HE 50%' casava com 'RSR SOBRE
    HORAS EXTRAS 100%' (mesma interseção de tokens, empate resolvido pela ordem).
    Isso cruzava os reflexos entre as HEs do mesmo caso e destruía a acurácia da
    camada. O percentual passa a ser critério de veto.
    """
    return set(re.findall(r"(\d{1,3})\s*%", _apos_sobre(nome)))


# ---- de-para PJC -> glossário: vive em src/depara.py (16/10/2026), para a tabela do PJC
# (src/tabela_pjc.py) e o painel usarem a mesma regra -----------------------
from depara import norm as _norm_dep, pjc_info as _pjc_info, DEPARA as _DEPARA  # noqa: E402,F401


# ---- versão de prompt por etapa (ft_lift_tb_agente) -------------------------
# Toda tabela de resultado carrega `id_agente`, e o catálogo de agentes resolve
# esse id para (nome do agente, versão do prompt, criado_em, texto do prompt).
# Sem isso a acurácia agregada mistura safras de prompt: os casos foram
# processados em momentos diferentes, com prompts diferentes, e o número global é
# média ponderada de coortes distintas. Com o join, cada caso ganha a versão de
# cada etapa e a comparação passa a ser POR VERSÃO.
#
# ATENÇÃO de método: comparar safras entre si é OBSERVACIONAL, não experimental —
# cada safra tem casos diferentes. Só reprocessar os MESMOS casos em duas versões
# (teste pareado) atribui causa. A aba mostra o aviso.
_AGENTE = {}          # id_agente -> {nome, versao, criado_em}
_AG_PROMPT = {}       # (nome, versao) -> texto do prompt
_ag_fp = _CACHE_DIR / "raw__ft_lift_tb_agente.pkl"
if _ag_fp.exists():
    try:
        for _, r in pd.read_pickle(_ag_fp).iterrows():
            nome, ver = str(r["nome_agente"]), int(r["versao_agente"])
            _AGENTE[str(r["id_agente"])] = {
                "nome": nome, "versao": ver, "criado_em": str(r["criado_em"])[:19],
            }
            _AG_PROMPT[(nome, ver)] = str(r.get("prompt") or "")
    except Exception:
        print("[aviso] catálogo de agentes não pôde ser lido; aba de versões fica vazia.")

# etapa (rótulo na tela) -> alias da tabela no recorte. Só as que têm id_agente;
# os reflexos são feitos em CÓDIGO (lambda), não por agente, e ficam de fora.
_ETAPAS_AG = [
    ("P1", "P1", "Dados iniciais"),
    ("P4", "DEF", "Decisões / verbas deferidas"),
    ("P7", "HOLE", "Histórico salarial (filtro)"),
    ("P9a", "P9A", "Quantificador — roteamento"),
    ("P9b", "P9B", "Quantificador — mensais"),
    ("P10a", "P10A", "Principal — mensais"),
    ("P10b", "P10B", "Principal — rescisórias"),
]
# as etapas que compõem a "safra" (o miolo do cálculo). Upstream é praticamente
# constante na população, então a variação que interessa está nestas quatro.
_ETAPAS_SAFRA = ["P9a", "P9b", "P10a", "P10b"]


def _versoes(idp):
    """Versão de prompt de cada etapa para este caso. Mesma regra de seleção do
    montar_caso: a ÚLTIMA linha por criado_em em cada tabela."""
    out = {}
    for etapa, alias, _ in _ETAPAS_AG:
        df = globals().get(alias)
        if df is None or not len(df) or "id_agente" not in df.columns:
            out[etapa] = None
            continue
        sub = _linhas(df, "id_processado", idp).sort_values("criado_em")
        if not len(sub):
            out[etapa] = None
            continue
        info = _AGENTE.get(str(sub.iloc[-1]["id_agente"]))
        out[etapa] = info["versao"] if info else None
    return out


def _safra(vers):
    """Rótulo curto da combinação de versões do miolo (ex.: '5/3/2/2')."""
    vs = [vers.get(e) for e in _ETAPAS_SAFRA]
    return None if all(v is None for v in vs) else "/".join("?" if v is None else str(v) for v in vs)


def _mudancas_agentes(maxlin=8, maxchar=260):
    """Diff resumido entre versões CONSECUTIVAS de cada agente, direto do texto do
    prompt no catálogo. É o que responde 'o que entrou entre uma safra e a
    seguinte' sem depender de histórico de git."""
    import difflib
    porta = {}
    for (nome, ver) in _AG_PROMPT:
        porta.setdefault(nome, []).append(ver)
    out = []
    for nome, vers in porta.items():
        vers = sorted(vers)
        for va, vb in zip(vers, vers[1:]):
            a, b = _AG_PROMPT[(nome, va)].splitlines(), _AG_PROMPT[(nome, vb)].splitlines()
            sm = difflib.SequenceMatcher(None, a, b, autojunk=False)
            trechos = []
            for tag, i1, i2, j1, j2 in sm.get_opcodes():
                if tag == "equal":
                    continue
                rem = [l.strip()[:maxchar] for l in a[i1:i2] if l.strip()]
                add = [l.strip()[:maxchar] for l in b[j1:j2] if l.strip()]
                if not rem and not add:
                    continue
                trechos.append({"tipo": tag, "linha": j1,
                                "rem": rem[:maxlin], "rem_n": len(rem),
                                "add": add[:maxlin], "add_n": len(add)})
            info = next((v for v in _AGENTE.values()
                         if v["nome"] == nome and v["versao"] == vb), None)
            out.append({
                "agente": nome, "de": va, "para": vb,
                "criado_em": (info or {}).get("criado_em"),
                "chars_de": len(_AG_PROMPT[(nome, va)]),
                "chars_para": len(_AG_PROMPT[(nome, vb)]),
                "similaridade": round(sm.ratio(), 3),
                "trechos": trechos,
            })
    out.sort(key=lambda x: (x["criado_em"] or "", x["agente"]))
    return out


# Rótulos que são LINHA DE RESUMO do demonstrativo, não verba deferida. Quando o
# parse do PJC só devolve isto, não existe verba para comparar — e o "total" do
# gabarito vira a soma de agregados, não de verbas.
_ROTULOS_AGREGADOS = (
    "VERBAS TRIBUTAVEIS", "VERBAS NAO TRIBUTAVEIS", "CONTRIBUICAO SOCIAL",
    "PEDIDOS IMPROCEDENTES", "TOTAL GERAL", "TOTAL DA CONDENACAO", "SUBTOTAL",
    "TOTAL BRUTO", "TOTAL LIQUIDO", "VALOR DA CONDENACAO",
)


def _norm_rotulo(s):
    s = unicodedata.normalize("NFD", str(s or ""))
    s = "".join(ch for ch in s if unicodedata.category(ch) != "Mn")
    return " ".join(s.upper().split())


def _so_agregados(verbas_pjc):
    """Todas as 'verbas' da referência são rótulo de agregado?

    Só dispara quando NENHUMA linha é verba de verdade — um demonstrativo que
    traz o subtotal junto das verbas continua válido, e é o caso comum.
    """
    nomes = [_norm_rotulo(v.get("nome")) for v in verbas_pjc]
    if not nomes:
        return False
    return all(any(rot in n for rot in _ROTULOS_AGREGADOS) for n in nomes)


def _num_col(v):
    try:
        f = float(v)
        return None if f != f else f
    except Exception:
        return None


# Honorários, custas e perícia: o PJe-Calc não os traz como verba e não são
# crédito do reclamante. Ficam fora da lista, dos totais e das medidas.
RX_NAO_VERBA = re.compile(r"honor[aá]r|custas|perit|per[ií]cia", re.I)


def _verbas_rodada(cell, camada):
    """As verbas de UMA rodada, só o que o diff entre rodadas precisa.

    Deixa `competencias` de fora de propósito: é a série mensal inteira, o grosso
    do payload, e não responde "que verba mudou". O código do glossário vive em
    lugar diferente nas duas camadas — dentro de `reflexos_base` no mensal, no
    topo na rescisória — e `id_verba` NÃO serve de identidade: é posicional
    (verba_01, verba_02...), então a mesma posição pode ser outra verba na rodada
    seguinte. Por isso a chave é o código, com o id só como rótulo de fallback.
    """
    try:
        arr = _parse(cell) or []
    except Exception:
        return []
    if not isinstance(arr, list):
        return []
    out = []
    for v in arr:
        if not isinstance(v, dict):
            continue
        rb = v.get("reflexos_base")
        cod = (rb.get("codigo_glossario") if isinstance(rb, dict) else None) or v.get("codigo_glossario")
        out.append({"cod": cod, "nome": GLOSSARIO_NOME.get(cod) if cod else None,
                    "id": v.get("id_verba"), "total": _num_col(v.get("total_verba")),
                    "camada": camada})
    return out


def _rodadas(cnj_d):
    """Todas as RODADAS do caso, não só a última.

    O `_ultimo` fica com a linha mais recente de cada tabela, que é o certo para
    comparar contra a referência, mas joga fora o histórico. As tabelas raw
    guardam toda rodada, então um caso reprocessado tem o MESMO caso avaliado em
    duas versões de prompt — que é a única comparação que isola versão de
    complexidade do caso. Uma rodada = uma linha do P10a (o cálculo final);
    P10b e as versões de P9a/P9b vêm da linha vigente no mesmo instante.
    """
    if not len(PROC) or not len(P10A):
        return []
    idps = set(_linhas(PROC, "cnj", cnj_d)["id_processado"])
    if not idps:
        return []

    def _vers_em(df, idp, _quando=None):
        """Versão que produziu a saída DESTA rodada.

        Casa por `id_processado`, que É a rodada. Antes filtrava também por
        `criado_em <= quando` (o instante do P10a), e isso descartava a própria
        linha: dentro de uma rodada o P10b é gravado DEPOIS do P10a — 260 de 260
        pares conferidos no cache, nenhum empate. O efeito era o P10b da rodada
        ficar sempre fora, e a safra sair com `?` no 4º campo (`7/5/2/?`); quando
        não saía, era pior, porque o que entrava vinha de uma rodada ANTERIOR.
        """
        if df is None or not len(df) or "id_agente" not in df.columns:
            return None
        sub = _linhas(df, "id_processado", idp).sort_values("criado_em")
        if not len(sub):
            return None
        info = _AGENTE.get(str(sub.iloc[-1]["id_agente"]))
        return info["versao"] if info else None

    out = []
    for _, r in _linhas_de(P10A, "id_processado", idps).sort_values("criado_em").iterrows():
        idp, quando = r["id_processado"], r["criado_em"]
        info = _AGENTE.get(str(r.get("id_agente")))
        # rescisórias DA MESMA rodada: casa por id_processado, não por instante.
        # Com o `criado_em <= quando` de antes, o P10b da rodada (gravado depois
        # do P10a) ficava de fora e o `total_lift` saía só com o mensal — em 50
        # dos 125 casos reprocessados em 09/09/2026 havia rescisória, e ela não
        # entrava na comparação entre rodadas.
        resc = None
        vbs = _verbas_rodada(r.get("resultados_por_verba"), "mensal")
        # honorários/custas/perícia saem da rodada como saem do caso: o P10a os
        # calcula como verba comum e o nome só existe no P4 (id_verba posicional).
        # Nome pelo editor (casado por id_verba); sem editor, DEF posicional. Se o
        # código do P10a diverge do P4, a verba é a do código (real, entra na soma).
        editor = {e.get("id_verba"): e for e in (_ultimo(EDT, idp, "verbas") or []) if isinstance(e, dict)}
        deferidas = _ultimo(DEF, idp, "verbas_deferidas") or []
        honor_mens = 0.0
        for vb in vbs:
            d = editor.get(vb.get("id"))
            if d is None:
                m = re.fullmatch(r"verba_(\d+)", str(vb.get("id") or ""))
                i = int(m.group(1)) - 1 if m else -1
                d = deferidas[i] if 0 <= i < len(deferidas) else None
            if not d:
                continue
            c4 = d.get("codigo_glossario")
            if vb.get("cod") and c4 and vb["cod"] != c4:
                continue
            if RX_NAO_VERBA.search(d.get("nome_verba") or ""):
                vb["fora_comparacao"] = True
                honor_mens += vb["total"] or 0
        vbs = [vb for vb in vbs if not vb.get("fora_comparacao")]
        if len(P10B):
            sb = _linhas(P10B, "id_processado", idp).sort_values("criado_em")
            if len(sb):
                resc = _num_col(sb.iloc[-1].get("total_rescisorias"))
                vbs += _verbas_rodada(sb.iloc[-1].get("resultados_rescisorias"), "rescisoria")
        vers = {"P9a": _vers_em(P9A, idp, quando), "P9b": _vers_em(P9B, idp, quando),
                "P10a": info["versao"] if info else None, "P10b": _vers_em(P10B, idp, quando)}
        mens = _num_col(r.get("total_mensais"))
        if mens is not None:
            mens = round(mens - honor_mens, 2)
        out.append({
            "quando": str(quando)[:19], "versoes": vers, "safra": _safra(vers),
            "total_mensais": mens, "total_rescisorias": resc, "verbas": vbs,
            # principal + rescisórias, SEM reflexos (que são feitos em código e não
            # têm versão de prompt). Serve p/ comparar duas rodadas entre si com a
            # mesma definição, não p/ comparar com o total da tela.
            "total_lift": None if (mens is None and resc is None) else (mens or 0) + (resc or 0),
        })
    return out


def _pareado(casos):
    """Comparação PAREADA: o mesmo caso em duas versões diferentes.

    É a única leitura que separa efeito de versão de complexidade do caso.
    Comparar safra × safra na população não serve para isso: cada safra tem
    casos diferentes, então a diferença mistura prompt com amostra.

    Devolve, por caso reprocessado sob versões distintas, uma rodada por versão
    com o total do LIFT (principal + rescisórias, sem reflexos) e o total da
    referência, que não muda entre rodadas e serve de âncora fixa.
    """
    itens, transicoes = [], {}
    for cnj, c in casos.items():
        if c.get("sem_pjc") or not c.get("extracao_confiavel"):
            continue
        # já anexado ao caso no render (uma varredura só do P10a por caso, em vez
        # de uma aqui e outra lá para o mesmo resultado)
        rod = c.get("rodadas") or []
        safras = {r["safra"] for r in rod if r["safra"]}
        if len(rod) < 2 or len(safras) < 2:
            continue
        itens.append({
            "cnj": cnj, "apto": bool(c.get("apto")),
            # âncora SEM reflexos: o `total_lift` das rodadas também não os tem
            "total_pjc": (c.get("quadro") or {}).get("total_pjc_base"),
            "rodadas": rod,
        })
        # uma transição = par de safras consecutivas observado no mesmo caso
        vistos = [r for r in rod if r["safra"]]
        for a, b in zip(vistos, vistos[1:]):
            if a["safra"] == b["safra"]:
                continue
            k = f'{a["safra"]} → {b["safra"]}'
            t = transicoes.setdefault(k, {"de": a["safra"], "para": b["safra"], "casos": []})
            if a["total_lift"] and b["total_lift"]:
                t["casos"].append({"cnj": cnj, "apto": bool(c.get("apto")),
                                   "ia_de": a["total_lift"], "ia_para": b["total_lift"],
                                   "pjc": (c.get("quadro") or {}).get("total_pjc_base")})
    itens.sort(key=lambda x: (not x["apto"], x["cnj"]))
    # quantos casos têm histórico multi-safra mas NÃO deram par utilizável (total
    # ausente em algum dos lados). Sem isso a tela mostraria "2 casos" e pareceria
    # que só 2 foram reprocessados, quando 15 foram.
    comparaveis = {o["cnj"] for t in transicoes.values() for o in t["casos"]}
    return {"casos": itens,
            "n_hist": len(itens),
            "n_comparaveis": len(comparaveis),
            "transicoes": sorted(transicoes.values(), key=lambda t: -len(t["casos"]))}


def _catalogo_agentes():
    return sorted(
        ({"agente": v["nome"], "versao": v["versao"], "criado_em": v["criado_em"],
          "chars": len(_AG_PROMPT.get((v["nome"], v["versao"]), ""))}
         for v in _AGENTE.values()),
        key=lambda x: (x["agente"], x["versao"]))


# ---- dados cadastrais: cabeçalho da referência × dados iniciais do LIFT (P1) --
# O cabeçalho do cálculo de referência traz as partes e as datas que amarram TODO
# o cálculo: admissão, demissão e o período apurado (que no PJC já é o recorte não
# prescrito). Se a admissão ou o recorte do período divergem, NENHUMA verba pode
# bater — e o erro não é de conta, é de insumo. Comparar isso separa "errou o
# cálculo" de "calculou outro contrato". Lado LIFT = P1 (`dados_extraidos`).
_SUFIXOS_EMPRESA = {"ltda", "sa", "s a", "me", "epp", "eireli", "sociedade",
                    "anonima", "em", "recuperacao", "judicial", "massa", "falida",
                    "cia", "companhia", "do", "da", "de", "dos", "das", "e"}


def _iso(d):
    """Data em ISO (aaaa-mm-dd) a partir de 'dd/mm/aaaa' ou 'aaaa-mm-dd...'."""
    if not d:
        return None
    s = str(d).strip()
    m = re.match(r"^(\d{2})/(\d{2})/(\d{4})$", s)
    if m:
        return f"{m.group(3)}-{m.group(2)}-{m.group(1)}"
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", s)
    return m.group(0) if m else None


def _br(d):
    """Data em dd/mm/aaaa (formato de exibição), de qualquer das duas fontes."""
    i = _iso(d)
    return f"{i[8:10]}/{i[5:7]}/{i[:4]}" if i else (str(d) if d else None)


def _dias_entre(a, b):
    ia, ib = _iso(a), _iso(b)
    if not ia or not ib:
        return None
    try:
        return (date(*map(int, ia.split("-"))) - date(*map(int, ib.split("-")))).days
    except (TypeError, ValueError):
        return None


def _casa_tok(t, outros):
    """Token bate contra o outro lado, tolerando ABREVIAÇÃO — a razão social vem
    truncada na base ('FORD CREDIT SERV ASS CONS LTDA' × 'FORD CREDIT SERVIÇOS DE
    ASSESSORIA E CONSULTORIA LTDA'). Prefixo de ≥3 letras conta como o mesmo."""
    return any(t == o or (len(t) >= 3 and (o.startswith(t) or t.startswith(o))) for o in outros)


def _nome_cmp(a, b):
    """'bate' | 'parcial' | 'diverge' para nomes de parte. Grafia de empresa varia
    (LTDA/S.A., 'EM RECUPERAÇÃO JUDICIAL', filial, razão social abreviada) — isso
    não é divergência; o que importa é ser OUTRA parte."""
    na, nb = _norm(a or ""), _norm(b or "")
    if not na or not nb:
        return None
    if na == nb:
        return "bate"
    ta = {t for t in na.split() if t not in _SUFIXOS_EMPRESA and len(t) > 2}
    tb = {t for t in nb.split() if t not in _SUFIXOS_EMPRESA and len(t) > 2}
    if ta and tb:
        cheios_a = sum(1 for t in ta if _casa_tok(t, tb))
        cheios_b = sum(1 for t in tb if _casa_tok(t, ta))
        # um lado inteiro contido no outro (com abreviação) = mesma parte
        if cheios_a == len(ta) or cheios_b == len(tb):
            return "bate"
        cob = max(cheios_a / len(ta), cheios_b / len(tb))
        if cob >= 0.6 or score(na, nb) >= 0.8:
            return "parcial"   # mesma raiz, grafia bem diferente -> olho humano
    return "diverge"


# campos comparáveis (chave estável p/ agregar no painel) + rótulo
_CAD_CAMPOS = [
    ("reclamante", "Nome do reclamante"),
    ("reclamada", "Reclamada"),
    ("admissao", "Data de admissão"),
    ("demissao", "Data de demissão"),
    ("ajuizamento", "Data de ajuizamento"),
    ("periodo_ini", "Início do período apurado (não prescrito)"),
    ("periodo_fim", "Fim do período apurado"),
]
# Campos cuja divergência é de INSUMO do cálculo (contrato e recorte do período):
# divergiu aqui, os dois lados apuram meses diferentes e a acurácia das verbas
# mede outra coisa. A reclamada fica fora: divergir ali é quase sempre
# litisconsórcio/tomador (o PJC nomeia a parte que paga, o P1 o empregador),
# não erro de insumo.
_CAD_GRAVES = {"admissao", "demissao"}
# entram no denominador do "% conferindo"; `ref_atualizada` fica fora (não é
# comparável: é a data em que a referência foi atualizada, não um fim de período)
_CAD_COMPARAVEIS = {"bate", "parcial", "diverge", "escopo_maior", "escopo_menor"}


def _cadastro(p1, cab):
    """Comparação dos dados cadastrais, linha a linha.

    Status por linha: `bate` · `parcial` (nome, grafia) · `diverge` (contrato/parte)
    · `escopo_maior`/`escopo_menor` (o período apurado difere: a referência apura
    mais/menos meses) · `ref_atualizada` (só no fim: o PJC foi atualizado depois do
    fim do contrato — esperado) · `sem_lift`/`sem_pjc`/`sem_ambos`.

    Devolve {linhas, n_comparados, n_ok, n_diverge, divergentes, n_escopo, escopo,
    graves} — `graves` = divergência de contrato (admissão/demissão), a que
    invalida a comparação de verbas."""
    d = p1 or {}
    ic = d.get("identificacao_caso") or {}
    dfp = d.get("datas_fundamentais_prescricao") or {}
    cdz = d.get("calculos_derivados") or {}

    def _val(v):
        """Campo do P1 que pode vir como {'fonte':..,'valor':..} ou valor cru."""
        if isinstance(v, dict):
            return v.get("valor"), v.get("fonte")
        return v, None

    adm, adm_f = _val(dfp.get("data_admissao"))
    dem, dem_f = _val(dfp.get("data_demissao"))
    per = cab.get("periodo_calculo") or ""
    ini_pjc, fim_pjc = (x.strip() for x in per.split(" a ", 1)) if " a " in per else (None, None)

    bruto = {
        "reclamante": ("nome", ic.get("nome_reclamante"), cab.get("reclamante"), None),
        "reclamada": ("nome", ic.get("nome_reclamada"), cab.get("reclamado"), None),
        "admissao": ("data", adm, cab.get("admissao"), adm_f),
        "demissao": ("data", dem, cab.get("demissao"), dem_f),
        "ajuizamento": ("data", dfp.get("data_distribuicao"), cab.get("data_ajuizamento"), None),
        "periodo_ini": ("data", cdz.get("periodo_nao_prescrito_inicio"), ini_pjc, None),
        "periodo_fim": ("data", cdz.get("periodo_nao_prescrito_fim"), fim_pjc, None),
    }
    linhas = []
    for chave, rotulo in _CAD_CAMPOS:
        tipo, lift, pjc, fonte = bruto[chave]
        delta, motivo = None, None
        if lift is None and pjc is None:
            status = "sem_ambos"
        elif lift is None:
            status = "sem_lift"
        elif pjc is None:
            status = "sem_pjc"
        elif tipo == "data":
            delta = _dias_entre(lift, pjc)
            # datas ilegíveis nos dois lados (ex.: campo livre no PDF) -> não julga
            status = ("bate" if delta == 0 else "diverge") if delta is not None else "sem_ambos"
        else:
            status = _nome_cmp(lift, pjc) or "sem_ambos"
        # As duas pontas do PERÍODO não são "certo/errado", são ESCOPO: cada lado
        # apura um intervalo. Escopo diferente muda o nº de meses de toda verba —
        # logo a acurácia compara coisas diferentes, mesmo com a conta correta.
        # Caso especial do FIM: no PJC é a data de TÉRMINO DO CÁLCULO (atualização),
        # não o fim do contrato — medido, ela passa do fim do vínculo em 156 dos
        # 380 casos. Referência indo além ali é esperado e não vira alerta.
        # delta = LIFT − referência, em dias. No INÍCIO, referência mais antiga
        # (delta>0) = referência apura mais; no FIM é o contrário (referência mais
        # recente = apura mais) — daí os sinais invertidos entre as duas pontas.
        if status == "diverge" and chave in ("periodo_ini", "periodo_fim"):
            if chave == "periodo_ini":
                status = "escopo_maior" if delta > 0 else "escopo_menor"
            elif delta < 0:
                status, motivo = "ref_atualizada", "fim do PJC = data de término do cálculo (atualizado)"
            else:
                status = "escopo_menor"
        if chave == "periodo_ini" and status == "escopo_maior" and _iso(pjc) == _iso(bruto["admissao"][2]):
            motivo = "a referência apura desde a ADMISSÃO (sem corte de prescrição)"
        elif chave == "periodo_ini" and status == "escopo_menor":
            motivo = "a referência começa depois — em geral no início do período deferido na decisão"
        linhas.append({
            "chave": chave, "campo": rotulo, "tipo": tipo,
            "lift": _br(lift) if tipo == "data" else lift,
            "pjc": _br(pjc) if tipo == "data" else pjc,
            "status": status, "delta_dias": delta, "fonte_lift": fonte, "motivo": motivo,
        })
    comp = [l for l in linhas if l["status"] in _CAD_COMPARAVEIS]
    div = [l for l in comp if l["status"] == "diverge"]
    esc = [l for l in comp if l["status"] in ("escopo_maior", "escopo_menor")]
    return {"linhas": linhas, "n_comparados": len(comp), "n_ok": len(comp) - len(div) - len(esc),
            "n_diverge": len(div), "divergentes": [l["chave"] for l in div],
            "n_escopo": len(esc), "escopo": [l["chave"] for l in esc],
            "graves": [l["chave"] for l in div if l["chave"] in _CAD_GRAVES],
            # contexto (sem par no cabeçalho da referência): a prescrição que o LIFT derivou
            "data_prescricao": _br(cdz.get("data_prescricao")),
            "causa_afastamento": _val(dfp.get("causa_afastamento"))[0],
            "cnpj_reclamada": ic.get("cnpj_reclamada"), "cpf_reclamante": ic.get("cpf_reclamante")}


# ---- acurácia por camada (principais × rescisórias × reflexos) + global -------
# Três camadas com naturezas de erro diferentes (P10a mensal, P10b valor fixo,
# reflexo em código sobre a base). Duas medidas por camada, de propósito:
#  - `acc` = 1 − Σ|IA−PJC| / Σ max(|IA|,|PJC|): erro ABSOLUTO, não deixa um erro
#    pra cima cancelar um pra baixo (a assertividade do total cancela). Conta
#    verba só-IA e só-PJC como erro cheio — verba perdida é erro, não ausência.
#  - `accs` = acurácias das verbas casadas (p/ mediana), como na aba por verba.
def _f(x):
    """float ou None (NaN/None/vazio -> None). As consolidadas usam Decimal/NaN."""
    if x is None:
        return None
    try:
        if pd.isna(x):
            return None
    except (TypeError, ValueError):
        pass
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def _soma(g, col):
    """Soma da coluna no grupo, ou None se a coluna não existe ou está toda vazia
    (soma 0 diria 'a atualização deu zero', que é diferente de 'não foi calculada')."""
    if col not in g.columns:
        return None
    vals = [_f(x) for x in g[col]]
    vals = [x for x in vals if x is not None]
    return round(sum(vals), 2) if vals else None


def _cons(df, cnj_d):
    """Linhas da tabela consolidada deste caso (chave = cnj só dígitos)."""
    if df is None or not len(df) or "cnj" not in df.columns:
        return pd.DataFrame()
    return _linhas(df, "cnj", cnj_d, digitos=True)


def _camada_de(v):
    return "reflexo" if v.get("is_reflexo") else ("rescisoria" if v.get("is_rescisoria") else "principal")


# ---- as três CAMADAS DE VALOR (pré-índice, pós-índice, pós-juros) -------------
# O mesmo cálculo tem três valores, e a divergência pode nascer em qualquer um:
#   nominal   = o devido, sem atualização (é onde mora a lógica do FT);
#   corrigido = nominal × fator do índice de correção monetária (IPCA-E até a
#               distribuição, no padrão atual) — divergir SÓ aqui é índice/data-base;
#   juros     = corrigido + juros de mora (SELIC acumulada) — divergir só aqui é
#               marco inicial/taxa.
# Comparar camada a camada separa "errou a conta" de "errou a atualização".
LAYERS = ("nominal", "corrigido", "juros")


def _val(v, layer):
    """(ia, pjc, acuracia) da verba na camada pedida. Camada ausente cai para None
    (nunca para o nominal: silenciar a falta faria a atualização parecer correta)."""
    if layer == "nominal":
        return v.get("total_ia"), v.get("total_pjc"), v.get("acuracia")
    d = v.get(layer) or {}
    return d.get("ia"), d.get("pjc"), d.get("acc")


def _camadas(verbas, sem_pjc, layer="nominal"):
    z = lambda: {"ia": 0.0, "pjc": 0.0, "dif_abs": 0.0, "den": 0.0, "n": 0, "n_par": 0,
                 "accs": [], "accs_base_ok": []}
    out = {k: z() for k in ("principal", "rescisoria", "reflexo", "global")}
    for v in verbas:
        v_ia, v_pjc, v_acc = _val(v, layer)
        if v_ia is None and v_pjc is None:
            continue                      # verba sem valor de nenhum lado nesta camada
        ia, pj = v_ia or 0.0, v_pjc or 0.0
        for k in (_camada_de(v), "global"):
            e = out[k]
            e["ia"] += ia
            e["pjc"] += pj
            e["n"] += 1
            if not sem_pjc:
                e["dif_abs"] += abs(ia - pj)
                e["den"] += abs(pj)          # o PJC, nao o maior lado
            # "Valor quando casa" (③): fora só o que não tem valor a comparar —
            # verba que casou pelo nome mas tem um dos lados zerado. Verba que
            # errou feio FICA. Mesmo critério do card ③ do Placar, que até
            # 24/09/2026 usava outro (`acuracia>0`) e media outra amostra.
            if v.get("status") == "coincide" and v_acc is not None and v_ia and v_pjc:
                e["n_par"] += 1
                e["accs"].append(v_acc)
                if v.get("acuracia_base") is not None and v["acuracia_base"] >= 95:
                    e["accs_base_ok"].append(v_acc)
    for e in out.values():
        e["ia"], e["pjc"] = round(e["ia"], 2), round(e["pjc"], 2)
        e["dif_abs"], e["den"] = round(e["dif_abs"], 2), round(e["den"], 2)
        # sem gabarito não há acurácia: fica None, fora de toda média. Camada sem
        # nenhuma verba com valor (n=0) também é None, e não 100% — não há dinheiro
        # a medir, e 100% ali afirmaria que está tudo certo. É a mesma primeira
        # guarda do medidas.acuracia_global(); as duas têm de responder igual.
        # denominador zero com n>0: 100% se nao houve erro, 0% se houve (D4)
        e["acc"] = (None if (sem_pjc or not e["n"]) else
                    (100.0 if not e["den"] and not e["dif_abs"] else
                     0.0 if not e["den"] else
                     round(100 * (1 - e["dif_abs"] / e["den"]), 1)))
    return out


# ---- jornada: cartão de ponto × pré-fixada ----------------------------------
# Duas perguntas DIFERENTES, e a divergência entre elas é o achado:
#   tipo_decisao   = o que a decisão manda (P9a `definicoes_contextuais.jornadas`:
#                    `documental_dependente` = apura pelos cartões; `fixada`/`fixa`/
#                    `semanal`/`padrão` = jornada arbitrada na decisão).
#   fonte_apuracao = o que o cálculo REALMENTE usou, lido da memória do P9b
#                    ("Apurado do cartão (batidas reais). Origem: <dia> hh:mm–hh:mm; …").
# Medido na base: 436 fixa→sem cartão · 47 documental→cartão · **6 documental→SEM
# cartão** (cartão deferido como método e o cálculo presumiu) · 1 mista→cartão.
# Esses 6 são o risco de [[project_jornada_fixa_zera_he]]: com cartão deferido, 2h/dia
# é TETO a apurar dia a dia, não regra fixa.
_RE_CARTAO = re.compile(r"apurado do cart|batidas reais", re.I)
_RE_BATIDA = re.compile(r"(\d{4}-\d{2}-\d{2})\s+(\d{1,2}:\d{2})\s*[–\-—a]{1,3}\s*(\d{1,2}:\d{2})")


def _jornada(idp, deferidas):
    dc = _ultimo(P9A, idp, "definicoes_contextuais") or {}
    if not isinstance(dc, dict):
        dc = {}
    jornadas = []
    for j in (dc.get("jornadas") or []):
        if not isinstance(j, dict):
            continue
        jornadas.append({
            "id": j.get("id_jornada"), "tipo": j.get("tipo_jornada"),
            "divisor": j.get("divisor"), "origem": j.get("origem_horaria"),
            "global": j.get("jornada_global"), "fonte_documento": j.get("fonte_documento"),
            "premissa": j.get("premissa_adotada"),
            "descricao": j.get("descricao_textual"),
            "logica": j.get("logica_composicao"),
            "observacoes": j.get("observacoes_tecnicas"),
            "regimes": [{
                "id": (r or {}).get("regime_id"), "tipo": (r or {}).get("regime_tipo"),
                "padrao": (r or {}).get("padrao_horario"),
                "periodo": ((r or {}).get("periodo_aplicacao") or {}).get("texto_origem"),
            } for r in (j.get("regimes") or []) if isinstance(r, dict)],
        })
    tipos = {str(j.get("tipo") or "").lower() for j in jornadas}
    tipos |= {str(r.get("tipo") or "").lower() for j in jornadas for r in j["regimes"]}
    doc = any("documental" in t for t in tipos)
    fix = any(t and "documental" not in t for t in tipos)
    tipo_decisao = "mista" if (doc and fix) else ("cartao" if doc else ("fixa" if fix else None))

    # o que o cálculo usou: batidas na memória do P9b. O cartão é do CASO, não da
    # verba (verba_01 e verba_02 repetem a mesma memória), então guardo uma vez,
    # pela verba com mais dias, e registro quais verbas apuraram assim.
    ap = _ultimo(P9B, idp, "apuracao_por_verba") or []
    por_comp, verbas_cartao = {}, []
    for v in (ap if isinstance(ap, list) else []):
        if not isinstance(v, dict):
            continue
        usou = False
        for c in (v.get("competencias") or []):
            q = (c or {}).get("quantidade_apurada") or {}
            mem = str(q.get("memoria_calculo") or "")
            if not _RE_CARTAO.search(mem):
                continue
            usou = True
            comp = _comp(c.get("competencia"))
            dias = {}
            for d, ent, sai in _RE_BATIDA.findall(mem):
                dias.setdefault(d, []).append([ent, sai])
            item = {"competencia": comp, "horas": _f(q.get("total_horas")),
                    "n_dias": len(dias),
                    "dias": [[d, *sum(iv, [])] for d, iv in sorted(dias.items())]}
            # mantém a leitura mais rica da competência (mais dias registrados)
            if comp not in por_comp or item["n_dias"] > por_comp[comp]["n_dias"]:
                por_comp[comp] = item
        if usou:
            verbas_cartao.append({"id_verba": v.get("id_verba"),
                                  "codigo": v.get("codigo_glossario"),
                                  "nome": v.get("verba_glossario")})
    cartao = None
    if por_comp:
        comps = [por_comp[k] for k in sorted(por_comp)]
        cartao = {"competencias": comps, "n_comp": len(comps),
                  "n_dias": sum(c["n_dias"] for c in comps),
                  "horas": round(sum(c["horas"] or 0 for c in comps), 2),
                  "verbas": verbas_cartao}
    fonte = "cartao" if cartao else ("fixa" if tipo_decisao else None)
    # jornada do P4: o texto vinculante da decisão (o mesmo que alimenta o critério
    # por verba). Fica na tela quando a jornada é pré-fixada, que é quando ele MANDA.
    jg = _ultimo(DEF, idp, "jornada_global") or []
    p4 = [{"divisor": (x or {}).get("divisor_jornada"), "fonte": (x or {}).get("fonte_documento"),
           "periodo": (x or {}).get("periodo_jornada"), "descricao": (x or {}).get("descricao_jornada")}
          for x in (jg if isinstance(jg, list) else []) if isinstance(x, dict)]
    esp = [{"nome": (d or {}).get("nome_verba"), "codigo": (d or {}).get("codigo_glossario"),
            "texto": (d or {}).get("jornada_especifica")}
           for d in (deferidas or []) if isinstance(d, dict) and (d or {}).get("jornada_especifica")]
    return {
        "tipo_decisao": tipo_decisao, "fonte_apuracao": fonte,
        # decisão manda cartão e a apuração não usou: erro de método, não de valor
        "cartao_nao_usado": bool(tipo_decisao in ("cartao", "mista") and not cartao),
        "jornadas": jornadas, "parametros": dc.get("parametros_globais_apuracao") or {},
        "cartao": cartao, "p4_global": p4, "p4_especifica": esp,
    }


def _idp_vigente(m):
    """A execução que o caso deve exibir: a ÚLTIMA que chegou ao cálculo.

    Era `m.iloc[-1]` — a última da PROC, chegasse ela ao P10 ou não. Com lote em
    voo isso quebra o painel inteiro: a execução recém-criada já está na PROC e
    ainda não tem P10a, então `_ultimo()` não acha linha nenhuma e o caso sai com
    data nula e total zero, apagando a rodada BOA anterior. Em 02/10/2026,
    renderizar no meio de um lote produziu 95 casos sem data e 134 zeros
    artificiais; o painel gerado duas horas antes, com o mesmo código, tinha 3 e
    nenhum. O sintoma é de dado corrompido e a causa é de relógio.

    Cai na última da PROC só quando NENHUMA chegou ao cálculo — aí o caso é
    legitimamente "rodou e ainda não calculou", e é assim que ele tem de aparecer.

    Só a execução EM ANDAMENTO (sem P10 e sem erro) é pulada. A que TERMINOU com erro
    depois do último cálculo é a vigente: o processo rodou de novo e travou, então o
    caso é FT Travado, e não o cálculo antigo (0001019-28.2022.5.09.0088 mostrava o
    cálculo de 23/07 como apto depois de três execuções com erro em set–out/2026).
    """
    def com_calc(i):
        return any(len(df) and len(_linhas(df, "id_processado", i)) for df in (P10A, P10B))

    def terminou_com_erro(i):
        if not len(STATUS) or "status" not in STATUS.columns:
            return False
        sub = _linhas(STATUS, "id_processado", i).sort_values("criado_em")
        return bool(len(sub)) and str(sub.iloc[-1]["status"]).upper() == "ERRO"

    for i in range(len(m) - 1, -1, -1):
        idp = m.iloc[i]["id_processado"]
        if com_calc(idp) or terminou_com_erro(idp):
            return idp
    return m.iloc[-1]["id_processado"]


def montar_caso(cnj):
    cnj_d = "".join(c for c in cnj if c.isdigit())
    m = _linhas(PROC, "cnj", cnj_d).sort_values("criado_em")
    if not len(m):
        return None
    idp = _idp_vigente(m)

    def _data_proc():
        for df in (P10A, P10B, P9A, DEF):
            sub = _linhas(df, "id_processado", idp).sort_values("criado_em")
            if len(sub):
                return str(sub.iloc[-1]["criado_em"])[:10]
        return None
    data_processamento = _data_proc()

    deferidas = _ultimo(DEF, idp, "verbas_deferidas") or []
    _codigos = {d.get("codigo_glossario") for d in deferidas if d.get("codigo_glossario")}
    codigos_inelegiveis = sorted(_codigos & INELEGIVEIS)
    apto = not codigos_inelegiveis
    rpv = _ultimo(P10A, idp, "resultados_por_verba") or []          # principal (P10a)
    resc = _ultimo(P10B, idp, "resultados_rescisorias") or []       # rescisórias (P10b)
    nc_p9a = _ultimo(P9A, idp, "verbas_nao_calculaveis") or []      # não-calculáveis (P9a)
    mapa_p9a = _ultimo(P9A, idp, "mapa_execucao") or []             # P9a: insumos/roteamento por verba
    ap_p9b = _ultimo(P9B, idp, "apuracao_por_verba") or []          # P9b: apuração mensal por verba
    _p9a_por_id = {x.get("id_verba"): x for x in mapa_p9a}
    _p9b_por_id = {x.get("id_verba"): x for x in ap_p9b}

    def _p9a_de(vid):
        """Saída integral do P9a (mapa_execucao) da verba — insumos gerais, sem competências."""
        return _p9a_por_id.get(vid)

    def _p9b_de(vid):
        """Saída integral do P9b da verba, com APENAS 1 competência (amostra) p/ não repetir."""
        it = _p9b_por_id.get(vid)
        if not it:
            return None
        comps = it.get("competencias") or []
        amostra = dict(it)
        amostra["competencias"] = comps[:1]               # só a 1ª competência como amostra
        amostra["_total_competencias"] = len(comps)       # quantas existem no total
        return amostra

    # P8 (passthrough no P9a): calendário por competência. É a ÚNICA fonte dos
    # DIAS da IA — o P10 guarda horas e devolve `dias_trabalhados` nulo, e era por
    # isso que a coluna Dias saía vazia na tela.
    _ctx = _ultimo(P9A, idp, "contexto_mensal") or []
    cal_p8 = {}
    for it in (_ctx if isinstance(_ctx, list) else []):
        c = (it or {}).get("competencia")
        cal = (it or {}).get("calendario_mensal") or {}
        if not c or not cal:
            continue
        dec, ev, res = (cal.get("decomposicao_dias") or {}, cal.get("eventos_e_deducoes") or {},
                        cal.get("resultados_consolidados") or {})
        cal_p8[_comp(c)] = {
            "dias": res.get("dias_trabalhados_efetivos"),
            "uteis": dec.get("dias_uteis_brutos"), "total_mes": dec.get("total_dias_mes"),
            "dsr": dec.get("dias_dsr_brutos"), "dsr_remunerar": res.get("dias_dsr_a_remunerar"),
            "ferias": ev.get("dias_ferias_em_dia_util"), "feriados": ev.get("dias_feriados_em_dia_util"),
            "afast": ev.get("dias_afastamentos_em_dia_util"),
            "horas_contratuais": (cal.get("apuracao_horas") or {}).get("total_horas_contratuais_mes"),
        }
    # fator de correção da IA por (verba, competência), da tabela consolidada
    _ind_ia = {}
    _c10a_ind = _cons(C10A, cnj_d)
    if len(_c10a_ind) and "atualizacao_monetaria_indice_correcao_monetaria" in _c10a_ind.columns:
        for _, r in _c10a_ind.iterrows():
            f = _f(r.get("atualizacao_monetaria_indice_correcao_monetaria"))
            if f is not None:
                _ind_ia[(r.get("id_verba"), _comp(str(r.get("competencia"))))] = f

    holer = _ultimo(HOLE, idp, "verbas_filtradas") or []
    refl_sub = _linhas(REFL, "id_processado", idp).sort_values("criado_em")
    refl_row = refl_sub.iloc[-1] if len(refl_sub) else None

    # P4 editor (EDITOR_DECISOES): é a lista que o P9a/P10a numeram, e cada verba
    # traz o próprio `id_verba`. O DEF (infos_decisoes) é anterior ao editor e,
    # casado por posição, apontava para outra verba em 68 de 2.666 (14/10/2026);
    # com o editor, 1. Sem linha do editor (rodada antiga), cai no DEF posicional.
    _editor = {e.get("id_verba"): e for e in (_ultimo(EDT, idp, "verbas") or [])
               if isinstance(e, dict) and e.get("id_verba")}

    def _entrada_p4(vid):
        if vid in _editor:
            return _editor[vid]
        try:
            i = int(vid.split("_")[1]) - 1
        except (ValueError, IndexError, AttributeError):
            return None
        return deferidas[i] if 0 <= i < len(deferidas) else None

    def nome_lift(vid):
        d = _entrada_p4(vid)
        if not d:
            return vid
        nm = (d.get("nome_verba") or "").strip()
        # nome veio como código cru (ex.: "BT052") -> resolve pelo de-para
        if re.fullmatch(r"BT\d+", nm):
            return GLOSSARIO_NOME.get(nm, nm)
        if not nm:
            cod = d.get("codigo_glossario")
            return GLOSSARIO_NOME.get(cod, cod or vid)
        return nm

    def comps_lift(v):
        out = {}
        for c in v.get("competencias", []):
            mm = c.get("memoria_de_calculo_estruturada") or {}
            tipo = mm.get("tipo_calculo") or ""
            out[_comp(c["competencia"])] = {
                "base": mm.get("base_calculo_bruta"),
                "base_fixa": mm.get("base_fixa"), "base_variavel": mm.get("base_variavel"),
                "subtotal_fixo": mm.get("subtotal_fixo"), "subtotal_variavel": mm.get("subtotal_variavel"),
                "percentual": mm.get("percentual_da_verba"),
                "dias": mm.get("dias_trabalhados"),
                "horas": mm.get("quantidade_horas"),
                "valor": c.get("valor_final_competencia"),
                # dedução do que já foi pago na folha: o `valor_final_competencia`
                # já vem líquido (= valor_mensal_calculado − valores_compensados),
                # como o "Diferença" do PJC. Guardamos as duas parcelas p/ comparar
                # a dedução em si — valor líquido igual pode esconder bruto e
                # dedução ambos errados, e dedução zerada é o padrão da IA.
                "valor_bruto": c.get("valor_mensal_calculado"),
                "compensado": c.get("valores_compensados"),
                "memoria": c.get("memoria_textual"),
                "s340": ("s340" in tipo) or (mm.get("base_fixa") is not None and mm.get("base_variavel") is not None),
            }
        return out

    def _cod_lift(vid):
        d = _entrada_p4(vid)
        return d.get("codigo_glossario") if d else None

    # código da verba: prefere o `reflexos_base.codigo_glossario` (por-linha, no
    # próprio P10A) e cai no P4 (editor, ou DEF posicional) só se faltar.
    # O nome só existe no P4. Se ainda assim os códigos divergem (resto de
    # desalinhamento, ou rodada sem editor caindo no DEF — ex. 0010416 com
    # "Honorários Periciais" no lugar de uma HE BT089 de R$ 1.925), o nome sai do
    # glossário pelo código do P10a: verba com código real fica e soma.
    def _nome_verba(v):
        c10 = (v.get("reflexos_base") or {}).get("codigo_glossario")
        c4 = _cod_lift(v["id_verba"])
        if c10 and c4 and c10 != c4:
            return GLOSSARIO_NOME.get(c10, c10)
        return nome_lift(v["id_verba"])

    lift_verbas = [{"id_verba": v["id_verba"], "nome": _nome_verba(v),
                    "codigo": (v.get("reflexos_base") or {}).get("codigo_glossario") or _cod_lift(v["id_verba"]),
                    "total": round(v.get("total_verba") or 0, 2), "comps": comps_lift(v)} for v in rpv]
    _nome_por_id = {lv["id_verba"]: lv["nome"] for lv in lift_verbas}

    pjc = _parse_pjc_cached(cnj)
    # 07/11/2026: "HORAS SOBREAVISO" não é reflexo ("SOBRE" só como palavra inteira). Aplicado aqui, sobre o PJC
    # já lido do cache, para não reler os ~4.700 PJCs (bump de _PJC_SCHEMA levava ~40 h). O .pjc nativo marca
    # reflexo também pela classe; só desmarca quando o nome não tem "SOBRE" inteiro e não é da classe Reflexo.
    if pjc and pjc.get("verbas"):
        for _v in pjc["verbas"]:
            if _v.get("reflexo") and "SOBREAVISO" in _v["nome"].upper() and not re.search(r"\bSOBRE\b", _v["nome"].upper()):
                _v["reflexo"] = False
    # PJC ainda não carregado: não há gabarito. O caso continua sendo montado (o
    # lado LIFT é analisável sozinho), mas TODO campo de referência fica vazio e
    # nenhuma acurácia é calculada — comparar contra "nada" daria 0% e sujaria as
    # médias. O flag `sem_pjc` viaja até a tela para gatear os agregados.
    sem_pjc = bool(pjc.get("_sem_pjc"))
    # "Observações de cálculo" (campo do formulário Zeev, trazido pelo auto_pjc):
    # a metodologia que o cálculo de referência declara (período limitado a
    # holerites, dedução de ausências, IPCA-E/SELIC...). Ajuda a explicar a origem
    # de uma divergência em vez de adivinhar. Arquivo local, como o pjc.pdf.
    _obs_fp = Path(f"casos/{cnj}/observacoes_calculo.txt")
    observacoes_calculo = _obs_fp.read_text(encoding="utf-8").strip() if _obs_fp.exists() else None
    # ---- MULTAS do PJC (bloco "Multas e Indenizações", só no .pjc) ----
    # O PJC soma ao crédito as multas lançadas à parte (embargos protelatórios,
    # litigância de má-fé, astreinte); o painel lia só as verbas, e a BT073 da IA
    # aparecia "a mais" (0000399: R$ 60.000). Entram aqui como linha do PJC sem
    # competência, marcadas `multa`, e só as que o RECLAMANTE recebe — a devida
    # pelo reclamante ou a terceiro (IRRF) não é crédito e vai para o aviso de
    # "fora do principal". Casamento: BT073 da IA, no loop das rescisórias; multa
    # cujo nome é indenização (ex.: "DANO MORAL") casa pela natureza, com o teto.
    # Fonte PDF não tem esse bloco: lá nada muda (limite registrado).
    _multas = pjc.get("multas") or []
    _nomes_pjc = {v["nome"] for v in pjc["verbas"]}
    _linhas_multa = []
    for m in _multas:
        if not m.get("credor_reclamante"):
            continue
        nm = m["nome"] if m["nome"] not in _nomes_pjc else f"{m['nome']} (multa)"
        _nomes_pjc.add(nm)
        _linhas_multa.append({"nome": nm, "soma_devido": m["valor"], "soma_pago": 0.0,
                              "soma_corrigido": m["corrigido"], "reflexo": False,
                              "competencias": [], "multa": True})
    if _linhas_multa:
        pjc = {**pjc, "verbas": list(pjc["verbas"]) + _linhas_multa}
    pjc_principais = [v for v in pjc["verbas"] if not v["reflexo"]]
    dias_fer = pjc["dias_ferias_mes"]
    cab = pjc["cabecalho"]

    # ---- FORA DA RÉGUA: execução com erro e gabarito errado ----
    # Dois casos que não são acurácia ruim, são ausência de medida, e por isso
    # saem de assertividade/mediana/totais de comparação (continuam na tela):
    #  - "nao_calculado": a execução parou com ERRO antes do P10 (ver
    #    `_erro_execucao`). Antes entrava como 0% e derrubava a mediana.
    #  - "gabarito_a_corrigir": o PJC em casos/<CNJ>/ é de OUTRO processo (CNJ do
    #    .pjc ≠ CNJ do caso) ou é outro cálculo do mesmo processo (curadoria
    #    GABARITO_ID_CALCULO). Sem o arquivo certo localmente, nada é inventado:
    #    o caso só sai da régua até o gabarito ser trocado.
    fora_regua, motivo_fora_regua = None, None
    erro_exec = _erro_execucao(idp)
    if erro_exec:
        fora_regua = "nao_calculado"
        motivo_fora_regua = f"{erro_exec['etapa']}: {erro_exec['motivo'] or 'sem motivo registrado'}"
    elif not sem_pjc:
        _proc_ref = "".join(ch for ch in str(cab.get("processo") or "") if ch.isdigit())
        if len(_proc_ref) == 20 and _proc_ref != cnj_d:
            fora_regua = "gabarito_a_corrigir"
            motivo_fora_regua = (f"o cálculo de referência em casos/{cnj}/ é do processo "
                                 f"{cab.get('processo')}, não deste")
        elif cnj in GABARITO_ID_CALCULO and str(cab.get("id_calculo") or "") != GABARITO_ID_CALCULO[cnj]:
            fora_regua = "gabarito_a_corrigir"
            motivo_fora_regua = (f"o .pjc local é o cálculo {cab.get('id_calculo') or '?'}; o de referência "
                                 f"é o {GABARITO_ID_CALCULO[cnj]}, que não está em casos/{cnj}/")
    # PJC e PDF de cálculos diferentes (ids divergem): vale o .pjc e o caso fica marcado (Raíra, 30/10/2026);
    # só se corrige o gabarito dos que forem aptos com assertividade baixa
    gabarito_pdf_dif = None
    if not fora_regua and not sem_pjc and (pjc.get("_outro_calculo") or {}).get("usado") == "pjc":
        _oc = pjc["_outro_calculo"]
        gabarito_pdf_dif = {"id_pjc": _oc["id_pjc"], "id_pdf": _oc["id_pdf"]}
    # sem medida = sem gabarito OU fora da régua: nenhuma acurácia do caso é calculada
    sem_medida = sem_pjc or bool(fora_regua)
    # dados cadastrais: P1 (partes, admissão/demissão com fonte, período não
    # prescrito) × cabeçalho da referência. Sem P1 no recorte, sai vazio (não
    # inventa) — re-rodar `ingerir.py` traz a tabela.
    _p1 = _ultimo(P1, idp, "dados_extraidos")
    cadastro = _cadastro(_p1, cab)
    # férias que o P1 leu da ficha de registro. None = sem P1 (não se sabe);
    # [] = a ficha não tem férias, e o calendário conta todo dia como trabalhado
    ferias_p1 = (((_p1.get("historico_funcional") or {}).get("datas_ferias_concedidas"))
                 if isinstance(_p1, dict) else None)
    fim_per = None
    ini_per = None
    if cab.get("periodo_calculo") and " a " in cab["periodo_calculo"]:
        a, b = cab["periodo_calculo"].split(" a ")
        def _d(s):
            try:
                return date(*map(int, reversed(s.split("/"))))
            except Exception:
                return None
        ini_per, fim_per = _d(a), _d(b)

    def dias_trab_pjc(comp):
        if sem_pjc:
            return None      # sem período de cálculo do PJC não há dias do PJC
        ano, mes = map(int, comp.split("-"))
        ult = calendar.monthrange(ano, mes)[1]
        d1, d2 = date(ano, mes, 1), date(ano, mes, ult)
        if ini_per and d1 < ini_per <= d2:
            d1 = ini_per
        if fim_per and d1 <= fim_per < d2:
            d2 = fim_per
        return (d2 - d1).days + 1 - dias_fer.get(comp, 0)

    # ---- match: cada verba LIFT -> verbas PJC por nome (não soma; mantém componentes)
    from comparar import normaliza

    def _toks(n):
        return {t for t in normaliza(n).split() if len(t) >= 4}

    atrib = defaultdict(list)
    usados = set()
    # índice código glossário -> verbas LIFT com esse código (match autoritativo)
    _lift_por_cod = defaultdict(list)
    for i, lv in enumerate(lift_verbas):
        if lv.get("codigo"):
            _lift_por_cod[lv["codigo"]].append(i)
    for p in pjc_principais:
        if p.get("multa"):
            continue   # multa não é verba mensal: casa no loop das rescisórias
        # CÓDIGO MANDA: se o de-para resolve o nome do PJC a um BTxxx e existe verba
        # LIFT com esse código, casa por código (autoritativo).
        info = _pjc_info(p["nome"])
        cod = info["codigo"] if info else None
        # NOME GENÉRICO DE HE (07/11/2026, mesma regra do src/matcher_verbas.py): "HORAS EXTRAS 50%"
        # sem qualificação é a hora além da 8ª (BT089); BT081 só se o caso não tem BT089. Sem isso o
        # fuzzy dava a linha ao intervalo ou à 7ª/8ª (0000409-64: BT081 R$ 1.742 × PJC R$ 166.981,
        # enquanto o BT089 de R$ 89.211 ficava "só IA").
        _gen = " ".join(normaliza(p["nome"]).replace("%", " ").split())
        if not cod and _gen in _GENERICO_HE:
            _c = next((c for c in ("BT089", "BT081") if _lift_por_cod.get(c)), None)
            if _c:
                i = min(_lift_por_cod[_c], key=lambda j: abs((lift_verbas[j]["total"] or 0) - (p.get("soma_devido") or 0)))
                atrib[i].append(p)
                usados.add(p["nome"])
                continue
        if cod and _lift_por_cod.get(cod):
            # >1 verba LIFT com o mesmo código: casa com a de valor mais próximo
            # (não empilha todos os componentes do PJC na primeira verba).
            idxs = _lift_por_cod[cod]
            i = min(idxs, key=lambda j: abs((lift_verbas[j]["total"] or 0) - (p.get("soma_devido") or 0)))
            atrib[i].append(p)
            usados.add(p["nome"])
            continue
        if cod:
            # de-para resolveu o código mas NENHUMA verba mensal LIFT tem esse código:
            # a verba é de outra lista (ex.: rescisória, tratada à parte). NÃO cai no
            # fuzzy — senão contamina verba de nome parecido (ex.: dano moral casando
            # com "Indenização por Supressão de Intervalo").
            continue
        # nome do PJC não resolvido no de-para -> fuzzy por nome (última opção)
        cand = []
        for i, lv in enumerate(lift_verbas):
            # só considera match se houver token significativo (>=4 letras) em comum,
            # evitando casar "Horas Extras" com "Diferenças de Remuneração Variável"
            partilha = bool(_toks(p["nome"]) & _toks(lv["nome"])) and not _incompat(p["nome"], lv["nome"])
            cand.append((score(p["nome"], lv["nome"]) if partilha else 0.0, i))
        s, i = max(cand) if cand else (0.0, -1)
        if s >= 0.4:
            atrib[i].append(p)
            usados.add(p["nome"])

    verbas_out = []
    componentes_perdidos = []  # PJC matched mas que a IA não computou (base não bate)

    for i, lv in enumerate(lift_verbas):
        pjcs = atrib.get(i, [])
        # escolhe o componente PJC que a IA de fato calculou (base mais próxima)
        comp_amostra = next(iter(lv["comps"]), None)
        base_ia_amostra = lv["comps"].get(comp_amostra, {}).get("base") if comp_amostra else None
        def alinha_base(p):
            cc = next((c for c in p["competencias"] if c["competencia"] == comp_amostra), None)
            if cc and cc.get("base") and base_ia_amostra:
                return abs(cc["base"] - base_ia_amostra) / max(cc["base"], base_ia_amostra)
            return 9
        principal = min(pjcs, key=alinha_base) if pjcs else None
        # UMA linha por verba do PJC (Raíra, 16/10/2026): a verba da IA fica com a verba do PJC
        # mais parecida; as outras voltam para as sobras e ganham linha própria (casam com outra
        # verba da IA, se houver, ou ficam "só PJC"). Antes elas eram somadas embaixo desta
        # linha (0000740-56: três verbas de HE do PJC contra o BT089 da IA).
        for p in pjcs:
            if p is not principal:
                usados.discard(p["nome"])
        pjcs = [principal] if principal else []
        outros = []

        # competências: IA + componentes PJC (separados)
        meses = sorted(set(lv["comps"]) | {c["competencia"] for p in pjcs for c in p["competencias"]})
        comps = []
        for mes in meses:
            a = lv["comps"].get(mes, {})
            pjc_comp = []
            for p in pjcs:
                cc = next((c for c in p["competencias"] if c["competencia"] == mes), None)
                if cc:
                    pjc_comp.append({"rotulo": _rotulo_pjc(p["nome"]), "base": cc["base"],
                                     "indice": cc.get("indice"), "corrigido": cc.get("corrigido"),
                                     "perc": round(cc["multiplicador"] * 100, 2) if cc.get("multiplicador") else None,
                                     "horas": cc.get("quantidade"), "valor": cc["devido"],
                                     "valor_bruto": cc.get("devido_bruto"), "pago": cc.get("pago")})
            _c8 = cal_p8.get(mes) or {}
            comps.append({"competencia": mes, "ferias_pjc": dias_fer.get(mes, 0),
                          "dias_pjc": dias_trab_pjc(mes),
                          "cal_p8": _c8 or None,
                          "ia": {"base": a.get("base"), "perc": a.get("percentual"),
                                 # dias: P10 quase sempre nulo -> cai no P8 (dias
                                 # trabalhados efetivos = úteis − férias/feriado/afast.)
                                 "dias": a.get("dias") if a.get("dias") is not None else _c8.get("dias"),
                                 "dias_fonte": ("P10" if a.get("dias") is not None
                                                else ("P8" if _c8.get("dias") is not None else None)),
                                 "indice": _ind_ia.get((lv["id_verba"], mes)),
                                 "horas": a.get("horas"), "valor": a.get("valor"),
                                 "valor_bruto": a.get("valor_bruto"), "compensado": a.get("compensado"),
                                 "base_fixa": a.get("base_fixa"), "base_variavel": a.get("base_variavel"),
                                 "subtotal_fixo": a.get("subtotal_fixo"), "subtotal_variavel": a.get("subtotal_variavel"),
                                 "memoria": a.get("memoria"), "s340": a.get("s340", False)},
                          "pjc": pjc_comp})

        # acurácia reflete a verba INTEIRA (soma de todos os componentes do PJC),
        # não só o componente que a IA acertou. Assim o que a IA deixou de computar
        # (ex.: base variável) puxa a acurácia para baixo, como deve.
        total_pjc_full = round(sum(p["soma_devido"] for p in pjcs), 2) if pjcs else None
        # dedução acumulada dos dois lados (o que já foi pago na folha e é abatido)
        total_compensado_ia = round(sum(x["ia"].get("compensado") or 0 for x in comps), 2)
        total_pago_pjc = round(sum(p.get("soma_pago") or 0 for p in pjcs), 2) if pjcs else None
        # denominador é o PJC da verba inteira, e a regra D4 vale aqui também:
        # sem componente do PJC não há referência e fica None, mas PJC zero com
        # IA zero é 100% e PJC zero com IA qualquer é 0%.
        acuracia = None if not pjcs else assertividade(lv["total"], total_pjc_full)
        acuracia_fixa = None  # acurácia só no componente que a IA calculou (para contexto)
        if principal:
            acuracia_fixa = assertividade(lv["total"], principal["soma_devido"])

        for p in outros:
            componentes_perdidos.append({"verba_ia": lv["nome"], "rotulo": _rotulo_pjc(p["nome"]),
                                         "nome_pjc": p["nome"], "total_pjc": round(p["soma_devido"], 2)})

        verbas_out.append({
            "nome_ia": lv["nome"], "nome_pjc": principal["nome"] if principal else None,
            "codigo": lv.get("codigo"),
            "_idv": lv["id_verba"], "_pjc_nomes": [x["nome"] for x in pjcs],
            "rotulo_principal": _rotulo_pjc(principal["nome"]) if principal else None,
            "rotulos_pjc": [_rotulo_pjc(p["nome"]) for p in pjcs],
            "status": "coincide" if principal else "so_ia",
            "total_ia": lv["total"], "total_pjc": total_pjc_full, "acuracia": acuracia,
            "acuracia_componente": acuracia_fixa,
            "compensado_ia": total_compensado_ia, "pago_pjc": total_pago_pjc,
            "competencias": comps,
            # bloco do P4 vem do DEF (tem contexto/explicação); posição desalinhada
            # com o código da verba -> procura pelo código
            "p4": (_p4_por_cod(deferidas, lv["codigo"])
                   if lv.get("codigo") and ((_p4_de(deferidas, lv["id_verba"]) or {}).get("codigo_glossario")
                                            not in (None, lv["codigo"]))
                   else _p4_de(deferidas, lv["id_verba"])),
            "p9a_raw": _p9a_de(lv["id_verba"]), "p9b_raw": _p9b_de(lv["id_verba"]),
            "componente_perdido": [_rotulo_pjc(p["nome"]) for p in outros],
            "usa_s340": any(x["ia"].get("s340") for x in comps),
        })

    def _match_pjc(nome, pool, alvo=None):
        # linha de multa fica de fora do fuzzy: o token "multa" casaria a multa de
        # embargos com a do art. 477, que é outra verba. Multa casa só no BT073
        # (ou pela natureza, quando o PJC lança uma indenização como multa).
        # Linha do PJC que é indenização (dano moral etc.) só casa com verba da IA
        # que também é: "Desconto Indevido" pegava "DANO MORAL - DESCONTO INDEVIDO".
        nat_ia = _natureza(nome)
        cand = [p for p in pool if p["nome"] not in usados and not p.get("multa")
                and not _incompat(nome, p["nome"])
                and (nat_ia or not _natureza(p["nome"]))
                and (_toks(nome) & _toks(p["nome"])) and score(nome, p["nome"]) >= 0.4]
        if len(cand) > 1:
            # 07/11/2026: primeiro o nome mais parecido (palavras em comum), só depois o valor; "Saldo de Salário"
            # pegava "SALÁRIO RETIDO" (valor mais perto) com "SALDO DE SALÁRIO" na lista (0100275-60)
            _ov = {id(p): len(_toks(nome) & _toks(p["nome"])) for p in cand}
            _mx = max(_ov.values())
            cand = [p for p in cand if _ov[id(p)] == _mx]
        if len(cand) > 1 and alvo is not None:
            # mais de uma linha com nome parecido (ex.: dano material "PARC.
            # VENCIDAS" × "PARC. VINCENDAS"): a de valor mais próximo, não a 1ª
            return min(cand, key=lambda p: abs((p.get("soma_devido") or 0) - alvo))
        return cand[0] if cand else None

    def _match_natureza(cod, pool):
        """Linha do PJC com a mesma natureza de indenização do código de teto
        (BT052/BT050/BT040), pelo NOME — "02. DANO MORAL", "INDENIZAÇÃO POR DANO
        MORAL". Preferência pela natureza própria do código; empate, pelo nome
        mais parecido com o do glossário. Nome que também indica outra natureza
        (dano moral E material na mesma linha) fica de fora: na dúvida não casa."""
        prefs = _NAT_TETO.get(cod) or ()
        cand = []
        for p in pool:
            if p["nome"] in usados or p.get("reflexo"):
                continue
            nat = _natureza(p["nome"])
            if not nat or len(nat) > 1 and "material" in nat:
                continue
            rank = next((k for k, n in enumerate(prefs) if n in nat), None)
            if rank is None:
                continue
            # natureza a mais no nome (moral + acidente) perde para a pura: a linha
            # "DANO MORAL - DOENÇA DO TRABALHO" é do BT040, não do BT052
            extra = int(bool(nat - set(prefs)))
            cand.append((rank, extra, -score(GLOSSARIO_NOME.get(cod, cod), p["nome"]), p["nome"], p))
        return min(cand, key=lambda x: x[:4])[4] if cand else None

    def _match_multa(tot, pool):
        """Multa do PJC (bloco de multas) para a BT073 da IA: a de valor mais
        próximo entre as que o reclamante recebe e que não são indenização."""
        cand = [p for p in pool if p.get("multa") and p["nome"] not in usados and not _natureza(p["nome"])]
        return min(cand, key=lambda p: abs((p.get("soma_devido") or 0) - (tot or 0))) if cand else None

    def _acc(ia, pj):
        if not pj:
            return None
        return acuracia_verba(ia, pj)

    # ---- REFLEXOS: linhas separadas, espelhando "X SOBRE Y" do PJC ----
    # Acurácia da VERBA-BASE no mesmo caso, por nome: o reflexo multiplica o
    # principal, então reflexo ruim com base ruim é erro HERDADO (um erro contado
    # cinco vezes), e reflexo ruim com base certa é erro do reflexo. Sem esse par
    # não dá para separar os dois — e a leitura do número fica errada.
    _acc_base_por_nome = {v["nome_ia"]: v["acuracia"] for v in verbas_out
                          if v.get("nome_ia") and v.get("status") == "coincide"}
    _cod_base_por_nome = {v["nome_ia"]: v.get("codigo") for v in verbas_out if v.get("nome_ia")}
    _tot_base_ia = {v["nome_ia"]: v.get("total_ia") for v in verbas_out if v.get("nome_ia")}
    _tot_base_pjc = {v["nome_ia"]: v.get("total_pjc") for v in verbas_out if v.get("nome_ia")}
    _pjc_par_por_nome = {v["nome_ia"]: v.get("_pjc_nomes") or [] for v in verbas_out
                         if v.get("nome_ia") and v.get("status") == "coincide" and not v.get("is_reflexo")}
    pjc_reflexos = [v for v in pjc["verbas"] if v["reflexo"]]
    if refl_row is not None:
        for tipo, (label, _kw) in _REFLEXO_TIPOS.items():
            for item in (_parse(refl_row.get(tipo)) or []):
                tot = round(_total_reflexo(tipo, item), 2)
                if not tot:
                    continue
                vid = item.get("id_verba")
                nome_v = (_nome_por_id.get(vid) or nome_lift(vid)) if vid else "?"
                base_ia = _marca_por_fora(nome_v, _toks(nome_v))
                perc_ia = _perc_base(nome_v)
                cand = []
                for p in pjc_reflexos:
                    if _pjc_reflexo_tipo(p["nome"]) != tipo or p["nome"] in usados:
                        continue
                    base_pjc = _apos_sobre(p["nome"])
                    if _incompat(nome_v, base_pjc):
                        continue    # HE 50% × HE 100%/384, intra × interjornada
                    perc_pjc = _perc_base(p["nome"])
                    if perc_ia and perc_pjc and not (perc_ia & perc_pjc):
                        continue    # HE 50% × HE 75%: verbas-base distintas
                    n = len(base_ia & _base_apos_sobre(p["nome"]))
                    if n:
                        # o nº de tokens em comum empata entre as HEs do mesmo caso;
                        # desempata pela similaridade do texto da base
                        cand.append((n, score(nome_v, base_pjc), p))
                # o reflexo segue o par da principal: se a verba-base da IA casou com a verba X
                # do PJC, fica com o reflexo "… sobre X" (0000740-56: o 13º da HE da IA casava
                # com o 13º sobre o FERIADO do PJC, e o 13º sobre a verba 01 ficava "só PJC")
                _pares = [normaliza(n) for n in _pjc_par_por_nome.get(nome_v, [])]
                if _pares:
                    _pref = [x for x in cand if any(pn and pn in normaliza(_apos_sobre(x[2]["nome"])) for pn in _pares)]
                    if _pref:
                        cand = _pref
                melhor = max(cand, key=lambda x: (x[0], x[1]))[2] if cand else None
                # soma as FATIAS DE PERÍODO da mesma verba-base (canônica), como o
                # loop das principais já faz — senão a fatia sobrante vira "só PJC"
                # e a acurácia do reflexo despenca por pareamento.
                fatias = ([p for _n, _s, p in cand
                           if _base_canon(p["nome"]) == _base_canon(melhor["nome"])]
                          if melhor else [])
                tpjc = round(sum(p["soma_devido"] for p in fatias), 2) if fatias else None
                for p in fatias:
                    usados.add(p["nome"])
                verbas_out.append({
                    "nome_ia": f"{label} sobre {nome_v}",
                    "nome_pjc": ((melhor["nome"] + (f" (+{len(fatias) - 1} fatia(s) de período somada(s))"
                                                    if len(fatias) > 1 else ""))
                                 if melhor else None),
                    "rotulo_principal": None, "rotulos_pjc": [], "status": "coincide" if melhor else "so_ia",
                    "total_ia": tot, "total_pjc": tpjc, "acuracia": _acc(tot, tpjc), "acuracia_componente": None,
                    "competencias": [], "p4": None, "componente_perdido": [], "usa_s340": False, "is_reflexo": True,
                    "_idv": vid, "_tipo_refl": tipo,
                    "_pjc_nomes": [x["nome"] for x in fatias],
                    "tipo_reflexo": label, "verba_base": nome_v,
                    "codigo_base": _cod_base_por_nome.get(nome_v),
                    "acuracia_base": _acc_base_por_nome.get(nome_v),
                    # proporção reflexo/base dos dois lados: a assinatura do viés
                    # "coeficiente fixo (IA) × avos apurados (PJC)" aparece aqui.
                    "ratio_base_ia": (round(tot / _tot_base_ia[nome_v], 4)
                                      if _tot_base_ia.get(nome_v) else None),
                    "ratio_base_pjc": (round(tpjc / _tot_base_pjc[nome_v], 4)
                                       if tpjc and _tot_base_pjc.get(nome_v) else None),
                })

    # ---- RESCISÓRIAS (P10b) ----
    for rv in resc:
        cod = rv.get("codigo_glossario")
        nome = rv.get("verba_glossario") or GLOSSARIO_NOME.get(cod) or cod or "Rescisória"
        tot = round(rv.get("total_verba") or 0, 2)
        # ordem de casamento: (1) BT073 → multa do bloco de multas do PJC;
        # (2) código de teto → linha do PJC com a mesma natureza pelo nome (antes
        # do fuzzy, que casava BT052 com "INDENIZAÇÃO ESTABILITÁRIA" de R$ 2.080 em
        # 0010341 enquanto "Indenização por Danos Morais" R$ 20.000 ficava só PJC);
        # (3) fuzzy de nome, como sempre foi.
        pm = None
        if cod == "BT073":
            pm = _match_multa(tot, pjc_principais)
        elif cod in CODIGOS_TETO_DANO:
            pm = _match_natureza(cod, pjc_principais)
            if pm is None:
                # sem a natureza própria do código, qualquer linha de DANO do PJC (moral,
                # assédio, acidente): a IA às vezes lança o dano moral do acidente como BT040
                # (1000225-08: "INDENIZAÇÃO POR DANO MORAL" de R$ 25 mil contra o BT040)
                _viz = [c2 for c2 in CODIGOS_TETO_DANO if c2 != cod]
                pm = next((m for m in (_match_natureza(c2, pjc_principais) for c2 in _viz) if m), None)
        # verba de teto (dano) só casa pela natureza: o fuzzy casava "Indenização por Danos
        # Morais" com "INDENIZAÇÃO SUBSTITUTIVA ESTABILIDADE" pelo token "indenização" e o
        # teto cortava o PJC de R$ 90 mil para R$ 5 mil (0000558-61, 1000225-08, 1000617-36,
        # 0020486-56; 16/10/2026). Sem natureza no nome do PJC, não casa: a linha do PJC fica
        # livre para a verba certa da IA (ex.: a estabilidade) ou como "só PJC".
        if cod not in CODIGOS_TETO_DANO:
            pm = pm or _match_pjc(nome, pjc_principais, alvo=tot)
        if pm:
            usados.add(pm["nome"])
        pjc_val = pm["soma_devido"] if pm else None
        # Teto do dano moral no FT (BT052 = R$5.000): comparar contra o PJC também
        # CAPADO — mas só quando a IA de fato aplicou o teto (total ≤ 5.000). Senão a
        # acurácia despencaria por divergência de POLÍTICA (o PJC traz o valor cheio
        # que o juiz fixou), não de cálculo. Casos em que a IA NÃO capou (> 5.000,
        # teto não vigente) seguem comparando com o PJC cheio.
        teto = (cod in CODIGOS_TETO_DANO and pjc_val is not None
                and tot <= TETO_DANO_MORAL and pjc_val > TETO_DANO_MORAL)
        pjc_cheio = round(pjc_val, 2) if pjc_val is not None else None
        if teto:
            pjc_val = TETO_DANO_MORAL
        # P4 da MESMA verba: o id do P10b é posicional como o do P4 (verba_0N);
        # pelo código só quando a posição não confere. Com "Não encontrado" o
        # código se repete entre verbas e o 1º de mesmo código era o P4 errado.
        p4_resc = _p4_de(deferidas, rv.get("id_verba") or "")
        if not p4_resc or p4_resc.get("codigo_glossario") != cod:
            p4_resc = _p4_por_cod(deferidas, cod)
        verbas_out.append({
            "nome_ia": nome, "nome_pjc": pm["nome"] if pm else None, "rotulo_principal": None, "rotulos_pjc": [],
            "status": "coincide" if pm else "so_ia", "total_ia": tot,
            "total_pjc": round(pjc_val, 2) if pjc_val is not None else None,
            "acuracia": _acc(tot, pjc_val) if pm else None,
            "acuracia_componente": None, "competencias": [], "p4": p4_resc,
            "_idv": rv.get("id_verba"), "_pjc_nomes": [pm["nome"]] if pm else [],
            "componente_perdido": [], "usa_s340": False, "is_rescisoria": True, "codigo_glossario": cod,
            "teto_pjc": pjc_cheio if teto else None,  # valor cheio do PJC quando capado (transparência)
        })

    # ---- NÃO CALCULÁVEIS (P9a, com razões) ----
    ids_calc = {v["id_verba"] for v in rpv}
    # códigos que de fato FORAM calculados (principal ou rescisória) — não devem
    # reaparecer como "não calculável" (ex.: dano moral BT052 calculado em P10b).
    cods_calc = {rv.get("codigo_glossario") for rv in resc if rv.get("codigo_glossario")}
    for v in rpv:
        try:
            cods_calc.add(deferidas[int(v["id_verba"].split("_")[1]) - 1].get("codigo_glossario"))
        except (ValueError, IndexError, KeyError, AttributeError):
            pass
    nc_ids, nao_calc = set(), []
    for d in nc_p9a:
        if d.get("codigo_glossario") and d.get("codigo_glossario") in cods_calc:
            continue  # já calculada em outro estágio → não é "não calculável"
        vid = d.get("id_verba")
        nc_ids.add(vid)
        nome = d.get("verba_glossario") or (nome_lift(vid) if vid else "?")
        pm = _match_pjc(nome, pjc_principais)
        if pm:
            usados.add(pm["nome"])  # consome a verba do PJC p/ não duplicar como "só PJC"
        verbas_out.append({
            "nome_ia": nome, "nome_pjc": pm["nome"] if pm else None, "rotulo_principal": None, "rotulos_pjc": [],
            "status": "nao_calc", "total_ia": None, "total_pjc": round(pm["soma_devido"], 2) if pm else None,
            "acuracia": None, "competencias": [], "componente_perdido": [], "p4": _p4_de(deferidas, vid) if vid else None,
            "p9a_raw": _p9a_de(vid) if vid else None, "p9b_raw": _p9b_de(vid) if vid else None,
            "motivo_classificacao": d.get("motivo_classificacao"), "codigo_glossario": d.get("codigo_glossario"), "id_verba": vid,
            "natureza": d.get("natureza_juridica"), "_pjc_nomes": [pm["nome"]] if pm else [],
        })
        nao_calc.append(nome)

    # ---- deferidas não calculadas e não classificadas (fallback) ----
    for i in range(len(deferidas)):
        vid = f"verba_0{i + 1}"
        if vid in ids_calc or vid in nc_ids:
            continue
        d = deferidas[i]
        if d.get("codigo_glossario") and d.get("codigo_glossario") in cods_calc:
            continue  # já calculada via rescisórias (P10b) → não é "só IA não calculada"
        nome = d.get("nome_verba")
        p4 = _p4_de(deferidas, vid)
        pm = _match_pjc(nome, pjc_principais)
        if pm:
            usados.add(pm["nome"])  # consome a verba do PJC p/ não duplicar como "só PJC"
        # "sem_pjc" aqui = a verba NÃO aparece no cálculo de referência (o PJC existe
        # e não a traz). Quando a referência sequer subiu, o motivo é outro
        # ("ref_nao_carregada") — não dá para afirmar que o PJC não tem a verba.
        if pm:
            motivo = "no_pjc"
        elif p4 and p4.get("depende_documento"):
            motivo = "documental"
        else:
            motivo = "ref_nao_carregada" if sem_pjc else "sem_pjc"
        verbas_out.append({
            "nome_ia": nome, "nome_pjc": None, "rotulo_principal": None, "rotulos_pjc": [],
            "status": "so_ia", "total_ia": None, "total_pjc": round(pm["soma_devido"], 2) if pm else None,
            "acuracia": None, "competencias": [], "componente_perdido": [], "p4": p4, "motivo_nao_calc": motivo,
            "codigo_glossario": d.get("codigo_glossario"), "id_verba": vid,
            "_pjc_nomes": [pm["nome"]] if pm else [],
        })
        nao_calc.append(nome)

    # ---- PAREAMENTO das sobras: "só IA" × "só PJC" ----
    # Verba com código "Não encontrado" (nome do glossário vira o próprio código)
    # ou com nome que o PJC escreve diferente não casava, e o mesmo dinheiro
    # aparecia duas vezes: a mais na IA e a menos no PJC (0000399: R$ 1,5 mi de
    # "indenização por justa remuneração" × "INDENIZAÇÃO (CONTRIBUIÇÃO
    # INTELECTUAL)"; 0000505: PDE do P4 × "PDE" do PJC; 0000578: prêmio de
    # desligamento × "PDV"). Conservador — na dúvida não casa:
    #  - só sobra com sobra (verba da IA calculada e sem par; linha do PJC não
    #    usada), nunca reflexo, nunca família de HE (tem leitura própria);
    #  - natureza de indenização diferente veta (dano moral × material), e
    #    `_incompat` também (intra × inter, HE 50 × 100);
    #  - casa por VALOR só se for ÚNICO dos dois lados a até 2%; por NOME só com
    #    duas palavras significativas em comum, sigla igual ("PDE" × "(PDE)") ou
    #    sigla do PJC cuja expansão está no nome da IA (`_SIGLAS`).
    #  O nome da IA inclui o do P4 (o do glossário é "Não encontrado").
    _GEN = {"indenizacao", "indenizacoes", "indenizatoria", "indenizatorio", "diferenca", "diferencas",
            "verba", "verbas", "valor", "valores", "pagamento", "parcela", "parcelas", "devido", "devida",
            "devidos", "devidas", "encontrado", "sobre", "reflexo", "reflexos", "total", "integral",
            "proporcional", "proporcionais", "salario", "salarios", "adicional", "multa", "programa", "plano"}
    # o PJC escreve tudo em caixa alta, então "POR"/"USO" também parecem sigla:
    # sigla = 3–5 letras maiúsculas com no máximo uma vogal, fora desta lista
    _SIGLA_STOP = {"CLT", "CPC", "TRT", "TST", "FGTS", "DSR", "RSR", "PJC", "CCT", "ACT", "INSS", "IRRF",
                   "POR", "DOS", "DAS", "NOS", "NAS", "COM", "SEM", "AOS", "SOB", "MES", "ANO", "DIA",
                   "PRO", "SER", "FIM", "LEI", "ART", "PAR", "VIA", "MAIS", "PELO", "PELA", "TRES"}
    _SIGLAS = {"PDV": ("desligamento", "demissao voluntaria", "demissao incentivada"),
               "PDI": ("desligamento incentivado", "demissao incentivada"),
               "PLR": ("participacao nos lucros", "participacao em lucros", "participacao nos resultados")}

    def _sig(n):
        return {t for t in normaliza(n or "").split() if len(t) >= 4 and t not in _GEN}

    def _siglas(n):
        return {s for s in re.findall(r"\b[A-Z]{3,5}\b", n or "")
                if s not in _SIGLA_STOP and sum(ch in "AEIOU" for ch in s) <= 1}

    def _nome_bate(nomes_ia, nome_pjc):
        """'nome' | 'sigla' | None — evidência de nome de que é a mesma verba."""
        sp = _siglas(nome_pjc)
        for n in nomes_ia:
            if len(_sig(n) & _sig(nome_pjc)) >= 2:
                return "nome"
            if sp & _siglas(n):
                return "sigla"
            nn = normaliza(n)
            if any(any(f in nn for f in _SIGLAS.get(s, ())) for s in sp):
                return "sigla"
        return None

    _rx_honor = re.compile(r"honor[aá]r|custas|perit|pericia", re.I)
    sobras_ia = [v for v in verbas_out
                 if v["status"] == "so_ia" and v.get("total_ia") and not v.get("is_reflexo")
                 and not _rx_honor.search(v.get("nome_ia") or "")
                 and not _he_grupo(normaliza(v.get("nome_ia") or ""))]
    sobras_pjc = [p for p in pjc["verbas"]
                  if not p["reflexo"] and p["nome"] not in usados and (p.get("soma_devido") or 0) > 0
                  and not _rx_honor.search(p["nome"]) and not _he_grupo(normaliza(p["nome"]))]

    def _perto(a, b):
        return abs(a - b) / max(abs(a), abs(b)) <= 0.02

    def _radicais(n):
        return {t[:5] for t in _sig(n)}

    def _sem_identidade(v):
        cod = v.get("codigo") or v.get("codigo_glossario")
        return not cod or not re.fullmatch(r"BT\d+", str(cod))

    # Indenização com natureza no nome que o PJC FATIA em linhas da mesma natureza
    # (dano material = "PENSÃO VENCIDAS" + "PENSÃO VINCENDAS"): soma as fatias,
    # como já se faz com os períodos dos reflexos. Antes, o BT051 casava com a
    # linha de DANO MORAL (token "indenização") ou ficava só IA, e as duas fatias
    # só PJC. Fora os códigos de teto: duas linhas de dano moral no PJC são, em
    # geral, duas indenizações (ex.: desconto indevido × doença do trabalho).
    for v in verbas_out:
        cod_v = v.get("codigo_glossario")
        if (not v.get("is_rescisoria") or v["status"] not in ("so_ia", "coincide")
                or not v.get("total_ia") or cod_v in CODIGOS_TETO_DANO):
            continue
        nat_v = _natureza(v.get("nome_ia"))
        if not nat_v:
            continue
        fat = [p for p in pjc["verbas"] if not p["reflexo"] and p["nome"] not in usados
               and (p.get("soma_devido") or 0) > 0 and _natureza(p["nome"]) == nat_v]
        if not fat:
            continue
        for p in fat:
            usados.add(p["nome"])
        tp = round((v.get("total_pjc") or 0) + sum(p["soma_devido"] for p in fat), 2)
        base_nome = v.get("nome_pjc") or fat[0]["nome"]
        n_mais = len(fat) - (0 if v.get("nome_pjc") else 1)
        v.update({"status": "coincide", "total_pjc": tp, "acuracia": _acc(v["total_ia"], tp),
                  "nome_pjc": base_nome + (f" (+{n_mais} linha(s) da mesma natureza somada(s))" if n_mais else ""),
                  "_pjc_nomes": (v.get("_pjc_nomes") or []) + [p["nome"] for p in fat],
                  "pareado_por": v.get("pareado_por") or "natureza"})

    for v in sorted(sobras_ia, key=lambda x: -(x["total_ia"] or 0)):
        if v["status"] != "so_ia":
            continue   # já casou acima (fatias da mesma natureza)
        nomes_ia = [v.get("nome_ia") or ""] + ([v["p4"]["_raw"].get("nome_verba") or ""]
                                               if (v.get("p4") or {}).get("_raw") else [])
        livres = [p for p in sobras_pjc if p["nome"] not in usados
                  and not any(_incompat(n, p["nome"]) for n in nomes_ia if n)
                  and (any(_natureza(n) for n in nomes_ia) or not _natureza(p["nome"]))]
        por_nome = [(p, _nome_bate(nomes_ia, p["nome"])) for p in livres]
        por_nome = [(p, k) for p, k in por_nome if k]
        par, como = (por_nome[0] if len(por_nome) == 1 else (None, None))
        if par is None:
            # valor sozinho não basta (Adicional Noturno R$ 1.752 × "DEVOLUÇÃO DE
            # DESCONTOS" R$ 1.766): precisa de um radical em comum no nome — salvo
            # verba sem código de glossário, cujo nome não diz nada
            perto = [p for p in livres if _perto(v["total_ia"], p["soma_devido"])
                     and (_sem_identidade(v) or any(_radicais(n) & _radicais(p["nome"]) for n in nomes_ia))]
            # único dos dois lados: nenhuma outra sobra da IA a até 2% da mesma linha
            if (len(perto) == 1 and sum(1 for o in sobras_ia if o["status"] == "so_ia"
                                        and _perto(o["total_ia"], perto[0]["soma_devido"])) == 1):
                par, como = perto[0], "valor"
        if par is None:
            continue
        usados.add(par["nome"])
        tp = round(par["soma_devido"], 2)
        v.update({"status": "coincide", "nome_pjc": par["nome"], "total_pjc": tp,
                  "acuracia": _acc(v["total_ia"], tp), "_pjc_nomes": [par["nome"]],
                  "rotulos_pjc": [_rotulo_pjc(par["nome"])],
                  "pareado_por": como})   # 'nome' | 'sigla' | 'valor': casamento das sobras

    # ---- hora extra que sobrou dos dois lados: casa uma a uma ----
    # Com uma linha por verba do PJC (16/10), a 2ª HE do PJC volta para as sobras, mas as sobras
    # excluem HE (para não fundir 50% com 100%/384). Sem este passo, a mesma verba ficava "só PJC"
    # de um lado e "só IA" do outro (0000847-86: HE além da 6ª R$ 11.438 × HE excedentes à 6ª
    # R$ 11.732). Casa a HE da IA que sobrou com a HE do PJC compatível de nome mais parecido.
    he_ia = [v for v in verbas_out if v["status"] == "so_ia" and not v.get("is_reflexo")
             and v.get("total_ia") and _he_grupo(normaliza(v.get("nome_ia") or ""))]
    for v in sorted(he_ia, key=lambda x: -(x["total_ia"] or 0)):
        cod_v = v.get("codigo")
        # código do PJC (de-para) diferente do da IA veta: HE além da 6ª (BT001) × HE domingos (BT011)
        cand = [p for p in pjc["verbas"] if not p["reflexo"] and not p.get("multa") and p["nome"] not in usados
                and (p.get("soma_devido") or 0) > 0 and _he_grupo(normaliza(p["nome"]))
                and not _incompat(v["nome_ia"], p["nome"])
                and (not cod_v or ((_pjc_info(p["nome"]) or {}).get("codigo") or cod_v) == cod_v)]
        if not cand:
            continue
        # valor mais próximo (0010265-37: "HE 90% COM ADIC." R$ 49.895 e não "SÓ ADIC." R$ 1.481)
        par = min(cand, key=lambda p: abs((p.get("soma_devido") or 0) - (v["total_ia"] or 0)))
        usados.add(par["nome"])
        tp = round(par["soma_devido"], 2)
        v.update({"status": "coincide", "nome_pjc": par["nome"], "total_pjc": tp,
                  "acuracia": _acc(v["total_ia"], tp), "_pjc_nomes": [par["nome"]],
                  "rotulos_pjc": [_rotulo_pjc(par["nome"])], "pareado_por": "he_sobra"})

    # ---- mesma família que sobrou dos dois lados (07/11/2026, Raíra) ----
    # Férias, intervalo, aviso, 13º, saldo e FGTS escritos de outro jeito no PJC ("Férias em Dobro /
    # Férias Integral / Férias Proporcionais" × "05) FÉRIAS + 1/3"; "Horas Extras - intervalo
    # intrajornada" × "INTERVALO INTRAJORNADA") não tinham duas palavras em comum e ficavam "só IA" e
    # "só PJC": 97 processos no painel 03/11. Casa uma a uma pela família lida no nome, a de valor mais
    # próximo, nunca reflexo nem multa, e respeitando `_incompat`. Código de-para diferente veta.
    def _familia(nome):
        n = normaliza(nome or "")
        if re.search(r"\b(intervalo|intrajornada|interjornada|entrejornada)\b", n):
            return "intervalo"
        if re.search(r"\bferias\b", n):
            return "ferias"
        if re.search(r"\baviso\b", n) and "sobreaviso" not in n:
            return "aviso"
        if "saldo" in n:
            return "saldo"
        if re.search(r"\b13o?\b|decimo terceiro|natalin", n):
            return "13"
        if re.search(r"\bfgts\b|fundo de garantia", n):
            return "fgts"
        return None

    fam_ia = [v for v in verbas_out if v["status"] == "so_ia" and not v.get("is_reflexo")
              and v.get("total_ia") and _familia(v.get("nome_ia"))]
    for v in sorted(fam_ia, key=lambda x: -(x["total_ia"] or 0)):
        f = _familia(v["nome_ia"])
        cod_v = v.get("codigo") or v.get("codigo_glossario")
        cand = [p for p in pjc["verbas"] if not p["reflexo"] and not p.get("multa") and p["nome"] not in usados
                and (p.get("soma_devido") or 0) > 0 and _familia(p["nome"]) == f
                and not _incompat(v["nome_ia"], p["nome"])
                and (not cod_v or ((_pjc_info(p["nome"]) or {}).get("codigo") or cod_v) == cod_v)]
        if not cand:
            continue
        par = min(cand, key=lambda p: abs((p.get("soma_devido") or 0) - (v["total_ia"] or 0)))
        usados.add(par["nome"])
        tp = round(par["soma_devido"], 2)
        v.update({"status": "coincide", "nome_pjc": par["nome"], "total_pjc": tp,
                  "acuracia": _acc(v["total_ia"], tp), "_pjc_nomes": [par["nome"]],
                  "rotulos_pjc": [_rotulo_pjc(par["nome"])], "pareado_por": "familia"})

    # ---- verbas só no PJC (principal + reflexo) não casadas ----
    for p in pjc["verbas"]:
        if p["nome"] not in usados:
            verbas_out.append({"nome_ia": None, "nome_pjc": p["nome"], "rotulo_principal": None,
                               # código pelo de-para do nome do PJC (ex.: HE feriado → BT011), só para exibir
                               "codigo_depara": (None if p["reflexo"] else ((_pjc_info(p["nome"]) or {}).get("codigo"))),
                               "rotulos_pjc": [_rotulo_pjc(p["nome"])], "status": "so_pjc", "total_ia": None,
                               "total_pjc": round(p["soma_devido"], 2), "acuracia": None, "competencias": [],
                               "componente_perdido": [], "p4": None, "is_reflexo": p["reflexo"],
                               "is_multa": bool(p.get("multa")),   # linha do bloco de multas do PJC
                               "_pjc_nomes": [p["nome"]]})


    # ---- CAMADAS DE VALOR: pós-índice (corrigido) e pós-juros --------------
    # Lado IA: tabelas "consolidada" (trusted), que já traziam a atualização em
    # coluna. Lado PJC: `soma_corrigido` do .pjc (devido × indiceAcumulado, exato)
    # e, para os juros, a linha da verba no "Resumo do Cálculo" do PDF — hoje a
    # única fonte de juros por verba (no .pjc os juros vivem em ApuracaoDeJuros,
    # ainda não mapeado). Faltando a fonte, o campo fica None: nunca cai para o
    # nominal, senão a atualização apareceria como se estivesse correta.
    _c10a = _cons(C10A, cnj_d)
    _c10b = _cons(C10B, cnj_d)
    _ia_corr, _ia_jur, _ia_nom = {}, {}, {}          # id_verba -> valor (principais)
    if len(_c10a):
        for idv, g in _c10a.groupby("id_verba"):
            _ia_nom[idv] = _soma(g, "valor_final_competencia")
            _ia_corr[idv] = _soma(g, "atualizacao_monetaria_valor_principal_corrigido")
            _ia_jur[idv] = _soma(g, "atualizacao_monetaria_valor_atualizado")
    _rc_corr, _rc_jur = {}, {}                        # id_verba -> valor (rescisórias)
    if len(_c10b):
        for _, r in _c10b.iterrows():
            idv, cod = r.get("id_verba"), r.get("codigo_glossario")
            nom, atu = _f(r.get("total_verba")), _f(r.get("total_verba_atualizado"))
            # só verba punitiva (BT073) tem correção; nas outras o campo
            # `total_verba_atualizado` guarda o valor COM JUROS
            if cod == "BT073":
                _rc_corr[idv], _rc_jur[idv] = (atu if atu is not None else nom), None
            else:
                _rc_corr[idv], _rc_jur[idv] = nom, atu
    # reflexos: uma tabela por tipo; soma as linhas (período/ano/competência) por verba
    _RF_COLS = {
        "aviso_previo": (CRAV, "valor_final_aviso_previo_por_verba"),
        "ferias": (CRFE, "valor_final_ferias_periodo"),
        "decimo_terceiro": (CR13, "valor_final_decimo_terceiro_por_ano"),
        "dsr": (CRDS, "valor_final_dsr_competencia"),
    }
    _rf = {}                                          # (tipo, id_verba) -> (nom, corr, jur)
    for tipo, (df, base) in _RF_COLS.items():
        sub_df = _cons(df, cnj_d)
        if not len(sub_df) or "id_verba" not in sub_df.columns:
            continue
        for idv, g in sub_df.groupby("id_verba"):
            # `_bruto` = corrigido + juros (nome enganoso da tabela; `_juros` é só
            # o montante). Confirmado na aritmética: 425,62 + 192,42 = 618,04.
            _rf[(tipo, idv)] = (_soma(g, base), _soma(g, base + "_corrigido"),
                                _soma(g, base + "_bruto"))
    # índice de correção que a IA aplicou (fator médio do caso, p/ comparar com o PJC)
    _fator_ia_caso = None
    if _ia_nom and _ia_corr:
        _tn = sum(x for x in _ia_nom.values() if x)
        _tc = sum(x for x in _ia_corr.values() if x)
        _fator_ia_caso = round(_tc / _tn, 6) if _tn and _tc else None

    # Resumo do PJC por verba (corrigido + juros). Vem do PDF; com .pjc como fonte
    # primária, é leitura complementar (pode haver defasagem de versão entre os dois
    # arquivos — por isso o corrigido prefere sempre o .pjc).
    _res_idx = {}
    for l in (pjc.get("resumo_pdf") or pjc.get("resumo") or []):
        d = (l.get("descricao") or "").strip()
        if not d or d.lower() == "total":
            continue
        _res_idx[_norm(d)] = l
    _pjc_por_nome = {p["nome"]: p for p in pjc["verbas"]}

    def _pjc_atual(nomes):
        """(corrigido, com_juros) somados das linhas do PJC casadas com a verba."""
        corr = jur = None
        for nm in nomes or []:
            p = _pjc_por_nome.get(nm) or {}
            c = p.get("soma_corrigido")
            info = _res_idx.get(_norm(nm))
            if c is None and info:
                c = info.get("valor_corrigido")
            if c is not None:
                corr = (corr or 0.0) + c
            if info and info.get("total") is not None:
                jur = (jur or 0.0) + info["total"]
        return (round(corr, 2) if corr is not None else None,
                round(jur, 2) if jur is not None else None)

    for v in verbas_out:
        idv, cam = v.get("_idv"), _camada_de(v)
        if cam == "reflexo":
            nom, ia_c, ia_j = _rf.get((v.get("_tipo_refl"), idv), (None, None, None))
        elif cam == "rescisoria":
            nom, ia_c, ia_j = v.get("total_ia"), _rc_corr.get(idv), _rc_jur.get(idv)
        else:
            nom, ia_c, ia_j = _ia_nom.get(idv), _ia_corr.get(idv), _ia_jur.get(idv)
        # O agrupamento da consolidada é por id_verba, mas o P10 às vezes devolve
        # DUAS verbas com o mesmo id (saída duplicada) — aí a soma da consolidada
        # cobre as duas e seria contada em cada uma. Quando o nominal da
        # consolidada não bate com o do cálculo, reescala pelo fator do nominal:
        # mantém o índice aplicado e não duplica valor. Também cobre safra diferente.
        rescalado = False
        if nom and v.get("total_ia") is not None and abs(nom - v["total_ia"]) > max(0.5, 0.005 * nom):
            k = v["total_ia"] / nom
            ia_c = round(ia_c * k, 2) if ia_c is not None else None
            ia_j = round(ia_j * k, 2) if ia_j is not None else None
            rescalado = True
        p_c, p_j = _pjc_atual(v.get("_pjc_nomes"))
        # fator aplicado de cada lado (corrigido ÷ nominal): divergência de fator
        # com nominal batendo é erro de ÍNDICE/data-base, não de cálculo
        f_ia = round(ia_c / nom, 4) if (ia_c and nom) else None
        soma_nom_pjc = sum((_pjc_por_nome.get(n) or {}).get("soma_devido") or 0
                           for n in (v.get("_pjc_nomes") or []))
        f_pjc = round(p_c / soma_nom_pjc, 4) if (p_c and soma_nom_pjc) else None
        v["corrigido"] = {"ia": ia_c, "pjc": p_c,
                          "acc": (_acc(ia_c, p_c) if (ia_c is not None and p_c is not None) else None),
                          "fator_ia": f_ia, "fator_pjc": f_pjc,
                          # o nominal da consolidada tem de bater com o nominal do app;
                          # se não bater, a safra da consolidada é outra (sinaliza)
                          "nominal_consolidada": nom, "rescalado": rescalado}
        v["juros"] = {"ia": ia_j, "pjc": p_j,
                      "acc": (_acc(ia_j, p_j) if (ia_j is not None and p_j is not None) else None)}
        v.pop("_pjc_nomes", None)
        v.pop("_idv", None)
        v.pop("_tipo_refl", None)

    # ---- histórico salarial (PJC × P7) + composição (P6/proventos)
    hist_pjc = {_comp(k): v for k, v in pjc["historico_salarial"].items()}

    def _rub(filtro):
        return next((r for r in holer if filtro(r)), None)
    rub_prem = _rub(lambda r: r.get("codigo_glossario") == "BT031"
                    or any("rêmio" in (n or "") for n in (r.get("nomes_origem") or [])))
    rub_sal = _rub(lambda r: r.get("codigo_glossario") == "BT090"
                   or "alário Base" in (r.get("descricao_glossario") or ""))
    p7_prem = {_comp(c["competencia"]): c.get("valor") for c in ((rub_prem or {}).get("competencias_filtradas") or []) if isinstance(c, dict) and c.get("competencia")}
    p7_sal = {_comp(c["competencia"]): c.get("valor") for c in ((rub_sal or {}).get("competencias_filtradas") or []) if isinstance(c, dict) and c.get("competencia")}

    prov = _ultimo(PROV, idp, "proventos_mensais") or []
    prov_por_comp = {_comp(p.get("vigencia")): p for p in prov}

    def premio_comps(mm):
        p = prov_por_comp.get(mm)
        if not p:
            return []
        return [{"desc": v.get("descricao_original"), "valor": v.get("valor")}
                for v in p.get("valores", [])
                if "rêmio" in (v.get("descricao_original") or "") or "remio" in (v.get("descricao_original") or "").lower()]

    historico = [{"competencia": mm,
                  "salario_base_pjc": hist_pjc.get(mm, {}).get("salario_base"), "salario_p7": p7_sal.get(mm),
                  "premio_pjc": hist_pjc.get(mm, {}).get("premio_metas"), "premio_p7": p7_prem.get(mm),
                  "premio_componentes": premio_comps(mm)}
                 for mm in sorted(set(hist_pjc) | set(p7_prem) | set(p7_sal))]

    # tabela cheia do PJC (todas as colunas) e do P7 (todas as rubricas), separadas
    pjc_cols = []
    for mm in sorted(hist_pjc):
        for col in (hist_pjc[mm].get("todas") or {}):
            if col not in pjc_cols:
                pjc_cols.append(col)
    historico_pjc = {"colunas": pjc_cols,
                     "linhas": [{"competencia": mm, "valores": hist_pjc[mm].get("todas") or {}}
                                for mm in sorted(hist_pjc)]}
    p7_rubs = [{"nome": (r.get("descricao_glossario") or (r.get("nomes_origem") or ["?"])[0]),
                "codigo": r.get("codigo_glossario"),
                "comps": {_comp(c["competencia"]): c.get("valor") for c in (r.get("competencias_filtradas") or []) if isinstance(c, dict) and _comp(c.get("competencia"))}}
               for r in holer]
    p7_meses = sorted({mm for r in p7_rubs for mm in r["comps"]})
    historico_p7 = {"rubricas": [f'{r["nome"]} ({r["codigo"]})' if r["codigo"] else r["nome"] for r in p7_rubs],
                    "linhas": [{"competencia": mm, "valores": [r["comps"].get(mm) for r in p7_rubs]}
                               for mm in p7_meses]}

    # ---- coluna CÓDIGO (cálculo determinístico): total + acurácia por verba ----
    # Post-pass uniforme sobre todas as verbas: resolve o total do código pelo
    # ---- fora da comparação: honorários, custas e perícia ----
    # O PJe-Calc não traz honorários nem custas como verba, e eles não são crédito do
    # reclamante; a IA às vezes os calcula como verba. Contam só na regra de
    # aptidão (que lê `verbas_out`); somem da lista do caso, de totais, quadro e medidas.
    for v in verbas_out:
        if RX_NAO_VERBA.search(v.get("nome_ia") or v.get("nome_pjc") or ""):
            v["fora_comparacao"] = True
    verbas_cmp = [v for v in verbas_out if not v.get("fora_comparacao")]

    # ---- quadro-resumo + assertividade
    quadro = []
    for v in verbas_cmp:
        quadro.append({"nome": v["nome_ia"] or v["nome_pjc"], "status": v["status"],
                       "codigo": v.get("codigo") or v.get("codigo_glossario"),
                       "ia": v["total_ia"], "pjc": v["total_pjc"],
                       "dif": (round((v["total_ia"] or 0) - (v["total_pjc"] or 0), 2)
                               if v["total_ia"] is not None and v["total_pjc"] is not None else None),
                       "acuracia": v["acuracia"]})
    tot_ia = round(sum(v["total_ia"] or 0 for v in verbas_cmp), 2)
    # sem referência: total do PJC e assertividade ficam NULOS (não zero — zero
    # seria lido como "o PJC não apurou nada", e 0% de acurácia puxaria as médias).
    tot_pjc = None if sem_pjc else round(sum(q["pjc"] or 0 for q in quadro), 2)
    # Total da referência SEM REFLEXOS. É o espelho do `total_lift` das rodadas
    # (principal + rescisórias, sem reflexo), e existe porque comparar os dois
    # totais cheios seria comparar coisas diferentes: o lado LIFT do histórico
    # não tem reflexo, o lado PJC tem. Com a âncora errada o sinal do delta
    # invertia em 23% dos casos reprocessados — caso que melhorou aparecia como
    # queda de 34 pontos.
    tot_pjc_base = (None if sem_pjc else
                    round(sum(v["total_pjc"] or 0 for v in verbas_cmp if not v.get("is_reflexo")), 2))
    # fora da régua (execução com erro / gabarito a corrigir): sem assertividade,
    # igual a quem não tem PJC — 0% ali seria "errou tudo", e não houve medida.
    assert_geral = None if sem_medida else assertividade(tot_ia, tot_pjc)
    # Índice de compensação do caso, com os dois erros em R$ que o sustentam.
    # Calculado aqui e gravado no JSON: a tela não refaz soma de verba nenhuma.
    _ic, _bruto, _liq = compensacao(verbas_cmp)
    # camadas + acurácia GLOBAL do caso. A assertividade acima compara TOTAIS, e
    # total esconde erro: uma verba 40% acima e outra 40% abaixo se anulam e o caso
    # aparenta 100%. A acurácia global soma o erro em MÓDULO verba a verba (todas
    # as camadas, inclusive só-IA/só-PJC) — é ≤ assertividade, exceto quando alguma
    # verba do PJC é negativa: aí |Σ PJC| < Σ|PJC|, a assertividade fica com o
    # denominador menor e a ordem inverte.
    # O índice de compensação, calculado por caso, mede a compensação do erro, o
    # quanto ele está se cancelando.
    camadas = _camadas(verbas_cmp, sem_medida)
    camadas_layer = {L: _camadas(verbas_cmp, sem_medida, L) for L in LAYERS}

    # ---- resumo textual interpretativo (prosa) + observações por verba
    coincid = [v for v in verbas_out if v["status"] == "coincide"
               and not v.get("is_reflexo") and not v.get("is_rescisoria")]
    resumo = _resumo_prosa(cab, lift_verbas, pjc_principais, coincid, nao_calc, componentes_perdidos,
                           verbas_cmp, historico, tot_ia, tot_pjc, assert_geral, sem_pjc,
                           camadas, cadastro)
    if fora_regua == "nao_calculado":
        resumo.insert(0, f"<b>⛔ Não calculado — a execução terminou com ERRO</b> ({motivo_fora_regua}). "
                         "Não há P10, então não existe valor da IA para comparar: o caso está <b>fora da régua</b> "
                         "(assertividade, mediana e totais de comparação). O que aparece abaixo é o que o PJC traz "
                         "e o que o P4 deferiu antes do erro.")
    elif fora_regua == "gabarito_a_corrigir":
        resumo.insert(0, f"<b>⚠️ Gabarito a corrigir</b> — {motivo_fora_regua}. A comparação abaixo é contra o "
                         "cálculo errado e o caso está <b>fora da régua</b> até o arquivo certo subir.")
    for v in verbas_out:
        v["obs_texto"] = _obs_prosa(v, historico, componentes_perdidos, sem_pjc)

    # --- guardas de confiabilidade da extração do PJC ---
    # As guardas abaixo nasceram para o parser de PDF (frágil a layout): checavam
    # se a seção "Resumo" foi lida, se o parser leu a coluna errada, se o salário
    # base saiu do layout. Com o .pjc (fonte estruturada, sem layout) esses
    # sintomas NÃO existem — logo, só valem para fonte=PDF. Para o .pjc, a única
    # falha real é "não extraiu verba nenhuma" (arquivo vazio/corrompido).
    fonte = pjc.get("_fonte")
    de_pdf = fonte == "pdf"   # sem fonte (PJC não subiu) não é caso de guarda de parser
    corrigido_total = next((l["valor_corrigido"] for l in pjc["resumo"]
                            if l["descricao"].strip().lower() == "total"), None)
    devido_total = round(sum(v["soma_devido"] for v in pjc["verbas"]), 2)
    n_verbas_pjc = len(pjc["verbas"])
    motivos_extracao = []
    if sem_pjc:
        pass   # nada a extrair: a referência não subiu. Não é falha de parser.
    elif n_verbas_pjc == 0 or devido_total == 0:
        motivos_extracao.append("nenhuma verba foi extraída do cálculo de referência.")
    elif _so_agregados([v for v in pjc["verbas"] if not v.get("multa")]):   # multa não é verba
        # O parse devolveu SÓ linha de resumo do demonstrativo — "VERBAS
        # TRIBUTÁVEIS", "CONTRIBUIÇÃO SOCIAL", "PEDIDOS IMPROCEDENTES" — e
        # nenhuma verba deferida. Não há o que comparar verba a verba, e o total
        # não é soma de verbas: em 25 casos de 507 (base de 09/2026) isso entrava
        # em todas as médias, com valores de até R$ 1,5 mi distorcendo qualquer
        # agregado ponderado por dinheiro.
        motivos_extracao.append(
            "a referência foi lida só como linha de resumo do demonstrativo "
            f"({', '.join(sorted({v['nome'] for v in pjc['verbas']}))[:120]}), "
            "sem verba deferida — não há comparação verba a verba possível."
        )
    if de_pdf and corrigido_total is None:
        motivos_extracao.append("Resumo do Cálculo não foi lido (sem Valor Corrigido total).")
    if de_pdf and corrigido_total and devido_total > corrigido_total * 1.1:
        motivos_extracao.append(
            f"o Devido somado ({_brl(devido_total)}) supera o Valor Corrigido "
            f"({_brl(corrigido_total)}) — o parser lê coluna errada do Demonstrativo neste layout."
        )
    # Fora da régua também reprova a guarda: é por ela que TODO agregado da tela
    # (placar, funil, verbas, confiança) exclui o caso, sem precisar caçar cada
    # filtro. O motivo vai em primeiro lugar e a tela mostra a categoria própria.
    if fora_regua == "nao_calculado":
        motivos_extracao.insert(0, f"Não calculado — execução terminou com ERRO em {motivo_fora_regua}")
    elif fora_regua == "gabarito_a_corrigir":
        motivos_extracao.insert(0, f"Gabarito a corrigir — {motivo_fora_regua}")
    extracao_confiavel = not motivos_extracao

    sal = sorted(h["salario_base_pjc"] for h in historico if h.get("salario_base_pjc"))
    mediana_sal = sal[len(sal) // 2] if sal else 0
    cobertura_salario = (len(sal) / len(historico)) if historico else 0.0
    motivos_hist = []
    if sem_pjc:
        pass   # sem referência não há histórico do PJC para julgar
    elif not historico:
        motivos_hist.append("nenhum mês de histórico foi extraído.")
    # No .pjc, ausência de salário-base NÃO é falha de extração: significa que o
    # cálculo não marca rubricas com vínculo BASE (salário composto sem base única).
    # Só é "pouco confiável" no PDF, onde é sintoma de layout não reconhecido.
    if de_pdf and historico and mediana_sal < 100:
        motivos_hist.append("salário-base não foi localizado neste layout (mediana < R$100).")
    elif de_pdf and historico and cobertura_salario < 0.3:
        motivos_hist.append(
            f"só {len(sal)}/{len(historico)} meses ({cobertura_salario:.0%}) têm salário-base lido."
        )
    hist_confiavel = not motivos_hist

    esteira = _esteira_info(cnj_d)

    # --- APTIDÃO ao Fast Track automatizado (regra de status do FT, 14/10/2026) ---
    # Ordem: FT-Travado (não chegou ao P10) > verba de cálculo crítico (INELEGIVEIS) >
    # verba deferida não calculada. Mais as duas regras próprias do painel: tipo de cálculo
    # que não é Risco Real e curadoria de apuração provável via cartão.
    # Verba não calculada = deferida e SEM valor no cálculo (valor zero conta como
    # calculado), que não seja não relevante nem BT063, que tenha código BT (sem código =
    # "Não encontrado", não avaliada) e cuja dependência não esteja resolvida:
    #   - depende de outra verba (P9a `depende_de`) que foi calculada -> resolvida;
    #   - depende do valor da condenação e a decisão traz o percentual -> resolvida.
    # Honorários de sucumbência sem valor continuam não bloqueando, como antes.
    def _eh_honor_sucumb(nome):
        return "sucumb" in _norm(nome or "")

    _dep_de = {m.get("id_verba"): (m.get("depende_de") or []) for m in mapa_p9a if isinstance(m, dict)}

    def _calculada(vid):
        if vid in ids_calc:
            return True
        try:
            return deferidas[int(str(vid).split("_")[1]) - 1].get("codigo_glossario") in cods_calc
        except (ValueError, IndexError, KeyError, AttributeError):
            return False

    def _dependencia_resolvida(v):
        deps = _dep_de.get(v.get("id_verba")) or []
        if deps and all(_calculada(d) for d in deps):
            return True
        # "depende do valor da condenação": só pelo MOTIVO do roteamento falando da base
        # (a palavra "condenação" no critério é comum, "Condenação ao pagamento de…", e
        # dava falso positivo — 0100840-70.2023.5.01.0030, adicional noturno, 15/10).
        motivo = _norm(str(v.get("motivo_classificacao") or ""))
        crit = str((v.get("p4") or {}).get("criterio") or "")
        base_condenacao = re.search(r"valor (final |total )?da condenac|valor (total )?dos pedidos"
                                    r"|valor apurado (na|em) liquidac|valor (da|de) liquidac", motivo)
        return bool(base_condenacao) and "%" in crit

    def _sem_codigo(cod):
        return not cod or not re.fullmatch(r"BT\d{3}", str(cod).strip().upper())

    verbas_nc = [v for v in verbas_out
                 if v["status"] in ("nao_calc", "so_ia") and v.get("total_ia") is None
                 and not _sem_codigo(v.get("codigo_glossario"))
                 and v.get("codigo_glossario") not in NAO_BLOQUEIA_SEM_VALOR
                 and v.get("codigo_glossario") not in INELEGIVEIS
                 and not _eh_honor_sucumb(v.get("nome_ia") or v.get("nome_pjc"))
                 and not _dependencia_resolvida(v)]
    nc_documental = [v for v in verbas_nc
                     if v.get("motivo_nao_calc") == "documental"
                     or (v.get("p4") and v["p4"].get("depende_documento"))]

    tipo_calc = esteira.get("tipo_calculo")
    tipo_informado = bool(tipo_calc)
    tipo_ok = tipo_calc == "Cálculo de Risco Real"
    # tipo AUSENTE na esteira NÃO demove sozinho: não dá pra afirmar que não é
    # Risco Real (muitos casos do bomtrato não estão na esteira de pré-compra).
    # Fica apto, só sinalizado por `tipo_nao_encontrado`. Só demove quando a
    # esteira INFORMA um tipo que não é Risco Real (Autos/Adequação/etc.).
    tipo_nao_encontrado = not tipo_informado

    # Curadoria: PJC de referência apurou HE por cartão com oscilação extrema.
    cartao_provavel = cnj_d in CARTAO_PROVAVEL

    # Verba com TOTAL negativo (IA ou PJC): o painel não zera nada, só sinaliza na lista que a
    # assertividade do caso não é confiável (Raíra, 15/10/2026). No PJC, linha de desconto
    # ("valor pago", "verbas rescisórias pagas", dedução) é negativa de propósito e fica de fora.
    _desconto = re.compile(r"\bpag[oa]s?\b|descont|dedu", re.I)
    verbas_negativas = []
    for v in verbas_out:
        nome = v.get("nome_ia") or v.get("nome_pjc") or "?"
        if (v.get("total_ia") or 0) < -0.01:
            verbas_negativas.append({"lado": "IA", "verba": nome, "total": round(v["total_ia"], 2)})
        if (v.get("total_pjc") or 0) < -0.01 and not _desconto.search(str(v.get("nome_pjc") or "")):
            verbas_negativas.append({"lado": "PJC", "verba": nome, "total": round(v["total_pjc"], 2)})

    # Nenhuma verba calculada: a IA não chegou a valor em nenhuma verba que conta (fora
    # honorários e as que não bloqueiam sem valor). É erro da IA (ex.: o editor de decisões só
    # achou o BT062 e perdeu a gratificação de R$ 516 mil do 0001414-49.2022.5.12.0019), mas o
    # caso fica não apto (Raíra, 15/10/2026). Verba calculada com valor 0 conta como calculada.
    sem_verba_calc = fora_regua != "nao_calculado" and not any(
        v.get("total_ia") is not None
        and v.get("codigo_glossario") not in NAO_BLOQUEIA_SEM_VALOR
        and not _eh_honor_sucumb(v.get("nome_ia") or v.get("nome_pjc"))
        for v in verbas_out)

    motivos_inaptidao = []
    # Não chegou ao P10: a execução parou com ERRO antes do cálculo. Na esteira o caso fica
    # "FT Travado", isto é, não apto (regra da Raíra, 15/10/2026). Já estava fora da régua
    # ("nao_calculado"); aqui só passa a aparecer também como não apto.
    if fora_regua == "nao_calculado":
        motivos_inaptidao.append({"categoria": "Não chegou ao P10 (FT Travado)",
                                  "detalhe": motivo_fora_regua})
    # Gabarito de outro processo ou de outro cálculo: não há medida, então não é apto
    # (Raíra, 15/10/2026: 0000417-46.2024.5.10.0021 tinha o PJC do 0000752-81.2022.5.10.0006).
    if fora_regua == "gabarito_a_corrigir":
        motivos_inaptidao.append({"categoria": "Gabarito a corrigir", "detalhe": motivo_fora_regua})
    if sem_verba_calc:
        motivos_inaptidao.append({"categoria": "Nenhuma verba calculada",
                                  "detalhe": "a IA não chegou a valor em nenhuma verba que entra na conta"})
    if tipo_informado and not tipo_ok:
        motivos_inaptidao.append({"categoria": "Tipo de cálculo (não é Risco Real)",
                                  "detalhe": tipo_calc})
    if cartao_provavel:
        motivos_inaptidao.append({"categoria": "Provável apuração via cartão",
                                  "detalhe": "HE com oscilação extrema mês a mês no PJC de referência (cartão de ponto)"})
    for c in codigos_inelegiveis:
        motivos_inaptidao.append({"categoria": "Verba de cálculo crítico",
                                  "detalhe": f"{c} — {GLOSSARIO_NOME.get(c, c)}"})
    for v in verbas_nc:
        doc = v in nc_documental
        motivos_inaptidao.append({
            "categoria": "Verba não calculada",
            "detalhe": f"{v.get('codigo_glossario')} — " + (v.get("nome_ia") or v.get("nome_pjc") or "?")
                       + (" (depende de documento)" if doc else "")})
    apto = not motivos_inaptidao
    # categoria primária p/ agrupar (prioridade: travado > gabarito > nenhuma calculada > crítico > não calculada > tipo > cartão)
    if fora_regua == "nao_calculado":
        categoria_inaptidao = "Não chegou ao P10 (FT Travado)"
    elif fora_regua == "gabarito_a_corrigir":
        categoria_inaptidao = "Gabarito a corrigir"
    elif sem_verba_calc:
        categoria_inaptidao = "Nenhuma verba calculada"
    elif codigos_inelegiveis:
        categoria_inaptidao = "Verba de cálculo crítico"
    elif verbas_nc:
        categoria_inaptidao = "Verba não calculada"
    elif tipo_informado and not tipo_ok:
        categoria_inaptidao = "Tipo de cálculo (não é Risco Real)"
    elif cartao_provavel:
        categoria_inaptidao = "Provável apuração via cartão"
    else:
        categoria_inaptidao = None

    # --- linhas do PJC fora do principal (bloco "Verbas que não compõem o Principal") ---
    # Já saem do total e da comparação no parser. "Pedidos improcedentes" é a base dos
    # honorários de sucumbência que a sentença manda o RECLAMANTE pagar: não é crédito,
    # mas sinaliza sucumbência recíproca — o caso fica perto de não apto.
    fora_principal = [{"nome": v["nome"], "total": round(v.get("soma_devido") or 0, 2)}
                      for v in (pjc.get("verbas_fora_principal") or [])]
    # multas do PJC que o reclamante NÃO recebe (ele paga, ou é de terceiro/IRRF):
    # não são crédito, ficam fora da conta e só aparecem no aviso
    fora_principal += [{"nome": f"{m['nome']} (multa · {m.get('tipo_credor_devedor') or '?'})",
                        "total": m["valor"]}
                       for m in _multas if not m.get("credor_reclamante")]
    alertas_pjc = []
    improc = [v for v in fora_principal if "improced" in _norm(v["nome"])]
    if improc:
        alertas_pjc.append({
            "tipo": "pedidos_improcedentes",
            "titulo": "Pedidos improcedentes no PJC",
            "detalhe": (f"O PJC lista {_brl(sum(v['total'] for v in improc))} de pedidos julgados improcedentes. "
                        "É a base dos honorários de sucumbência que a sentença manda o reclamante pagar ao "
                        "advogado da reclamada; não é crédito e ficou fora do total. Conferir na sentença o "
                        "percentual e se o reclamante tem justiça gratuita.")})
    outras_fora = [v for v in fora_principal if v not in improc]
    if outras_fora:
        alertas_pjc.append({
            "tipo": "fora_do_principal",
            "titulo": "Linhas do PJC fora do principal",
            "detalhe": "Ficaram fora do total, como no PJC: "
                       + "; ".join(f"{v['nome']} ({_brl(v['total'])})" for v in outras_fora[:6])})
    if (pjc.get("_outro_calculo") or {}).get("usado") == "pdf":
        _oc = pjc["_outro_calculo"]
        alertas_pjc.append({
            "tipo": "pjc_outro_calculo",
            "titulo": "PJC e PDF de cálculos diferentes",
            "detalhe": (f"O .pjc na pasta é o cálculo {_oc['id_pjc']} e o PDF é o {_oc['id_pdf']}. "
                        "O PDF foi conferido como o gabarito e a comparação usa ele.")})
    if gabarito_pdf_dif:
        alertas_pjc.append({
            "tipo": "pjc_pdf_diferentes",
            "titulo": "* PJC e PDF de cálculos diferentes",
            "detalhe": (f"O .pjc na pasta é o cálculo {gabarito_pdf_dif['id_pjc']} e o PDF é o {gabarito_pdf_dif['id_pdf']}. "
                        "A comparação usa o .pjc; o gabarito só é conferido se o caso for apto com assertividade baixa.")})

    # --- horas extras como família ---
    # O PJC costuma apurar toda hora acima da jornada numa linha só; a IA separa em
    # 7ª/8ª (BT081/BT001) e além da 8ª (BT089). O casamento verba a verba deixa uma
    # das verbas da IA como "só IA" e a outra com o PJC inteiro. Somar a família
    # dos dois lados mostra a diferença real (principal, sem reflexos).
    _HE = ("BT001", "BT081", "BT089")
    he_ia = [v for v in verbas_out if v.get("codigo") in _HE and v.get("total_ia") is not None]
    _rx_he_pjc = re.compile(r"hora.*extra|extra.*hora|\bh\.?\s?e\.?\b", re.I)
    _rx_fora = re.compile(r"interval|intrajornada|interjornada|itinere|sobreaviso|doming|feriad", re.I)
    he_pjc = [p for p in pjc["verbas"] if not p.get("reflexo")
              and _rx_he_pjc.search(p["nome"]) and not _rx_fora.search(p["nome"])]
    familia_he = None
    if not sem_pjc and he_ia and (len(he_ia) > 1 or any(v.get("status") == "so_ia" for v in he_ia)):
        _fi = round(sum(v["total_ia"] or 0 for v in he_ia), 2)
        _fp = round(sum(p["soma_devido"] or 0 for p in he_pjc), 2)
        familia_he = {"total_ia": _fi, "total_pjc": _fp,
                      "assertividade": assertividade(_fi, _fp) if _fp else None,
                      "verbas_ia": [{"codigo": v["codigo"], "nome": v.get("nome_ia"), "total": v["total_ia"],
                                     "status": v.get("status")} for v in he_ia],
                      "linhas_pjc": [{"nome": p["nome"], "total": round(p["soma_devido"] or 0, 2)} for p in he_pjc]}

    _vers = _versoes(idp)
    return {
        "processo": {**cab, "cnj": cnj},
        "observacoes_calculo": observacoes_calculo,
        "data_processamento": data_processamento,
        # versão do prompt de cada etapa que produziu ESTA saída, e o rótulo da
        # safra (combinação do miolo P9a/P9b/P10a/P10b). Ver `_versoes`.
        "versoes": _vers,
        "safra": _safra(_vers),
        "tipo_calculo": esteira["tipo_calculo"],
        "data_validade_calculo": esteira["data_validade_calculo"],
        "calculo_adequacao": esteira["calculo_adequacao"],
        "apto": apto,
        "categoria_inaptidao": categoria_inaptidao,
        "motivos_inaptidao": motivos_inaptidao,
        "tipo_nao_encontrado": tipo_nao_encontrado,   # apto, mas sem tipo na esteira
        "verbas_negativas": verbas_negativas,    # total negativo: assertividade não confiável (só sinaliza)
        "codigos_inelegiveis": codigos_inelegiveis,
        "alertas_pjc": alertas_pjc,              # avisos sobre o gabarito (não mudam a aptidão)
        "pjc_fora_principal": fora_principal,    # linhas informativas do PJC, fora do total
        "familia_he": familia_he,                # HE somadas dos dois lados (7ª/8ª + além da 8ª)
        "resumo_texto": resumo,
        "verbas": verbas_cmp,
        "quadro": {"linhas": quadro, "total_ia": tot_ia, "total_pjc": tot_pjc,
                   "total_pjc_base": tot_pjc_base, "assertividade": assert_geral,
                   "acuracia_global": camadas["global"]["acc"],
                   # sem referência os três ficam NULOS, nunca 0 — zero entraria
                   # nas medianas afirmando que não há compensação, que é falso
                   "indice_compensacao": None if sem_medida else _ic,
                   "erro_bruto": None if sem_medida else _bruto,
                   "erro_liquido": None if sem_medida else _liq,
                   # totais e as duas medidas em cada camada de valor (pré-índice,
                   # pós-índice, pós-juros) — a tela troca de camada sem recalcular
                   "layers": {L: {
                       "total_ia": camadas_layer[L]["global"]["ia"],
                       "total_pjc": camadas_layer[L]["global"]["pjc"],
                       "acuracia_global": camadas_layer[L]["global"]["acc"],
                       "assertividade": (None if (sem_medida or not camadas_layer[L]["global"]["ia"]) else
                           assertividade(camadas_layer[L]["global"]["ia"],
                                         camadas_layer[L]["global"]["pjc"])),
                   } for L in LAYERS}},
        "camadas": camadas,
        "camadas_layer": camadas_layer,
        "fator_ia_caso": _fator_ia_caso,
        "cadastro": cadastro,
        "ferias_p1": ferias_p1,
        "jornada": _jornada(idp, deferidas),
        "historico": historico,
        "historico_pjc": historico_pjc,
        "historico_p7": historico_p7,
        "rubricas_base": pjc.get("rubricas_base") or [],   # compõem o salário base (só .pjc)
        "fonte_ref": pjc.get("_fonte"),                     # 'pjc' | 'pdf' | None (não subiu)
        "sem_pjc": sem_pjc,                                 # sem gabarito: fora de toda média
        # fora da régua: "nao_calculado" (execução com ERRO, sem P10) ou
        # "gabarito_a_corrigir" (PJC de outro processo/cálculo). None = na régua.
        "fora_regua": fora_regua,
        "motivo_fora_regua": motivo_fora_regua,         # ex.: "CARTAO_PONTO: Jornada mista ..."
        "gabarito_pdf_dif": gabarito_pdf_dif,           # {id_pjc, id_pdf}: na régua pelo .pjc, marcado com *
        "erro_execucao": erro_exec,                     # {etapa, motivo, quando} da trilha de status
        "extracao_confiavel": extracao_confiavel,
        "hist_confiavel": hist_confiavel,
        "diag_extracao": {
            "corrigido_total": corrigido_total, "devido_total": devido_total,
            "mediana_salario": mediana_sal, "n_verbas_pjc": n_verbas_pjc,
            "cobertura_salario": round(cobertura_salario, 2),
            "motivos_extracao": motivos_extracao, "motivos_hist": motivos_hist,
        },
    }


def _mesf(c):
    return c[5:] + "/" + c[:4]


def _eh_premio(v):
    return bool(v["nome_ia"]) and ("rêmio" in v["nome_ia"] or "remio" in v["nome_ia"].lower())


def _comp_principal(v, c):
    if not c["pjc"]:
        return None
    return next((x for x in c["pjc"] if x["rotulo"] == v.get("rotulo_principal")), c["pjc"][0])


def _stats(v):
    perc = base = dias = 0
    fer = []
    n = 0
    for x in v["competencias"]:
        p = _comp_principal(v, x)
        if not p:
            continue
        n += 1
        if x["ia"]["perc"] is not None and p["perc"] is not None and not _prox(x["ia"]["perc"], p["perc"]):
            perc += 1
        if x["ia"]["base"] is not None and p["base"] is not None and not _prox(x["ia"]["base"], p["base"]):
            base += 1
        if x["ia"]["dias"] is not None and x["dias_pjc"] is not None and abs(x["ia"]["dias"] - x["dias_pjc"]) >= 1:
            dias += 1
        if x["ferias_pjc"] > 0:
            fer.append(x)
    return {"perc": perc, "base": base, "dias": dias, "fer": fer, "n": n}


def _causa(v, perdidos):
    """Frase concreta com a causa da divergência de uma verba coincidente."""
    if _eh_premio(v) and "SONEGAD" in (v["nome_pjc"] or "").upper():
        return (f"a IA apura “Diferenças de Prêmios” ({_brl(v['total_ia'])}) e o PJC apura “Prêmios Sonegados” "
                f"({_brl(v['total_pjc'])}). São verbas de conceito diferente — a IA calcula a diferença mensal "
                "(alguns meses negativos), o PJC o prêmio sonegado integral. A divergência não é erro de conta, é verba distinta")
    s = _stats(v)
    partes = []
    if s["base"] and not s["perc"]:
        partes.append(f"o percentual bate, mas a base de cálculo diverge em {s['base']} de {s['n']} competências "
                      "(em geral nos meses parciais, em que a IA e o PJC tratam a proporcionalidade de formas diferentes)")
    elif s["perc"]:
        partes.append(f"o percentual aplicado diverge em {s['perc']} competências")
    if s["fer"]:
        ex = max(s["fer"], key=lambda x: abs((x["ia"]["dias"] or 0) - (x["dias_pjc"] or 0)))
        partes.append(f"e a IA não desconta os dias de férias — em {_mesf(ex['competencia'])} houve {ex['ferias_pjc']} dias de férias, "
                      f"mas a IA usou {ex['ia']['dias']} dias contra {ex['dias_pjc']} do PJC, inflando o valor")
    perd = [c for c in perdidos if c["verba_ia"] == v["nome_ia"]]
    if perd:
        itens = ", ".join(f'base {c["rotulo"]}' + (f' ({_brl(c["total_pjc"])})' if c.get("total_pjc") is not None else "")
                          for c in perd)
        frase = f"e, sobretudo, a IA usou uma única base (a Fixa, que coincide), deixando de computar a {itens} que o PJC também aplica"
        p4 = v.get("p4") or {}
        if not p4.get("menciona_variavel") and not p4.get("menciona_s340"):
            frase += " — e o deferimento do P4 não menciona a parte variável nem a Súmula 340, ou seja, o prompt não capturou esse componente (causa raiz, não erro de conta)"
        partes.append(frase)
    if not partes:
        partes.append("os valores acompanham o PJC competência a competência")
    return "; ".join(partes)


def _prosa_cadastro(cad):
    """Parágrafo sobre os dados cadastrais. Vem ANTES da leitura das verbas: se a
    admissão, a demissão ou o recorte do período divergem, o cálculo comparado é
    de outro contrato/período e a acurácia das verbas mede a coisa errada."""
    if not cad or not cad.get("n_comparados"):
        return None
    div = [l for l in cad["linhas"] if l["status"] == "diverge"]
    parc = [l for l in cad["linhas"] if l["status"] == "parcial"]
    esc = [l for l in cad["linhas"] if l["status"] in ("escopo_maior", "escopo_menor")]
    if not div and not parc and not esc:
        return (f"<b>Dados cadastrais conferem</b> ({cad['n_ok']}/{cad['n_comparados']} campos): partes, "
                "admissão, demissão e o recorte do período batem com o cálculo de referência — "
                "as divergências abaixo são de cálculo, não de insumo.")

    def _d(l):
        d = l.get("delta_dias")
        alvo = f" (LIFT {l['lift']} × referência {l['pjc']}"
        alvo += f", {abs(d)} dia{'s' if abs(d) != 1 else ''} de diferença)" if d else ")"
        return f"<b>{l['campo']}</b>{alvo}"
    p = ""
    if div:
        p += ("<b>⚠️ Dados cadastrais divergem</b> em " + str(len(div)) + " de "
              + str(cad["n_comparados"]) + " campos: " + "; ".join(_d(l) for l in div) + ". ")
        if cad.get("graves"):
            p += ("Isso é <b>insumo, não conta</b>: com contrato ou recorte de período diferentes, "
                  "os dois lados apuram meses diferentes e a acurácia abaixo não é comparável até isso "
                  "fechar. Conferir a fonte da data no P1 antes de investigar qualquer verba. ")
        if any(l["chave"] == "reclamada" for l in div) and not cad.get("graves"):
            p += ("A divergência é só na reclamada — em geral litisconsórcio/tomador (a referência nomeia "
                  "a parte que paga, o P1 o empregador), não erro de insumo. ")
    if esc:
        alvo = " e ".join(
            f"{'início' if l['chave'] == 'periodo_ini' else 'fim'} "
            f"(LIFT {l['lift']} × referência {l['pjc']}, {abs(l['delta_dias'])} dias"
            + (f"; {l['motivo']}" if l.get("motivo") else "") + ")"
            for l in esc)
        maior = any(l["status"] == "escopo_maior" for l in esc)
        p += (f"<b>O período apurado não é o mesmo nos dois lados:</b> {alvo}. "
              + ("A referência apura MAIS meses que o LIFT, então toda verba mensal tende a sair menor no "
                 "LIFT por escopo, não por erro de conta — a acurácia aqui compara intervalos diferentes. "
                 if maior else
                 "A referência apura MENOS meses que o LIFT, então o LIFT tende a sair maior por escopo. "))
    if parc:
        p += ("Grafia diferente (mesma parte, provavelmente) em: "
              + ", ".join(l["campo"] for l in parc) + " — vale o olho humano, não é erro de cálculo.")
    return p


def _med(a):
    s = sorted(x for x in a if x is not None)
    if not s:
        return None
    m = len(s) // 2
    return round(s[m] if len(s) % 2 else (s[m - 1] + s[m]) / 2, 1)


def _prosa_camadas(cam, sem_pjc):
    """Parágrafo das três camadas + a leitura própria dos reflexos (herdado × próprio)."""
    if sem_pjc or not cam:
        return None
    rot = {"principal": "principais", "rescisoria": "rescisórias", "reflexo": "reflexos"}
    itens = [f"{rot[k]} <b>{cam[k]['acc']}%</b> (IA {_brl(cam[k]['ia'])} × PJC {_brl(cam[k]['pjc'])})"
             for k in ("principal", "rescisoria", "reflexo")
             if cam.get(k) and cam[k].get("n") and cam[k].get("acc") is not None]
    if not itens:
        return None
    txt = "<b>Acurácia por camada:</b> " + "; ".join(itens) + ". "
    r = cam.get("reflexo") or {}
    g = cam.get("global") or {}
    if r.get("n") and g.get("ia"):
        peso = round(100 * r["ia"] / g["ia"]) if g["ia"] else None
        if peso:
            txt += f"Os reflexos são {peso}% do que a IA calculou. "
        base_ok = _med(r.get("accs_base_ok") or [])
        med_todos = _med(r.get("accs") or [])
        if base_ok is not None and med_todos is not None:
            txt += (f"Lendo só os reflexos cuja <b>verba-base já bate (≥95%)</b>, a mediana é <b>{base_ok}%</b> "
                    f"contra {med_todos}% no conjunto — a diferença é <b>erro herdado</b> da base, "
                    "não erro do reflexo (o reflexo multiplica o principal, então um erro de hora extra "
                    "é contado de novo no 13º, nas férias, no aviso e no DSR). ")
        elif med_todos is not None:
            txt += (f"Mediana dos reflexos {med_todos}%, mas nenhuma verba-base bate a ≥95% neste caso — "
                    "aqui não dá para separar erro do reflexo de erro herdado: arrumar a base vem primeiro. ")
    return txt


def _resumo_prosa(cab, lift, pjc_p, coincid, nao_calc, perdidos, verbas, historico, tot_ia, tot_pjc,
                  assert_geral, sem_pjc=False, camadas=None, cadastro=None):
    p = []
    nome = cab.get("reclamante") or "o reclamante"
    if sem_pjc:
        # Sem gabarito não existe divergência a explicar: a prosa vira leitura do
        # que o LIFT produziu. Nada aqui pode afirmar acerto/erro de valor.
        p.append(f"<b>Cálculo de referência (PJC) ainda não carregado.</b> A IA totaliza {_brl(tot_ia)}; "
                 "não há acurácia porque não existe com o que comparar. O que dá para ler aqui é só o lado LIFT: "
                 "verbas deferidas, o que foi calculado, o que ficou de fora e a aptidão ao Fast Track. "
                 "Quando o PJC subir, o caso passa a ser comparado automaticamente.")
    else:
        acc_g = ((camadas or {}).get("global") or {}).get("acc")
        canc = (round(assert_geral - acc_g, 1)
                if (acc_g is not None and assert_geral is not None) else None)
        p.append(
            f"Cálculo de {nome} ({cab.get('periodo_calculo','')}). A IA totaliza {_brl(tot_ia)} e o PJC {_brl(tot_pjc)} "
            f"— assertividade do total {assert_geral}%"
            + (f" e <b>acurácia global {acc_g}%</b> (erro somado em módulo, verba a verba, nas três camadas)"
               if acc_g is not None else "")
            + (f". Os {canc} pontos entre as duas são erro que <b>se cancela no total</b> — verba acima compensando "
               "verba abaixo, que o total esconde e a acurácia global não"
               if canc is not None and canc >= 3 else "")
            + ". A leitura verba a verba aponta causas distintas para cada diferença.")
    pcad = _prosa_cadastro(cadastro)
    if pcad:
        p.append(pcad)
    pcam = _prosa_camadas(camadas, sem_pjc)
    if pcam:
        p.append(pcam)
    for v in sorted(coincid, key=lambda v: v["acuracia"] if v["acuracia"] is not None else -1):
        p.append(f"<b>{v['nome_ia']}</b> — IA {_brl(v['total_ia'])} × PJC {_brl(v['total_pjc'])} ({v['acuracia']}%): {_causa(v, perdidos)}.")
    so_ia = [v for v in verbas if v["status"] == "so_ia"]
    calc_so_ia = [v for v in so_ia if v["total_ia"] is not None]
    if calc_so_ia and sem_pjc:
        soma = sum(v["total_ia"] for v in calc_so_ia)
        nomes = ", ".join(f"{v['nome_ia']} ({_brl(v['total_ia'])})" for v in calc_so_ia)
        p.append(f"<b>Verbas que a IA calculou ({_brl(soma)}):</b> {nomes}. "
                 "Sem o PJC não dá para dizer se algum valor está acima ou abaixo — nem se alguma verba "
                 "foi deferida a mais ou a menos. Isso só é aferível quando a referência subir.")
    elif calc_so_ia:
        soma = sum(v["total_ia"] for v in calc_so_ia)
        nomes = ", ".join(f"{v['nome_ia']} ({_brl(v['total_ia'])})" for v in calc_so_ia)
        p.append(f"<b>Verbas que a IA calculou e o PJC não tem ({_brl(soma)}):</b> {nomes}. "
                 "São o principal motivo de o total da IA superar o do PJC. Como o cálculo oficial não as traz, indicam super-identificação no P4. "
                 + ("Pior: algumas dependem de dado documental (ex.: cartão de ponto) e ainda assim foram calculadas — sinal de quantidade/valor extrapolado. "
                    if any(v["p4"] and v["p4"].get("depende_documento") for v in calc_so_ia) else "")
                 + "É o ponto de maior impacto para revisar no prompt de deferimento (P4).")
    nc = [v for v in so_ia if v["total_ia"] is None]
    g_no_pjc = [v for v in nc if v.get("motivo_nao_calc") == "no_pjc"]
    g_doc = [v for v in nc if v.get("motivo_nao_calc") == "documental"]
    g_sem = [v for v in nc if v.get("motivo_nao_calc") == "sem_pjc"]
    g_ref = [v for v in nc if v.get("motivo_nao_calc") == "ref_nao_carregada"]
    if g_no_pjc:
        soma = sum(v["total_pjc"] or 0 for v in g_no_pjc)
        p.append(f"<b>Verbas deferidas que a IA NÃO calculou, mas o PJC tem ({_brl(soma)}):</b> "
                 + ", ".join(v["nome_ia"] for v in g_no_pjc)
                 + ". São calculáveis e ficaram de fora — falha entre o deferimento (P4) e o cálculo (P10), "
                 "não “não calculável”. É o ponto mais crítico deste caso.")
    if g_doc:
        p.append("<b>Dependentes de documento (não calculáveis sem ele):</b> "
                 + ", ".join(v["nome_ia"] for v in g_doc)
                 + " — exigem cartão de ponto/ficha que não estava disponível na apuração.")
    if g_ref:
        p.append("<b>Deferidas e não calculadas:</b> "
                 + ", ".join(v["nome_ia"] for v in g_ref)
                 + " — ficaram entre o deferimento (P4) e o cálculo (P10). Sem o PJC não dá para separar "
                   "“o cálculo oficial também não traz” de “a IA perdeu a verba”; vale olhar o motivo no P9a.")
    if g_sem:
        p.append("<b>Deferidas, não calculadas e ausentes do PJC:</b> "
                 + ", ".join(v["nome_ia"] for v in g_sem)
                 + " — avaliar se o deferimento procede ou se houve super-identificação no P4.")
    so_pjc = [v for v in verbas if v["status"] == "so_pjc"]
    if so_pjc:
        soma = sum(v["total_pjc"] or 0 for v in so_pjc)
        nomes = ", ".join(f"{v['nome_pjc']} ({_brl(v['total_pjc'])})" for v in so_pjc)
        p.append(f"<b>Verbas que o PJC tem e a IA não deferiu ({_brl(soma)}):</b> {nomes}. "
                 "Aqui é o oposto: sub-identificação — o P4 deixou de reconhecer verbas que a decisão concedeu. Conferir o documento-fonte de cada uma.")
    ncv = [v for v in verbas if v["status"] == "nao_calc"]
    if ncv:
        com_pjc = [v for v in ncv if v.get("total_pjc") is not None]
        itens = "; ".join(f"{v['nome_ia']} ({(v.get('motivo_classificacao') or '')[:90]})" for v in ncv)
        extra = (f" Destas, {len(com_pjc)} o PJC calculou — logo são calculáveis na prática, e a divergência é por falta de dado/critério, não por serem incalculáveis."
                 if com_pjc else "")
        p.append(f"<b>Verbas que a IA marcou como não calculáveis (P9a), com o motivo:</b> {itens}.{extra}")
    # composição do prêmio (P6) — explica a diferença do histórico
    comp_prem = next((h for h in historico if h.get("premio_componentes") and h.get("premio_p7") is not None), None)
    if comp_prem:
        itens = " + ".join(f'{c["desc"]} ({_brl(c["valor"])})' for c in comp_prem["premio_componentes"])
        p.append(f"Na origem do dado (Histórico Salarial), o prêmio filtrado no P7 não é igual ao do PJC porque o P7 agrega mais de um provento: "
                 f"em {_mesf(comp_prem['competencia'])}, o P7 traz {_brl(comp_prem['premio_p7'])} = {itens}, enquanto o PJC lista só o Prêmio Metas "
                 f"({_brl(comp_prem['premio_pjc'])}). Parte da diferença dos prêmios nasce aí — vale alinhar o que o filtro do P7 deve incluir.")
    return p


def _obs_prosa(v, historico, perdidos, sem_pjc=False):
    if v["status"] == "nao_calc":
        motivo = v.get("motivo_classificacao") or "—"
        cod = v.get("codigo_glossario") or "—"
        base = f"<b>A IA classificou como não calculável</b> (glossário {cod}). Motivo: {motivo}"
        if v.get("total_pjc") is not None:
            base += (f" <b>Mas o PJC calculou esta verba ({_brl(v['total_pjc'])})</b> — ou seja, é calculável na prática; "
                     "a IA não a produziu por falta do dado/critério acima. Divergência a investigar.")
        return base
    if sem_pjc:
        # Sem gabarito, a observação descreve o que a IA fez — sem julgar valor.
        if v.get("is_reflexo"):
            return f"Reflexo calculado pela IA ({_brl(v['total_ia'])}). Sem PJC para conferir."
        if v["total_ia"] is not None:
            return (f"A IA calculou esta verba ({_brl(v['total_ia'])}). <b>Sem cálculo de referência carregado</b>, "
                    "não há como aferir o valor — o que dá para revisar aqui é o deferimento (P4) e a "
                    "memória de apuração (P9/P10) nos blocos abaixo.")
        p4 = v.get("p4") or {}
        if v.get("motivo_nao_calc") == "documental":
            return (f"<b>Não calculável sem o documento:</b> depende de {p4.get('dados_necessarios') or '—'} "
                    "(ex.: cartão de ponto), que não estava disponível. Independe do PJC.")
        return ("Deferida no P4 e <b>não calculada</b> pela IA. Sem o PJC não dá para saber se o cálculo "
                "oficial traz esta verba — quando a referência subir, isso vira acerto ou perda de verba.")
    if v.get("is_reflexo"):
        base, ab = v.get("verba_base"), v.get("acuracia_base")
        ctx = ""
        if base:
            ctx = f" Verba-base: <b>{base}</b>"
            if ab is None:
                ctx += " — que não tem par no PJC, então aqui não dá para separar erro herdado de erro do reflexo."
            elif ab >= 95:
                ctx += (f", que bate {ab}% neste caso. Base praticamente certa, logo a diferença deste reflexo é "
                        "<b>dele</b> — o padrão típico é a IA aplicar coeficiente fixo (1/12) e o PJC apurar avos "
                        "(meses ≥15 dias, período aquisitivo incompleto).")
            else:
                ctx += (f", que bate só {ab}%. <b>Boa parte deste erro é herdada</b>: o reflexo multiplica o "
                        "principal, então arrumar a base corrige a maior parte daqui também.")
        ri, rp = v.get("ratio_base_ia"), v.get("ratio_base_pjc")
        if ri and rp:
            ctx += (f" Proporção reflexo/base: IA {round(ri * 100, 1)}% × PJC {round(rp * 100, 1)}%"
                    + (" (coeficiente fixo × avos apurados)." if abs(ri - rp) / max(ri, rp) > 0.03 else " (batem)."))
        if v["status"] == "coincide":
            return f"Reflexo — IA {_brl(v['total_ia'])} × PJC {_brl(v['total_pjc'])} ({v['acuracia']}%).{ctx}"
        return (f"Reflexo calculado pela IA ({_brl(v['total_ia'])}) <b>sem linha correspondente no PJC</b> — "
                f"ou o PJC não reflete essa verba, ou o pareamento não achou a linha.{ctx}")
    if v["status"] == "so_ia":
        p4 = v["p4"] or {}
        calculada = bool(v["competencias"]) or v["total_ia"] is not None
        fonte = p4.get("fonte_documento") or "documento não identificado"
        if calculada:
            txt = (f"A IA <b>calculou</b> esta verba ({_brl(v['total_ia'])}), deferida a partir de “{fonte}”, "
                   "mas ela <b>não consta no PJC</b>. Como o cálculo oficial não a reconhece, há forte indício de "
                   "super-identificação no P4 (deferir verba que a decisão/PJC não traz).")
            if p4.get("depende_documento"):
                txt += (f" Agravante: o próprio deferimento aponta dependência de dado documental "
                        f"({p4.get('dados_necessarios') or '—'}); calcular sem esse documento tende a gerar quantidade e valor extrapolados — "
                        "o que pode explicar um total tão alto.")
            return txt + " Revisar o prompt de deferimento (P4). O bloco abaixo traz o que o P4 usou."
        # deferida mas NÃO calculada — três motivos distintos
        motivo = v.get("motivo_nao_calc")
        if motivo == "no_pjc":
            return (f"⚠️ Deferida no P4 e <b>não calculada</b> pela IA — mas o <b>PJC traz esta verba ({_brl(v['total_pjc'])})</b>. "
                    "É uma verba calculável que se perdeu entre o deferimento (P4) e o cálculo (P10) — <b>não é caso de “não calculável”</b>, "
                    "é uma falha de pipeline: a IA deveria ter calculado e não calculou. Ponto crítico de revisão.")
        if motivo == "documental":
            s340 = " O critério cita base variável e Súmula 340." if p4.get("menciona_s340") else ""
            return (f"<b>Não calculável sem o documento:</b> depende de {p4.get('dados_necessarios') or '—'} "
                    f"(ex.: cartão de ponto), que não estava disponível. Deferida no P4 a partir de “{fonte}”.{s340} "
                    "Aqui o gargalo é a falta do dado, não o prompt.")
        return (f"Deferida no P4 (fonte: {fonte}) mas <b>não calculada e ausente do PJC</b>. "
                f"Depende de: {p4.get('dados_necessarios') or '—'}. "
                "Avaliar se o deferimento procede ou se houve super-identificação no P4.")
    if v["status"] == "so_pjc":
        return "Verba presente no PJC sem contrapartida da IA — o P4 deixou de deferir. Conferir o documento-fonte da decisão."
    if not v["competencias"]:
        return ""
    falta = "Nesta verba, " + _causa(v, perdidos) + "."
    if v["acuracia"] is not None and v["acuracia"] < 60:
        falta += " A baixa acurácia confirma que não é um ajuste fino: a verba precisa ser revista na origem (deferimento, base ou fórmula)."
    return falta


def _pendentes_pjc():
    """Lê os pendentes que o ingerir.py computou (dependem das tabelas inteiras,
    por isso ficam do lado da ingestão). Ausente -> lista vazia."""
    fp = _CACHE_DIR / "pendentes.json"
    if fp.exists():
        try:
            return json.loads(fp.read_text(encoding="utf-8"))
        except Exception:
            pass
    return []


# ------------------------------------------------------------------ premissas
# Conta as premissas de cálculo mais citadas no campo "Observações de cálculo"
# do PJC (Zeev), agregando pelo NÚMERO da premissa (ex.: 6.2, 8.0, 11.0) — a
# chave estável, já que o mesmo item vem com grafias diferentes ("Diferenças de
# FGTS" / "FGTS a depositar"). Duas formas no texto: "(item N.N Nome)" e
# "Conforme premissa - N.N Nome". Métrica = nº de casos distintos que citam.
_PAT_ITEM = re.compile(r"\(\s*item\s+(\d{1,2}\.\d+)\s*([^)]*)\)", re.I)
_PAT_PREM = re.compile(r"premissas?\s*[-–:]?\s*(\d{1,2}\.\d+)\s+([^\n.]{2,60})", re.I)
_PAT_NUM = re.compile(r"^\s*\d{1,2}\s*[-.)]\s+")  # marcador de item numerado "1 - ", "2."


def _blocos(texto):
    """Quebra as observações nos itens numerados ('1 -', '2.', ...) — cada item é
    a unidade de contexto de uma premissa (o detalhe pode vir na linha seguinte).
    Texto sem numeração vira um bloco só."""
    blocos, atual = [], []
    for l in texto.split("\n"):
        if _PAT_NUM.match(l) and atual:
            blocos.append("\n".join(atual))
            atual = []
        atual.append(l)
    if atual:
        blocos.append("\n".join(atual))
    return blocos


def _premissas(casos):
    nomes = defaultdict(Counter)           # num -> Counter(grafias) p/ rotular
    cnjs_por_num = defaultdict(set)         # num -> {cnjs que citam}
    trechos_por_num = defaultdict(dict)     # num -> {cnj: trecho do item}
    n_com_obs = 0
    for cnj, c in casos.items():
        txt = c.get("observacoes_calculo")
        if not txt:
            continue
        n_com_obs += 1
        for bloco in _blocos(txt):
            nums = set()
            for pat in (_PAT_ITEM, _PAT_PREM):
                for m in pat.finditer(bloco):
                    num = m.group(1)
                    nome = re.sub(r"\s+", " ", m.group(2)).strip(" .-")
                    if nome:
                        nomes[num][nome[:60]] += 1
                    nums.add(num)
            if not nums:
                continue
            # trecho = o item inteiro, sem o marcador "N -", colapsado numa linha
            trecho = re.sub(r"\s+", " ", _PAT_NUM.sub("", bloco, count=1)).strip()
            if len(trecho) > 600:
                trecho = trecho[:600].rstrip() + "…"
            for num in nums:
                cnjs_por_num[num].add(cnj)
                trechos_por_num[num].setdefault(cnj, trecho)
    itens = [{"num": num, "nome": (nomes[num].most_common(1)[0][0] if nomes[num] else None),
              "n_casos": len(cnjs),
              "casos": [{"cnj": j, "trecho": trechos_por_num[num].get(j, "")} for j in sorted(cnjs)]}
             for num, cnjs in cnjs_por_num.items()]
    itens.sort(key=lambda x: (-x["n_casos"], x["num"]))
    n_distintos = len({cnj for cnjs in cnjs_por_num.values() for cnj in cnjs})
    return {"itens": itens, "n_casos_com_premissa": n_distintos, "n_casos_com_obs": n_com_obs}


# ------------------------------------------------------------------ render
casos = {}
for cnj in CNJS:
    c = montar_caso(cnj)
    if c:
        casos[cnj] = c
        print("ok:", cnj)
    else:
        print("sem dados:", cnj)

# HISTÓRICO de rodadas, anexado a CADA caso (não só aos que trocaram de safra,
# que é o recorte do bloco pareado). Um caso reprocessado tem o mesmo gabarito
# avaliado duas vezes, e sem isso a única forma de ver a rodada anterior era
# guardar um `antes.json` ANTES de reprocessar — o que ninguém lembra de fazer,
# e que não existia para o lote de 09/09/2026 (152 casos, 130 já rodados antes).
# As tabelas raw guardam toda rodada, então o histórico é reconstruível sempre.
# Limite conhecido: só o NOMINAL volta. As `*_consolidada` (corrigido/juros)
# guardam apenas a safra mais recente por CNJ (ver `_recorta` no ingerir.py), de
# propósito, então as camadas corrigido/pós-juros das rodadas antigas não existem.
for _cnj, _c in casos.items():
    _c["rodadas"] = _rodadas("".join(ch for ch in _cnj if ch.isdigit()))
    # só lado LIFT: o score tem que existir antes do gabarito (ver src/confianca.py)
    _c["confianca"] = score_confianca(_c)

# Diagnóstico do agente (análise caso a caso), quando existir: agente/agente_por_caso.json, gravado por
# ft_arvore_divergencias/ferramentas/agente_para_painel.py. Vale a análise da MESMA execução que o caso mostra;
# se o processo rodou de novo depois, vai a mais recente, marcada como de execução anterior (os valores mudaram).
_fp_ag = Path("agente/agente_por_caso.json")
_AG = (json.loads(_fp_ag.read_text(encoding="utf-8")).get("casos") or {}) if _fp_ag.exists() else {}
for _cnj, _c in casos.items():
    _an = _AG.get(_cnj) or []
    if not _an:
        continue
    _dexec = str(_c.get("data_processamento") or "")[:10]
    _tot = (_c.get("quadro") or {}).get("total_ia")

    def _mesma_exec(a):
        # mesma execução = mesmo dia E mesmo total da IA (quando o agente registrou o total):
        # o processo pode rodar de novo no mesmo dia, e aí a análise é de uma execução anterior
        if a.get("data_processamento") != _dexec:
            return False
        ta = a.get("total_ia")
        return ta is None or _tot is None or abs(float(ta) - float(_tot)) < 1.0

    _mesma = next((a for a in _an if _mesma_exec(a)), None)
    _c["agente"] = dict(_mesma or _an[0], mesma_execucao=_mesma is not None)

dados = {"cnjs": list(casos.keys()), "casos": casos, "pendentes_pjc": _pendentes_pjc(),
         "premissas": _premissas(casos),
         # catálogo de versões de prompt + o que mudou de uma versão p/ a seguinte
         # (diff do próprio texto do prompt, que vive no catálogo de agentes)
         "agentes": {"etapas": [{"etapa": e, "rotulo": r} for e, _, r in _ETAPAS_AG],
                     "etapas_safra": _ETAPAS_SAFRA,
                     "catalogo": _catalogo_agentes(),
                     "mudancas": _mudancas_agentes(),
                     # o mesmo caso em versões diferentes: a única comparação que
                     # isola versão de complexidade do caso
                     "pareado": _pareado(casos)}}
Path("saidas").mkdir(exist_ok=True)
Path("saidas/validacao_calculos.json").write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding="utf-8")
html = Path("codigo/src/template_telas.html").read_text(encoding="utf-8")
html = html.replace("/*__DADOS__*/", json.dumps(dados, ensure_ascii=False))
Path("saidas/validacao_calculos.html").write_text(html, encoding="utf-8")
print("gerado: saidas/validacao_calculos.html")
