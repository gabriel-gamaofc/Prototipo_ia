import nltk
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import mysql.connector
import tkinter as tk
from tkinter import messagebox

nltk.download('punkt')

# Configurações de conexão com o servidor MySQL
config = {
     'user': 'root',
    'password': '',
    'host': 'localhost',  # Endereço do servidor MySQL
    'database': 'i_a',
    'raise_on_warnings': True
}

# Função para conectar ao servidor MySQL
def conectar_banco_de_dados():
    try:
        conn = mysql.connector.connect(**config)
        return conn
    except mysql.connector.Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        return None




# Função para inserir uma nova pergunta e resposta no banco de dados com categoria
def inserir_pergunta_resposta(conn, pergunta, resposta, categoria):
    try:
        cursor = conn.cursor()
        # Verificar se a categoria já existe no banco de dados
        cursor.execute("SELECT id FROM categorias WHERE nome = %s", (categoria,))
        categoria_id = cursor.fetchone()
        if not categoria_id:
            # Se a categoria não existe, insira-a na tabela de categorias
            cursor.execute("INSERT INTO categorias (nome) VALUES (%s)", (categoria,))
            conn.commit()
            categoria_id = cursor.lastrowid
        else:
            categoria_id = categoria_id[0]
        # Inserir a nova pergunta, resposta e categoria na tabela de perguntas_respostas
        cursor.execute("INSERT INTO perguntas_respostas (pergunta, resposta, categoria_id) VALUES (%s, %s, %s)", (pergunta, resposta, categoria_id))
        conn.commit()
        print("Pergunta e resposta inseridas com sucesso no banco de dados.")
    except mysql.connector.Error as err:
        print(f"Erro ao inserir pergunta e resposta no banco de dados: {err}")

# Função para lidar com a ação do botão "Enviar"
def enviar_pergunta():
    pergunta_atual = pergunta_entry.get()

    # Verificar se pelo menos uma pergunta não está vazia após o pré-processamento
    if len(pergunta_atual) > 0:
        # Vetorização TF-IDF para a pergunta atual
        tfidf_vectorizer = TfidfVectorizer()

        # Consulta ao banco de dados para obter as perguntas de referência
        cursor = conn.cursor()
        select_query = "SELECT pergunta, resposta, categorias.nome FROM perguntas_respostas JOIN categorias ON perguntas_respostas.categoria_id = categorias.id"
        cursor.execute(select_query)
        rows = cursor.fetchall()

        perguntas_respostas = [(row[0], row[1]) for row in rows]
        categorias = [row[2] for row in rows]

        # Extrair apenas as perguntas de referência da lista de tuplas
        perguntas_referencia = [pergunta for pergunta, _ in perguntas_respostas]

        tfidf_matrix_referencia = tfidf_vectorizer.fit_transform(perguntas_referencia)

        tfidf_matrix_atual = tfidf_vectorizer.transform([pergunta_atual])

        similaridades = cosine_similarity(tfidf_matrix_atual, tfidf_matrix_referencia)
        limite_similaridade = 0.15  # Reduzido para um valor menor

        # Identificar a categoria da pergunta atual
        categorias_identificadas = set()
        for i, similaridade in enumerate(similaridades[0]):
            if similaridade >= limite_similaridade:
                categorias_identificadas.add(categorias[i])

        categorias_label.config(text=f"Categorias associadas: {', '.join(categorias_identificadas)}")
        resposta_label.config(text=f"Resposta: {perguntas_respostas[categorias.index(list(categorias_identificadas)[0])][1]}")

        # Se a pergunta não estiver associada a nenhuma categoria, pergunte se deseja adicioná-la ao banco de dados
        if not categorias_identificadas:
            resposta_adicionar = messagebox.askquestion("Adicionar Pergunta", "Deseja adicionar esta pergunta ao banco de dados?")
            if resposta_adicionar == "yes":
                resposta_nova = resposta_entry.get()
                categoria_nova = categoria_entry.get()
                # Inserir a nova pergunta, resposta e categoria no banco de dados
                inserir_pergunta_resposta(conn, pergunta_atual, resposta_nova, categoria_nova)

# Inicializar a interface gráfica
root = tk.Tk()
root.title("Sistema de Perguntas e Categorias")

# Rótulo e campo de entrada para a pergunta
pergunta_label = tk.Label(root, text="Digite a pergunta:")
pergunta_label.pack()
pergunta_entry = tk.Entry(root)
pergunta_entry.pack()

# Rótulo para exibir as categorias identificadas
categorias_label = tk.Label(root, text="Categorias associadas:")
categorias_label.pack()

# Rótulo para exibir a resposta
resposta_label = tk.Label(root, text="Resposta:")
resposta_label.pack()

# Conectar-se ao banco de dados
conn = conectar_banco_de_dados()


# Iniciar a interface gráfica
root.mainloop()
