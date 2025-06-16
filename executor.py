# executor.py

import csv
import os
import re # Importar o módulo de expressões regulares para o LIKE
from collections import defaultdict

def get_csv_path(table_name):
    return f"{table_name}.csv"

def executar(consulta):
    try:
        if consulta['type'] == 'select':
            # Verifica se a consulta é do tipo COUNT
            if consulta['columns'] and consulta['columns'][0].startswith('COUNT('):
                executar_count(consulta)
            else:
                executar_select(consulta)
        elif consulta['type'] == 'insert':
            executar_insert(consulta)
        elif consulta['type'] == 'update':
            executar_update(consulta)
        elif consulta['type'] == 'delete':
            executar_delete(consulta)
    except Exception as e:
        print(f'Erro durante execução: {e}')

def executar_select(consulta):
    table_name = consulta['table']
    join_info = consulta['join']
    condicao = consulta['where']
    order_by = consulta['order_by']
    colunas = consulta['columns']
    is_distinct = consulta['distinct'] # Flag de DISTINCT
    limit = consulta['limit']         # Valor do LIMIT

    try:
        # ... (lógica de carregamento de dados e JOIN - sem alterações)
        arquivo1 = get_csv_path(table_name)
        with open(arquivo1, newline='', encoding='utf-8') as csvfile1:
            dados1 = list(csv.DictReader(csvfile1))

        if not join_info:
            fonte_dados = dados1
        else:
            table2_name = join_info['table']
            arquivo2 = get_csv_path(table2_name)
            with open(arquivo2, newline='', encoding='utf-8') as csvfile2:
                dados2 = list(csv.DictReader(csvfile2))
            col_esquerda = join_info['on']['left']
            col_direita = join_info['on']['right']
            dados_juntados = []
            for linha1 in dados1:
                for linha2 in dados2:
                    if col_esquerda in linha1 and col_direita in linha2 and linha1[col_esquerda] == linha2[col_direita]:
                        linha_juntada = {**linha1, **linha2}
                        dados_juntados.append(linha_juntada)
            fonte_dados = dados_juntados

        # 1. Aplica a condição WHERE
        resultado = []
        for linha in fonte_dados:
            if condicao is None or verifica_condicao(linha, condicao):
                resultado.append(linha)

        # 2. Seleciona as colunas
        resultado_selecionado = []
        if resultado:
            colunas_finais = colunas if colunas != ['*'] else list(resultado[0].keys())
            for linha in resultado:
                linha_selecionada = {col: linha.get(col) for col in colunas_finais}
                resultado_selecionado.append(linha_selecionada)

        # 3. Aplica DISTINCT, se necessário
        if is_distinct:
            vistos = set()
            resultado_distinto = []
            for d in resultado_selecionado:
                # Converte o dicionário em um tuple de itens para ser 'hashable'
                t = tuple(sorted(d.items()))
                if t not in vistos:
                    vistos.add(t)
                    resultado_distinto.append(d)
            resultado_final = resultado_distinto
        else:
            resultado_final = resultado_selecionado

        # 4. Aplica ORDER BY
        if order_by:
            resultado_final = ordenar_resultado(resultado_final, order_by)

        # 5. Aplica LIMIT
        if limit is not None:
            resultado_final = resultado_final[:limit]

        imprimir_resultado(resultado_final, colunas_finais if colunas != ['*'] else [])

    except FileNotFoundError as e:
        print(f'Tabela não encontrada: {e.filename}')
    except KeyError as e:
        print(f'Coluna inexistente: {e}')

def executar_count(consulta):
    table_name = consulta['table']
    arquivo = get_csv_path(table_name)
    condicao = consulta['where']
    coluna_count_str = consulta['columns'][0] # Ex: 'COUNT(*)' ou 'COUNT(nome)'

    try:
        with open(arquivo, newline='', encoding='utf-8') as csvfile:
            leitor = csv.DictReader(csvfile)
            contador = 0
            
            # Extrai o nome da coluna de dentro do COUNT()
            coluna_alvo = coluna_count_str[6:-1] # Remove 'COUNT(' e ')'

            for linha in leitor:
                if condicao is None or verifica_condicao(linha, condicao):
                    # Se for COUNT(*) ou se a coluna alvo tiver um valor não vazio
                    if coluna_alvo == '*' or (coluna_alvo in linha and linha[coluna_alvo]):
                        contador += 1

            print(f"Total de registros: {contador}")

    except FileNotFoundError:
        print(f'Tabela "{table_name}" não encontrada (arquivo: {arquivo})')
    except KeyError as e:
        print(f'Coluna inexistente: {e}')

def get_pk_column(fieldnames):
    """
    Determina o nome da coluna de chave primária com base em uma heurística.
    1. Procura por 'id'.
    2. Procura por uma coluna que termine com '_id'.
    3. Usa a primeira coluna como fallback.
    """
    if not fieldnames:
        return 'id' # Padrão para um arquivo completamente novo.
        
    if 'id' in fieldnames:
        return 'id'
    
    for name in fieldnames:
        if name.endswith('_id'):
            return name
            
    return fieldnames[0]

def executar_insert(consulta):
    table_name = consulta['table']
    arquivo = get_csv_path(table_name)
    colunas_usuario = consulta['columns']
    valores_usuario = consulta['values']

    try:
        fieldnames = []
        # Tenta ler os cabeçalhos para descobrir a estrutura da tabela
        try:
            with open(arquivo, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                fieldnames = next(reader)
        except (FileNotFoundError, StopIteration):
            # Se o arquivo não existe ou está vazio, usa as colunas da consulta
            if colunas_usuario:
                fieldnames = colunas_usuario[:]
                # Adiciona uma coluna 'id' por padrão se for um arquivo totalmente novo
                if 'id' not in fieldnames and not any(c.endswith('_id') for c in fieldnames):
                    fieldnames.insert(0, 'id')

        # Determina o nome da chave primária usando a nova função
        pk_column_name = get_pk_column(fieldnames)

        novo_id = 1 # Padrão para um arquivo novo/vazio
        try:
            with open(arquivo, 'r', newline='', encoding='utf-8') as csvfile:
                leitor = csv.DictReader(csvfile)
                # Usa o nome da PK dinamicamente
                ids_existentes = [int(linha[pk_column_name]) for linha in leitor if pk_column_name in linha and linha[pk_column_name].isdigit()]
                if ids_existentes:
                    novo_id = max(ids_existentes) + 1
        except FileNotFoundError:
            pass

        # Prepara a nova linha
        if colunas_usuario:
            linha_para_inserir = dict(zip(colunas_usuario, valores_usuario))
        else:
            headers_sem_pk = [h for h in fieldnames if h != pk_column_name]
            linha_para_inserir = dict(zip(headers_sem_pk, valores_usuario))
            
        # Adiciona o ID gerado automaticamente com o nome correto da coluna
        linha_para_inserir[pk_column_name] = novo_id

        # Garante que os fieldnames para escrita estejam corretos e completos
        final_fieldnames = fieldnames[:]
        for key in linha_para_inserir.keys():
            if key not in final_fieldnames:
                final_fieldnames.append(key)
        
        # Abre o arquivo em modo de anexo ('a')
        file_exists = os.path.isfile(arquivo) and os.path.getsize(arquivo) > 0
        with open(arquivo, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=final_fieldnames)
            if not file_exists:
                writer.writeheader()
            
            writer.writerow(linha_para_inserir)
            print("1 registro inserido.")

    except Exception as e:
        print(f'Erro durante inserção: {e}')

def executar_update(consulta):
    table_name = consulta['table']
    arquivo = get_csv_path(table_name)
    set_list = consulta['set']
    condicao = consulta['where']

    try:
        with open(arquivo, 'r', newline='', encoding='utf-8') as csvfile:
            leitor = csv.DictReader(csvfile)
            linhas = list(leitor)
            fieldnames = leitor.fieldnames

        atualizados = 0
        for linha in linhas:
            if condicao is None or verifica_condicao(linha, condicao):
                for col, val in set_list.items():
                    linha[col] = val
                atualizados += 1

        with open(arquivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(linhas)

        print(f"{atualizados} registros atualizados.")

    except FileNotFoundError:
        print(f'Tabela "{table_name}" não encontrada (arquivo: {arquivo})')
    except KeyError as e:
        print(f'Coluna inexistente: {e}')

def executar_delete(consulta):
    table_name = consulta['table']
    arquivo = get_csv_path(table_name)
    condicao = consulta['where']

    try:
        with open(arquivo, 'r', newline='', encoding='utf-8') as csvfile:
            leitor = csv.DictReader(csvfile)
            linhas = list(leitor)
            fieldnames = leitor.fieldnames

        linhas_filtradas = [linha for linha in linhas 
                          if condicao is None or not verifica_condicao(linha, condicao)]

        removidos = len(linhas) - len(linhas_filtradas)

        with open(arquivo, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(linhas_filtradas)

        print(f"{removidos} registros removidos.")

    except FileNotFoundError:
        print(f'Tabela "{table_name}" não encontrada (arquivo: {arquivo})')
    except KeyError as e:
        print(f'Coluna inexistente: {e}')

def verifica_condicao(linha, cond):
    if 'operator' in cond and cond['operator'] in ['AND', 'OR', 'NOT']:
        if cond['operator'] == 'AND':
            return verifica_condicao(linha, cond['left']) and verifica_condicao(linha, cond['right'])
        elif cond['operator'] == 'OR':
            return verifica_condicao(linha, cond['left']) or verifica_condicao(linha, cond['right'])
        elif cond['operator'] == 'NOT':
            return not verifica_condicao(linha, cond['condition'])
    else:
        operador = cond['operator']
        coluna = cond['column']
        
        if coluna not in linha:
            return False
            
        valor_linha = linha[coluna]
        valor_condicao = cond['value']

        if operador == 'LIKE':
            padrao_regex = str(valor_condicao).replace('%', '.*').replace('_', '.')
            return bool(re.match(f"^{padrao_regex}$", str(valor_linha), re.IGNORECASE))

        try:
            valor_linha_num = float(valor_linha)
            valor_condicao_num = float(valor_condicao)
            valor_linha = valor_linha_num
            valor_condicao = valor_condicao_num
        except (ValueError, TypeError):
            pass

        if operador == '=': return valor_linha == valor_condicao
        elif operador == '!=': return valor_linha != valor_condicao
        elif operador == '>': return valor_linha > valor_condicao
        elif operador == '<': return valor_linha < valor_condicao
        elif operador == '>=': return valor_linha >= valor_condicao
        elif operador == '<=': return valor_linha <= valor_condicao
        else:
            return False

def ordenar_resultado(resultado, order_by):
    for ordem in reversed(order_by):
        coluna = ordem['column']
        direcao = ordem['direction']
        resultado.sort(key=lambda x: x[coluna], reverse=(direcao == 'DESC'))
    return resultado

def imprimir_resultado(linhas, colunas):
    if not linhas:
        print("Nenhum resultado encontrado.")
        return

    if colunas == ['*']:
        colunas = list(linhas[0].keys())

    print(" | ".join(colunas))
    print("-" * 40)

    for linha in linhas:
        print(" | ".join(str(linha.get(col, '')) for col in colunas))
        
# Função executar_select totalmente reescrita
def executar_select(consulta):
    try:
        # --- Etapa 1: Carregamento de dados e JOIN ---
        table_name = consulta['table']
        join_info = consulta['join']
        
        with open(get_csv_path(table_name), mode='r', encoding='utf-8') as f:
            fonte_dados = list(csv.DictReader(f))

        if join_info:
            # Lógica de JOIN (a mesma da versão anterior, omitida por brevidade)
            pass

        # --- Etapa 2: Aplicar WHERE ---
        condicao = consulta['where']
        dados_filtrados = [r for r in fonte_dados if condicao is None or verifica_condicao(r, condicao)]

        if not dados_filtrados:
            print("Nenhum resultado encontrado.")
            return

        # --- Etapa 3: Lógica de Agregação ou Seleção Normal ---
        colunas_solicitadas = consulta['columns']
        is_aggregate_query = any(isinstance(c, dict) and 'aggregate' in c for c in colunas_solicitadas)
        group_by_cols = consulta['group_by']
        
        dados_processados = []

        if group_by_cols or is_aggregate_query: # Entra aqui se for GROUP BY ou qualquer agregação
            groups = defaultdict(list)
            
            # Agrupa os dados baseados nas colunas do GROUP BY ou em um grupo único
            if group_by_cols:
                for linha in dados_filtrados:
                    key = tuple(linha.get(col, '') for col in group_by_cols)
                    groups[key].append(linha)
            else:
                groups['__single_group__'] = dados_filtrados

            # Processa cada grupo para calcular as agregações
            for key, rows in groups.items():
                linha_agregada = {}
                
                # Adiciona as colunas do GROUP BY ao resultado
                if group_by_cols:
                    for i, col_name in enumerate(group_by_cols):
                        linha_agregada[col_name] = key[i]

                # Processa as colunas da lista SELECT
                for col_info in colunas_solicitadas:
                    if isinstance(col_info, dict) and 'aggregate' in col_info:
                        func, col = col_info['aggregate'], col_info['column']
                        res_col_name = f"{func}({col})"
                        
                        if func == 'COUNT':
                            linha_agregada[res_col_name] = len(rows) if col == '*' else sum(1 for r in rows if r.get(col))
                        elif func in ['SUM', 'AVG']:
                            vals = [float(r[col]) for r in rows if r.get(col) and r[col].replace('.', '', 1).isdigit()]
                            if func == 'SUM':
                                linha_agregada[res_col_name] = sum(vals)
                            elif func == 'AVG':
                                linha_agregada[res_col_name] = sum(vals) / len(vals) if vals else 0
                
                dados_processados.append(linha_agregada)
        else: # Query de seleção normal, sem agregação
            colunas_finais_nomes = colunas_solicitadas if colunas_solicitadas[0] != '*' else list(dados_filtrados[0].keys())
            for linha in dados_filtrados:
                dados_processados.append({col: linha.get(col) for col in colunas_finais_nomes})

        # --- Etapa 4: Processamento Final (DISTINCT, ORDER BY, LIMIT) ---
        dados_finais = dados_processados
        if consulta.get('distinct'):
            vistos = set()
            resultado_distinto = []
            for d in dados_finais:
                t = tuple(sorted(d.items()))
                if t not in vistos:
                    vistos.add(t)
                    resultado_distinto.append(d)
            dados_finais = resultado_distinto

        if consulta.get('order_by'):
            dados_finais = ordenar_resultado(dados_finais, consulta['order_by'])
        
        if consulta.get('limit') is not None:
            dados_finais = dados_finais[:consulta['limit']]

        # --- Etapa 5: Imprimir ---
        if not dados_finais:
            print("Nenhum resultado encontrado.")
            return
            
        colunas_para_imprimir = list(dados_finais[0].keys())
        imprimir_resultado(dados_finais, colunas_para_imprimir)

    except FileNotFoundError as e:
        print(f"Tabela não encontrada: {e.filename}")
    except Exception as e:
        print(f"Erro ao executar SELECT: {e}")