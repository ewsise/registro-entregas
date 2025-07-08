from tkinter import *
from tkinter import ttk
from tkcalendar import DateEntry
import datetime
from functools import partial
import pandas as pd
import os

# Data sets
dataset_dia = {'NOME': [], 'QUANTIDADE': [], 'PAGAMENTO': [], 'DATA': []}
dataset_mes = {'DATA': [], 'ENTREGAS': [], 'PARADAS': [], 'FATURAMENTO': []}
dataset_ano = {'MÊS': [], 'ENTREGAS': [], 'PARADAS': [], 'FATURAMENTO': []}

dataset_dia = pd.DataFrame(dataset_dia)
dataset_mes = pd.DataFrame(dataset_mes)
dataset_ano = pd.DataFrame(dataset_ano)

# Configurações iniciais
valor_pacote = 50
data_dir = "data"
os.makedirs(data_dir, exist_ok=True)

# Carregar ou criar o arquivo CSV
csv_path = os.path.join(data_dir, "data.csv")
if os.path.exists(csv_path):
    data_frame = pd.read_csv(csv_path, parse_dates=["DATA"], dayfirst=True)
else:
    data_frame = pd.DataFrame(columns=["NOME", "QUANTIDADE", "PAGAMENTO", "DATA"])

data_frame['DATA'] = pd.to_datetime(data_frame['DATA'], errors='coerce').dt.normalize()
hoje = pd.Timestamp.today().normalize()

# Funções
def update_dia_amostra():
    datas = sorted(list(data_frame.groupby('DATA').groups.keys()), reverse=True)
    index = index_dia.get()
    index_dia.set(index)
    dia_visivel.set((datas[index].strftime("%Y-%m-%d")))

def update_mes_visivel():
    datas = list(data_frame.groupby('DATA').groups.keys().month)
    idx = index_mes.get()
    index_mes.set(idx)
    mes_visivel.set(str(datas[idx]))

def update_outputs():
    amostra = selecao_visualizacao_data.get()
    output_widgets = [output_dia, output_mes, output_ano]
    alvo = output_widgets[amostra]

    if data_frame.empty:
        alvo.config(state="normal")
        alvo.delete("1.0", END)
        alvo.insert(END, "Sem dados.")
        alvo.config(state="disabled")
        return

    df = data_frame.copy()
    output = pd.DataFrame()

    if amostra == 0:
        dia = dia_visivel.get()
        try:
            dia_dt = pd.to_datetime(dia).normalize()
            output = df[df["DATA"].dt.normalize() == dia_dt]
            if e_visivel.get():
                output = output.copy()
                output["QUANTIDADE"] = "***"
        except Exception:
            output = pd.DataFrame()
    elif amostra == 1:
        df["MÊS"] = df["DATA"].dt.date
        output = df.groupby("MÊS").agg(
            ENTREGAS=("QUANTIDADE", "sum"),
            PARADAS=("NOME", "count"),
            FATURAMENTO=("QUANTIDADE", lambda x: x.sum() * valor_pacote)
        ).reset_index()
        if e_visivel.get():
            output["FATURAMENTO"] = "***"
    elif amostra == 2:
        df["ANO"] = df["DATA"].dt.to_period("M")
        output = df.groupby("ANO").agg(
            ENTREGAS=("QUANTIDADE", "sum"),
            PARADAS=("NOME", "count"),
            FATURAMENTO=("QUANTIDADE", lambda x: x.sum() * valor_pacote)
        ).reset_index()
        if e_visivel.get():
            output["FATURAMENTO"] = "***"

    # Atualiza texto
    alvo.config(state="normal")
    alvo.delete("1.0", END)
    alvo.insert(END, output.to_string(index=False))
    alvo.config(state="disabled")
    organizar_datas()
    
def organizar_datas():
    global data_frame
    global dataset_dia, dataset_mes

    dia = dia_visivel.get()
    n_entregas = 0
    n_paradas = 0

    for valor, grupo in data_frame.groupby('DATA'):
        n_paradas = len(grupo)
        n_entregas = grupo['QUANTIDADE'].sum()

        novo_segmento = {
            'DATA': valor,
            'ENTREGAS': n_entregas,
            'PARADAS': n_paradas,
            'FATURAMENTO': n_entregas * 50
        }
        
        dataset_mes = pd.concat([dataset_mes, pd.DataFrame([novo_segmento])], ignore_index=True)
        dia = pd.to_datetime(dia_visivel.get()).normalize()
        dataset_dia = data_frame[data_frame['DATA'] == dia]

def adicionar():
    global data_frame
    global hoje

    nome = nome_cliente.get()
    pag = forma_pagamento.get()
    qtd = quantidade_pacote.get()

    if calendario.get_date():
        dia_alvo = pd.to_datetime(calendario.get_date()).normalize()
    else:
        dia_alvo = hoje

    novo = {"NOME": nome, "QUANTIDADE": qtd, "PAGAMENTO": pag, "DATA": dia_alvo}
    data_frame = pd.concat([data_frame, pd.DataFrame([novo])], ignore_index=True)
    #print(data_frame)
    update_outputs()
    salvar()

def salvar():
    dataset_dia.to_csv(f"{DATA_DIR}/daily.csv", index=False)
    dataset_mes.to_csv(f"{DATA_DIR}/monthly.csv", index=False)
    dataset_ano.to_csv(f"{DATA_DIR}/yearly.csv", index=False)
    data_frame.sort_values(by="DATA", ascending=False).to_csv(f"{DATA_DIR}/data.csv", index=False)

def trocar_visualizacao():
    frame_dia.grid_remove()
    frame_mes.grid_remove()
    frame_ano.grid_remove()

    amostra = selecao_visualizacao_data.get()

    if amostra == 0:
        frame_dia.grid()
    elif amostra == 1:
        frame_mes.grid(row=2, column=0, columnspan=3, sticky="nsew")
    elif amostra == 2:
        frame_ano.grid(row=2, column=0, columnspan=3, sticky="nsew")

    update_outputs()

def browse_datas(direction):
    global data_frame

    group = list(data_frame.groupby('DATA').groups.keys())
    index = index_dia.get()

    if direction == 0 and index + 1 < len(group):
        index_dia.set(index + 1)
        dia_visivel.set(str(group[index + 1]))
    elif direction == 1 and index - 1 >= 0:
        index_dia.set(index - 1)
        dia_visivel.set(str(group[index - 1]))

    update_dia_amostra()
    #update_mes_visivel()
    update_outputs()

### MAIN ###
root = Tk()
root.title("Registro de Entregas")

main = ttk.Frame(root, padding=20)
main.grid(row=0, column=0, sticky="nsew")
root.columnconfigure(0, weight=1)
root.rowconfigure(0, weight=1)

# Opções de visualização
e_visivel = BooleanVar(value=False)
ttk.Checkbutton(main, text='esconde/mostra', variable=e_visivel, command=update_outputs).grid(row=0, column=0, sticky="w")

selecao_visualizacao_data = IntVar(value=0)
frame_selecao = ttk.Frame(main, padding=10)
frame_selecao.grid(row=0, column=1, columnspan=2, sticky="e")

ttk.Radiobutton(frame_selecao, text="diário", variable=selecao_visualizacao_data, value=0, command=trocar_visualizacao).grid(row=0, column=0)
ttk.Radiobutton(frame_selecao, text="mensal", variable=selecao_visualizacao_data, value=1, command=trocar_visualizacao).grid(row=0, column=1)
ttk.Radiobutton(frame_selecao, text="anual", variable=selecao_visualizacao_data, value=2, command=trocar_visualizacao).grid(row=0, column=2)
    
# Navegação de datas
index_dia = IntVar(value=0)
frame_navegacao = ttk.Frame(main)
frame_navegacao.grid(row=1, column=0, columnspan=3, pady=5)

dia_visivel = StringVar(value=hoje.strftime("%Y-%m-%d"))
ttk.Button(frame_navegacao, text='<', command=partial(browse_datas, 0)).grid(row=0, column=0)
ttk.Label(frame_navegacao, textvariable=dia_visivel).grid(row=0, column=1, sticky="w")
ttk.Button(frame_navegacao, text='>', command=partial(browse_datas, 1)).grid(row=0, column=2)

### Frame Diário ###
frame_dia = ttk.Frame(main, padding=10)
frame_dia.grid(row=2, column=0, columnspan=3, sticky="nsew")

frame_dia.columnconfigure(2, weight=1)

output_dia = Text(frame_dia, height=10, width=60, font=("Courier", 10), state='disabled')
output_dia.grid(row=2, column=0, columnspan=2, pady=5, sticky="nsew")

# Entrada de cliente
ttk.Label(frame_dia, text="Nome do Cliente:").grid(row=3, column=0, sticky="w")
nome_cliente = StringVar()
ttk.Entry(frame_dia, textvariable=nome_cliente).grid(row=3, column=1, sticky="ew", pady=2)

quantidade_pacote = IntVar(value=1)
ttk.Label(frame_dia, text="Quantidade de Pacotes:").grid(row=4, column=0, sticky="w")
ttk.Combobox(frame_dia, textvariable=quantidade_pacote, values=list(range(1, 16)), state='readonly').grid(row=4, column=1, sticky="ew", pady=2)

opcoes_pagamento = ['PIX', 'DINHEIRO']
forma_pagamento = StringVar(value=opcoes_pagamento[0])
ttk.Label(frame_dia, text="Método de Pagamento:").grid(row=5, column=0, sticky="w")
ttk.Combobox(frame_dia, textvariable=forma_pagamento, values=opcoes_pagamento, state='readonly').grid(row=5, column=1, sticky="ew", pady=2)

dia_selecionado = StringVar(value=hoje)
ttk.Label(frame_dia, text="Data:").grid(row=6, column=0, sticky="w")
calendario = DateEntry(frame_dia, date_pattern = 'dd/mm/yyyy')
calendario.grid(row=6, column=1, sticky="ew", pady=2)

ttk.Button(frame_dia, text='Registrar', command=adicionar).grid(row=7, column=0, columnspan=2, pady=10)

### Frame Mensal ###
frame_mes = ttk.Frame(main)

output_mes = Text(frame_mes, height=10, width=60, font=("Courier", 10), state='disabled')
output_mes.pack()

mes_visivel = StringVar(value=hoje.month)
index_mes = IntVar(value=0)

### Frame anual ###
frame_ano = ttk.Frame(main)

output_ano = Text(frame_ano, height=10, width=60, font=("Courier", 10), state='disabled')
output_ano.pack()

### Mainloop ###

trocar_visualizacao()
organizar_datas()
update_dia_amostra()
update_outputs()
print(data_frame)

root.mainloop()
