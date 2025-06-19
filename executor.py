import csv
import os
import re
from collections import defaultdict

# Retorna o caminho completo para o arquivo CSV de uma tabela.
def get_csv_path(table_name):
    return f"{table_name}.csv"

# Função principal que recebe uma consulta e direciona para a função executora.
def executar(consulta):
    try:
        tipo_consulta = consulta['type']
        if tipo_consulta == 'select':
            executar_select(consulta)
        elif tipo_consulta == 'insert':
            executar_insert(consulta)
        elif tipo_consulta == 'update':
            executar_update(consulta)
        elif tipo_consulta == 'delete':
            executar_delete(consulta)
    except Exception as e:
        print(f'ERRO: Ocorreu um erro inesperado durante a execução: {e}')

# Executa SELECT com JOINs, WHERE, GROUP BY, agregações...
def executar_select(consulta):
    try:
        # ETAPA 1: CARREGAMENTO DE DADOS E JOIN
        tabela_principal_nome = consulta['table']
        info_join = consulta['join']

        with open(get_csv_path(tabela_principal_nome), mode='r', encoding='utf-8') as f:
            dados_tabela_principal = list(csv.DictReader(f))

        fonte_dados = dados_tabela_principal

        if info_join:
            tipo_join = info_join.get('type', 'INNER')
                        
            tabela_secundaria_nome = info_join['table']
            
            with open(get_csv_path(tabela_secundaria_nome), mode='r', encoding='utf-8') as f:
                dados_tabela_secundaria = list(csv.DictReader(f))

            col_esquerda, col_direita = info_join['on']['left'], info_join['on']['right']
            dados_juntados = []

            if tipo_join == 'INNER':
                for linha_esq in dados_tabela_principal:
                    for linha_dir in dados_tabela_secundaria:
                        if linha_esq.get(col_esquerda) == linha_dir.get(col_direita):
                            dados_juntados.append({**linha_dir, **linha_esq})
            
            elif tipo_join == 'LEFT':
                if dados_tabela_secundaria:
                    cabecalhos_direita = dados_tabela_secundaria[0].keys()
                else:
                    cabecalhos_direita = []
                for linha_esq in dados_tabela_principal:
                    encontrou_par = False
                    for linha_dir in dados_tabela_secundaria:
                        if linha_esq.get(col_esquerda) == linha_dir.get(col_direita):
                            dados_juntados.append({**linha_dir, **linha_esq})
                            encontrou_par = True
                    if not encontrou_par:
                        linha_preenchida = {}
                        for cabecalho in cabecalhos_direita:
                            linha_preenchida[cabecalho] = ''
                        dados_juntados.append({**linha_preenchida, **linha_esq})
            
            fonte_dados = dados_juntados

        # ETAPA 2: FILTRAGEM COM WHERE
        condicao_where = consulta['where']
        dados_filtrados = []

        for linha in fonte_dados:
            if condicao_where is None or verifica_condicao(linha, condicao_where):
                dados_filtrados.append(linha)
                
        if not dados_filtrados:
            print("Nenhum resultado encontrado.")
            return

        # ETAPA 3: AGRUPAMENTO (GROUP BY) E AGREGAÇÃO (SUM, COUNT, etc.)
        colunas_solicitadas = consulta['columns']
        colunas_group_by = consulta['group_by']
        funcao_agregacao = False        
        for coluna in colunas_solicitadas:
            if isinstance(coluna, dict):
                funcao_agregacao = True
                break
        
        is_consulta_agregada = funcao_agregacao or colunas_group_by
        dados_processados = []

        if is_consulta_agregada:
            grupos = defaultdict(list)
            if colunas_group_by:
                for linha in dados_filtrados:
                    valores_da_chave = []
                    for nome_da_coluna in colunas_group_by:
                        valor_da_celula = linha.get(nome_da_coluna, '')
                        valor_limpo = valor_da_celula.strip() # Limpa espaços em branco
                        valores_da_chave.append(valor_limpo)

                    chave_grupo = tuple(valores_da_chave)
                    grupos[chave_grupo].append(linha)
            else:
                grupos['__grupo_unico__'] = dados_filtrados

            for chave, linhas_do_grupo in grupos.items():
                linha_agregada = {}
                if colunas_group_by:
                    for i, nome_coluna in enumerate(colunas_group_by):
                        linha_agregada[nome_coluna] = chave[i]
                
                for info_coluna in colunas_solicitadas:
                    if isinstance(info_coluna, dict) and 'aggregate' in info_coluna:
                        funcao, coluna_alvo = info_coluna['aggregate'], info_coluna['column']
                        nome_coluna_resultado = f"{funcao}({coluna_alvo})"
                        
                        if funcao == 'COUNT':
                            if coluna_alvo == '*':
                                # COUNT(*)  
                                # Conta o numero total de linhas que pertencem a este grupo
                                contagem_total = len(linhas_do_grupo)
                                linha_agregada[nome_coluna_resultado] = contagem_total

                            else:
                                # COUNT(nome_da_coluna) 
                                # Contar apenas as linhas onde essa coluna tem um valor
                                contador_de_valores_nao_nulos = 0

                                for linha in linhas_do_grupo:
                                    if linha.get(coluna_alvo):
                                        contador_de_valores_nao_nulos += 1
                                        
                                linha_agregada[nome_coluna_resultado] = contador_de_valores_nao_nulos
                                
                        elif funcao in ['SUM', 'AVG']:
                            valores_numericos = []
                            for linha in linhas_do_grupo:
                                
                                # Verifica se a coluna existe
                                if linha.get(coluna_alvo):
                                    
                                    # Pegamos o valor da coluna
                                    valor_da_celula = linha[coluna_alvo]
                                    
                                    # Tenta converter para float
                                    try:
                                        valor_convertido = float(valor_da_celula)
                                        valores_numericos.append(valor_convertido)
                                        
                                    except (ValueError, TypeError):
                                        continue
                                    
                            if funcao == 'SUM':
                                linha_agregada[nome_coluna_resultado] = sum(valores_numericos)
                            elif funcao == 'AVG':
                                if valores_numericos:
                                    linha_agregada[nome_coluna_resultado] = sum(valores_numericos) / len(valores_numericos)
                                else:
                                    linha_agregada[nome_coluna_resultado] = 0
                                
                dados_processados.append(linha_agregada)
        else:
            if colunas_solicitadas[0] != '*':
                nomes_colunas_finais = colunas_solicitadas
                
            else:
                nomes_colunas_finais = list(dados_filtrados[0].keys())
            for linha in dados_filtrados:
                linha_de_resultado = {}
                for nome_da_coluna in nomes_colunas_finais:
                    valor_da_coluna = linha.get(nome_da_coluna)
                    linha_de_resultado[nome_da_coluna] = valor_da_coluna

                dados_processados.append(linha_de_resultado)

        # ETAPA 4: PROCESSAMENTO FINAL (DISTINCT, ORDER BY, LIMIT)
        dados_finais = dados_processados
        if consulta.get('distinct'):
            vistos, resultado_distinto = set(), []
            for d in dados_finais:
                tupla_ordenada = tuple(sorted(d.items()))
                if tupla_ordenada not in vistos:
                    vistos.add(tupla_ordenada)
                    resultado_distinto.append(d)
            dados_finais = resultado_distinto

        if consulta.get('order_by'):
            dados_finais = ordenar_resultado(dados_finais, consulta['order_by'])
        
        if consulta.get('limit') is not None:
            dados_finais = dados_finais[:consulta['limit']]

        # ETAPA 5: IMPRESSÃO DO RESULTADO
        if not dados_finais:
            print("Nenhum resultado encontrado.")
            return
            
        colunas_para_imprimir = list(dados_finais[0].keys())
        imprimir_resultado(dados_finais, colunas_para_imprimir)

    except FileNotFoundError as e:
        print(f"ERRO: Tabela não encontrada: {e.filename}")
    except Exception as e:
        print(f"ERRO: Ocorreu um erro inesperado ao executar a consulta: {e}")

def _get_pk_column(fieldnames):
    # Determina o nome da coluna de chave primária procurando por id ou sufixos _id
    if not fieldnames: return 'id'
    if 'id' in fieldnames: return 'id'
    for name in fieldnames:
        if name.endswith('_id'): return name
    return fieldnames[0]

def executar_insert(consulta):
    # Executa INSERT, gerando um ID único automaticamente
    table_name = consulta['table']
    arquivo = get_csv_path(table_name)
    colunas_usuario = consulta['columns']
    valores_usuario = consulta['values']

    try:
        fieldnames, novo_id = [], 1
        try:
            with open(arquivo, 'r', newline='', encoding='utf-8') as f:
                leitor = csv.reader(f)
                fieldnames = next(leitor)
                
                f.seek(0)
                dict_leitor = csv.DictReader(f)
                pk_column_name = _get_pk_column(fieldnames)
                ids_existentes = []
                for linha in dict_leitor:
                    if pk_column_name in linha:
                        id_como_texto = linha[pk_column_name]
                        if id_como_texto.isdigit():
                            id_numerico = int(id_como_texto)
                            ids_existentes.append(id_numerico)
                if ids_existentes:
                    novo_id = max(ids_existentes) + 1
        except (FileNotFoundError, StopIteration):
            if colunas_usuario:
                fieldnames = colunas_usuario[:]
                tem_coluna_id = 'id' in fieldnames
                tem_coluna_com_sufixo_id = False
                for nome_coluna in fieldnames:
                    if nome_coluna.endswith('_id'):
                        tem_coluna_com_sufixo_id = True
                        break

                if not tem_coluna_id and not tem_coluna_com_sufixo_id:
                    fieldnames.insert(0, 'id')
                    fieldnames.insert(0, 'id')
            else:
                print("ERRO: INSERT em tabela nova sem especificar colunas.")
                return

        pk_column_name = _get_pk_column(fieldnames)
        if colunas_usuario:
            linha_para_inserir = dict(zip(colunas_usuario, valores_usuario))
        else:
            linha_para_inserir = dict(zip(fieldnames, valores_usuario))
        linha_para_inserir[pk_column_name] = novo_id
        
        file_exists = os.path.isfile(arquivo) and os.path.getsize(arquivo) > 0
        with open(arquivo, 'a', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if not file_exists:
                writer.writeheader()
            writer.writerow(linha_para_inserir)
        print("1 registro inserido.")

    except Exception as e:
        print(f'ERRO durante inserção: {e}')

def executar_update(consulta):
    # Executa UPDATE
    table_name, set_list, condicao = consulta['table'], consulta['set'], consulta['where']
    arquivo = get_csv_path(table_name)
    try:
        with open(arquivo, 'r', newline='', encoding='utf-8') as f:
            leitor = csv.DictReader(f)
            linhas = list(leitor)
            fieldnames = leitor.fieldnames
        
        for coluna_a_atualizar in set_list.keys():
            if coluna_a_atualizar not in fieldnames:
                print(f"ERRO: A coluna '{coluna_a_atualizar}' não existe na tabela '{table_name}'. Operação de UPDATE cancelada.")
                return

        atualizados = 0
        for linha in linhas:
            if condicao is None or verifica_condicao(linha, condicao):
                for coluna, novo_valor in set_list.items():
                    linha[coluna] = novo_valor
                atualizados += 1
        
        with open(arquivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(linhas)
        
        print(f"{atualizados} registro(s) atualizado(s).")
    except FileNotFoundError:
        print(f'ERRO: Tabela "{table_name}" não encontrada.')

def executar_delete(consulta):
    # Executa DELETE
    table_name, condicao = consulta['table'], consulta['where']
    arquivo = get_csv_path(table_name)
    try:
        with open(arquivo, 'r', newline='', encoding='utf-8') as f:
            linhas = list(csv.DictReader(f))
            if linhas:
                primeira_linha = linhas[0]
                fieldnames = primeira_linha.keys()
            else:
                fieldnames = []

        linhas_mantidas = []
        for linha in linhas:
            deve_ser_deletada = False
            if condicao is None:
                deve_ser_deletada = True
            elif verifica_condicao(linha, condicao):
                deve_ser_deletada = True

            if not deve_ser_deletada:
                linhas_mantidas.append(linha)
        removidos = len(linhas) - len(linhas_mantidas)
        
        with open(arquivo, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(linhas_mantidas)
            
        print(f"{removidos} registro(s) removido(s).")
    except FileNotFoundError:
        print(f'ERRO: Tabela "{table_name}" não encontrada.')


# Verifica se uma linha satisfaz uma condição (simples ou aninhada)
def verifica_condicao(linha, cond):
    if 'operator' in cond and cond['operator'] in ['AND', 'OR', 'NOT']:
        if cond['operator'] == 'AND':
            return verifica_condicao(linha, cond['left']) and verifica_condicao(linha, cond['right'])
        elif cond['operator'] == 'OR':
            return verifica_condicao(linha, cond['left']) or verifica_condicao(linha, cond['right'])
        elif cond['operator'] == 'NOT':
            return not verifica_condicao(linha, cond['condition'])
    else:
        operador, coluna, valor_condicao = cond['operator'], cond['column'], cond['value']
        if coluna not in linha: return False
        valor_linha = linha[coluna]

        if operador == 'LIKE':
            padrao_regex = str(valor_condicao).replace('%', '.*').replace('_', '.')
            return bool(re.match(f"^{padrao_regex}$", str(valor_linha), re.IGNORECASE))

        try:
            valor_linha_num, valor_condicao_num = float(valor_linha), float(valor_condicao)
            valor_linha, valor_condicao = valor_linha_num, valor_condicao_num
        except (ValueError, TypeError): pass

        if operador == '=': return valor_linha == valor_condicao
        elif operador == '!=': return valor_linha != valor_condicao
        elif operador == '>': return valor_linha > valor_condicao
        elif operador == '<': return valor_linha < valor_condicao
        elif operador == '>=': return valor_linha >= valor_condicao
        elif operador == '<=': return valor_linha <= valor_condicao
        return False

def ordenar_resultado(resultado, order_by):
    # Ordena as linhas com base nas colunas e direcoes especificadas
    for ordem in reversed(order_by):
        coluna, direcao = ordem['column'], ordem['direction']
        def sort_key(x):
            val = x.get(coluna, 0)
            try: return float(val)
            except (ValueError, TypeError): return val
        
        resultado.sort(key=sort_key, reverse=(direcao == 'DESC'))
    return resultado

def imprimir_resultado(linhas, colunas):
    # Imprime uma lista de resultados
    if not linhas:
        print("Nenhum resultado encontrado.")
        return
    if not colunas:
        colunas = list(linhas[0].keys())

    print(" | ".join(map(str, colunas)))
    
    largura_total_dos_nomes = 0
    for nome_coluna in colunas:
        largura_total_dos_nomes += len(str(nome_coluna))
        
    numero_de_colunas = len(colunas)
    if numero_de_colunas > 0:
        numero_de_separadores = numero_de_colunas - 1
    else:
        numero_de_separadores = 0

    largura_total_dos_separadores = 3 * numero_de_separadores
    comprimento_total = largura_total_dos_nomes + largura_total_dos_separadores
    linha_separadora = "-" * comprimento_total

    print(linha_separadora)
    
    for linha in linhas:
        valores_desta_linha = []
        for nome_da_coluna in colunas:
            valor_da_celula = linha.get(nome_da_coluna, '')
            valor_em_texto = str(valor_da_celula)
            valores_desta_linha.append(valor_em_texto)

        linha_formatada_para_impressao = " | ".join(valores_desta_linha)

        print(linha_formatada_para_impressao)
