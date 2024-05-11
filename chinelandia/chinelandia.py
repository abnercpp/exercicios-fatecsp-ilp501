from dataclasses import dataclass
from enum import IntEnum
from itertools import groupby
from pathlib import Path
from sys import stderr
from typing import Iterable, TextIO, Final

_MSG_INICIO: Final[str] = '''Chinelândia
Abner Eduardo Ramos Ferreira
Fernando Martins de Gouvêa
Joilson Briana dos Santos
Lucas de Abreu Tondin
'''

_MSG_INSERIR_NUM_CASO_TESTE: Final[str] = 'Digite o número do caso de teste'

_MSG_ARQUIVO_TESTE_NAO_ENCONTRADO: Final[str] = 'Arquivo de teste não encontrado'

_MSG_SEM_TROCAS: Final[str] = 'SEM TROCAS DESTA VEZ'


class _Lado(IntEnum):
    """
    Utilizado para representar esquerda ou direita para pés de chinelos.
    """
    E = 0
    D = 1


@dataclass(frozen=True, kw_only=True, slots=True, order=True)
class _Chinelo:
    """
    Modelo com estatísticas de um chinelo após leitura de arquivo de input.
    """
    id_modelo: int
    lado: _Lado
    num_repeticoes: int

    def __str__(self) -> str:
        return f'{self.id_modelo} {self.lado.name} {self.num_repeticoes}'


def _buscar_estatisticas_chinelisticas(pares: Iterable[tuple[int, int]]) -> list[_Chinelo]:
    """
    Gera estatísticas para cada combinação de modelo e pé informados.
    :param pares: Os pares de modelos de chinelo. Primeiro o pé esquerdo e depois, o direito.
    :return: Lista com estatísticas para cada combinação de modelo e pé de chinelo.
    """
    return sorted(
        (_Chinelo(lado=_Lado(index_lado), id_modelo=id_modelo, num_repeticoes=num_repeticoes)
         for index_lado, ids_modelo in enumerate(zip(*pares))
         for id_modelo, instancias_id_modelo in groupby(sorted(ids_modelo))
         if (num_repeticoes := len(tuple(instancias_id_modelo)) - 1)),
        key=lambda chinelo: (chinelo.id_modelo, chinelo.lado)
    )


def _exec_caso_de_teste(arquivo_input: TextIO) -> None:
    """
    Lê dados do arquivo de teste e exibe estatísticas no console.
    :param arquivo_input: Arquivo de teste para leitura.
    """
    num_linhas = int(arquivo_input.readline())
    linhas = [
        (int(chinelo_esq), int(chinelo_dir))
        for chinelo_esq, chinelo_dir in (arquivo_input.readline().split() for _ in range(num_linhas))
    ]
    chinelos = _buscar_estatisticas_chinelisticas(linhas)

    if not len(chinelos):
        print(_MSG_SEM_TROCAS)
        return

    for chinelo in chinelos:
        print(chinelo)


def _main() -> None:
    """
    Ponto de entrada da aplicação. Executa o arquivo de teste escolhido via console.
    """
    print(_MSG_INICIO)
    nct = 0
    while nct not in (limits := range(1, 8)):
        raw = input(f'{_MSG_INSERIR_NUM_CASO_TESTE} ({limits.start}-{limits.stop - 1}): ')
        if raw.isdigit():
            nct = int(raw)
    caminho_arquivo = Path(f'{nct}_in.txt')
    if not caminho_arquivo.is_file():
        print(f'{_MSG_ARQUIVO_TESTE_NAO_ENCONTRADO}: {caminho_arquivo.resolve()}', file=stderr)
        return
    with caminho_arquivo.open() as arquivo_input:
        _exec_caso_de_teste(arquivo_input)


if __name__ == '__main__':
    _main()
