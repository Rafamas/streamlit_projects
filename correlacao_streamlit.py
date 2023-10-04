import pandas as pd
import seaborn as sns
import streamlit as st
from datetime import datetime 
import plotly.express as px
import plotly.subplots as sp
import plotly.graph_objs as go

concat_excel = 'concat.xlsx'
df_concat = pd.read_excel(concat_excel)

def faixa_data(ano_incio,ano_fim,df):
    df_filtrado = df[df['ano'].between(ano_incio,ano_fim)]
    return df_filtrado

def heatmap(df):
    plot = px.imshow(df, color_continuous_scale = 'reds')
    plot.update_layout(title='Mapa de Calor')
    return plot

def grafico_linha(df,x,y):
    fig = px.line(df_concat, x=x, y=y, 
              title='Gráfico de Linha com Múltiplas Séries')
    
    lista_segundo_eixo = ['energia_comercial','energia_residencial','energia_industrial','energia_outros','energia_total']

    if len(y) > 1:
        for serie in y[1:]:
            if serie in lista_segundo_eixo:
                fig.add_trace(go.Scatter(x=df[x], y=df[serie], mode='lines', name=serie, yaxis='y2'))
            fig.update_yaxes(title_text='Eixo Y secundário', secondary_y=True)
    return fig

st.title('Correlação entre IPCA, IGPM, INCC, consumo de energia  e tabela FIPE')

ano_inicio = st.number_input("Digite o ano de início:", min_value = 1995)
ano_fim = st.number_input("Digite o ano de fim:", max_value = datetime.now().year)

df_valores = faixa_data(ano_inicio,ano_fim,df_concat)
lista_drop = ['data','ano','mes']
valores_drop = df_valores.drop(lista_drop,axis=1)
correlation = valores_drop.corr()

gerar_grafico = st.button('Gerar Heatmap')

if gerar_grafico:
    tabela = heatmap(correlation)
    st.plotly_chart(tabela)

option = st.multiselect(
    'Quais parâmetros apresentar no gráfico de linhas?',
     list(valores_drop.columns))

st.write('Opções selecionadas: ', option)

gerar_grafico_linha = st.button('Gerar Gráfico de linhas')

if gerar_grafico_linha:
    grafico = grafico_linha(df_valores,'data',option)
    st.plotly_chart(grafico)
