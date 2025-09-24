import streamlit as st
import pandas as pd
import os

# -------------------- CONFIGURAÇÃO DA PÁGINA --------------------
st.set_page_config(
    page_title="Produtividade",
    page_icon="⚡",
    layout="wide"
)

st.title("📊 Dashboard de Produtividade")
st.write("Selecione o mês, ano e obra para calcular RUP automaticamente.")

# -------------------- SIDEBAR --------------------
st.sidebar.header("Filtros")

meses = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
anos = [2025, 2024]

mes_selecionado = st.sidebar.selectbox("Mês", meses)
ano_selecionado = st.sidebar.selectbox("Ano", anos)

obras = ["Marie Curie"]
obra_selecionada = st.sidebar.selectbox("Obra", obras)

# -------------------- NOMES DOS ARQUIVOS --------------------
arquivo_apropriacao = os.path.join(
    "Apropriacao",
    f"{ano_selecionado}.{meses.index(mes_selecionado)+1:02d} - Apropriacao - {obra_selecionada} - {mes_selecionado[:3]}.{str(ano_selecionado)[2:]} PREENCHIDO.xlsx"
)

arquivo_folha = os.path.join(
    "Folha",
    f"{mes_selecionado}{ano_selecionado}.xlsx"
)

arquivo_producao = "PRODUCAO_EXECUTADA.xlsx"

st.write("### Arquivos carregados")
st.write(f"Apropriacao: {arquivo_apropriacao}")
st.write(f"Folha: {arquivo_folha}")
st.write(f"Producao Executada: {arquivo_producao}")

# -------------------- LEITURA DAS PLANILHAS --------------------
try:
    df_apropriacao = pd.read_excel(arquivo_apropriacao, header=9)
    st.success("Planilha de Apropriacao carregada com sucesso!")
except Exception as e:
    st.error(f"Erro ao carregar Apropriacao: {e}")
    st.stop()

try:
    df_folha = pd.read_excel(arquivo_folha)
    st.success("Planilha de Folha carregada com sucesso!")
except Exception as e:
    st.error(f"Erro ao carregar Folha: {e}")
    st.stop()

try:
    df_producao = pd.read_excel(arquivo_producao)
    st.success("Planilha de Producao Executada carregada com sucesso!")
except Exception as e:
    st.error(f"Erro ao carregar Producao Executada: {e}")
    st.stop()

# -------------------- FILTRAGEM DE SERVICO --------------------
servico_selecionado = st.text_input("Digite o serviço a filtrar (ex: Concreto)")

if servico_selecionado:
    df_servico = df_apropriacao[df_apropriacao['L'] == servico_selecionado]
    df_servico = df_servico[['C','D']].rename(columns={'C':'Nome','D':'Funcao'})
    
    col_folha = ["Hora Extra 70% - Sábado","Hora Extra 70% - Semana","Produção","Reflexos Produção","Repouso Remunerado"]
    df_folha_filtrado = df_folha[df_folha['NOME DA EMPRESA'].isin(df_servico['Nome'])]
    df_folha_filtrado = df_folha_filtrado[['NOME DA EMPRESA'] + col_folha]
    
    df_merge = pd.merge(df_servico, df_folha_filtrado, left_on='Nome', right_on='NOME DA EMPRESA', how='left')
    
    def tipo_funcao(func):
        return 'Profissional' if not func.startswith('Servente') else 'Ajudante'
    
    df_merge['Tipo'] = df_merge['Funcao'].apply(tipo_funcao)
    df_merge['ValorHora'] = df_merge['Tipo'].apply(lambda x: 10.5 if x=='Profissional' else 7.9)
    
    df_merge['HorasTotais'] = (df_merge["Hora Extra 70% - Sábado"] +
                               df_merge["Hora Extra 70% - Semana"] +
                               df_merge["Produção"] +
                               df_merge["Reflexos Produção"] +
                               df_merge["Repouso Remunerado"]) / df_merge['ValorHora']
    
    mes_ref = f"{ano_selecionado}-{meses.index(mes_selecionado)+1:02d}"
    df_prod_mes = df_producao[df_producao['Mês Referência'] == mes_ref]
    df_prod_servico = df_prod_mes[df_prod_mes['Serviço'] == servico_selecionado]
    
    if not df_prod_servico.empty:
        qtd_executada = df_prod_servico.iloc[0]['Quantidade Executada']
        df_merge['RUP'] = df_merge['HorasTotais'] / qtd_executada
        
        total_profissional = df_merge[df_merge['Tipo']=='Profissional']['RUP'].sum()
        total_ajudante = df_merge[df_merge['Tipo']=='Ajudante']['RUP'].sum()
        RUP_final = total_profissional + (total_ajudante / 1.33)
        
        st.write("### Tabela de Funcionarios com Horas e RUP")
        st.dataframe(df_merge[['Nome','Funcao','Tipo','HorasTotais','RUP']])
        
        st.success(f"RUP Final do Serviço '{servico_selecionado}': {RUP_final:.2f}")
    else:
        st.warning("Serviço nao encontrado na planilha de Producao Executada.")
