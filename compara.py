"""Compara o cálculo da IA com o gabarito em PDF (PJe-Calc) de um processo ou de um lote inteiro.

Entrada: uma pasta com os PDFs dos gabaritos. Pode ser um PDF solto (um processo) ou muitos (um lote); também
vale uma subpasta por processo. O CNJ de cada PDF sai do nome do arquivo (20 dígitos) ou, se não estiver lá, do
texto da primeira página do PDF.

Arquivos `.pjc` na pasta são ignorados: em geral são o PJC que a própria esteira gerou do cálculo da IA (o nome
traz a data e a hora da execução) e comparar com ele dá 100% sempre. Use --pjc-gabarito só quando o `.pjc` for
mesmo o gabarito do calculista (aí cada .pjc precisa estar na pasta do seu processo, junto do PDF).

Passos:
  1. lê os PDFs e descobre o CNJ de cada um;
  2. copia cada gabarito para `casos/<CNJ>/pjc.pdf` (o nome que o motor espera);
  3. baixa da Nekt as saídas da IA de todos os CNJs de uma vez (baixa_cnj.py);
  4. roda o motor de comparação do painel (codigo/pipeline/gerar_telas.py) para todos;
  5. grava em `saidas/<rótulo>/`: a página (html), o JSON, `resumo.csv` (uma linha por processo) e
     `verbas.csv` (uma linha por verba de cada processo).

Uso:
    python compara.py <pasta> [--rotulo lote_nov] [--sem-nekt] [--pjc-gabarito]
ex.: python compara.py "C:/Users/<você>/Downloads/a_avaliar"
     python compara.py "D:/gabaritos_lote_2000" --rotulo lote_2000

--sem-nekt: não baixa de novo os processos que já têm recorte em .cache.
"""
import csv
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI))
from baixa_cnj import _digitos, _formata, recorta_lote, referencias  # noqa: E402

RX_CNJ = re.compile(r"\d{7}-\d{2}\.\d{4}\.\d\.\d{2}\.\d{4}")


def _opcao(nome, padrao=None):
    return sys.argv[sys.argv.index(nome) + 1] if nome in sys.argv else padrao


def _cnj_do_pdf(pdf):
    try:
        import pdfplumber
        with pdfplumber.open(pdf) as p:
            txt = " ".join((pg.extract_text() or "") for pg in p.pages[:2])
        m = RX_CNJ.search(txt)
        return m.group(0) if m else None
    except Exception:  # noqa: BLE001
        return None


def _cnj(arquivo):
    for nome in (arquivo.name, arquivo.parent.name):  # nome do arquivo ou da subpasta
        d = _digitos(nome)
        if len(d) >= 20:
            return _formata(d[:20])
    c = _cnj_do_pdf(arquivo) if arquivo.suffix.lower() == ".pdf" else None
    return _formata(_digitos(c)) if c else None


def _brl(v):
    return "—" if v is None else f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def monta_pagina(arq_json, arq_html):
    """Página no layout do painel dos parciais (template da cópia desde_2026-10-14), não no de produção que o
    gerar_telas usa. Mesmos dados; a aba Premissas lê a situação de cada premissa na esteira."""
    html = (AQUI / "codigo/src/template_telas_parciais.html").read_text(encoding="utf-8")
    prem_arq = AQUI / "contexto/premissas/premissas_situacao_esteira.json"
    prem = [{k: x.get(k) for k in ("id", "secao", "regra", "situacao", "falta")}
            for x in json.loads(prem_arq.read_text(encoding="utf-8"))] if prem_arq.exists() else []
    html = html.replace("/*__PREMISSAS_ESTEIRA__*/[]", json.dumps(prem, ensure_ascii=False))
    antes, depois = html.split("/*__DADOS__*/", 1)
    dados = json.loads(Path(arq_json).read_text(encoding="utf-8"))
    with open(arq_html, "w", encoding="utf-8") as f:
        f.write(antes)
        json.dump(dados, f, ensure_ascii=False)
        f.write(depois)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if "--so-pagina" in sys.argv:  # remonta a página de uma saída já gerada: compara.py --so-pagina saidas/<rótulo>
        for p in [a for a in sys.argv[1:] if not a.startswith("--")]:
            monta_pagina(Path(p) / "comparacao.json", Path(p) / "comparacao.html")
            print("página:", Path(p) / "comparacao.html")
        return
    args = [a for i, a in enumerate(sys.argv[1:], 1) if not a.startswith("--") and sys.argv[i - 1] != "--rotulo"]
    if not args:
        sys.exit(__doc__)
    pasta = Path(args[0])
    usa_pjc = "--pjc-gabarito" in sys.argv

    # 1-2. gabaritos -> casos/<CNJ>/
    gab, sem_cnj, repetidos = {}, [], []
    for pdf in sorted(pasta.rglob("*.pdf")):
        c = _cnj(pdf)
        if not c:
            sem_cnj.append(pdf.name)
        elif c in gab:
            repetidos.append(f"{c}: {pdf.name}")
        else:
            gab[c] = pdf
    if not gab:
        sys.exit(f"nenhum PDF com CNJ em {pasta}")
    for c, pdf in gab.items():
        caso = AQUI / "casos" / c
        if caso.exists():
            shutil.rmtree(caso)
        caso.mkdir(parents=True)
        shutil.copy2(pdf, caso / "pjc.pdf")
        if usa_pjc:
            for pjc in pdf.parent.glob("*.pjc"):
                shutil.copy2(pjc, caso / "pjc.pjc")
                break
    print(f"{len(gab)} gabarito(s) em PDF" + (f" · {len(sem_cnj)} PDF(s) sem CNJ: {', '.join(sem_cnj[:5])}" if sem_cnj else "")
          + (f" · {len(repetidos)} repetido(s), fica o 1º: {'; '.join(repetidos[:3])}" if repetidos else ""))
    ign = [] if usa_pjc else list(pasta.rglob("*.pjc"))
    if ign:
        print(f"  {len(ign)} .pjc ignorado(s) (PJC gerado pela esteira; use --pjc-gabarito se for gabarito)")

    # 3. saídas da IA, uma leitura por tabela para o lote todo
    cnjs = sorted(gab)
    falta = [c for c in cnjs if "--sem-nekt" not in sys.argv or not (AQUI / ".cache" / f"caso_raw__{c}.pkl").exists()]
    referencias()
    if falta:
        recorta_lote(falta)
    cnjs = [c for c in cnjs if (AQUI / ".cache" / f"caso_raw__{c}.pkl").exists()]
    if not cnjs:
        sys.exit("nenhum desses processos rodou na esteira")

    # 4. motor de comparação (lista em arquivo: 2.000 CNJs não cabem na linha de comando do Windows)
    rot = _opcao("--rotulo") or (cnjs[0] if len(cnjs) == 1 else f"lote_{len(cnjs)}")
    saida = AQUI / "saidas" / rot
    saida.mkdir(parents=True, exist_ok=True)
    lista = saida / "cnjs.txt"
    lista.write_text("\n".join(cnjs), encoding="utf-8")
    r = subprocess.run([sys.executable, "codigo/pipeline/gerar_telas.py", f"@{lista}"], cwd=AQUI)
    if r.returncode:
        sys.exit("o motor de comparação falhou (veja a mensagem acima)")
    shutil.copy2(AQUI / "saidas" / "validacao_calculos.json", saida / "comparacao.json")
    monta_pagina(saida / "comparacao.json", saida / "comparacao.html")
    casos = json.loads((saida / "comparacao.json").read_text(encoding="utf-8"))["casos"]

    # 5. resumo e verba a verba
    with open(saida / "resumo.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["cnj", "apto", "motivo_inapto", "assertividade", "total_ia", "total_pjc", "gabarito_pdf"])
        for c in cnjs:
            x = casos.get(c) or {}
            q = x.get("quadro") or {}
            w.writerow([c, x.get("apto"), "; ".join(m.get("categoria", "") for m in x.get("motivos_inaptidao") or []),
                        q.get("assertividade"), q.get("total_ia"), q.get("total_pjc"), gab[c].name])
    with open(saida / "verbas.csv", "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["cnj", "tipo", "status", "verba_ia", "verba_pjc", "codigo", "total_ia", "total_pjc", "acuracia"])
        for c in cnjs:
            for v in (casos.get(c) or {}).get("verbas") or []:
                tipo = "reflexo" if v.get("is_reflexo") else ("rescisoria" if v.get("is_rescisoria") else "principal")
                w.writerow([c, tipo, v.get("status"), v.get("nome_ia"), v.get("nome_pjc"),
                            v.get("codigo") or v.get("codigo_glossario"), v.get("total_ia"), v.get("total_pjc"),
                            v.get("acuracia")])

    print()
    if len(cnjs) == 1:
        x = casos.get(cnjs[0]) or {}
        q = x.get("quadro") or {}
        print(f"{cnjs[0]} · assertividade {q.get('assertividade')}% · IA {_brl(q.get('total_ia'))} · PJC {_brl(q.get('total_pjc'))}")
        for v in x.get("verbas") or []:
            if not v.get("is_reflexo"):
                print(f"  {(v.get('nome_ia') or '—')[:48]:48} | {(v.get('nome_pjc') or '—')[:36]:36} | "
                      f"{_brl(v.get('total_ia')):>16} | {_brl(v.get('total_pjc')):>16}")
    else:
        a = [(casos.get(c) or {}).get("quadro", {}).get("assertividade") for c in cnjs if (casos.get(c) or {}).get("apto")]
        a = sorted(v for v in a if v is not None)
        if a:
            print(f"{len(cnjs)} processos · {len(a)} aptos · mediana {a[len(a) // 2]}% · "
                  f"{sum(v >= 80 for v in a) / len(a):.0%} com 80% ou mais")
    print(f"\npágina:  {saida / 'comparacao.html'}\nresumo:  {saida / 'resumo.csv'}\nverbas:  {saida / 'verbas.csv'}")


if __name__ == "__main__":
    main()
