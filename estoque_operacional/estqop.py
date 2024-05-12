from dataclasses import dataclass
from enum import IntEnum
from itertools import groupby, chain
from pathlib import Path
from sys import stderr
from typing import Final, Iterable, Self, ClassVar, Sequence

_MSG_INICIO: Final[str] = '''Estoque Operacional
Abner Eduardo Ramos Ferreira
Fernando Martins de Gouvêa
Joilson Briana dos Santos
Lucas de Abreu Tondin
'''

_MSG_ARQUIVO_NAO_ENCONTRADO: Final[str] = 'Arquivo de teste não encontrado'

_CAMINHO_ARQUIVO_PRODUTOS: Final[Path] = Path('produtos.txt')
_CAMINHO_ARQUIVO_VENDAS: Final[Path] = Path('vendas.txt')

_CAMINHO_ARQUIVO_TRANSFERENCIAS: Final[Path] = Path('transfere.txt')
_CAMINHO_ARQUIVO_DIVERGENCIAS: Final[Path] = Path('divergencias.txt')
_CAMINHO_ARQUIVO_VENDAS_POR_CANAL: Final[Path] = Path('totcanais.txt')

_DELIMITADOR_DADOS: Final[str] = ';'


@dataclass(frozen=True, kw_only=True, slots=True)
class _Produto:
    """
    Utilizado para representar os dados de um produto em um arquivo de entrada.
    """
    codigo: int
    qtd_estoque: int
    qtd_min_co: int


class _SituacaoVenda(IntEnum):
    """
    Utilizado para representar a situação de uma venda em um arquivo de entrada.
    """
    CONFIRMADA_PGTO_OK = 100
    CONFIRMADA_PGTO_PENDENTE = 102
    CANCELADA = 135
    NAO_FINALIZADA = 190
    ERRO_NAO_IDENTIFICADO = 999

    def is_confirmada(self) -> bool:
        """
        Verifica se a situação de venda pode ser considerada como confirmada.
        :return: `True`, caso a situação de venda seja confirmada; caso contrário, `False`.
        """
        return self in (self.CONFIRMADA_PGTO_OK, self.CONFIRMADA_PGTO_PENDENTE)

    def msg_erro(self) -> str:
        """
        Retorna a mensagem de erro associada à situação de venda, ou "N/A" em caso de sucesso.
        :return: Mensagem de erro associada à situação de venda, ou "N/A" em caso de sucesso.
        """
        match self:
            case self.CANCELADA:
                return 'Venda cancelada'
            case self.NAO_FINALIZADA:
                return 'Venda não finalizada'
            case self.ERRO_NAO_IDENTIFICADO:
                # IMPORTANTE: O documento pede ponto final apesar dos arquivos de teste não seguirem isso.
                return 'Erro desconhecido. Acionar equipe de TI.'
            case _:
                return 'N/A'


class _CanalVenda(IntEnum):
    """
    Utilizado para representar o canal de uma venda em um arquivo de entrada.
    """
    REPR_COMERCIAL = 1
    WEBSITE = 2
    APP_ANDROID = 3
    APP_IOS = 4

    def descricao(self) -> str:
        """
        Retorna a descrição de um canal de venda, utilizada na relação gerada em um arquivo de saída.
        :return: Descrição do canal de venda.
        """
        match self:
            case self.REPR_COMERCIAL:
                return 'Representantes'
            case self.WEBSITE:
                return 'Website'
            case self.APP_ANDROID:
                return 'App móvel Android'
            case self.APP_IOS:
                return 'App móvel iPhone'


@dataclass(frozen=True, kw_only=True, slots=True)
class _Venda:
    """
    Utilizado para representar uma venda em um arquivo de entrada.
    """
    cod_produto: int
    qtd: int
    situacao: _SituacaoVenda
    canal: _CanalVenda


@dataclass(frozen=True, kw_only=True, slots=True)
class _VendasPorProduto:
    """
    Associação entre um produto e várias vendas.
    """
    index: int
    produto: _Produto
    vendas: Sequence[_Venda]


@dataclass(frozen=True, kw_only=True, slots=True)
class _NecessidadeTransferencia:
    """
    Utilizado para representar a relação de necessidades de transferência em um arquivo de saída.
    """
    __NE_LO: ClassVar[int] = 1
    __NE_HI: ClassVar[int] = 10
    __NE_ESP: ClassVar[int] = 10

    cod_produto: int
    qtd_produto_co: int
    qtd_min_produto_co: int
    qtd_vendas: int
    qtd_estoque_pos_vendas: int
    qtd_necessidade: int
    qtd_transf_arm_co: int

    @classmethod
    def multigerar(cls, produtos: Iterable[_Produto], vendas: Iterable[_Venda]) -> Iterable[Self]:
        """
        Gera uma relação de necessidades de transferência com base nos produtos e vendas informados.
        :param produtos: Lista de produtos vinda de um arquivo de entrada.
        :param vendas: Lista de vendas vinda de um arquivo de entrada.
        :return: Relação de necessidades de transferência de armazenamento de produtos.
        """
        vendas_produtos_raw = sorted((_VendasPorProduto(index=i, produto=p, vendas=(v,))
                                      for v in vendas
                                      for i, p in enumerate(produtos)
                                      if v.cod_produto == p.codigo and v.situacao.is_confirmada()),
                                     key=lambda vp: vp.produto.codigo)
        vendas_produtos_agrupados = (_VendasPorProduto(index=rvp.index,
                                                       produto=rvp.produto,
                                                       vendas=tuple(chain.from_iterable((vp.vendas for vp in vps))))
                                     for rvp, vps in groupby(vendas_produtos_raw,
                                                             key=lambda vp: _VendasPorProduto(index=vp.index,
                                                                                              produto=vp.produto,
                                                                                              vendas=())))
        vendas_produtos_ordem_original = sorted(vendas_produtos_agrupados, key=lambda vp: vp.index)
        return (_NecessidadeTransferencia(cod_produto=vp.produto.codigo,
                                          qtd_produto_co=vp.produto.qtd_estoque,
                                          qtd_min_produto_co=vp.produto.qtd_min_co,
                                          qtd_vendas=(qtd_vendas := sum(v.qtd for v in vp.vendas)),
                                          qtd_estoque_pos_vendas=(est_pos_venda := vp.produto.qtd_estoque - qtd_vendas),
                                          qtd_necessidade=(ne := abs(max(vp.produto.qtd_min_co - est_pos_venda, 0))),
                                          qtd_transf_arm_co=cls.__NE_ESP if cls.__NE_LO < ne < cls.__NE_HI else ne)
                for vp in vendas_produtos_ordem_original)


@dataclass(frozen=True, kw_only=True, slots=True)
class _Divergencia:
    """
    Utilizado para representar a relação de divergências de vendas em um arquivo de saída.
    """
    __MSG_SEM_COD: ClassVar[str] = 'Código de Produto não encontrado'

    num_linha_venda: int
    msg_err: str

    @classmethod
    def multigerar(cls, produtos: Iterable[_Produto], vendas: Iterable[_Venda]) -> Iterable[Self]:
        return (_Divergencia(num_linha_venda=i + 1,
                             msg_err=f'{cls.__MSG_SEM_COD} {v.cod_produto:05d}' if s_produto else v.situacao.msg_erro())
                for i, v in enumerate(vendas)
                if (s_produto := v.cod_produto not in (p.codigo for p in produtos)) or not v.situacao.is_confirmada())


@dataclass(frozen=True, kw_only=True, slots=True)
class _QtdVendasPorCanal:
    """"
    Utilizado para representar a relação de vendas por canal em um arquivo de saída.
    """
    canal: _CanalVenda
    qtd_vendas: int

    @classmethod
    def multigerar(cls, vendas: Iterable[_Venda]) -> list[Self]:
        """
        Gera uma relação de quantidade de vendas por canal com base nas vendas informadas.
        :param vendas: Relação de vendas vinda de um arquivo de entrada.
        :return: Relação de quantidade de vendas por canal.
        """
        return sorted((_QtdVendasPorCanal(canal=canal, qtd_vendas=sum(v.qtd for v in vendas))
                       for canal, vendas in groupby(sorted((v for v in vendas if v.situacao.is_confirmada()),
                                                           key=lambda v: v.canal),
                                                    key=lambda v: v.canal)),
                      key=lambda vpc: vpc.canal)


@dataclass(frozen=True, kw_only=True, slots=True)
class _Resultado:
    """
    Utilizado para representar o resultado dos cálculos de dados sobre vendas e produtos vindos de arquivos de entrada.
    """
    necessidades: Iterable[_NecessidadeTransferencia]
    divergencias: Iterable[_Divergencia]
    vendas_por_canal: Iterable[_QtdVendasPorCanal]


def _garantir_arquivos_entrada() -> bool:
    """
    Verifica se os arquivos de entrada necessários estão presentes.
    :return: `True` se os arquivos de entrada necessários estiverem presentes; caso contrário, `False`.
    """
    success = True
    for path in (path for path in (_CAMINHO_ARQUIVO_PRODUTOS, _CAMINHO_ARQUIVO_VENDAS) if not path.is_file()):
        success = False
        print(f'{_MSG_ARQUIVO_NAO_ENCONTRADO}: {path.resolve()}', file=stderr)
    return success


def _gerar_resultado() -> _Resultado | None:
    """
    Gera resultados dos cálculos de informações sobre produtos e vendas caso seja possível encontrar os arquivos.
    :return: Resultado dos cálculos, ou `None` se não for possível encontrar os arquivos de entrada necessários.
    """
    if not _garantir_arquivos_entrada():
        return None

    with (_CAMINHO_ARQUIVO_PRODUTOS.open() as arq_produtos,
          _CAMINHO_ARQUIVO_VENDAS.open() as arq_vendas):
        produtos = tuple(_Produto(codigo=int(cod), qtd_estoque=int(qtd_est), qtd_min_co=int(qtd_min))
                         for cod, qtd_est, qtd_min in
                         (linha.split(_DELIMITADOR_DADOS) for linha in arq_produtos.readlines()))

        vendas = tuple(_Venda(cod_produto=int(cod_prd),
                              qtd=int(qtd),
                              situacao=_SituacaoVenda(int(sit)),
                              canal=_CanalVenda(int(can)))
                       for cod_prd, qtd, sit, can in
                       (linha.split(_DELIMITADOR_DADOS) for linha in arq_vendas.readlines()))

        necessidades = _NecessidadeTransferencia.multigerar(produtos, vendas)
        divergencias = _Divergencia.multigerar(produtos, vendas)
        vendas_por_canal = _QtdVendasPorCanal.multigerar(vendas)

        return _Resultado(necessidades=necessidades, divergencias=divergencias, vendas_por_canal=vendas_por_canal)


def _salvar_necessidades(necessidades: Iterable[_NecessidadeTransferencia]) -> None:
    """
    Guarda informações sobre necessidade de transferência de armazenamento de produtos em um arquivo predefinido.
    :param necessidades: Lista de necessidades.
    """
    with _CAMINHO_ARQUIVO_TRANSFERENCIAS.open('w') as arq_transf:
        arq_transf.write('Necessidade de Transferência Armazém para CO\n\n'
                         'Produto  QtCO  QtMin  QtVendas  Estq.após  Necess.  Transf. de\n'
                         '                                   Vendas            Arm p/ CO\n')
        for n in necessidades:
            arq_transf.write(f'{n.cod_produto:<5} '
                             f'{n.qtd_produto_co:>7} '
                             f'{n.qtd_min_produto_co:>6} '
                             f'{n.qtd_vendas:>9} '
                             f'{n.qtd_estoque_pos_vendas:>10} '
                             f'{n.qtd_necessidade:>8} '
                             f'{n.qtd_transf_arm_co:>11}\n')


def _salvar_divergencias(divergencias: Iterable[_Divergencia]) -> None:
    """
    Guarda informações sobre divergências em um arquivo de texto predefinido.
    :param divergencias: Lista de vendas de produtos não existentes ou com erro.
    """
    with _CAMINHO_ARQUIVO_DIVERGENCIAS.open('w') as arq_diver:
        for divergencia in divergencias:
            arq_diver.write(f'Linha {divergencia.num_linha_venda:02d} – {divergencia.msg_err}\n')


def _salvar_vendas_por_canal(vendas_por_canal: Iterable[_QtdVendasPorCanal]) -> None:
    """
    Guarda informações sobre vendas por canal em um arquivo de texto predefinido.
    :param vendas_por_canal: Relação de vendas por canal.
    """
    with _CAMINHO_ARQUIVO_VENDAS_POR_CANAL.open('w') as arq_totcanais:
        arq_totcanais.write('Quantidades de Vendas por canal\n\n')
        arq_totcanais.write(f'{'Canal':<21} {'QtVendas':>9}\n')
        for vpc in vendas_por_canal:
            arq_totcanais.write(f'{f'{vpc.canal.value} - {vpc.canal.descricao()}':<21} {vpc.qtd_vendas:>9}\n')


def _main() -> None:
    """
    Ponto de entrada da aplicação.
    """
    print(_MSG_INICIO)
    if (resultado := _gerar_resultado()) is None:
        return
    _salvar_necessidades(resultado.necessidades)
    _salvar_divergencias(resultado.divergencias)
    _salvar_vendas_por_canal(resultado.vendas_por_canal)


if __name__ == '__main__':
    _main()
