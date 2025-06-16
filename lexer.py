import ply.lex as lex

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
    'into': 'INTO',
    'set': 'SET',
    'values': 'VALUES',
    'order': 'ORDER',
    'by': 'BY',
    'asc': 'ASC',
    'desc': 'DESC',
    'join': 'JOIN',
    'on': 'ON',
    'limit': 'LIMIT',
    'distinct': 'DISTINCT',
    'like': 'LIKE',
    'left': 'LEFT',
    'sum': 'SUM',
    'avg': 'AVG',
    'group': 'GROUP'
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

def t_IDENTIFIER(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = keywords.get(t.value.lower(), 'IDENTIFIER')
    return t

def t_STRING_LITERAL(t):
    r'\"[^\"]*\"|\'[^\']*\''
    t.value = t.value[1:-1]
    return t

def t_NUMBER(t):
    r'\d+\.?\d*'
    if '.' in t.value:
        t.value = float(t.value)
    else:
        t.value = int(t.value)
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    print(f"Caracter inválido: {t.value[0]}")
    t.lexer.skip(1)

lexer = lex.lex()