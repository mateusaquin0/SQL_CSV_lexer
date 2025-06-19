from parser_sql import parser
from executor import executar

# Lista de consultas para demonstrar as funcionalidades do sistema
consultas = [
    "-- Consultas básicas --",
    "SELECT nome, idade FROM usuarios WHERE idade > 20 ORDER BY idade DESC",
    "SELECT * FROM usuarios LIMIT 3",
    
    "-- Testando LIKE e DISTINCT --",
    "SELECT nome, email FROM usuarios WHERE nome LIKE '%na%'",
    "SELECT DISTINCT idade FROM usuarios",

    "-- Testando JOINs --",
    "SELECT nome, produto, valor FROM usuarios JOIN pedidos ON id = id_usuario",
    "SELECT nome, produto FROM usuarios LEFT JOIN pedidos ON id = id_usuario",

    "-- Testando Agregação e GROUP BY --",
    "SELECT AVG(idade) FROM usuarios",
    "SELECT id_usuario, SUM(valor) FROM pedidos GROUP BY id_usuario",
    "SELECT idade, COUNT(*) FROM usuarios GROUP BY idade ORDER BY idade"
]

for sql in consultas:
    if sql.startswith("--"):
        print(f"\n{sql}")
        continue
    
    print(f"\n> Executando: {sql}")
    ast = parser.parse(sql) # AST (Abstract Syntax Tree)
    
    # --- LINHA DE DEPURAÇÃO ---
    # print(f"--- [DEPURAÇÃO] AST Gerado: {ast} ---")
    
    if ast:
        executar(ast)
