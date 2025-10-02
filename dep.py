import sqlite3
import pandas as pd

# Caminho do banco de dados
DB_PATH = "leads.db"

# Conectar ao SQLite
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Listar todas as tabelas para garantir que a tabela existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tabelas no banco:", tables)

# Verificar se a tabela 'leads' existe
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='leads';")
if cursor.fetchone() is None:
    print("Tabela 'leads' não encontrada!")
else:
    
    print("Tabela 'leads' encontrada.")

    # Puxar todos os registros
    df = pd.read_sql_query("SELECT id, nome, etapa, cidade, estado FROM leads", conn)
    
    if df.empty:
        print("Nenhum lead cadastrado no banco.")
    else:
        print(f"Total de leads: {len(df)}")
        print(df)

# Fechar conexão
conn.close()
