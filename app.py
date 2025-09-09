import os
import csv
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from flask import Flask, render_template, request, redirect, url_for, flash

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "instance"
DB_DIR.mkdir(exist_ok=True)
DB_PATH = DB_DIR / "ranking.db"
LOG_PATH = BASE_DIR / "erros.log"

# Configura logging para linhas inválidas de CSV
logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("FLASK_SECRET_KEY", "dev-key"),
    DATABASE=str(DB_PATH),
)

# -----------------------------
# Banco de dados
# -----------------------------

def get_db():
    conn = sqlite3.connect(app.config["DATABASE"])  # autocria
    conn.row_factory = sqlite3.Row
    # Habilita FK para funcionar o ON DELETE CASCADE
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS score_list (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS player_score (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            list_id INTEGER NOT NULL,
            nome TEXT NOT NULL,
            nivel INTEGER NOT NULL,
            pontuacao REAL NOT NULL,
            FOREIGN KEY(list_id) REFERENCES score_list(id)
                ON DELETE CASCADE
        )
        """
    )
    conn.commit()
    conn.close()


# ✅ Inicializa o banco (Flask 3 não tem before_first_request)
with app.app_context():
    init_db()


# -----------------------------
# Utilitários
# -----------------------------

def parse_int(value: str) -> Tuple[bool, int]:
    try:
        return True, int(value)
    except Exception:
        return False, 0


def parse_float(value: str) -> Tuple[bool, float]:
    """Aceita ponto ou vírgula como separador decimal."""
    try:
        value = (value or "").replace(",", ".")
        return True, float(value)
    except Exception:
        return False, 0.0


# -----------------------------
# Rotas
# -----------------------------

@app.route("/", methods=["GET"])
def index():
    conn = get_db()
    cur = conn.cursor()

    # listas disponíveis (histórico)
    lists = cur.execute(
        "SELECT id, name, created_at FROM score_list ORDER BY datetime(created_at) DESC"
    ).fetchall()

    # lista selecionada (querystring ?list_id=)
    list_id = request.args.get("list_id")
    selected = None
    players = []

    if lists:
        if list_id is None:
            selected = lists[0]
            list_id = selected["id"]
        else:
            selected = cur.execute(
                "SELECT id, name, created_at FROM score_list WHERE id=?", (list_id,)
            ).fetchone()
            if selected is None:
                # fallback: mais recente
                selected = lists[0]
                list_id = selected["id"]

        players = cur.execute(
            """
            SELECT nome, nivel, pontuacao
            FROM player_score
            WHERE list_id=?
            ORDER BY pontuacao DESC, nivel DESC, nome ASC
            """,
            (list_id,)
        ).fetchall()

    conn.close()
    return render_template("index.html", lists=lists, selected=selected, players=players)


@app.route("/upload", methods=["POST"])
def upload():
    file = request.files.get("csv_file")
    list_name = request.form.get("list_name") or f"Lista de {datetime.now().strftime('%d/%m/%Y %H:%M')}"

    if not file or file.filename == "":
        flash("Selecione um arquivo CSV.", "warning")
        return redirect(url_for("index"))

    # Lê CSV (aceita BOM e normaliza cabeçalhos)
    decoded = file.stream.read().decode("utf-8-sig", errors="ignore").splitlines()
    reader = csv.DictReader(decoded)

    expected = {"nome", "nivel", "pontuacao"}

    # Normaliza os nomes de coluna para minúsculo e sem espaços
    headers = [(h or "").strip().lower() for h in (reader.fieldnames or [])]
    if set(headers) != expected:
        flash("Cabeçalho inválido. Esperado: nome,nivel,pontuacao", "danger")
        return redirect(url_for("index"))

    # Faz o DictReader devolver chaves normalizadas (nome, nivel, pontuacao)
    reader.fieldnames = headers

    conn = get_db()
    cur = conn.cursor()

    # Cria lista
    now_iso = datetime.now(timezone.utc).isoformat()
    cur.execute(
        "INSERT INTO score_list (name, created_at) VALUES (?, ?)", (list_name, now_iso)
    )
    list_id = cur.lastrowid

    valid_count = 0
    line_no = 1  # começa após o cabeçalho visualmente (DictReader já consome header)

    for row in reader:
        line_no += 1
        nome = (row.get("nome") or "").strip()
        niv_ok, nivel = parse_int((row.get("nivel") or "").strip())
        pts_ok, pontuacao = parse_float((row.get("pontuacao") or "").strip())

        if not nome or not niv_ok or not pts_ok:
            logging.info(
                "Linha %s inválida: %s", line_no, {"row": row, "errors": {
                    "nome": bool(nome), "nivel": niv_ok, "pontuacao": pts_ok
                }}
            )
            continue

        cur.execute(
            "INSERT INTO player_score (list_id, nome, nivel, pontuacao) VALUES (?,?,?,?)",
            (list_id, nome, nivel, pontuacao),
        )
        valid_count += 1

    conn.commit()
    conn.close()

    if valid_count == 0:
        flash("Nenhuma linha válida importada. Verifique o arquivo e o erros.log.", "danger")
        # apaga lista vazia
        conn = get_db()
        conn.execute("DELETE FROM score_list WHERE id=?", (list_id,))
        conn.commit()
        conn.close()
    else:
        flash(f"Lista '{list_name}' importada com {valid_count} registro(s).", "success")

    return redirect(url_for("index", list_id=list_id))


@app.route("/delete_list", methods=["POST"])
def delete_list():
    """Exclui uma lista e seus jogadores (cascade)."""
    list_id = request.form.get("list_id")
    if not list_id:
        flash("Lista não informada.", "warning")
        return redirect(url_for("index"))

    conn = get_db()
    cur = conn.cursor()

    # Verifica se existe
    exists = cur.execute(
        "SELECT id, name FROM score_list WHERE id = ?", (list_id,)
    ).fetchone()

    if not exists:
        conn.close()
        flash("Lista não encontrada.", "warning")
        return redirect(url_for("index"))

    # Exclui (player_score será apagada por ON DELETE CASCADE)
    cur.execute("DELETE FROM score_list WHERE id = ?", (list_id,))
    conn.commit()
    conn.close()

    flash(f"Lista '{exists['name']}' excluída com sucesso.", "success")
    return redirect(url_for("index"))
    

if __name__ == "__main__":
    # Execução local
    app.run(debug=True)
