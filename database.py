import os
from datetime import datetime, date
from typing import List, Dict, Optional, Any
import psycopg2
from psycopg2.extras import RealDictCursor

# Lê a URL do banco do ambiente (Streamlit Cloud usa st.secrets)
def _get_database_url() -> str:
    url = os.environ.get("DATABASE_URL", "")
    if not url:
        try:
            import streamlit as st
            url = st.secrets["DATABASE_URL"]
        except Exception:
            pass
    if not url:
        raise RuntimeError(
            "DATABASE_URL não configurada. "
            "Defina em .streamlit/secrets.toml (local) ou nos secrets do Streamlit Cloud."
        )
    return url


def _get_conn():
    url = _get_database_url()
    conn = psycopg2.connect(url, cursor_factory=RealDictCursor, connect_timeout=10)
    return conn


def _rows_to_list(rows) -> List[Dict]:
    return [dict(r) for r in rows] if rows else []


def _row_to_dict(row) -> Dict:
    return dict(row) if row else {}


# ─────────────────────────────────────────────
# INIT
# ─────────────────────────────────────────────

def init_db() -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()

        cur.execute("""
            CREATE TABLE IF NOT EXISTS pools (
                id          SERIAL PRIMARY KEY,
                nome        TEXT NOT NULL,
                protocolo   TEXT NOT NULL,
                chain       TEXT NOT NULL,
                token_a     TEXT NOT NULL,
                token_b     TEXT NOT NULL,
                fee_tier    TEXT DEFAULT '',
                preco_min   REAL,
                preco_max   REAL,
                ativa       INTEGER DEFAULT 1,
                criado_em   TEXT DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS posicoes (
                id                  SERIAL PRIMARY KEY,
                pool_id             INTEGER NOT NULL REFERENCES pools(id) ON DELETE CASCADE,
                data                TEXT NOT NULL,
                token_a_amount      REAL NOT NULL,
                token_b_amount      REAL NOT NULL,
                token_a_price_usd   REAL NOT NULL,
                token_b_price_usd   REAL NOT NULL,
                capital_usd         REAL NOT NULL,
                observacao          TEXT DEFAULT '',
                criado_em           TEXT DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS taxas (
                id                  SERIAL PRIMARY KEY,
                pool_id             INTEGER NOT NULL REFERENCES pools(id) ON DELETE CASCADE,
                data                TEXT NOT NULL,
                token_a_amount      REAL DEFAULT 0,
                token_b_amount      REAL DEFAULT 0,
                valor_usd           REAL NOT NULL,
                valor_pool_usd      REAL,
                token_a_price_usd   REAL,
                token_b_price_usd   REAL,
                observacao          TEXT DEFAULT '',
                criado_em           TEXT DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS snapshots (
                id                  SERIAL PRIMARY KEY,
                pool_id             INTEGER NOT NULL REFERENCES pools(id) ON DELETE CASCADE,
                data                TEXT NOT NULL,
                valor_usd           REAL NOT NULL,
                token_a_price_usd   REAL,
                token_b_price_usd   REAL,
                criado_em           TEXT DEFAULT to_char(NOW(), 'YYYY-MM-DD HH24:MI:SS')
            )
        """)

        # Migração: adiciona colunas se não existirem
        def _add_col_if_missing(table, col, definition):
            cur.execute("""
                SELECT column_name FROM information_schema.columns
                WHERE table_name = %s AND column_name = %s AND table_schema = 'public'
            """, (table, col))
            if not cur.fetchone():
                cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {definition}")

        for col in ["preco_min", "preco_max"]:
            _add_col_if_missing("pools", col, "REAL")
        for col, defn in [("valor_pool_usd", "REAL"), ("token_a_price_usd", "REAL"), ("token_b_price_usd", "REAL")]:
            _add_col_if_missing("taxas", col, defn)

        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────
# POOLS
# ─────────────────────────────────────────────

def criar_pool(nome, protocolo, chain, token_a, token_b, fee_tier="", preco_min=None, preco_max=None) -> int:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO pools (nome, protocolo, chain, token_a, token_b, fee_tier, preco_min, preco_max)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (nome, protocolo, chain, token_a, token_b, fee_tier, preco_min, preco_max))
        row = cur.fetchone()
        conn.commit()
        return row["id"]
    finally:
        conn.close()


def atualizar_pool_range(pool_id: int, preco_min, preco_max) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE pools SET preco_min = %s, preco_max = %s WHERE id = %s", (preco_min, preco_max, pool_id))
        conn.commit()
    finally:
        conn.close()


def listar_pools(apenas_ativas: bool = True) -> List[Dict]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        if apenas_ativas:
            cur.execute("SELECT * FROM pools WHERE ativa = 1 ORDER BY criado_em DESC")
        else:
            cur.execute("SELECT * FROM pools ORDER BY ativa DESC, criado_em DESC")
        return _rows_to_list(cur.fetchall())
    finally:
        conn.close()


def get_pool(pool_id: int) -> Dict:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM pools WHERE id = %s", (pool_id,))
        return _row_to_dict(cur.fetchone())
    finally:
        conn.close()


def atualizar_pool_status(pool_id: int, ativa: bool) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("UPDATE pools SET ativa = %s WHERE id = %s", (1 if ativa else 0, pool_id))
        conn.commit()
    finally:
        conn.close()


def deletar_pool(pool_id: int) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM pools WHERE id = %s", (pool_id,))
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────
# POSIÇÕES
# ─────────────────────────────────────────────

def adicionar_posicao(pool_id, data, token_a_amount, token_b_amount, token_a_price_usd, token_b_price_usd, capital_usd, observacao="") -> int:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO posicoes (pool_id, data, token_a_amount, token_b_amount, token_a_price_usd, token_b_price_usd, capital_usd, observacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (pool_id, data, token_a_amount, token_b_amount, token_a_price_usd, token_b_price_usd, capital_usd, observacao))
        row = cur.fetchone()
        conn.commit()
        return row["id"]
    finally:
        conn.close()


def listar_posicoes(pool_id: int) -> List[Dict]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM posicoes WHERE pool_id = %s ORDER BY data ASC", (pool_id,))
        return _rows_to_list(cur.fetchall())
    finally:
        conn.close()


def deletar_posicao(posicao_id: int) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM posicoes WHERE id = %s", (posicao_id,))
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────
# TAXAS
# ─────────────────────────────────────────────

def adicionar_taxa(pool_id, data, token_a_amount, token_b_amount, valor_usd, valor_pool_usd=None, token_a_price_usd=None, token_b_price_usd=None, observacao="") -> int:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO taxas (pool_id, data, token_a_amount, token_b_amount, valor_usd, valor_pool_usd, token_a_price_usd, token_b_price_usd, observacao)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
        """, (pool_id, data, token_a_amount, token_b_amount, valor_usd, valor_pool_usd, token_a_price_usd, token_b_price_usd, observacao))
        row = cur.fetchone()
        conn.commit()
        return row["id"]
    finally:
        conn.close()


def listar_taxas(pool_id: int) -> List[Dict]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM taxas WHERE pool_id = %s ORDER BY data ASC", (pool_id,))
        return _rows_to_list(cur.fetchall())
    finally:
        conn.close()


def total_taxas_pool(pool_id: int) -> float:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(SUM(valor_usd), 0) as total FROM taxas WHERE pool_id = %s", (pool_id,))
        row = cur.fetchone()
        return float(row["total"]) if row else 0.0
    finally:
        conn.close()


def deletar_taxa(taxa_id: int) -> None:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM taxas WHERE id = %s", (taxa_id,))
        conn.commit()
    finally:
        conn.close()


# ─────────────────────────────────────────────
# SNAPSHOTS
# ─────────────────────────────────────────────

def adicionar_snapshot(pool_id, data, valor_usd, token_a_price_usd=None, token_b_price_usd=None) -> int:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO snapshots (pool_id, data, valor_usd, token_a_price_usd, token_b_price_usd)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (pool_id, data, valor_usd, token_a_price_usd, token_b_price_usd))
        row = cur.fetchone()
        conn.commit()
        return row["id"]
    finally:
        conn.close()


def listar_snapshots(pool_id: int) -> List[Dict]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("SELECT * FROM snapshots WHERE pool_id = %s ORDER BY data ASC", (pool_id,))
        return _rows_to_list(cur.fetchall())
    finally:
        conn.close()


# ─────────────────────────────────────────────
# RESUMO
# ─────────────────────────────────────────────

def resumo_pools() -> List[Dict]:
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT
                p.id            AS pool_id,
                p.nome, p.protocolo, p.chain, p.token_a, p.token_b, p.fee_tier, p.ativa, p.criado_em,
                COALESCE(pos.capital_total, 0)   AS capital_total,
                COALESCE(pos.qtd_posicoes, 0)    AS qtd_posicoes,
                pos.data_primeira_posicao,
                COALESCE(tx.total_taxas, 0)      AS total_taxas
            FROM pools p
            LEFT JOIN (
                SELECT pool_id, SUM(capital_usd) AS capital_total,
                       COUNT(*) AS qtd_posicoes, MIN(data) AS data_primeira_posicao
                FROM posicoes GROUP BY pool_id
            ) pos ON pos.pool_id = p.id
            LEFT JOIN (
                SELECT pool_id, SUM(valor_usd) AS total_taxas
                FROM taxas GROUP BY pool_id
            ) tx ON tx.pool_id = p.id
            ORDER BY p.ativa DESC, p.criado_em DESC
        """)
        return _rows_to_list(cur.fetchall())
    finally:
        conn.close()


# init_db() é chamado explicitamente pelo app.py
