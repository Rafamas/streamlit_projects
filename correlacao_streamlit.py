import pandas as pd
import seaborn as sns
import streamlit as st
from datetime import datetime 

concat_excel = 'concat.xlsx'
df_concat = pd.read_excel(concat_excel)

def faixa_data(ano_incio,ano_fim,df):
    df_filtrado = df[df['ano'].between(ano_incio,ano_fim)]
    return df_filtrado

def heatmap(df):
    plot = sns.heatmap(correlation,annot = True, fmt = ".1f", linewidths = .6)
    return plot

st.title('Correlação entre IPCA, IGPM, INCC e tabela FIPE')

ano_inicio = st.number_input("Digite o ano de início:", min_value = 1995)
ano_fim = st.number_input("Digite o ano de fim:", max_value = datetime.now().year)

def_valores = faixa_data(ano_inicio,ano_fim,df_concat)
correlation = def_valores[['IGPM','IPCA','INCC','Habit.','Aliment.','Transp.','Desp.','Saúde','Vest.','Educ.','Geral']].corr()

gerar_grafico = st.button('Gerar Heatmap')

if gerar_grafico:
    tabela = heatmap(def_valores)
    st.pyplot(tabela.get_figure())
