# 🏆 Sistema de Ranking de Jogadores (Flask + Bootstrap/Bootswatch)

Este projeto é uma aplicação web em **Flask** que permite importar arquivos CSV com informações de jogadores e exibir um ranking interativo.  
Funcionalidades principais:

- Importar listas de jogadores via CSV (`Nome,Nivel,Pontuacao`);
- Armazenar dados em SQLite;
- Exibir ranking ordenado por **pontuação**, com destaque para os 3 primeiros 🥇🥈🥉;
- Manter histórico de listas importadas;
- Permitir excluir listas (com confirmação bonita via SweetAlert2);
- Interface responsiva usando **Flask + Bootstrap (Bootswatch Slate)**.

---

## 📋 Requisitos

- Python 3.10 ou superior
- Pip (gerenciador de pacotes do Python)
- Virtualenv (opcional, mas recomendado)

---

## ⚙️ Instalação e execução

### 1. Clonar ou baixar o projeto
Coloque os arquivos em uma pasta local, por exemplo:
```bash
C:\Users\aluno\Desktop\ranking_flask
```

### 2. Criar ambiente virtual
No **Windows (PowerShell)**:
```powershell
python -m venv venv
.\env\Scripts\ctivate
```

No **Linux/Mac**:
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instalar dependências
```bash
pip install -r requirements.txt
```

### 4. Executar a aplicação
Com o ambiente virtual ativado:
```bash
python app.py
```
ou:
```bash
flask run
```

A aplicação estará disponível em:  
👉 http://127.0.0.1:5000

---

## 📂 Estrutura de Arquivos

```
ranking_flask/
│── app.py              # Código principal Flask
│── requirements.txt    # Dependências
│── README.md           # Este guia
│── erros.log           # Log de linhas inválidas no CSV
│── instance/
│    └── ranking.db     # Banco SQLite (gerado automaticamente)
│── templates/
│    ├── base.html      # Layout base (navbar, includes)
│    └── index.html     # Página principal com ranking
│── static/
     └── custom.css     # Estilos extras (destaque dos top 3)
```

---

## 📑 Formato do CSV

O cabeçalho deve ser **exatamente**:

```
Nome,Nivel,Pontuacao
```

Exemplo de conteúdo:
```csv
Nome,Nivel,Pontuacao
Alice,10,1234.5
Bruno,8,950.0
Carla,12,1400.3
```

⚠️ Observações:
- Aceita **ponto ou vírgula** como separador decimal (`1234.5` ou `1234,5`);
- Linhas inválidas (sem nome ou valores incorretos) são ignoradas e registradas em `erros.log`.

---

## 🗑️ Exclusão de listas

- Cada lista pode ser excluída pelo botão **Excluir** na lateral esquerda.
- O sistema usa **SweetAlert2** para confirmar a exclusão de forma elegante.
- Quando uma lista é excluída, todos os jogadores vinculados a ela também são removidos.

---

## 🎨 Personalização

- O tema visual está configurado para **Bootswatch Slate**.
- Para trocar, edite `templates/base.html` e substitua a linha:

```html
https://cdn.jsdelivr.net/npm/bootswatch@5.3.3/dist/slate/bootstrap.min.css
```

por outro tema disponível em [Bootswatch](https://bootswatch.com/).

---

## 🚀 Ideias Futuras

- Adicionar paginação e busca no ranking;
- Exportar listas novamente em CSV;
- Criar autenticação para controlar quem pode importar/excluir listas.
