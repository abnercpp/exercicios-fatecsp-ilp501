from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from sys import stderr
from typing import Self, Final, TextIO, ClassVar

_MSG_INICIO: Final[str] = '''Cálculo de Salários
Abner Eduardo Ramos Ferreira
Fernando Martins de Gouvêa
Joilson Briana dos Santos
Lucas de Abreu Tondin
'''

_MSG_ARQUIVO_TESTE_NAO_ENCONTRADO: Final[str] = 'Arquivo de teste não encontrado'

_CAMINHO_ENTRADA: Final[Path] = Path('salario.txt')
_CAMINHO_SAIDA: Final[Path] = Path('calculos.txt')

_REF_PRECISAO: Final[Decimal] = Decimal('.01')


@dataclass(frozen=True, kw_only=True, slots=True, order=True)
class _INSS:
    """
    Utilizado para representar dados sobre desconto do INSS.
    """
    __VALOR_TETO: ClassVar[Decimal] = Decimal(642.34)

    __VALOR_SAL_MAX_N3: ClassVar[Decimal] = Decimal(5_839.45)
    __VALOR_SAL_MIN_N3: ClassVar[Decimal] = Decimal(2_919.73)
    __ALIQ_N3: ClassVar[Decimal] = Decimal(.11)

    __VALOR_SAL_MIN_N2: ClassVar[Decimal] = Decimal(1_751.82)
    __ALIQ_N2: ClassVar[Decimal] = Decimal(.09)

    __VALOR_SAL_MAX_N1: ClassVar[Decimal] = Decimal(1_751.81)
    __ALIQ_N1: ClassVar[Decimal] = Decimal(.08)

    aliquota: Decimal
    valor: Decimal
    base: Decimal

    @classmethod
    def from_valor_base(cls, valor_salario_bruto: Decimal) -> Self:
        """
        Calcula e retorna dados sobre o INSS a partir do salário bruto.
        :param valor_salario_bruto: Valor do salário bruto para base do cálculo
        :return: Dados sobre o desconto do INSS, com dados calculados a partir do salário bruto.
        """
        aliquota = Decimal(0)

        match valor_salario_bruto.quantize(_REF_PRECISAO, rounding=ROUND_HALF_UP):
            case num if num > cls.__VALOR_SAL_MAX_N3:
                pass
            case num if num >= cls.__VALOR_SAL_MIN_N3:
                aliquota = cls.__ALIQ_N3
            case num if num >= cls.__VALOR_SAL_MIN_N2:
                aliquota = cls.__ALIQ_N2
            case num if num <= cls.__VALOR_SAL_MAX_N1:
                aliquota = cls.__ALIQ_N1

        return _INSS(aliquota=aliquota,
                     valor=(valor_salario_bruto * aliquota) if aliquota else cls.__VALOR_TETO,
                     base=valor_salario_bruto)


@dataclass(frozen=True, kw_only=True, slots=True, order=True)
class _IR:
    """
    Utilizado para representar dados sobre desconto do Imposto de Renda.
    """
    __VALOR_BASE_MIN_N4_NAO_INCLUSIVO: ClassVar[Decimal] = Decimal(4_664.68)
    __ALIQ_N4: ClassVar[Decimal] = Decimal(.275)
    __VALOR_DEDUCAO_N4: ClassVar[Decimal] = Decimal(869.36)

    __VALOR_BASE_MIN_N3: ClassVar[Decimal] = Decimal(3_751.06)
    __ALIQ_N3: ClassVar[Decimal] = Decimal(.225)
    __VALOR_DEDUCAO_N3: ClassVar[Decimal] = Decimal(636.13)

    __VALOR_BASE_MIN_N2: ClassVar[Decimal] = Decimal(2_826.66)
    __ALIQ_N2: ClassVar[Decimal] = Decimal(.15)
    __VALOR_DEDUCAO_N2: ClassVar[Decimal] = Decimal(354.80)

    __VALOR_BASE_MIN_N1: ClassVar[Decimal] = Decimal(1_903.99)
    __ALIQ_N1: ClassVar[Decimal] = Decimal(.075)
    __VALOR_DEDUCAO_N1: ClassVar[Decimal] = Decimal(142.80)

    __VALOR_MINIMO_P_TAXACAO: ClassVar[Decimal] = Decimal(10)

    aliquota: Decimal
    valor: Decimal
    base: Decimal

    @classmethod
    def from_inss(cls, inss: _INSS) -> Self:
        """
        Calcula e retorna dados sobre o Imposto de Renda a partir dos dados do INSS.
        :param inss: Dados sobre o INSS para calcular o Imposto de Renda.
        :return: Dados sobre o Imposto de Renda a partir do INSS.
        """
        aliquota = Decimal(0)
        deducao = Decimal(0)

        match base := (inss.base - inss.valor).quantize(_REF_PRECISAO, rounding=ROUND_HALF_UP):
            case num if num > cls.__VALOR_BASE_MIN_N4_NAO_INCLUSIVO:
                aliquota = cls.__ALIQ_N4
                deducao = cls.__VALOR_DEDUCAO_N4
            case num if num >= cls.__VALOR_BASE_MIN_N3:
                aliquota = cls.__ALIQ_N3
                deducao = cls.__VALOR_DEDUCAO_N3
            case num if num >= cls.__VALOR_BASE_MIN_N2:
                aliquota = cls.__ALIQ_N2
                deducao = cls.__VALOR_DEDUCAO_N2
            case num if num >= cls.__VALOR_BASE_MIN_N1:
                aliquota = cls.__ALIQ_N1
                deducao = cls.__VALOR_DEDUCAO_N1

        return _IR(aliquota=aliquota,
                   valor=(valor := base * aliquota - deducao) * int(valor >= cls.__VALOR_MINIMO_P_TAXACAO),
                   base=base)


@dataclass(frozen=True, kw_only=True, slots=True, order=True)
class _Salario:
    """
    Utilizado para representar dados de salário, incluindo desconto de INSS e IR.
    """
    valor_bruto: Decimal
    inss: _INSS
    ir: _IR
    valor_liquido: Decimal

    @classmethod
    def from_valor_bruto(cls, valor_salario_bruto: Decimal) -> Self:
        return _Salario(valor_bruto=valor_salario_bruto,
                        inss=(inss := _INSS.from_valor_base(valor_salario_bruto)),
                        ir=(ir := _IR.from_inss(inss)),
                        valor_liquido=ir.base - ir.valor)


def _exec_teste_de_caso(arquivo_entrada: TextIO, arquivo_saida: TextIO) -> None:
    """
    Executa cálculo de salário e descontos com base nos arquivos de entrada e saída.
    :param arquivo_entrada: Arquivo de entrada com valores de salário bruto para cálculo de descontos.
    :param arquivo_saida: Arquivo de saída em que os resultados dos cálculos deverão ser escritos.
    """
    salarios = (_Salario.from_valor_bruto(Decimal(salario)) for salario in arquivo_entrada.readlines())
    arquivo_saida.write((f'{'Bruto':>9} '
                         f'{'AliqINSS':>9} '
                         f'{'Val.INSS':>9} '
                         f'{'Base I.R.':>9} '
                         f'{'AliqIR':>9} '
                         f'{'Val.IR':>9} '
                         f'{'Liquido':>9}\n'))
    for salario in sorted(salarios, key=lambda s: s.valor_bruto):
        arquivo_saida.write((f'{salario.valor_bruto:>9.2f} '
                             f'{salario.inss.aliquota * 100:>9.1f} '
                             f'{salario.inss.valor:>9.2f} '
                             f'{salario.ir.base:>9.2f} '
                             f'{salario.ir.aliquota * 100:>9.2f} '
                             f'{salario.ir.valor:>9.2f} '
                             f'{salario.valor_liquido:>9.2f}\n'))


def _main() -> None:
    """
    Ponto de entrada da aplicação.
    """
    print(_MSG_INICIO)

    if not _CAMINHO_ENTRADA.is_file():
        print(f'{_MSG_ARQUIVO_TESTE_NAO_ENCONTRADO}: {_CAMINHO_ENTRADA.resolve()}', file=stderr)
        return

    with _CAMINHO_ENTRADA.open() as arquivo_entrada, _CAMINHO_SAIDA.open('w') as arquivo_saida:
        _exec_teste_de_caso(arquivo_entrada, arquivo_saida)


if __name__ == '__main__':
    _main()
