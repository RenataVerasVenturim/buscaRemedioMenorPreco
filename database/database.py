"""Configuracao e acesso ao banco de dados do projeto."""

import sqlite3
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = BASE_DIR / "database" / "historico.db"


def conectar():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def inicializar_banco():
    conn = conectar()
    try:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS pesquisas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_hora TEXT NOT NULL,
                status TEXT NOT NULL
            )
        """)

        conn.execute("""
            CREATE TABLE IF NOT EXISTS ofertas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pesquisa_id INTEGER NOT NULL,
                produto_tipo TEXT NOT NULL,
                farmacia TEXT NOT NULL,
                produto TEXT NOT NULL,
                url TEXT,
                medicamento TEXT NOT NULL DEFAULT '',
                preco_produtos INTEGER NOT NULL,
                frete INTEGER,
                preco_total INTEGER,
                caixas INTEGER NOT NULL,
                produto_confirmado INTEGER NOT NULL DEFAULT 0,
                frete_confirmado INTEGER DEFAULT 0,
                estoque_confirmado INTEGER DEFAULT 0,
                data_consulta TEXT NOT NULL,
                origem TEXT NOT NULL DEFAULT 'manual',
                laboratorio TEXT,
                FOREIGN KEY (pesquisa_id)
                    REFERENCES pesquisas(id)
            )
        """)
        colunas = {
            coluna["name"]
            for coluna in conn.execute("PRAGMA table_info(ofertas)").fetchall()
        }
        if "medicamento" not in colunas:
            conn.execute(
                "ALTER TABLE ofertas ADD COLUMN medicamento TEXT NOT NULL DEFAULT ''"
            )
        if "produto_confirmado" not in colunas:
            conn.execute(
                "ALTER TABLE ofertas ADD COLUMN produto_confirmado "
                "INTEGER NOT NULL DEFAULT 0"
            )
        if "origem" not in colunas:
            conn.execute(
                "ALTER TABLE ofertas ADD COLUMN origem TEXT NOT NULL DEFAULT 'manual'"
            )
        if "laboratorio" not in colunas:
            conn.execute("ALTER TABLE ofertas ADD COLUMN laboratorio TEXT")
        conn.commit()
    finally:
        conn.close()


def registrar_oferta_manual(
    *,
    medicamento,
    farmacia,
    produto,
    produto_tipo,
    url,
    preco_produtos,
    frete,
    caixas,
    produto_confirmado,
    frete_confirmado,
    estoque_confirmado,
):
    """Registra uma cotacao observada manualmente, sem iniciar pesquisa."""
    if not medicamento.strip():
        raise ValueError("O princípio ativo é obrigatório.")
    if not farmacia.strip() or not produto.strip():
        raise ValueError("Farmácia e produto são obrigatórios.")
    if not produto_tipo.strip():
        raise ValueError("O tipo de produto é obrigatório.")
    if isinstance(preco_produtos, bool) or preco_produtos <= 0:
        raise ValueError("O preço dos produtos deve ser positivo em centavos.")
    if frete is not None and (isinstance(frete, bool) or frete < 0):
        raise ValueError("O frete não pode ser negativo.")
    if isinstance(caixas, bool) or caixas < 1:
        raise ValueError("A quantidade de caixas deve ser positiva.")
    if frete_confirmado and frete is None:
        raise ValueError("Não é possível confirmar o frete sem um valor.")

    data_consulta = datetime.now().astimezone().isoformat(timespec="seconds")
    preco_total = preco_produtos + frete if frete_confirmado else None
    conn = conectar()
    try:
        with conn:
            pesquisa = conn.execute(
                "INSERT INTO pesquisas (data_hora, status) VALUES (?, ?)",
                (data_consulta, "observacao_manual"),
            )
            cursor = conn.execute(
                """
                INSERT INTO ofertas (
                    pesquisa_id, produto_tipo, farmacia, produto, url,
                    medicamento, preco_produtos, frete, preco_total, caixas,
                    produto_confirmado, frete_confirmado, estoque_confirmado,
                    data_consulta, origem, laboratorio
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    pesquisa.lastrowid,
                    produto_tipo.strip(),
                    farmacia.strip(),
                    produto.strip(),
                    url,
                    medicamento.strip(),
                    preco_produtos,
                    frete,
                    preco_total,
                    caixas,
                    int(bool(produto_confirmado)),
                    int(bool(frete_confirmado)),
                    int(bool(estoque_confirmado)),
                    data_consulta,
                    "manual",
                    None,
                ),
            )
            return cursor.lastrowid
    finally:
        conn.close()


def registrar_pesquisa_automatica(medicamento, ofertas, caixas):
    """Grava o resultado de uma busca automatica no historico."""
    if not str(medicamento or "").strip():
        raise ValueError("O princípio ativo é obrigatório.")
    if isinstance(caixas, bool) or caixas < 1:
        raise ValueError("A quantidade de caixas deve ser positiva.")

    data_consulta = datetime.now().astimezone().isoformat(timespec="seconds")
    conn = conectar()
    try:
        with conn:
            pesquisa = conn.execute(
                "INSERT INTO pesquisas (data_hora, status) VALUES (?, ?)",
                (data_consulta, "pesquisa_automatica"),
            )
            pesquisa_id = pesquisa.lastrowid
            gravadas = 0
            for oferta in ofertas:
                preco_unitario = oferta["preco_produtos"]
                preco_produtos = preco_unitario * int(caixas)
                frete = oferta.get("frete")
                frete_confirmado = bool(oferta.get("frete_confirmado"))
                if frete is not None and (
                    isinstance(frete, bool)
                    or not isinstance(frete, int)
                    or frete < 0
                ):
                    raise ValueError("O frete não pode ser negativo.")
                if frete_confirmado and frete is None:
                    raise ValueError("Frete confirmado exige um valor informado.")
                preco_total = (
                    preco_produtos + frete if frete_confirmado else None
                )
                conn.execute(
                    """
                    INSERT INTO ofertas (
                        pesquisa_id, produto_tipo, farmacia, produto, url,
                        medicamento, preco_produtos, frete, preco_total, caixas,
                        produto_confirmado, frete_confirmado, estoque_confirmado,
                        data_consulta, origem, laboratorio
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        pesquisa_id,
                        oferta.get("produto_tipo") or "Não identificado",
                        oferta["farmacia"],
                        oferta["produto"],
                        oferta.get("url"),
                        medicamento.strip(),
                        preco_produtos,
                        frete,
                        preco_total,
                        int(caixas),
                        int(bool(oferta.get("produto_confirmado"))),
                        int(frete_confirmado),
                        int(bool(oferta.get("estoque_confirmado"))),
                        data_consulta,
                        oferta.get("origem") or "catalogo",
                        oferta.get("laboratorio"),
                    ),
                )
                gravadas += 1
            return {"pesquisa_id": pesquisa_id, "ofertas": gravadas}
    finally:
        conn.close()


def obter_historico(medicamento=None, limite=500):
    """Retorna as observacoes mais recentes, em centavos."""
    if isinstance(limite, bool) or limite < 1:
        raise ValueError("O limite deve ser um inteiro positivo.")
    conn = conectar()
    try:
        rows = conn.execute(
            """
            SELECT
                id, data_consulta, medicamento, farmacia, produto, produto_tipo,
                url, preco_produtos, frete, preco_total, caixas,
                produto_confirmado, frete_confirmado, estoque_confirmado,
                origem, laboratorio
            FROM ofertas
            WHERE (? IS NULL OR medicamento = ?)
            ORDER BY data_consulta DESC, id DESC
            LIMIT ?
            """,
            (medicamento, medicamento, int(limite)),
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()