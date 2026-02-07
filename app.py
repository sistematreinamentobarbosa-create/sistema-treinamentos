import streamlit as st
import pandas as pd
import os
from datetime import datetime
import plotly.express as px
import ast
import locale
import io
from streamlit_gsheets import GSheetsConnection

# --- CONFIGURAÇÃO REGIONAL (PT-BR) ---
try:
    locale.setlocale(locale.LC_ALL, 'pt_BR.utf8')
except:
    try:
        locale.setlocale(locale.LC_ALL, 'pt_BR')
    except:
        pass 

# --- 1. CONFIGURAÇÃO E CONEXÃO ---
st.set_page_config(page_title="Barbosa Contabilidade | Treinamentos", layout="wide")

conn = st.connection("gsheets", type=GSheetsConnection)

def carregar_dados():
    df = conn.read(worksheet="Treinamentos", ttl=0)
    if df.empty or len(df.columns) < 2:
        return pd.DataFrame(columns=["Data", "Funcionário", "Setor", "Líder", "Tema", "Horas", "Avaliação", "Nota_Lider"])
    
    df["Nota_Lider"] = df["Nota_Lider"].astype(str).replace(['nan', 'None', '', 'nan.0'], '-')
    df["Avaliação"] = df["Avaliação"].astype(str).replace(['nan', 'None', ''], '-')
    df["Data"] = pd.to_datetime(df["Data"], dayfirst=True, errors='coerce')
    df["Horas"] = pd.to_numeric(df["Horas"], errors='coerce').fillna(0)
    return df

def carregar_usuarios():
    return conn.read(worksheet="Usuarios", ttl=0)

def salvar_dados(df_atualizado):
    conn.update(worksheet="Treinamentos", data=df_atualizado)

def salvar_usuarios(df_usuarios):
    conn.update(worksheet="Usuarios", data=df_usuarios)

# --- UTILITÁRIOS ---
def format_to_time(decimal_hours):
    hours = int(decimal_hours)
    minutes = int((decimal_hours - hours) * 60)
    seconds = int(round(((decimal_hours - hours) * 60 - minutes) * 60))
    if seconds == 60: seconds = 0; minutes += 1
    if minutes == 60: minutes = 0; hours += 1
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def converter_perfil(perfil_raw):
    try:
        res = ast.literal_eval(str(perfil_raw))
        return res if isinstance(res, list) else [str(perfil_raw)]
    except:
        return [str(perfil_raw)]

# --- CONSTANTES ---
LISTA_SETORES = ["Selecione o Setor...", "Departamento T.I.", "Departamento Pessoal", "Departamento Fiscal", "Departamento Contábil", "Diretoria", "Departamento R.H.", "Departamento Legalização", "Departamento Recepção"]
LISTA_LIDERES = ["Selecione o Líder...", "Victor Souza", "Thiago Ferreira", "Rafael Pires", "Priscila Barbosa", "Franceli Dario", "Thamiris Afonso", "Ruth Moreira"]
LISTA_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
LISTA_NOTAS_VALIDAS = [str(i) for i in range(1, 11)]
LISTA_NOTAS_CADASTRO = ["Selecione..."] + LISTA_NOTAS_VALIDAS

# --- ESTADOS DE SESSÃO ---
if 'autenticado' not in st.session_state:
    st.session_state.autenticado = False

# --- TELA DE LOGIN ---
if not st.session_state.autenticado:
    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; background: radial-gradient(circle, #4a0000 0%, #000000 100%) !important; color: white; min-height: 100vh; }
        [data-testid="stHorizontalBlock"] { background-color: rgba(255, 255, 255, 0.05) !important; padding: 50px !important; border-radius: 30px !important; border: 1px solid rgba(255, 255, 255, 0.1) !important; backdrop-filter: blur(20px) !important; box-shadow: 0 25px 50px rgba(0,0,0,0.5) !important; margin-top: 50px; }
        .main-title { font-family: sans-serif; font-size: 38px; font-weight: 900; color: white; text-transform: uppercase; text-align: center; }
        .sub-title { font-family: sans-serif; font-size: 16px; color: #ff4b4b; text-align: center; margin-bottom: 30px; letter-spacing: 2px; font-weight: bold; }
        .stButton>button { background-color: white !important; color: black !important; border-radius: 50px !important; font-weight: bold; width: 100%; padding: 12px; border: none !important; }
        .stButton>button:hover { background-color: #ff0000 !important; color: white !important; box-shadow: 0 0 25px rgba(255, 0, 0, 0.6); }
        </style>
    """, unsafe_allow_html=True)
    
    _, login_col, _ = st.columns([1, 1.5, 1])
    with login_col:
        st.markdown('<h1 class="main-title">BARBOSA CONTABILIDADE</h1>', unsafe_allow_html=True)
        st.markdown('<p class="sub-title">Portal de Treinamentos Internos | Login</p>', unsafe_allow_html=True)
        u_in = st.text_input("Seu Nome de Usuário", placeholder="Ex: Matheus Oliveira")
        s_in = st.text_input("Senha de Acesso", type="password")
        if st.button("LOGIN"):
            users_df = carregar_usuarios()
            user_auth = users_df[(users_df['usuario'] == u_in) & (users_df['senha'].astype(str) == s_in)]
            if not user_auth.empty:
                st.session_state.autenticado = True
                st.session_state.usuario = u_in
                st.session_state.perfil = converter_perfil(user_auth.iloc[0]['perfil'])
                st.session_state.setor_usuario = user_auth.iloc[0]['setor']
                st.rerun()
            else: st.error("Credenciais incorretas.")

else:
    # --- CSS INTERNO (LOGADO) ---
    st.markdown("""
        <style>
        .stApp { background-color: #000000 !important; background: radial-gradient(circle, #4a0000 0%, #000000 100%) !important; color: white; min-height: 100vh; }
        section[data-testid="stSidebar"] { background-color: rgba(0, 0, 0, 0.8) !important; border-right: 1px solid #4a0000; }
        .main-title-logged { font-family: sans-serif; font-size: 30px; font-weight: 800; color: white; text-transform: uppercase; margin-bottom: 20px; }
        div[data-testid="stMetricValue"] { padding: 20px !important; border-radius: 15px !important; color: white !important; font-weight: bold !important; }
        .edit-container { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; border: 1px solid #ff4b4b; margin-top: 10px; }
        .metric-card { background-color: rgba(255, 255, 255, 0.05); padding: 20px; border-radius: 15px; text-align: center; border-bottom: 4px solid #ff4b4b; transition: transform 0.3s; margin-bottom: 10px;}
        .metric-label { color: #aaaaaa; font-size: 14px; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 10px; }
        .metric-value { color: white; font-size: 28px; font-weight: 800; }
        .inactive-alert { border-left: 5px solid #ff4b4b; background-color: rgba(255, 75, 75, 0.1); padding: 15px; border-radius: 5px; margin-bottom: 10px; font-size: 14px; }
        </style>
    """, unsafe_allow_html=True)
    
    df = carregar_dados()
    opcoes_menu = ["Dashboard", "Registrar Curso", "Relatório Geral"]
    if any(p in st.session_state.perfil for p in ["Admin", "Editor"]): 
        opcoes_menu.append("Painel Administrativo")
    
    menu = st.sidebar.selectbox("Menu", opcoes_menu)
    st.sidebar.divider()
    st.sidebar.write(f"👤 **{st.session_state.usuario}**")
    st.sidebar.write(f"🏢 Setor: **{st.session_state.setor_usuario}**")

    # --- ALTERAR SENHA (NA SIDEBAR) ---
    with st.sidebar.expander("🔑 Alterar Minha Senha"):
        with st.form("form_alterar_senha_pessoal"):
            nova_senha = st.text_input("Nova Senha", type="password")
            conf_senha = st.text_input("Confirmar Senha", type="password")
            if st.form_submit_button("ATUALIZAR"):
                if nova_senha == conf_senha and nova_senha != "":
                    u_df = carregar_usuarios()
                    u_df.loc[u_df['usuario'] == st.session_state.usuario, 'senha'] = nova_senha
                    salvar_usuarios(u_df)
                    st.success("Senha alterada!")
                else: st.error("As senhas não coincidem.")

    # --- LÓGICA DASHBOARD ---
    if menu == "Dashboard":
        mes_sel = st.sidebar.selectbox("Mês", LISTA_MESES, index=datetime.now().month-1)
        ano_sel = st.sidebar.number_input("Ano", 2024, 2030, datetime.now().year)
        
        target_users = [st.session_state.usuario]
        titulo_dash = f"MEU DASHBOARD - {mes_sel.upper()}"
        status_filtro_radio = "Todos"

        if any(p in st.session_state.perfil for p in ["Gestor", "Admin"]):
            st.sidebar.divider()
            df_base_filtros = df.copy()
            if "Admin" in st.session_state.perfil or st.session_state.setor_usuario == "Diretoria":
                setor_f = st.sidebar.selectbox("Filtrar por Setor:", ["Todos"] + LISTA_SETORES[1:])
                if setor_f != "Todos": df_base_filtros = df_base_filtros[df_base_filtros["Setor"] == setor_f]
            else:
                df_base_filtros = df_base_filtros[df_base_filtros["Setor"] == st.session_state.setor_usuario]
            
            colaboradores_lista = sorted(df_base_filtros["Funcionário"].unique().tolist())
            f_colabs = st.sidebar.multiselect("Filtrar Colaboradores:", colaboradores_lista)
            status_filtro_radio = st.sidebar.radio("Status de Avaliação:", ["Todos", "✅ Avaliados", "⏳ Pendentes"])
            
            if f_colabs:
                target_users = f_colabs
                titulo_dash = f"DASHBOARD: {f_colabs[0].upper()}" if len(f_colabs) == 1 else "DASHBOARD GRUPAL"
            else:
                target_users = colaboradores_lista if not df_base_filtros.empty else [st.session_state.usuario]

        if df.empty or df["Data"].isnull().all():
            st.info("Nenhum dado encontrado para o período.")
        else:
            # Filtragem principal
            user_df = df[(df["Funcionário"].isin(target_users)) & 
                         (df["Data"].dt.month == (LISTA_MESES.index(mes_sel)+1)) & 
                         (df["Data"].dt.year == ano_sel)].copy()
            
            # Filtro por avaliação do líder
            user_df["Nota_Lider_Str"] = user_df["Nota_Lider"].apply(lambda x: str(x).replace('.0', ''))
            if status_filtro_radio == "✅ Avaliados":
                user_df = user_df[user_df["Nota_Lider_Str"].isin(LISTA_NOTAS_VALIDAS)]
            elif status_filtro_radio == "⏳ Pendentes":
                user_df = user_df[~user_df["Nota_Lider_Str"].isin(LISTA_NOTAS_VALIDAS)]
            
            horas_totais = user_df["Horas"].sum()
            meta_dinamica = 7.0 * (len(target_users) if target_users else 1)

            # Lógica de cores baseada na meta
            if horas_totais < (meta_dinamica * 0.4): cor_card, cor_graf = "linear-gradient(135deg, #ff0000 0%, #8b0000 100%)", "#ff4b4b"
            elif horas_totais < meta_dinamica: cor_card, cor_graf = "linear-gradient(135deg, #ff8c00 0%, #ff4500 100%)", "#ffa500"
            else: cor_card, cor_graf = "linear-gradient(135deg, #00ff00 0%, #006400 100%)", "#00ff00"

            st.markdown(f"<style>div[data-testid='stMetricValue'] {{ background: {cor_card} !important; }}</style>", unsafe_allow_html=True)
            st.markdown(f'<h1 class="main-title-logged">{titulo_dash}</h1>', unsafe_allow_html=True)
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("HORAS NO MÊS", format_to_time(horas_totais))
            c2.metric("META TOTAL", format_to_time(meta_dinamica))
            progresso = min(100.0, (horas_totais/meta_dinamica)*100 if meta_dinamica > 0 else 0)
            c3.metric("PROGRESSO", f"{progresso:.1f}%")
            c4.metric("STATUS", "EM DIA" if horas_totais >= meta_dinamica else "PENDENTE")

            # --- SEÇÃO GESTOR: META 7H INDIVIDUAL ---
            if any(p in st.session_state.perfil for p in ["Gestor", "Admin"]):
                st.divider()
                st.subheader("🚩 Status de Cumprimento (Meta 7h/Colaborador)")
                udf_meta = carregar_usuarios()
                if not ("Admin" in st.session_state.perfil or st.session_state.setor_usuario == "Diretoria"):
                    udf_meta = udf_meta[udf_meta["setor"] == st.session_state.setor_usuario]
                
                todos_colabs = udf_meta["usuario"].unique()
                df_mes_meta = df[(df["Data"].dt.month == (LISTA_MESES.index(mes_sel)+1)) & (df["Data"].dt.year == ano_sel)]
                horas_por_colab = df_mes_meta.groupby("Funcionário")["Horas"].sum().reindex(todos_colabs, fill_value=0).reset_index()
                horas_por_colab.columns = ["Nome", "Total_Horas"]
                
                bateu_meta = horas_por_colab[horas_por_colab["Total_Horas"] >= 7.0]
                pendente_meta = horas_por_colab[horas_por_colab["Total_Horas"] < 7.0]
                
                m1, m2 = st.columns([1, 2])
                with m1:
                    fig_meta = px.pie(values=[len(bateu_meta), len(pendente_meta)], 
                                      names=['Bateu Meta', 'Pendente'], 
                                      hole=0.6, color=['Bateu Meta', 'Pendente'],
                                      color_discrete_map={'Bateu Meta':'#00ff00', 'Pendente':'#ff4b4b'},
                                      title="Panorama da Equipe")
                    fig_meta.update_layout(showlegend=False, height=220, margin=dict(t=30, b=0, l=0, r=0), template="plotly_dark")
                    st.plotly_chart(fig_meta, use_container_width=True)
                
                with m2:
                    cl1, cl2 = st.columns(2)
                    with cl1:
                        with st.expander(f"✅ CONCLUÍRAM ({len(bateu_meta)})"):
                            for _, r in bateu_meta.iterrows(): st.write(f"✔️ {r['Nome']}")
                    with cl2:
                        with st.expander(f"⏳ PENDENTES ({len(pendente_meta)})", expanded=True):
                            for _, r in pendente_meta.iterrows():
                                falta = 7.0 - r['Total_Horas']
                                st.write(f"❌ {r['Nome']} (-{format_to_time(falta)})")

            # --- GRÁFICOS E EDIÇÃO ---
            st.divider()
            cg1, cg2 = st.columns([1.5, 1])
            with cg1:
                st.subheader("Distribuição por Temas")
                if not user_df.empty:
                    cor_param = "Funcionário" if len(target_users) > 1 else None
                    fig = px.bar(user_df, x="Tema", y="Horas", color=cor_param, template="plotly_dark", 
                                 color_discrete_sequence=[cor_graf] if not cor_param else px.colors.qualitative.Pastel)
                    fig.update_traces(width=0.4) 
                    st.plotly_chart(fig, use_container_width=True)
            
            with cg2:
                st.subheader("Ajustar Registro")
                if not user_df.empty:
                    sel_id = st.selectbox("Escolha o registro:", user_df.index, format_func=lambda x: f"[{user_df.loc[x, 'Funcionário']}] {user_df.loc[x, 'Tema']}")
                    
                    # Permissões de edição
                    func_reg = user_df.loc[sel_id, 'Funcionário']
                    sou_adm = "Admin" in st.session_state.perfil
                    sou_gestor = "Gestor" in st.session_state.perfil
                    eh_meu = (func_reg == st.session_state.usuario)
                    
                    pode_excluir = eh_meu or sou_adm
                    pode_editar = eh_meu or sou_adm or sou_gestor

                    col_b1, col_b2 = st.columns(2)
                    if col_b1.button("❌ EXCLUIR", disabled=not pode_excluir, use_container_width=True):
                        df_exc = carregar_dados()
                        df_exc = df_exc.drop(sel_id)
                        salvar_dados(df_exc); st.rerun()
                    
                    if col_b2.button("📝 EDITAR", disabled=not pode_editar, use_container_width=True):
                        st.session_state.editando_id = sel_id

                    if 'editando_id' in st.session_state and st.session_state.editando_id == sel_id:
                        st.markdown('<div class="edit-container">', unsafe_allow_html=True)
                        with st.form("form_edicao"):
                            trava_colab = not (eh_meu or sou_adm)
                            novo_tema = st.text_input("Tema", value=user_df.loc[sel_id, 'Tema'], disabled=trava_colab)
                            
                            n_c_raw = str(user_df.loc[sel_id, 'Avaliação']).replace('.0', '')
                            idx_c = LISTA_NOTAS_CADASTRO.index(n_c_raw) if n_c_raw in LISTA_NOTAS_CADASTRO else 0
                            nova_nota_c = st.selectbox("Sua Satisfação", LISTA_NOTAS_CADASTRO, index=idx_c, disabled=trava_colab)
                            
                            # Avaliação do Líder (Apenas Gestores avaliam o registro de outros)
                            pode_dar_nota_lider = (sou_gestor or sou_adm) and not eh_meu
                            n_l_raw = str(user_df.loc[sel_id, 'Nota_Lider']).replace('.0', '')
                            idx_l = LISTA_NOTAS_CADASTRO.index(n_l_raw) if n_l_raw in LISTA_NOTAS_CADASTRO else 0
                            nova_nota_l = st.selectbox("Avaliação Líder (Privada)", LISTA_NOTAS_CADASTRO, index=idx_l, disabled=not pode_dar_nota_lider)

                            h_dec = user_df.loc[sel_id, 'Horas']
                            h_ed, m_total = int(h_dec), (h_dec - int(h_dec)) * 60
                            m_ed, s_ed = int(m_total), int(round((m_total - int(m_total)) * 60))
                            
                            ec1, ec2, ec3 = st.columns(3)
                            nh = ec1.number_input("H", 0, 23, h_ed, disabled=trava_colab)
                            nm = ec2.number_input("M", 0, 59, m_ed, disabled=trava_colab)
                            ns = ec3.number_input("S", 0, 59, s_ed, disabled=trava_colab)

                            if st.form_submit_button("SALVAR"):
                                df_b = carregar_dados()
                                df_b.loc[sel_id, ["Tema", "Horas", "Avaliação", "Nota_Lider"]] = [novo_tema, nh + (nm/60) + (ns/3600), nova_nota_c, nova_nota_l]
                                salvar_dados(df_b)
                                del st.session_state.editando_id; st.rerun()
                        if st.button("Fechar"): del st.session_state.editando_id; st.rerun()
                        st.markdown('</div>', unsafe_allow_html=True)

            # --- HISTÓRICO ---
            st.divider(); st.subheader("📋 Detalhamento dos Registros")
            if not user_df.empty:
                disp = user_df.copy()
                def mask_nota(row):
                    if row['Funcionário'] == st.session_state.usuario and not sou_adm: return "🔒 Privada"
                    return row['Nota_Lider']
                disp["Nota_Lider"] = disp.apply(mask_nota, axis=1)
                disp["Horas"] = disp["Horas"].apply(format_to_time)
                disp["Data"] = disp["Data"].dt.strftime('%d/%m/%Y')
                st.dataframe(disp[["Data", "Funcionário", "Tema", "Horas", "Líder", "Avaliação", "Nota_Lider"]], use_container_width=True)

    # --- REGISTRO DE CURSO ---
    elif menu == "Registrar Curso":
        st.markdown('<h1 class="main-title-logged">NOVO REGISTRO</h1>', unsafe_allow_html=True)
        with st.form("form_reg"):
            tema = st.text_input("Nome do Treinamento")
            data = st.date_input("Data Realizada", format="DD/MM/YYYY")
            c1, c2, c3, c4 = st.columns([1, 1, 1, 2])
            h, m, s = c1.number_input("H", 0, 23), c2.number_input("M", 0, 59), c3.number_input("S", 0, 59)
            nota = c4.selectbox("Sua Satisfação (1 a 10)", LISTA_NOTAS_CADASTRO)
            lider = st.selectbox("Líder Responsável", LISTA_LIDERES)
            if st.form_submit_button("CONFIRMAR REGISTRO"):
                if not tema or lider == LISTA_LIDERES[0] or nota == "Selecione...":
                    st.error("Preencha todos os campos obrigatórios.")
                else:
                    total = h + (m/60) + (s/3600)
                    nova = pd.DataFrame([{"Data": data.strftime("%d/%m/%Y"), "Funcionário": st.session_state.usuario, "Setor": st.session_state.setor_usuario, "Líder": lider, "Tema": tema, "Horas": total, "Avaliação": nota, "Nota_Lider": "-"}])
                    df_full = pd.concat([carregar_dados(), nova], ignore_index=True)
                    salvar_dados(df_full)
                    st.success("Treinamento registrado com sucesso!"); st.rerun()

    # --- RELATÓRIOS ---
    elif menu == "Relatório Geral":
        st.markdown('<h1 class="main-title-logged">RELATÓRIOS E DESEMPENHO</h1>', unsafe_allow_html=True)
        df_rel = carregar_dados()
        if not df_rel.empty:
            # Filtros de Relatório por Perfil
            if "Admin" in st.session_state.perfil or st.session_state.setor_usuario == "Diretoria":
                cf1, cf2, cf3 = st.columns(3)
                f_s = cf1.selectbox("Setor", ["Todos"] + LISTA_SETORES[1:])
                if f_s != "Todos": df_rel = df_rel[df_rel["Setor"] == f_s]
                f_c = cf2.selectbox("Colaborador", ["Todos"] + sorted(df_rel["Funcionário"].unique().tolist()))
                if f_c != "Todos": df_rel = df_rel[df_rel["Funcionário"] == f_c]
                f_m = cf3.selectbox("Mês", ["Todos"] + LISTA_MESES)
            elif "Gestor" in st.session_state.perfil:
                cf1, cf2 = st.columns(2)
                df_rel = df_rel[df_rel["Setor"] == st.session_state.setor_usuario]
                f_c = cf1.selectbox("Colaborador", ["Todos"] + sorted(df_rel["Funcionário"].unique().tolist()))
                if f_c != "Todos": df_rel = df_rel[df_rel["Funcionário"] == f_c]
                f_m = cf2.selectbox("Mês", ["Todos"] + LISTA_MESES)
            else:
                df_rel = df_rel[df_rel["Funcionário"] == st.session_state.usuario]
                f_m = st.selectbox("Filtrar Mês", ["Todos"] + LISTA_MESES)

            if f_m != "Todos": df_rel = df_rel[df_rel["Data"].dt.month == LISTA_MESES.index(f_m)+1]

            # Cards de Resumo
            st.divider()
            r1, r2, r3 = st.columns(3)
            with r1: st.markdown(f'<div class="metric-card"><div class="metric-label">Total Cursos</div><div class="metric-value">{len(df_rel)}</div></div>', unsafe_allow_html=True)
            with r2: st.markdown(f'<div class="metric-card"><div class="metric-label">Carga Horária</div><div class="metric-value">{format_to_time(df_rel["Horas"].sum())}</div></div>', unsafe_allow_html=True)
            with r3: 
                media_n = pd.to_numeric(df_rel["Nota_Lider"], errors='coerce').mean()
                st.markdown(f'<div class="metric-card"><div class="metric-label">Média Avaliação</div><div class="metric-value">{f"{media_n:.1f} ⭐" if not pd.isna(media_n) else "-"}</div></div>', unsafe_allow_html=True)

            # Exportação
            towrite = io.BytesIO()
            df_export = df_rel.copy()
            df_export['Data'] = df_export['Data'].dt.strftime('%d/%m/%Y')
            df_export.to_excel(towrite, index=False, engine='openpyxl')
            st.download_button("📥 BAIXAR EXCEL", towrite.getvalue(), f"Relatorio_Barbosa_{datetime.now().year}.xlsx", "application/vnd.ms-excel")

    # --- ADMINISTRAÇÃO ---
    elif menu == "Painel Administrativo":
        st.markdown('<h1 class="main-title-logged">ADMINISTRAÇÃO DE SISTEMA</h1>', unsafe_allow_html=True)
        udf = carregar_usuarios()
        
        # Alertas de Inatividade
        st.subheader("⚠️ Alertas de Inatividade (> 15 dias)")
        df_inat = carregar_dados()
        if not df_inat.empty:
            hoje = datetime.now()
            ult_reg = df_inat.groupby("Funcionário")["Data"].max().reset_index()
            alertas = []
            for _, u in udf.iterrows():
                reg = ult_reg[ult_reg["Funcionário"] == u['usuario']]
                if reg.empty: alertas.append(f"🔴 {u['usuario']}: Nunca registrou treinamento.")
                else:
                    dias = (hoje - reg.iloc[0]['Data']).days
                    if dias > 15: alertas.append(f"🟠 {u['usuario']}: Inativo há {dias} dias.")
            
            if alertas:
                for a in alertas: st.markdown(f'<div class="inactive-alert">{a}</div>', unsafe_allow_html=True)
            else: st.success("Todos os colaboradores estão ativos!")

        t1, t2, t3 = st.tabs(["Lista de Usuários", "Criar Novo", "Editar Perfil"])
        with t1: st.dataframe(udf, use_container_width=True)
        with t2:
            with st.form("new_user"):
                nu, ns = st.text_input("Nome Completo"), st.text_input("Senha", type="password")
                nset = st.selectbox("Setor", LISTA_SETORES[1:])
                np = st.multiselect("Perfis", ["Comum", "Gestor", "Editor", "Admin"], default=["Comum"])
                if st.form_submit_button("CADASTRAR"):
                    if nu and ns:
                        new_u = pd.DataFrame([{"usuario": nu, "senha": ns, "perfil": str(np), "setor": nset}])
                        salvar_usuarios(pd.concat([udf, new_u], ignore_index=True))
                        st.success("Usuário cadastrado!"); st.rerun()
        with t3:
            u_sel = st.selectbox("Selecionar Usuário", udf['usuario'].tolist())
            d = udf[udf['usuario'] == u_sel].iloc[0]
            with st.form("edit_user"):
                es = st.text_input("Senha", value=str(d['senha']))
                eset = st.selectbox("Setor", LISTA_SETORES[1:], index=LISTA_SETORES[1:].index(d['setor']) if d['setor'] in LISTA_SETORES else 0)
                ep = st.multiselect("Perfis", ["Comum", "Gestor", "Editor", "Admin"], default=converter_perfil(d['perfil']))
                if st.form_submit_button("ATUALIZAR"):
                    udf.loc[udf['usuario'] == u_sel, ["senha", "perfil", "setor"]] = [es, str(ep), eset]
                    salvar_usuarios(udf); st.success("Dados atualizados!"); st.rerun()

    if st.sidebar.button("SAIR"):
        st.session_state.autenticado = False
        st.rerun()
