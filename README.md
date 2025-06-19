# SQL CSV Parser - Interpretador SQL para Ficheiros CSV

## Sobre o Projeto

Este projeto é um interpretador de comandos SQL escrito em Python, utilizando as bibliotecas `ply` (para análise léxica e sintática) e `csv`. Ele permite executar uma vasta gama de consultas SQL diretamente em ficheiros de dados no formato `.csv`, tratando cada ficheiro como se fosse uma tabela de um banco de dados relacional.

O objetivo é fornecer uma ferramenta leve e poderosa para análise e manipulação de dados em CSV sem a necessidade de um sistema de gestão de banco de dados completo.

---

## Como Funciona o Sistema

O interpretador processa uma consulta SQL em três etapas principais, cada uma gerida por um módulo específico:

1.  **Análise Léxica (`lexer.py`)**
    * **Função:** Recebe a string de consulta SQL e a "quebra" em pequenos pedaços chamados *tokens*.
    * **Exemplo:** A consulta `SELECT nome FROM usuarios` é transformada numa sequência de tokens como `[SELECT, IDENTIFIER('nome'), FROM, IDENTIFIER('usuarios')]`. Ele reconhece palavras-chave, nomes, operadores e valores.

2.  **Análise Sintática (`parser_sql.py`)**
    * **Função:** Recebe a lista de tokens do lexer e verifica se eles formam um comando SQL válido, de acordo com uma gramática que definimos.
    * **Resultado:** Se a sintaxe estiver correta, o parser constrói uma estrutura de dados (uma Árvore de Sintaxe Abstrata, ou AST), que é um dicionário Python organizado representando a consulta. Por exemplo, ele sabe qual é a tabela, quais são as colunas e qual é a condição `WHERE`. Se a sintaxe estiver errada, ele reporta um erro.

3.  **Execução (`executor.py`)**
    * **Função:** Este é o "coração" do sistema. Ele recebe a estrutura de dados do parser e executa a lógica necessária para produzir o resultado.
    * **Processo:** Ele abre os ficheiros `.csv`, lê os dados para a memória, aplica os filtros (`WHERE`), realiza as junções (`JOIN`), agrupa os dados (`GROUP BY`), calcula as agregações (`COUNT`, `SUM`, etc.) e, finalmente, formata e imprime o resultado no ecrã.

Este fluxo garante que o código seja modular e organizado: cada parte tem uma responsabilidade clara e distinta.

---

## Funcionalidades Implementadas

O interpretador suporta um subconjunto robusto da linguagem SQL:

* **Seleção e Consulta (`SELECT`)**: `SELECT`, `FROM`, `WHERE`, `ORDER BY`, `LIMIT`, `DISTINCT`.
* **Junção de Tabelas (`JOIN`)**: `INNER JOIN` (palavra-chave `JOIN`) e `LEFT JOIN`.
* **Agregação e Agrupamento**: `GROUP BY` com as funções `COUNT(*)`, `COUNT(coluna)`, `SUM(coluna)`, `AVG(coluna)`.
* **Pesquisa de Padrões**: Operador `LIKE` com os caracteres especiais `%` e `_`.
* **Manipulação de Dados (DML)**: `INSERT`, `UPDATE` e `DELETE`.
* **Funcionalidades Automáticas**: Geração de IDs únicos para `INSERT` e validação de colunas para `UPDATE`.

---

## Como Utilizar

### Pré-requisitos
-   Python 3.x
-   Biblioteca `ply`

### Instalação
1.  Certifique-se de que tem o Python instalado.
2.  Instale a biblioteca `ply` através do pip:
    ```bash
    pip install ply
    ```

### Execução
1.  Clone ou descarregue os ficheiros do projeto para um diretório local.
2.  Coloque os ficheiros `.csv` que deseja consultar no mesmo diretório.
3.  Execute o ficheiro `main.py` para correr a suite de testes pré-definida:
    ```bash
    python main.py
    ```

---

## Exemplos de Uso e Teste

Use as consultas abaixo para testar as funcionalidades do sistema e verificar se os resultados correspondem ao esperado.

### Dados de Teste
* **`usuarios.csv`**: `id,nome,idade,email`
* **`pedidos.csv`**: `pedido_id,id_usuario,produto,valor`

### Consultas de Teste

1.  **Seleção Simples com `WHERE` e `ORDER BY`**
    * **Comando:** `SELECT nome, idade FROM usuarios WHERE idade > 20 ORDER BY idade DESC`
    * **Resultado Esperado:**
        ```
        nome | idade
        ------------
        Ana | 40
        Carlos | 31
        Carlos | 31
        João | 25
        Ricardo | 25
        ```

2.  **`INNER JOIN`**
    * **Comando:** `SELECT nome, produto, valor FROM usuarios JOIN pedidos ON id = id_usuario`
    * **Resultado Esperado:**
        ```
        nome | produto | valor
        -----------------------
        João | Mouse | 80
        Maria | Notebook | 3500
        Maria | Teclado | 150
        Carlos | Cadeira | 800
        Ricardo | Monitor | 1200
        ```

3.  **`LEFT JOIN`**
    * **Comando:** `SELECT nome, produto FROM usuarios LEFT JOIN pedidos ON id = id_usuario`
    * **Resultado Esperado:**
        ```
        nome | produto
        ---------------
        João | Mouse
        Maria | Notebook
        Maria | Teclado
        Carlos | Cadeira
        Ricardo | Monitor
        Carlos | 
        Ana | 
        ```

4.  **`GROUP BY` com `COUNT`**
    * **Comando:** `SELECT idade, COUNT(*) FROM usuarios GROUP BY idade ORDER BY idade`
    * **Resultado Esperado:**
        ```
        idade | COUNT(*)
        ----------------
        19 | 1
        25 | 2
        31 | 2
        40 | 1
        ```

5.  **`GROUP BY` com `SUM`**
    * **Comando:** `SELECT id_usuario, SUM(valor) FROM pedidos GROUP BY id_usuario`
    * **Resultado Esperado:** (A ordem pode variar)
        ```
        id_usuario | SUM(valor)
        -----------------------
        2 | 3650.0
        1 | 80.0
        4 | 1200.0
        3 | 800.0
        ```

6.  **`INSERT`**
    * **Comando:** `INSERT INTO usuarios (nome, idade, email) VALUES ('Beatriz', 29, 'bia@email.com')`
    * **Resultado Esperado:** `1 registro inserido.` (Uma nova linha com id=7 deve aparecer no `usuarios.csv`)

7.  **`UPDATE`**
    * **Comando:** `UPDATE usuarios SET idade = 26 WHERE nome = 'Ricardo'`
    * **Resultado Esperado:** `1 registro(s) atualizado(s).`

8.  **`DELETE`**
    * **Comando:** `DELETE FROM usuarios WHERE nome = 'Beatriz'`
    * **Resultado Esperado:** `1 registro(s) removido(s).`

---

## Construindo as Consultas SQL

* **Palavras-chave (Keywords):** `SELECT`, `FROM`, etc., não são sensíveis a maiúsculas/minúsculas.
* **Nomes de Tabelas e Colunas:** Devem ser escritos diretamente, sem aspas (`usuarios`, `id_usuario`).
* **Valores de Texto (Strings):** Devem estar **sempre** entre aspas simples (`'`) ou duplas (`"`). Ex: `WHERE nome = 'Carlos'`.
* **Valores Numéricos:** Devem ser escritos diretamente, sem aspas. Ex: `WHERE idade > 25`.

---

## Limitações e Considerações Importantes

* **Geração de IDs:** A funcionalidade de `INSERT` automático pressupõe que a coluna da chave primária (identificada por `id` ou por um nome que termine em `_id`) contém apenas valores numéricos inteiros.
* **Performance:** Para ficheiros CSV muito grandes, as operações podem ser lentas, pois todos os dados são carregados para a memória.