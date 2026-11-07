"""As tres medidas de acuracia do painel, isoladas para poderem ser testadas.

Todas dividem pelo PJC, a referencia — nao pelo maior dos dois lados. Medir o
erro do Fast Track contra o gabarito e o ponto: dividir pelo maior dava desconto
justamente a quem erra mais (calcular 20x a referencia tirava 5%).

O preco e que NAO HA PISO: calcular 20x a referencia da -1800%. E de proposito
(decisao da gerencia, 09/2026). Por isso toda leitura agregada do painel usa
MEDIANA.

Regra do denominador zero, valida para as tres: a medida e 100% quando o
numerador tambem e zero, e 0% caso contrario.
"""


def assertividade(total_ia, total_pjc):
    """② — a soma final bate? Compara so os dois totais."""
    if total_ia is None or total_pjc is None:
        return None
    num, den = abs(total_ia - total_pjc), abs(total_pjc)
    if den == 0:
        return 100.0 if num == 0 else 0.0
    return round(100 * (1 - num / den), 1)


def _soma(verbas):
    """(liquido, bruto, denominador, n) — verba sem valor dos dois lados nao entra."""
    liq = bruto = den = 0.0
    n = 0
    for v in verbas:
        ia, pj = v.get("total_ia"), v.get("total_pjc")
        if ia is None and pj is None:
            continue
        ia, pj = ia or 0.0, pj or 0.0
        liq += ia - pj
        bruto += abs(ia - pj)
        den += abs(pj)
        n += 1
    return liq, bruto, den, n


def acuracia_global(verbas):
    """① — de todo o dinheiro do caso, quanto esta no lugar certo?

    Soma o erro em MODULO verba a verba, entao nao cancela. Verba que so um dos
    lados tem conta pelo valor inteiro.
    """
    _liq, bruto, den, n = _soma(verbas)
    if n == 0:
        return None
    if den == 0:
        return 100.0 if bruto == 0 else 0.0
    return round(100 * (1 - bruto / den), 1)


def acuracia_verba(total_ia, total_pjc):
    """③ — quando os dois lados tem a mesma verba, o valor bate?"""
    return assertividade(total_ia, total_pjc)


def compensacao(verbas):
    """Indice de compensacao — quanto do erro do caso some ao olhar so o total.

    0%   = os erros vao todos na mesma direcao; o total mostra o erro inteiro.
    100% = o total bate por acaso; a assertividade deste caso nao quer dizer nada.
    None = erro bruto zero. INDEFINIDO, nao zero: nao ha compensacao a medir.

    Devolve tambem os dois valores em R$, que a tela "Onde o erro nasce" usa como
    unidade e que permitem auditar o indice sem refazer a soma.
    """
    liq, bruto, _den, _n = _soma(verbas)
    indice = None if bruto <= 0 else round(100 * (1 - abs(liq) / bruto), 1)
    return indice, round(bruto, 2), round(liq, 2)


def indice_compensacao(verbas):
    """So o indice, sem os dois valores em R$.

    Quem mede a REGRA (os testes) so precisa do indice; os R$ existem para a tela
    e para auditar a conta. Separar as duas leituras evita que um `[0]` solto no
    meio de um teste passe a valer como afirmacao sobre a formula.
    """
    return compensacao(verbas)[0]
