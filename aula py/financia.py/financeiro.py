import csv
from flask import Flask, render_template, request, send_file, redirect, url_for
from fpdf import FPDF
import os

# Nome do arquivo para armazenar os dados
FILE_NAME = "financeiro.csv"
CATEGORIES_FILE = "categorias.csv"  # Novo arquivo para armazenar categorias

app = Flask(__name__)

def criar_arquivos():
    """Cria os arquivos CSV se eles não existirem."""
    try:
        with open(FILE_NAME, "x", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Tipo", "Valor", "Descrição", "Categoria"])
    except FileExistsError:
        pass

    try:
        with open(CATEGORIES_FILE, "x", newline="", encoding="utf-8") as file:
            writer = csv.writer(file)
            writer.writerow(["Categoria"])  # Adiciona o cabeçalho do arquivo de categorias
    except FileExistsError:
        pass

def definir_ganho(valor, investimento_perc):
    """Define o saldo inicial com base no ganho mensal e já retira o investimento."""
    investimento_valor = (investimento_perc / 100) * valor
    saldo_inicial = valor - investimento_valor
    with open(FILE_NAME, "w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Tipo", "Valor", "Descrição", "Categoria"])
        writer.writerow(["Ganho", valor, "Ganho Mensal", "Receita"])
        writer.writerow(["Investimento", investimento_valor, "Investimento Inicial", "Investimentos"])
    return saldo_inicial

def adicionar_gasto(valor, descricao, categoria):
    """Adiciona um novo gasto em uma categoria específica."""
    with open(FILE_NAME, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Gasto", valor, descricao, categoria])

def calcular_saldo():
    """Calcula e exibe o saldo disponível e separa os gastos por categoria."""
    saldo = 0
    registros = []
    categorias = carregar_categorias()  # Carrega as categorias salvas
    try:
        with open(FILE_NAME, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Pular cabeçalho
            for row in reader:
                tipo, valor, descricao, categoria = row
                valor = float(valor)
                registros.append([tipo, f"R$ {valor:.2f}", descricao, categoria])
                if tipo == "Ganho":
                    saldo = valor  # O ganho é definido uma única vez
                elif tipo == "Gasto" or tipo == "Investimento":
                    saldo -= valor
    except FileNotFoundError:
        print("Arquivo de dados não encontrado.")
    
    return saldo, registros, categorias

def adicionar_categoria(nova_categoria):
    """Adiciona uma nova categoria ao arquivo de categorias."""
    with open(CATEGORIES_FILE, "a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([nova_categoria])

def carregar_categorias():
    """Carrega as categorias do arquivo CSV."""
    categorias = []
    try:
        with open(CATEGORIES_FILE, "r", encoding="utf-8") as file:
            reader = csv.reader(file)
            next(reader)  # Pular cabeçalho
            for row in reader:
                categorias.append(row[0])
    except FileNotFoundError:
        pass
    return categorias

@app.route('/')
def index():
    saldo, registros, categorias = calcular_saldo()
    mostrar_ganho = True if saldo == 0 else False
    return render_template('index.html', saldo=saldo, registros=registros, categorias=categorias, mostrar_ganho=mostrar_ganho)

@app.route('/definir_ganho', methods=['POST'])
def definir_ganho_route():
    """Define o ganho mensal e o investimento."""
    valor = float(request.form['valor'])
    investimento_perc = float(request.form['investimento_perc'])
    saldo_inicial = definir_ganho(valor, investimento_perc)
    return redirect(url_for('index'))

@app.route('/adicionar_gasto', methods=['POST'])
def adicionar_gasto_route():
    """Adiciona um novo gasto."""
    valor = float(request.form['valor'])
    descricao = request.form['descricao']
    categoria = request.form['categoria']
    adicionar_gasto(valor, descricao, categoria)
    return redirect(url_for('index'))

@app.route('/adicionar_categoria', methods=['POST'])
def adicionar_categoria_route():
    """Adiciona uma nova categoria."""
    nova_categoria = request.form['nova_categoria']
    adicionar_categoria(nova_categoria)
    return redirect(url_for('index'))

@app.route('/reset_dados', methods=['POST'])
def reset_dados():
    """Reseta os dados, removendo o arquivo CSV e criando um novo vazio."""
    if os.path.exists(FILE_NAME):
        os.remove(FILE_NAME)
    if os.path.exists(CATEGORIES_FILE):
        os.remove(CATEGORIES_FILE)
    criar_arquivos()
    return redirect(url_for('index'))

@app.route('/download_pdf')
def download_pdf():
    """Gera e permite o download de um PDF com as transações e resumo."""
    saldo, registros, categorias = calcular_saldo()

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)

    # Título
    pdf.cell(200, 10, txt="Relatório Financeiro", ln=True, align="C")

    # Saldo atual
    pdf.cell(200, 10, txt=f"Saldo Atual: R$ {saldo:.2f}", ln=True, align="L")

    # Histórico de Transações
    pdf.cell(200, 10, txt="Histórico de Transações:", ln=True, align="L")
    for tipo, valor, descricao, categoria in registros:
        pdf.cell(200, 10, txt=f"{tipo}: {descricao} - {valor} ({categoria})", ln=True, align="L")

    # Resumo por Categoria
    pdf.cell(200, 10, txt="Resumo por Categoria:", ln=True, align="L")
    for categoria in categorias:
        pdf.cell(200, 10, txt=f"{categoria}", ln=True, align="L")

    pdf_output = "relatorio_financeiro.pdf"
    pdf.output(pdf_output)

    return send_file(pdf_output, as_attachment=True)

if __name__ == "__main__":
    criar_arquivos()
    app.run(debug=True)
