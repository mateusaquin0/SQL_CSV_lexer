from parser_sql import parser
from lexer import lexer
from executor import executar

# consultas = [
#     "SELECT nome, idade FROM usuarios WHERE idade >= 25",
#     "INSERT INTO usuarios (nome, idade) VALUES ('Carlos', 15)",
#     "DELETE FROM usuarios WHERE idade < 18",
#     "UPDATE usuarios SET idade = 31 WHERE nome = 'Carlos'",
#     "SELECT COUNT(*) FROM usuarios",
#     "SELECT produto, preco FROM produtos ORDER BY preco DESC"
# ]

consultas= ["SELECT idade, COUNT(*) FROM usuarios GROUP BY idade"
            ]

for sql in consultas:
    print(f"\nExecutando: {sql}")
    resultado = parser.parse(sql)
    if resultado:
        executar(resultado)

# sql = "SELECT * FROM usuarios WHERE (nome != 'Maria' AND idade >= "'10'") AND idade <= 28"
# resultado = parser.parse(sql)
# if resultado:
#     executar(resultado)