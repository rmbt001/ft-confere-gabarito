"""Parser do PJC (PJe-Calc Cidadão, "Planilha de Cálculo").

Formato padronizado e com texto selecionável -> extração determinística.
Primeira versão foca no CABEÇALHO e no RESUMO DO CÁLCULO (verbas + valores
finais), que já cobrem "as verbas certas?" e "o valor final bate?".

Validar contra um PDF real (casos/<processo>/pjc.pdf) antes de confiar.
Depende de: pdfplumber.
"""
from __future__ import annotations

import re
from pathlib import Path

import pdfplumber


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _num(s: str | None) -> float | None:
    """Converte número pt-BR ('1.234,56', '(40.343,60)') em float.

    Parênteses indicam valor negativo. Retorna None se não for número.
    """
    if s is None:
        return None
    t = s.strip()
    if not t or t in {"-", "–"}:
        return None
    neg = t.startswith("(") and t.endswith(")")
    t = t.strip("()").replace(".", "").replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        return None
    return -v if neg else v


def _texto_paginas(pdf: pdfplumber.PDF, ate_pagina: int | None = None) -> str:
    paginas = pdf.pages if ate_pagina is None else pdf.pages[:ate_pagina]
    return "\n".join((p.extract_text() or "") for p in paginas)


# ---------------------------------------------------------------------------
# Cabeçalho
# ---------------------------------------------------------------------------
def parse_cabecalho(pdf: pdfplumber.PDF) -> dict:
    """Extrai metadados do cabeçalho (processo, partes, datas)."""
    txt = _texto_paginas(pdf, ate_pagina=3)

    def busca(padrao: str) -> str | None:
        m = re.search(padrao, txt)
        return m.group(1).strip() if m else None

    # nº do cálculo no PJe-Calc (linha "Cálculo: N" logo abaixo do processo): é o
    # que diz se o .pjc da pasta é o MESMO cálculo deste PDF
    mid = re.search(r"^\s*Cálculo:\s*(\d+)\s*$", txt, re.M)
    return {
        "processo": busca(r"Processo:\s*([\d.\-]+\.\d{4}\.\d\.\d{2}\.\d{4})"),
        "id_calculo": mid.group(1) if mid else None,
        "reclamante": busca(r"Reclamante:\s*(.+)"),
        "reclamado": busca(r"Reclamado:\s*(.+)"),
        "periodo_calculo": busca(r"Período do Cálculo:\s*([\d/]+ a [\d/]+)"),
        "data_ajuizamento": busca(r"Data Ajuizamento:\s*([\d/]+)"),
        "admissao": busca(r"Admissão:\s*([\d/]+)"),
        "demissao": busca(r"Demissão:\s*([\d/]+)"),
    }


# ---------------------------------------------------------------------------
# Resumo do Cálculo
# ---------------------------------------------------------------------------
def parse_resumo_calculo(pdf: pdfplumber.PDF) -> list[dict]:
    """Extrai a tabela 'Resumo do Cálculo' (verba -> valores finais).

    Retorna lista de dicts: descricao, valor_corrigido, juros, total.
    A linha 'Total' é incluída com descricao='Total'.
    """
    linhas: list[dict] = []
    for page in pdf.pages:
        texto = page.extract_text() or ""
        if "Resumo do Cálculo" not in texto:
            continue
        for tabela in page.extract_tables():
            header = " ".join(c or "" for c in (tabela[0] if tabela else []))
            if "Valor Corrigido" not in header and "Descrição" not in header:
                continue
            for row in tabela[1:]:
                cels = [c.strip() if c else "" for c in row]
                if not cels or not cels[0]:
                    continue
                descricao = cels[0]
                # últimas 3 colunas numéricas: corrigido, juros, total
                nums = [_num(c) for c in cels[1:]]
                nums = [n for n in nums if n is not None]
                if not nums:
                    continue
                linhas.append({
                    "descricao": descricao,
                    "valor_corrigido": nums[0] if len(nums) >= 1 else None,
                    "juros": nums[1] if len(nums) >= 2 else None,
                    "total": nums[-1],
                })
                # O Resumo termina na linha "Total"; o que vem depois (na mesma
                # página) é o bloco de Créditos/Débitos, capturado à parte.
                if descricao.strip().lower() == "total":
                    return linhas
        if linhas:
            break  # Resumo está na(s) primeira(s) página(s)
    return linhas


# ---------------------------------------------------------------------------
# Demonstrativo de Verbas (Devido nominal por verba)
# ---------------------------------------------------------------------------
_RE_PERIODO = re.compile(r"^\d{1,2}[/ ].*?\d{2,4}")   # linha de dado começa com período
_RE_NUM = re.compile(r"\(?-?[\d.]*\d,\d+\)?|\b0,00\b")  # números pt-BR
_RE_COMP = re.compile(r"(\d{2})/(\d{4})")              # MM/AAAA dentro do período


def _nums_da_linha(linha: str) -> list[float]:
    vals = []
    for tok in _RE_NUM.findall(linha):
        n = _num(tok)
        if n is not None:
            vals.append(n)
    return vals


def _competencia(linha: str) -> str | None:
    """Período '20 a 31/12/2011' -> '2011-12' (usa a última data da linha)."""
    achados = _RE_COMP.findall(linha)
    if not achados:
        return None
    mes, ano = achados[-1]
    return f"{ano}-{mes}"


_TS = {"vertical_strategy": "lines", "horizontal_strategy": "lines"}


def _col(header, *subs):
    """Índice da 1ª coluna cujo cabeçalho (maiúsculo) contém todos os termos."""
    for ci, h in enumerate(header):
        H = (h or "").upper().replace("\n", " ")
        if all(s in H for s in subs):
            return ci
    return None


def _nomes_verba(page):
    """[(top, nome)] das linhas 'Nome: X' da página (por posição vertical)."""
    linhas: dict = {}
    for w in page.extract_words():
        linhas.setdefault(round(w["top"] / 2), []).append(w)
    out = []
    for ws in linhas.values():
        ws.sort(key=lambda w: w["x0"])
        txt = " ".join(w["text"] for w in ws)
        m = re.match(r"Nome:\s*(.+)", txt)
        if m and m.group(1).strip():
            nome = re.split(r"\s+Per[íi]odo\b|\s+Incid", m.group(1))[0].strip()
            out.append((min(w["top"] for w in ws), nome))
    return out


def parse_demonstrativo_verbas(pdf: pdfplumber.PDF) -> list[dict]:
    """Soma a coluna 'Devido' (nominal) por verba do Demonstrativo de Verbas.

    Extração por LINHAS (tabelas bordadas), mapeando colunas pelo cabeçalho
    (Devido, Base, Multiplicador...). O nome da verba vem das linhas 'Nome: X',
    correlacionadas por posição vertical com cada tabela.
    """
    verbas: dict = {}
    ordem: list = []
    nome_atual = None

    def verba(nome):
        if nome not in verbas:
            verbas[nome] = {"nome": nome, "soma_devido": 0.0,
                            # palavra inteira: "HORAS SOBREAVISO" não é reflexo (07/11/2026)
                            "reflexo": bool(re.search(r"\bSOBRE\b", nome.upper())), "competencias": []}
            ordem.append(nome)
        return verbas[nome]

    for page in pdf.pages:
        eventos = [(top, "nome", nm) for top, nm in _nomes_verba(page)]
        for t in page.find_tables(_TS):
            data = t.extract()
            if not data or len(data) < 2:
                continue
            hidx = next((ri for ri, row in enumerate(data[:3])
                         if _col(row, "DEVIDO") is not None and _col(row, "DIVISOR") is not None), None)
            if hidx is None:
                continue  # Juros/FGTS/INSS têm outro cabeçalho — ignora
            eventos.append((t.bbox[1], "tab", (data, hidx)))
        for _, kind, payload in sorted(eventos, key=lambda e: e[0]):
            if kind == "nome":
                nome_atual = payload
                continue
            if nome_atual is None:
                continue
            data, hidx = payload
            header = data[hidx]
            ci_per = _col(header, "PER")
            # o valor realmente devido é a DIFERENÇA (Devido − Pago); quando não há
            # pagamento, Diferença == Devido. Somar Devido infla verbas com Pago>0
            # (ex.: equiparação, integração). Fallback p/ Devido se não houver Diferença.
            ci_dif = _col(header, "DIFEREN") or _col(header, "DEVIDO")
            ci_dev, ci_pago = _col(header, "DEVIDO"), _col(header, "PAGO")
            ci_base, ci_mult, ci_qtd = _col(header, "BASE"), _col(header, "MULTIPLICADOR"), _col(header, "QUANTIDADE")
            v = verba(nome_atual)
            for row in data[hidx + 1:]:
                cel = (row[ci_per] if ci_per is not None and ci_per < len(row) else "") or ""
                comp = _competencia(cel)
                dev = _num(row[ci_dif]) if ci_dif is not None and ci_dif < len(row) else None
                if comp is None or dev is None:
                    continue
                # parcelas da diferença, p/ comparar a DEDUÇÃO com a da IA
                # (`valores_compensados`). Sem coluna Pago no layout, deriva de
                # Devido − Diferença; se nem Devido houver, fica 0.
                bruto = _num(row[ci_dev]) if ci_dev is not None and ci_dev < len(row) else None
                pago = _num(row[ci_pago]) if ci_pago is not None and ci_pago < len(row) else None
                if pago is None:
                    pago = round(bruto - dev, 2) if bruto is not None else 0.0
                v["competencias"].append({
                    "competencia": comp,
                    "base": _num(row[ci_base]) if ci_base is not None and ci_base < len(row) else None,
                    "multiplicador": _num(row[ci_mult]) if ci_mult is not None and ci_mult < len(row) else None,
                    "quantidade": _num(row[ci_qtd]) if ci_qtd is not None and ci_qtd < len(row) else None,
                    "devido": round(dev, 2),
                    "devido_bruto": round(bruto, 2) if bruto is not None else round(dev + pago, 2),
                    "pago": round(pago, 2),
                })
                v["soma_devido"] += dev
    out = [verbas[n] for n in ordem]
    for v in out:
        v["soma_devido"] = round(v["soma_devido"], 2)
        v["soma_pago"] = round(sum(c["pago"] for c in v["competencias"]), 2)
        v["n_competencias"] = len(v["competencias"])
    return out


# ---------------------------------------------------------------------------
# Histórico Salarial
# ---------------------------------------------------------------------------
def parse_historico_salarial(pdf: pdfplumber.PDF) -> dict:
    """{ 'AAAA-MM': {'salario_base', 'premio_metas', 'todas': {coluna: valor}} }.

    Extração por LINHAS da tabela 'Ocorrências do Histórico Salarial'; identifica
    a coluna 'SALÁRIO BASE' pelo cabeçalho (evitando 'SALÁRIO REAJUSTADO').
    """
    hist: dict = {}
    for page in pdf.pages:
        for data in page.extract_tables(_TS):
            if not data or len(data) < 2:
                continue
            hidx = next((ri for ri, row in enumerate(data[:3]) if _col(row, "S/ANO") is not None), None)
            if hidx is None:
                continue
            header = [(c or "").replace("\n", " ").strip() for c in data[hidx]]
            ci_mes = _col(header, "S/ANO") or 0
            ci_sal = None
            for ci, h in enumerate(header):
                if h.upper().replace("Á", "A") == "SALARIO BASE":
                    ci_sal = ci
            if ci_sal is None:
                for ci, h in enumerate(header):
                    H = h.upper().replace("Á", "A")
                    if "SALARIO" in H and "BASE" in H and "REAJUST" not in H:
                        ci_sal = ci
            ci_prem = _col(header, "PR", "MIO")  # PRÊMIO METAS (layout simples)
            for row in data[hidx + 1:]:
                cel = (row[ci_mes] if ci_mes < len(row) else "") or ""
                m = re.match(r"(\d{2})/(\d{4})", cel.strip())
                if not m:
                    continue
                comp = f"{m.group(2)}-{m.group(1)}"
                hist[comp] = {
                    "salario_base": _num(row[ci_sal]) if ci_sal is not None and ci_sal < len(row) else None,
                    "premio_metas": _num(row[ci_prem]) if ci_prem is not None and ci_prem < len(row) else None,
                    "todas": {header[ci]: _num(row[ci]) for ci in range(len(header))
                              if ci != ci_mes and ci < len(row) and header[ci]},
                }
    return hist


# ---------------------------------------------------------------------------
# Faltas e Férias -> dias de férias por competência
# ---------------------------------------------------------------------------
def parse_ferias_gozo(pdf: pdfplumber.PDF) -> list[tuple[str, str]]:
    """Períodos de gozo de férias (lista de (inicio, fim) em dd/mm/aaaa)."""
    periodos: list[tuple[str, str]] = []
    dentro = False
    ja_entrou = False
    for page in pdf.pages:
        for l in (page.extract_text() or "").splitlines():
            if "Faltas e F" in l or l.strip() == "FÉRIAS":
                dentro = True
                ja_entrou = True
            if "Hist" in l and "Salarial" in l:
                dentro = False
            if not dentro:
                continue
            for m in re.finditer(r"(\d{2}/\d{2}/\d{4})\s+a\s+(\d{2}/\d{2}/\d{4})", l):
                periodos.append((m.group(1), m.group(2)))
        # a seção de férias vem antes do Histórico Salarial; se já passamos por ela,
        # não há mais nada útil adiante — evita extrair texto das páginas restantes
        # (o gargalo em PDFs grandes: extract_text é caro por página).
        if ja_entrou and not dentro:
            break
    # mantém só períodos de GOZO (<=45 dias); exclui aquisitivo/concessivo (~1 ano)
    from datetime import date
    def dur(p):
        try:
            di = date(*map(int, reversed(p[0].split("/"))))
            df = date(*map(int, reversed(p[1].split("/"))))
            return (df - di).days
        except ValueError:
            return 9999
    gozo = [p for p in dict.fromkeys(periodos) if 0 <= dur(p) <= 45]
    return gozo


def dias_ferias_por_mes(periodos: list[tuple[str, str]]) -> dict:
    """{ 'AAAA-MM': dias_de_ferias } a partir dos períodos de gozo."""
    from datetime import date, timedelta
    dias: dict = {}
    for ini, fim in periodos:
        try:
            di = date(*map(int, reversed(ini.split("/"))))
            df = date(*map(int, reversed(fim.split("/"))))
        except ValueError:
            continue
        d = di
        while d <= df:
            k = f"{d.year}-{d.month:02d}"
            dias[k] = dias.get(k, 0) + 1
            d += timedelta(days=1)
    return dias


def parse_resumo_only(caminho: str | Path, max_paginas: int = 8) -> list[dict]:
    """Só o 'Resumo do Cálculo' do PDF (verba -> corrigido, juros, total).

    É a ÚNICA fonte de JUROS por verba que temos hoje: o .pjc nativo traz o fator
    de correção por ocorrência (`indiceAcumulado`), mas os juros vivem noutro bloco
    (ApuracaoDeJuros) ainda não mapeado. Lê só as primeiras páginas porque o resumo
    abre o documento — varrer um PDF de 100 páginas por caso custaria minutos.
    """
    with pdfplumber.open(Path(caminho)) as pdf:
        class _Fatia:                      # janela de páginas p/ reusar o parser
            pages = pdf.pages[:max_paginas]
        return parse_resumo_calculo(_Fatia)


def parse_cabecalho_only(caminho: str | Path) -> dict:
    """Só o cabeçalho do PDF (leve — lê 3 páginas). Usado pro header híbrido
    quando o .pjc é a fonte primária mas tem campos de cabeçalho nulos."""
    with pdfplumber.open(Path(caminho)) as pdf:
        return parse_cabecalho(pdf)


def _nomes_fora_principal(pdf: pdfplumber.PDF, ate_pagina: int = 6) -> set[str]:
    """Nomes do bloco "Verbas que não compõem o Principal" (logo após o resumo).
    É o mesmo `comporPrincipal = NAO` do .pjc: linha informativa (base de reflexo,
    pedidos improcedentes), fora do total. Nome quebrado em duas linhas é juntado."""
    txt = _texto_paginas(pdf, ate_pagina=ate_pagina)
    i = txt.find("Verbas que não compõem o Principal")
    if i < 0:
        return set()
    nomes, pend = set(), ""
    for linha in txt[i:].splitlines()[1:]:
        linha = linha.strip()
        if not linha or linha.startswith("Total"):
            break
        m = re.match(r"(.*?)\s*(\(?[\d.]+,\d{2}\)?)$", linha)
        if m:
            nomes.add(re.sub(r"\s+", " ", f"{pend} {m.group(1)}").strip().upper())
            pend = ""
        else:
            pend = f"{pend} {linha}"
    return nomes


def parse_pjc(caminho: str | Path) -> dict:
    """Lê o PDF do PJC e devolve cabecalho, resumo, verbas, historico e ferias."""
    caminho = Path(caminho)
    with pdfplumber.open(caminho) as pdf:
        gozo = parse_ferias_gozo(pdf)
        fora = _nomes_fora_principal(pdf)
        todas = parse_demonstrativo_verbas(pdf)
        return {
            "cabecalho": parse_cabecalho(pdf),
            "resumo": parse_resumo_calculo(pdf),
            "verbas": [v for v in todas if v["nome"].strip().upper() not in fora],
            "verbas_fora_principal": [{"nome": v["nome"], "soma_devido": v.get("soma_devido"),
                                       "reflexo": v.get("reflexo")}
                                      for v in todas if v["nome"].strip().upper() in fora],
            "historico_salarial": parse_historico_salarial(pdf),
            "ferias_gozo": gozo,
            "dias_ferias_mes": dias_ferias_por_mes(gozo),
        }


if __name__ == "__main__":
    import json
    import sys

    if len(sys.argv) < 2:
        print("uso: python parse_pjc.py <caminho_do_pjc.pdf>")
        raise SystemExit(1)
    resultado = parse_pjc(sys.argv[1])
    print(json.dumps(resultado["cabecalho"], ensure_ascii=False, indent=2))
    print(f"\nResumo do Cálculo: {len(resultado['resumo'])} linhas")
    for linha in resultado["resumo"]:
        print(f"  {linha['descricao'][:60]:<60} {linha['total']}")
