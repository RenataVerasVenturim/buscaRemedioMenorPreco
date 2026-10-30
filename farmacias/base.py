from dataclasses import dataclass
from typing import Optional


@dataclass
class Oferta:
    farmacia: str
    produto: str
    produto_tipo: str
    concentracao: str
    comprimidos: int
    caixas: int

    preco_produtos: int
    frete: Optional[int]

    url: str

    frete_confirmado: bool
    estoque_confirmado: bool

    @property
    def preco_total(self):
        if self.frete is None:
            return None

        return self.preco_produtos + self.frete

    @property
    def elegivel(self):
        return (
            self.concentracao == "300mg"
            and self.comprimidos == 30
            and self.caixas == 3
            and self.preco_produtos > 0
            and self.frete is not None
            and self.frete >= 0
            and self.frete_confirmado
            and self.estoque_confirmado
            and bool(self.url)
        )