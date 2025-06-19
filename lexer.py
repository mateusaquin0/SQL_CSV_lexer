import ply.lex as lex

# Dicionário de palavras-chave da nossa linguagem SQL.
# O lexer usa isso para diferenciar um comando (SELECT) de um identificador (nome_da_tabela).
keywords = {
    'select': 'SELECT',
    'delete': 'DELETE',
    'update': 'UPDATE',
    'insert': 'INSERT',
    'from': 'FROM',
    'where': 'WHERE',
    'and': 'AND',
    'or': 'OR',
    'not': 'NOT',
    'count': 'COUNT',
    'sum': 'SUM',
    'avg': 'AVG',
    'into': 'INTO',
    'set': 'SET',
    'values': 'VALUES',
    'order': 'ORDER',
    'by': 'BY',
    'group': 'GROUP',
    'asc': 'ASC',
    'desc': 'DESC',
    'join': 'JOIN',
    'on': 'ON',
    'left': 'LEFT',
    'limit': 'LIMIT',
    'distinct': 'DISTINCT',
    'like': 'LIKE'
}

tokens = [
    'IDENTIFIER',
    'STRING_LITERAL',
    'NUMBER',
    'EQ', 'NEQ', 'GT', 'LT', 'GE', 'LE',
    'COMMA', 'LPAREN', 'RPAREN',
    'TIMES',
] + list(keywords.values())

t_EQ = r'='
t_NEQ = r'!='
t_GT = r'>'
t_LT = r'<'
t_GE = r'>='
t_LE = r'<='
t_COMMA = r','
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_TIMES = r'\*'

t_ignore = ' \t'

# Regra para identificadores (nomes de tabelas, colunas).
def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = keywords.get(t.value.lower(), 'IDENTIFIER')
    return t

# Regra para strings (delimitadas por aspas simples ou duplas).
def t_STRING_LITERAL(t):
    r'\"[^\"]*\"|\'[^\']*\''
    t.value = t.value[1:-1]  # Remove as aspas.
    return t

# Regra para números (int ou float).
def t_NUMBER(t):
    r'\d+\.?\d*'
    if '.' in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t

# Regra para contar novas linhas.
def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

# Tratamento de erro para caracteres inválidos.
def t_error(t):
    print(f"Caracter inválido: {t.value[0]}")
    t.lexer.skip(1)

lexer = lex.lex()