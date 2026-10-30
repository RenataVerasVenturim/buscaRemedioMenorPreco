"""Identifica se um produto e a apresentacao desejada do medicamento."""

import re
import unicodedata
from dataclasses import dataclass, field


def normalizar(texto):
    if not texto:
        return ""
    sem_acento = unicodedata.normalize("NFKD", texto)
    sem_acento = "".join(ch for ch in sem_acento if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", " ", sem_acento.lower()).strip()


def slugify(texto):
    return re.sub(r"\s+", "-", normalizar(texto)).strip("-")


def dose_em_mg(concentracao):
    texto = normalizar(concentracao).replace(" ", "")
    match = re.search(r"(\d+)\s*mg", texto)
    if match:
        return int(match.group(1))
    so_numero = re.search(r"(\d+)", texto)
    return int(so_numero.group(1)) if so_numero else None


def reais_para_centavos(valor):
    if valor is None:
        return None
    if isinstance(valor, str):
        limpo = valor.strip()
        limpo = re.sub(r"[^\d,.\-]", "", limpo)
        if not limpo:
            return None
        if "," in limpo and "." in limpo:
            limpo = limpo.replace(".", "").replace(",", ".")
        elif "," in limpo:
            limpo = limpo.replace(",", ".")
        valor = float(limpo)
    centavos = int(round(float(valor) * 100))
    if centavos < 0:
        raise ValueError("O preço não pode ser negativo.")
    return centavos


def classificar_tipo(nome, marca=""):
    texto = f"{nome} {marca}".lower()
    if "ursacol" in texto:
        return "Marca"
    if "prour" in texto:
        return "Similar"
    if "generic" in normalizar(texto):
        return "Genérico"
    return "Não identificado"


def _marca_aceita(nome, tipo, marcas_aceitas):
    if not marcas_aceitas:
        return True
    texto = normalizar(f"{nome} {tipo}")
    for marca in marcas_aceitas:
        alvo = normalizar(marca)
        if not alvo:
            continue
        if alvo in texto:
            return True
        if alvo in {"generico", "genericos"} and tipo == "Genérico":
            return True
        if alvo in {"marca", "referencia"} and tipo == "Marca":
            return True
        if alvo == "similar" and tipo == "Similar":
            return True
    return False


@dataclass
class Consulta:
    principio_ativo: str
    concentracao: str = "300 mg"
    comprimidos: int = 30
    caixas: int = 1
    marcas_aceitas: list = field(default_factory=list)
    cep: str = ""

    def __post_init__(self):
        self.cep = re.sub(r"\D", "", self.cep or "")
        if self.cep and len(self.cep) != 8:
            raise ValueError("O CEP deve conter 8 dígitos.")

    @property
    def dose_mg(self):
        return dose_em_mg(self.concentracao) or 300

    @property
    def termo_busca(self):
        return f"{self.principio_ativo} {self.dose_mg}mg".strip()


_FALSOS_POSITIVOS = (
    "alfa lipoico",
    "acido alfa",
    "lipoico",
    "vitamina",
)


def produto_compativel(nome, consulta: Consulta, marca=""):
    texto = normalizar(nome)
    if not texto:
        return False
    if any(falso in texto for falso in _FALSOS_POSITIVOS):
        return False

    principio = normalizar(consulta.principio_ativo)
    tokens = [token for token in principio.split() if token not in {"acido", "acid"}]
    if tokens and not all(token in texto for token in tokens):
        # aceita marca de referencia do mesmo principio
        if "ursacol" not in texto and "prour" not in texto:
            return False

    dose = consulta.dose_mg
    if dose and f"{dose}mg" not in texto.replace(" ", ""):
        return False

    qtd = re.search(r"\b(\d+)\s*comprimidos?\b", texto)
    if qtd and int(qtd.group(1)) != int(consulta.comprimidos):
        return False

    tipo = classificar_tipo(nome, marca)
    return _marca_aceita(nome, tipo, consulta.marcas_aceitas)
