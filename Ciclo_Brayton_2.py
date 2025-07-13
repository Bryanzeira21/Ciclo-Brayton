import tkinter as tk
from tkinter import ttk
from tkinter import messagebox  # <-- Adicione esta linha
from tkinter import PhotoImage
import matplotlib
matplotlib.use("Agg")         # backend sem janela externa
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
import platform

nome_pc = platform.node()

# -------------------------------------------------------------------
#  CONSTANTES BÁSICAS
# -------------------------------------------------------------------
cp = 1.005        # kJ/kg·K
cv = 0.717         # kJ/kg·K
k  = 1.4         # razão cp/cv
R  = 0.287       # kJ/kg·K  (gás ideal – ar)

# -------------------------------------------------------------------
#  FUNÇÕES TERMODINÂMICAS AUXILIARES
# -------------------------------------------------------------------
def isentropic_T(T1, P1, P2, gamma):
    """T2 para compressão/expansão isentrópica (P em Pa, T em K)."""
    return T1 * (P2 / P1) ** ((gamma - 1) / gamma)

def specific_volume(P, T):
    """v (m³/kg) para ar ideal — P em Pa, T em K."""
    return (R * 1000) * T / P      # R em kJ → ×1000 para J

# -------------------------------------------------------------------
#  FUNÇÃO PRINCIPAL DE CÁLCULO + PLOT
# -------------------------------------------------------------------
def calcular():
    try:
        # --- 1. Ler entradas  ------------------------------------
        P1 = float(entry_p1.get()) * 1e3          # kPa → Pa
        T1 = float(entry_t1.get())
        RP = float(entry_rp.get())                # razão de pressões P2/P1
        W  = float(entry_w.get()) * 1e6           # MW → W
        T3 = float(entry_t4.get())                # Tmax (na turbina)
        Nreg = float(entry_nreg.get()) 
        gamma = k

        # --- 2. Pontos do ciclo  ---------------------------------
        # 1 → 2 (compressão isentrópica)
        P2 = P1 * RP
        T2 = isentropic_T(T1, P1, P2, gamma)

        # 2 → 3 (adição de calor isobárica)
        P3 = P2
        # cp em J/kg·K  (multiplica por 1000)
        q_in = cp * (T3 - T2) / 1000.0            # kJ/kg

        # 3 → 4 (expansão isentrópica até P1)
        P4 = P1
        T4 = isentropic_T(T3, P3, P4, gamma)

        # --- 3. Cálculos de trabalho e eficiência ---------------
        Wc  = cp * (T2 - T1)                      # kJ/kg
        Wt  = cp * (T3 - T4)                      # kJ/kg
        Wliq = Wt - Wc
        m_dot = W / (Wliq * 1e3)                 # kg/s    (Wliq→J/kg)
        eficiencia = Wliq / Wt

        # Só calcula T2l se Nreg != 1
        if Nreg != 1:
            T2l = T2 + (T4 - T2) * Nreg  # Temperatura após regenerador'
        else:
            T2l = None  # Não existe T2l para Nreg == 1

        # --- 4. Resultados numéricos na textbox -----------------
        resultado = (
            f"P2:  {P2/1_000:.2f} kPa\n"
            f"T2:  {T2:.2f} K\n"
            f"T5:  {T2:.2f} K\n"
            f"P3:  {P3/1_000:.2f} kPa\n"
            f"T2':  {T2l if T2l is not None else '---'} kPa\n"
            f"Wc:  {Wc:.2f} kJ/kg\n"
            f"T4:  {T4:.2f} K\n"
            f"Wt:  {Wt:.2f} kJ/kg\n"
            f"Wlíq: {Wliq:.2f} kJ/kg\n"
            f"ṁ:   {m_dot:.2f} kg/s\n"
            f"η:   {eficiencia*100:.2f} %"
        )
        resultado_txt.config(state="normal")
        resultado_txt.delete("1.0", tk.END)
        resultado_txt.insert(tk.END, resultado)
        resultado_txt.config(state="disabled")

        # --- 5. Volume específico nos pontos --------------------
        v1 = specific_volume(P1, T1)
        v2 = specific_volume(P2, T2)
        v3 = specific_volume(P3, T3)
        v4 = specific_volume(P4, T4)
        if T2l is not None:
            v2l = specific_volume(P2, T2l)  # Após regenerador

        # --- 6. Entropia nos pontos do ciclo --------------------
        def delta_s(Ta, Pa, Tb, Pb):
            # Δs = cp*ln(Tb/Ta) - R*ln(Pb/Pa)  (kJ/kg·K)
            return cp * np.log(Tb / Ta) - R * np.log(Pb / Pa)

        s1 = 0  # referência
        s2 = s1 + delta_s(T1, P1, T2, P2)
        s3_prov = s2 + delta_s(T2, P2, T3, P3)
        if T2l is not None:
            s2l = s2 + ((T4 - T1) / (T3 - T1)) * (s3_prov - s2)
            s3 = s2l + delta_s(T2l, P2, T3, P3)
        else:
            s2l = None
            s3 = s2 + delta_s(T2, P2, T3, P3)
        s4 = s3 + delta_s(T3, P3, T4, P4)

        # --- 7. Atualizar gráfico P×V com cores por etapa -------
        ax_pv.clear()
        etapas_pv = [
            ([v1, v2], [P1/1e3, P2/1e3], 'gold', 'Compressão (1→2)'),
        ]
        if T2l is not None:
            etapas_pv.append(([v2, v2l], [P2/1e3, P2/1e3], 'orange', 'Regeneração (2→2\')'))
            etapas_pv.append(([v2l, v3], [P2/1e3, P3/1e3], 'red', 'Adição de calor (2\'→3)'))
        else:
            etapas_pv.append(([v2, v3], [P2/1e3, P3/1e3], 'red', 'Adição de calor (2→3)'))
        etapas_pv += [
            ([v3, v4], [P3/1e3, P4/1e3], 'limegreen', 'Expansão (3→4)'),
            ([v4, v1], [P4/1e3, P1/1e3], 'deepskyblue', 'Rejeição de calor (4→1)'),
        ]
        for x, y, cor, rotulo in etapas_pv:
            ax_pv.plot(x, y, '-o', color=cor, label=rotulo, linewidth=2, markersize=6)
        ax_pv.set_title("Ciclo Brayton – P × V")
        ax_pv.set_xlabel("Volume específico  (m³/kg)")
        ax_pv.set_ylabel("Pressão  (kPa)")
        ax_pv.grid(True)
        ax_pv.legend(loc='best', fontsize=8)
        fig_pv.tight_layout()
        canvas_pv.draw()

        # --- 8. Atualizar gráfico T×S com cores por etapa -------
        ax_ts.clear()
        etapas_ts = [
            ([s1, s2], [T1, T2], 'gold', 'Compressão (1→2)'),
        ]
        if T2l is not None:
            etapas_ts.append(([s2, s2l], [T2, T2l], 'orange', 'Regeneração (2→2\')'))
            etapas_ts.append(([s2l, s3], [T2l, T3], 'red', 'Adição de calor (2\'→3)'))
        else:
            etapas_ts.append(([s2, s3], [T2, T3], 'red', 'Adição de calor (2→3)'))
        etapas_ts += [
            ([s3, s4], [T3, T4], 'limegreen', 'Expansão (3→4)'),
            ([s4, s1], [T4, T1], 'deepskyblue', 'Rejeição de calor (4→1)'),
        ]
        for x, y, cor, rotulo in etapas_ts:
            ax_ts.plot(x, y, '-o', color=cor, label=rotulo, linewidth=2, markersize=6)
        ax_ts.set_title("Ciclo Brayton – T × S")
        ax_ts.set_xlabel("Entropia específica (kJ/kg·K)")
        ax_ts.set_ylabel("Temperatura (K)")
        ax_ts.grid(True)
        ax_ts.legend(loc='best', fontsize=8)
        fig_ts.tight_layout()
        canvas_ts.draw()

    except Exception as e:
        resultado_txt.config(state="normal")
        resultado_txt.delete("1.0", tk.END)
        resultado_txt.insert(tk.END, f"Erro: {e}")
        resultado_txt.config(state="disabled")

# -------------------------------------------------------------------
#  FUNÇÃO PARA LIMPAR CAMPOS
# -------------------------------------------------------------------
def limpar_campos():
    entry_p1.delete(0, tk.END)
    entry_t1.delete(0, tk.END)
    entry_rp.delete(0, tk.END)
    entry_w.delete(0, tk.END)
    entry_t4.delete(0, tk.END)
    entry_nreg.delete(0, tk.END)
    # Opcional: limpar resultados também
    resultado_txt.config(state="normal")
    resultado_txt.delete("1.0", tk.END)
    resultado_txt.config(state="disabled")

# ---------------- Função para mostrar créditos -----------------
def mostrar_creditos():
    # Cria uma janela filha (Toplevel)
    win = tk.Toplevel(janela)
    win.title("Créditos")
    win.configure(bg="white")  # cor de fundo da janela

    # Centraliza a janela em relação à janela principal
    win.geometry("+%d+%d" % (janela.winfo_rootx() + 100, janela.winfo_rooty() + 60))

    # Frame branco para destacar a mensagem
    frame = tk.Frame(win, bg="white", bd=2, relief="groove")
    frame.pack(padx=20, pady=20)

    # Mensagem de créditos com os nomes
    label = tk.Label(
        frame,
        text=(
            "Desenvolvido por:\n\n"
            "BRYAN TEIXEIRA CARIDADE\n"
            "GUSTAVO FERNANDES DOS SANTOS\n"
            "IURY CRISTIAN LIMA MAIA\n"
            "KAYNÃ DE PAIVA ALVES CURY FRANCO\n"
            "LETÍCIA ARRUDA E ANDRADE\n"
            "LUCAS JOSÉ ALVES IZAIAS\n"
            "LUCAS LUIZ PINTO FERREIRA\n"
            "LUIS GUSTAVO ARAUJO CABALEIRO\n"
            "LUIZ GUSTAVO DA SILVA PEREIRA\n"
            "MARIANGELA PEREIRA DA SILVA\n"
            "VITÓRIA RODRIGUES MAIA MACEDO\n\n"
            "Disciplina: Máquinas Térmicas\n"
            "Ano: 2025"
        ),
        font=("Arial", 11),
        bg="white",
        fg="black",
        justify="left",
        anchor="w"
    )
    label.pack(padx=18, pady=14)

    # Botão para fechar a janela de créditos
    btn_fechar = tk.Button(frame, text="Fechar", command=win.destroy)
    btn_fechar.pack(pady=(0, 5))

# -------------------------------------------------------------------
#  GUI (Tkinter)
# -------------------------------------------------------------------
janela = tk.Tk()
janela.title("Ciclo Brayton – Trabalho prático")
janela.resizable(False, False)  # <-- trava o tamanho da janela

# ---------------- Cabeçalho com logo e texto -----------------
logo_img = PhotoImage(file="logo.png")  # Use PNG ou GIF

head_frame = tk.Frame(janela, bg="#ff7e5f")
head_frame.grid(row=0, column=0, columnspan=2, sticky="we", pady=(0, 20))

# Configura o peso das colunas para centralizar a logo
head_frame.grid_columnconfigure(0, weight=0)  # Texto fixo à esquerda
head_frame.grid_columnconfigure(1, weight=1)  # Logo centralizada
head_frame.grid_columnconfigure(2, weight=1)  # Espaço vazio à direita

# Texto à esquerda
head_label = tk.Label(
    head_frame, text=f"Bem vindo, {nome_pc}",
    font=("Arial", 18, "bold"),
    bg="#ff7e5f", fg="white",
    anchor="w", padx=20, pady=10
)
head_label.grid(row=0, column=0, sticky="w", padx=(10, 0), pady=(10, 0))

# Logo centralizada horizontal e verticalmente
logo_label = tk.Label(head_frame, image=logo_img, bg="#ff7e5f")
logo_label.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=(10, 0))

# Coluna vazia para ocupar espaço à direita
espaco_label = tk.Label(head_frame, bg="#ff7e5f")
espaco_label.grid(row=0, column=2, sticky="nsew")

# ---------------- Botão Créditos no canto superior direito, com caixa branca -----------------
frame_creditos = tk.Frame(janela, bg="white", bd=1, relief="solid")
frame_creditos.place(relx=0.96, y=6, anchor="ne")  # relx < 1.0 desloca para a esquerda

btn_creditos = tk.Button(
    frame_creditos, text="Créditos", font=("Arial", 10, "bold"),
    command=mostrar_creditos, bg="white", fg="gray", bd=0, cursor="hand2",
    highlightthickness=0, relief="flat"
)
btn_creditos.pack(padx=8, pady=2)

# ---------------- Card: entrada de dados -------------
entrada_frame = tk.LabelFrame(
    janela, text="Entrada de Dados",
    font=("Arial", 12, "bold"), padx=15, pady=10
)
entrada_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 20), sticky="we")

tk.Label(entrada_frame, text="P1 (kPa):").grid(row=0, column=0, sticky="e")
entry_p1 = tk.Entry(entrada_frame); entry_p1.grid(row=0, column=1)

tk.Label(entrada_frame, text="T1 (K):").grid(row=1, column=0, sticky="e")
entry_t1 = tk.Entry(entrada_frame); entry_t1.grid(row=1, column=1)

tk.Label(entrada_frame, text="RP (P2 / P1):").grid(row=2, column=0, sticky="e")
entry_rp = tk.Entry(entrada_frame); entry_rp.grid(row=2, column=1)

tk.Label(entrada_frame, text="Potência W (MW):").grid(row=3, column=0, sticky="e")
entry_w = tk.Entry(entrada_frame); entry_w.grid(row=3, column=1)

tk.Label(entrada_frame, text="Tmax (K):").grid(row=4, column=0, sticky="e")
entry_t4 = tk.Entry(entrada_frame); entry_t4.grid(row=4, column=1)

tk.Label(entrada_frame, text="Rendimento Regenerador").grid(row=5, column=0, sticky="e")
entry_nreg = tk.Entry(entrada_frame); entry_nreg.grid(row=5, column=1)

btn_calcular = tk.Button(entrada_frame, text="Calcular", command=calcular)
btn_calcular.grid(row=6, column=0, pady=10, sticky="we")

btn_limpar = tk.Button(entrada_frame, text="Limpar", command=limpar_campos)
btn_limpar.grid(row=6, column=1, pady=10, sticky="we")

# ---------------- Frame horizontal: resultados + gráficos ----------
cards_frame = tk.Frame(janela)
cards_frame.grid(row=2, column=0, columnspan=2, padx=10, pady=(0, 20), sticky="we")

# ---------- Card de resultados -------------
resultado_frame = tk.LabelFrame(
    cards_frame, text="Resultados",
    font=("Arial", 12, "bold"), padx=15, pady=20
)
resultado_frame.grid(row=0, column=0, padx=(0, 15), sticky="n")

resultado_frame.config(width=400, height=343)
resultado_frame.grid_propagate(False)  # Impede ajuste automático do frame

# Permite expansão do Text
resultado_frame.grid_rowconfigure(0, weight=1)
resultado_frame.grid_columnconfigure(0, weight=1)

resultado_txt = tk.Text(
    resultado_frame, height=1, width=1,  # valores mínimos, expansão via grid
    font=("Courier New", 12), state="disabled"
)
resultado_txt.grid(row=0, column=0, sticky="nsew")  # Expande em todas as direções

msg_label = tk.Label(
    resultado_frame,
    text="Este aplicativo foi criado como trabalho para a disciplina máquinas térmicas",
    font=("Arial", 9, "italic"),
    fg="gray25", wraplength=320, justify="left"
)
msg_label.grid(row=1, column=0, pady=(8, 0), sticky="w")

# ---------- Card de diagramas -------------
diagramas_frame = tk.LabelFrame(
    cards_frame, text="Diagramas",
    font=("Arial", 12, "bold"), padx=15, pady=20
)
diagramas_frame.grid(row=0, column=1, sticky="n")

# ---- Figura P×V (inicial vazia) ----
fig_pv = Figure(figsize=(4.2, 2.6), dpi=100)
ax_pv  = fig_pv.add_subplot(111)
ax_pv.set_title("P × V")
ax_pv.set_xlabel("Volume específico  (m³/kg)")
ax_pv.set_ylabel("Pressão  (kPa)")
ax_pv.grid(True)

canvas_pv = FigureCanvasTkAgg(fig_pv, master=diagramas_frame)
canvas_pv.draw()
canvas_pv.get_tk_widget().grid(row=0, column=0, padx=5, pady=10)

# ---- Figura T×S (inicial vazia) ----
fig_ts = Figure(figsize=(4.2, 2.6), dpi=100)
ax_ts  = fig_ts.add_subplot(111)
ax_ts.set_title("T × S")
ax_ts.set_xlabel("Entropia (S)")
ax_ts.set_ylabel("Temperatura (T)")
ax_ts.grid(True)
fig_ts.tight_layout()

canvas_ts = FigureCanvasTkAgg(fig_ts, master=diagramas_frame)
canvas_ts.draw()
canvas_ts.get_tk_widget().grid(row=0, column=1, padx=5, pady=10)

janela.mainloop()
