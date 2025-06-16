import ply.yacc as yacc
from lexer import tokens

def p_query(p):
    '''query : select_query
             | insert_query
             | update_query
             | delete_query'''
    p[0] = p[1]

# --- Regras SELECT ---

def p_select_query(p):
    '''select_query : SELECT distinct_opt select_list FROM IDENTIFIER join_clause_opt where_clause_opt group_by_clause_opt order_by_opt limit_clause_opt'''
    p[0] = {
        'type': 'select',
        'distinct': p[2],
        'columns': p[3],
        'table': p[5],
        'join': p[6],
        'where': p[7],
        'group_by': p[8],
        'order_by': p[9],
        'limit': p[10]
    }

def p_distinct_opt(p):
    '''distinct_opt : DISTINCT
                    | empty'''
    p[0] = (len(p) == 2)

def p_select_list(p):
    '''select_list : select_item
                   | select_item COMMA select_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_select_item(p):
    '''select_item : TIMES
                   | IDENTIFIER
                   | aggregate_function'''
    p[0] = p[1]

def p_aggregate_function(p):
    '''aggregate_function : COUNT LPAREN TIMES RPAREN
                          | COUNT LPAREN IDENTIFIER RPAREN
                          | SUM LPAREN IDENTIFIER RPAREN
                          | AVG LPAREN IDENTIFIER RPAREN'''
    func_name = p[1].upper()
    col_name = p[3]
    p[0] = {
        'aggregate': func_name,
        'column': col_name
    }

# --- Regras INSERT, UPDATE, DELETE ---

def p_insert_query(p):
    '''insert_query : INSERT INTO IDENTIFIER LPAREN column_list RPAREN VALUES LPAREN value_list RPAREN
                    | INSERT INTO IDENTIFIER VALUES LPAREN value_list RPAREN'''
    if len(p) == 11:
        p[0] = {
            'type': 'insert',
            'table': p[3],
            'columns': p[5],
            'values': p[9]
        }
    else:
        p[0] = {
            'type': 'insert',
            'table': p[3],
            'columns': None,
            'values': p[6]
        }

def p_update_query(p):
    '''update_query : UPDATE IDENTIFIER SET set_list where_clause_opt'''
    p[0] = {
        'type': 'update',
        'table': p[2],
        'set': p[4],
        'where': p[5]
    }

def p_delete_query(p):
    '''delete_query : DELETE FROM IDENTIFIER where_clause_opt'''
    p[0] = {
        'type': 'delete',
        'table': p[3],
        'where': p[4]
    }

# --- Cláusulas Opcionais (JOIN, WHERE, etc.) ---

def p_join_clause_opt(p):
    '''join_clause_opt : join_type JOIN IDENTIFIER ON join_condition
                       | empty'''
    if len(p) > 2:
        p[0] = {
            'type': p[1],
            'table': p[3],
            'on': p[5]
        }
    else:
        p[0] = None

def p_join_type(p):
    '''join_type : LEFT
                 | empty'''
    p[0] = 'LEFT' if len(p) == 2 else 'INNER'

def p_join_condition(p):
    '''join_condition : IDENTIFIER EQ IDENTIFIER'''
    p[0] = {'left': p[1], 'right': p[3]}

def p_where_clause_opt(p):
    '''where_clause_opt : WHERE condition
                        | empty'''
    p[0] = p[2] if len(p) > 2 else None

def p_group_by_clause_opt(p):
    '''group_by_clause_opt : GROUP BY column_list
                           | empty'''
    if len(p) > 2:
        p[0] = p[3]
    else:
        p[0] = None

def p_order_by_opt(p):
    '''order_by_opt : ORDER BY order_list
                    | empty'''
    p[0] = p[3] if len(p) > 2 else None

def p_limit_clause_opt(p):
    '''limit_clause_opt : LIMIT NUMBER
                        | empty'''
    p[0] = p[2] if len(p) > 2 else None

# --- Listas e Itens ---

def p_set_list(p):
    '''set_list : set_item
               | set_item COMMA set_list'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = {**p[1], **p[3]}

def p_set_item(p):
    '''set_item : IDENTIFIER EQ value'''
    p[0] = {p[1]: p[3]}

def p_value_list(p):
    '''value_list : value
                 | value COMMA value_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_column_list(p):
    '''column_list : IDENTIFIER
                  | IDENTIFIER COMMA column_list'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = [p[1]] + p[3]

def p_order_list(p):
    '''order_list : order_item
                 | order_item COMMA order_list'''
    p[0] = [p[1]] if len(p) == 2 else [p[1]] + p[3]

def p_order_item(p):
    '''order_item : IDENTIFIER asc_desc'''
    p[0] = {
        'column': p[1],
        'direction': p[2]
    }

def p_asc_desc(p):
    '''asc_desc : ASC
                | DESC
                | empty'''
    p[0] = p[1].upper() if len(p) > 1 and p[1] is not None else 'ASC'

# --- Condições e Operadores ---

def p_condition(p):
    '''condition : simple_condition
                | LPAREN condition RPAREN
                | condition AND condition
                | condition OR condition
                | NOT condition'''
    if len(p) == 2:
        p[0] = p[1]
    elif p[1] == '(':
        p[0] = p[2]
    elif p[2].upper() == 'AND':
        p[0] = {'operator': 'AND', 'left': p[1], 'right': p[3]}
    elif p[2].upper() == 'OR':
        p[0] = {'operator': 'OR', 'left': p[1], 'right': p[3]}
    elif p[1].upper() == 'NOT':
        p[0] = {'operator': 'NOT', 'condition': p[2]}

def p_simple_condition(p):
    '''simple_condition : IDENTIFIER operator value
                        | IDENTIFIER LIKE STRING_LITERAL'''
    if len(p) == 4 and p[2].lower() == 'like':
        p[0] = {'column': p[1], 'operator': 'LIKE', 'value': p[3]}
    elif len(p) == 4:
        p[0] = {'column': p[1], 'operator': p[2], 'value': p[3]}

def p_operator(p):
    '''operator : EQ
                | NEQ
                | GT
                | LT
                | GE
                | LE'''
    p[0] = p[1]

def p_value(p):
    '''value : NUMBER
             | STRING_LITERAL'''
    p[0] = p[1]

# --- Regras Vazias e de Erro ---

def p_empty(p):
    'empty :'
    pass

def p_error(p):
    if p:
        print(f"Erro de sintaxe na linha {p.lineno}, token={p.type}, valor={p.value}")
    else:
        print("Erro de sintaxe: fim inesperado da entrada")

# --- Construção do Parser ---
parser = yacc.yacc(debug=False)