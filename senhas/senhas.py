from enum import IntFlag, auto, StrEnum
from itertools import islice
from pathlib import Path
from random import randint, choice, shuffle
from sys import stderr
from typing import Iterable, Final

_MSG_INICIO: Final[str] = '''Gerador de Senhas
Abner Eduardo Ramos Ferreira
Fernando Martins de Gouvêa
Joilson Briana dos Santos
Lucas de Abreu Tondin
'''

_CAMINHO_ARQUIVO_ENTRADA: Final[Path] = Path('matr.txt')
_CAMINHO_ARQUIVO_SAIDA: Final[Path] = Path('senhas.txt')

_MSG_ARQUIVO_TESTE_NAO_ENCONTRADO: Final[str] = 'Arquivo de teste não encontrado'


class _ComponentesSenha(IntFlag):
    """
    Bitflags utilizados para representar os componentes que uma senha deve ter ao ser gerada.
    """
    Algarismos = auto()
    Maiusculas = auto()
    Minusculas = auto()
    Especiais = auto()

    def gerar(self) -> Iterable[str]:
        """
        Gera componentes individuais de uma senha.
        :return: Componentes básicos da senha.
        """
        if self & _ComponentesSenha.Algarismos:
            yield chr(randint(ord('0'), ord('9')))
        if self & _ComponentesSenha.Maiusculas:
            yield chr(randint(ord('A'), ord('Z')))
        if self & _ComponentesSenha.Minusculas:
            yield chr(randint(ord('a'), ord('z')))
        if self & _ComponentesSenha.Especiais:
            yield choice('-_:@#$&?')


class _TipoSenha(StrEnum):
    """
    Utilizado para representar o tipo de senha a ser gerada.
    """
    Numerica = 'a'
    Alfabetica = 'b'
    Alfanumerica1 = 'c'
    Alfanumerica2 = 'd'
    Geral = 'e'

    def __componentes(self) -> _ComponentesSenha:
        match self:
            case self.Numerica:
                return _ComponentesSenha.Algarismos
            case self.Alfabetica:
                return (_ComponentesSenha.Maiusculas |
                        _ComponentesSenha.Minusculas)
            case self.Alfanumerica1:
                return (_ComponentesSenha.Algarismos |
                        _ComponentesSenha.Maiusculas)
            case self.Alfanumerica2:
                return (_ComponentesSenha.Algarismos |
                        _ComponentesSenha.Maiusculas |
                        _ComponentesSenha.Minusculas)
            case self.Geral:
                return (_ComponentesSenha.Algarismos |
                        _ComponentesSenha.Maiusculas |
                        _ComponentesSenha.Minusculas |
                        _ComponentesSenha.Especiais)

    def gerar_senha(self, tamanho: int) -> str:
        """
        Gera senha com base no tipo de senha e tamanho informados.
        :param tamanho: Tamanho da senha gerada.
        :return: Uma nova senha pseudoaleatória com o tipo e tamanho informados.
        """
        senha = list(islice((char for _ in range(tamanho) for char in self.__componentes().gerar()), tamanho))
        shuffle(senha)
        return ''.join(senha)


def _main() -> None:
    """
    Ponto de entrada da aplicação.
    """
    if not _CAMINHO_ARQUIVO_ENTRADA.is_file():
        print(f'{_MSG_ARQUIVO_TESTE_NAO_ENCONTRADO}: {_CAMINHO_ARQUIVO_ENTRADA.resolve()}', file=stderr)
        return
    opcoes_senha = tuple(_TipoSenha(v) for v in _TipoSenha)
    selecao_senha = ''
    while selecao_senha not in (o.value for o in opcoes_senha):
        selecao_senha = input(f'Insira tipo de senha [{', '.join(f'{o} ({o.name})' for o in opcoes_senha)}]: ')
    tipo_senha = _TipoSenha(selecao_senha)
    tamanho_senha = abs(int(input('Insira tamanho da senha: ')))
    with _CAMINHO_ARQUIVO_ENTRADA.open() as arq_entrada, _CAMINHO_ARQUIVO_SAIDA.open('w') as arq_saida:
        for matricula in arq_entrada.readlines():
            arq_saida.write(f'{matricula.strip()};{tipo_senha.gerar_senha(tamanho_senha)}\n')


if __name__ == '__main__':
    _main()
