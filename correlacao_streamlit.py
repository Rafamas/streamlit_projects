import pandas as pd
import seaborn as sns
import streamlit as st
from datetime import datetime 
import plotly.express as px

concat_excel = 'concat.xlsx'
df_concat = pd.read_excel(concat_excel)

def faixa_data(ano_incio,ano_fim,df):
    df_filtrado = df[df['ano'].between(ano_incio,ano_fim)]
    return df_filtrado

def heatmap(df):
    plot = px.imshow(df, color_continuous_scale = 'reds')
    plot.update_layout(title='Mapa de Calor')
    return plot

st.title('Correlação entre IPCA, IGPM, INCC e tabela FIPE')

ano_inicio = st.number_input("Digite o ano de início:", min_value = 1995)
ano_fim = st.number_input("Digite o ano de fim:", max_value = datetime.now().year)

df_valores = faixa_data(ano_inicio,ano_fim,df_concat)
lista_drop = ['data','ano','mes']
correlation = df_valores.drop(lista_drop,axis=1).corr()

gerar_grafico = st.button('Gerar Heatmap')

if gerar_grafico:
    tabela = heatmap(correlation)
    st.plotly_chart(tabela)
