import requests as req
import pandas as pd
import pyodbc
import seaborn as sn
import time
from time import sleep
from bs4 import BeautifulSoup as bs
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import Select
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from urllib.request import urlopen, urlretrieve
from urllib.error import URLError, HTTPError 
import datetime
import numpy as np
from datetime import datetime
import streamlit as st
import os

# Função para buscar os indices
def consulta_api_indice(indice):

    
    '''
        Retorna JSON da série histórica da inflação.
        
        Parâmetros:
            indice (str): Indice a ser buscado ('IGPM' ou 'IPCA')   
            
        ---------------------------------------------------------------------------------
        
        Fonte: http://www.ipeadata.gov.br/
            
            IPCA: 
            Preços: Índice de Preços ao Consumidor Amplo (IPCA) geral com índice base (dez. 1993 = 100)
            Frequência: Mensal de 1979.12 até 2021.01
            Fonte: Instituto Brasileiro de Geografia e Estatística, Sistema Nacional de Índices de Preços ao Consumidor (IBGE/SNIPC)
           
            IGPM:
            Preços: índice geral de preços do mercado (IGP-M) - geral: índice (ago. 1994 = 100)
            Frequência: Mensal de 1989.06 até 2021.02
            Fonte: Fundação Getulio Vargas, Conjuntura Econômica - IGP (FGV/Conj. Econ. - IGP)
            
    '''
    def __filter__(item):
        """
        Filtra dados a partir do valor de referencia (Fator Acumulado = 100)
        """
        if item["fatorAcumulado"] >= 100:
            return True
        return False
        
    
    
    if indice.upper() not in ["IPCA","IGPM"]:
        raise Exception("Parametro inválido. Esperava-se 'IPCA' ou 'IGPM', recebeu {}".format(indice.upper()))
        return
    
    BASE_URL = "http://www.ipeadata.gov.br/api/odata4//ValoresSerie(SERCODIGO='{}')"
    SERCODIGO= {
        "IPCA":"PRECOS12_IPCA12",
        "IGPM":"IGP12_IGPM12"
    }
    
    
    response = req.get(BASE_URL.format(SERCODIGO[indice.upper()]))
    if response.status_code != 200:
        raise Exception("Algo deu errado")
        return
    else:
        data = response.json()["value"]
        df = pd.DataFrame(data=filter(__filter__,[{"data":x["VALDATA"].split("T")[0],"fatorAcumulado":x["VALVALOR"]} for x in data]))
        df["tipoIndice"] = indice
        return df

# Inclusão colunas extra (indice mensal, cenario, fator acumulado positivo)
def get_api_indice():    
    series = [consulta_api_indice("IPCA"), consulta_api_indice("IGPM")]
    for serie in series:
        serie['data'] = serie['data'].astype('datetime64[ns]')
        #serie.sort_values(by=["data"], inplace=True)
        var_mes_list = []
        acum_positivo = []
        for idx in serie.index:
            try:
                var = serie["fatorAcumulado"][idx]/serie["fatorAcumulado"][idx-1] - 1 
            except:
                var = 0
            var_mes_list.append(var *100)
            #var_mes_list.append(round(var *100,4))
            #print('idx)
            if var>=0:
                var_pos = var + 1
            else:
                var_pos = 1

            try:
                acum = acum_positivo[idx - 1]*var_pos
            except:
                acum = 100
            acum_positivo.append(acum)

        serie["indiceMensal"]= var_mes_list 
        serie["fatorAcumuladoPositivo"] = acum_positivo
        serie["cenario"] = "Oficial"

        df = pd.concat(series)
        df = df.infer_objects()
        
        def indiceMensalPositivo(df):
            i = df['indiceMensal']
            if (i <= 0):
                texto = 0
                return texto
            else:
                texto = i
                return texto
        df['indiceMensalPositivo'] = df.apply(indiceMensalPositivo, axis = 1)
    return df

# Função para retornar o DataFrame
def run():
    dff = get_api_indice()
    print(">> Concluído")
    return dff

if __name__ == "__main__":
    dff = run()
    #dff.dtypes
    #dff
    
df_ipca = dff[dff['tipoIndice'] == 'IPCA']
df_igpm = dff[dff['tipoIndice'] == 'IGPM']

def entre_datas(df,coluna_ano,ano_inicio,ano_fim):
    data_atual = datetime.now()
    df = df[(df[coluna_ano]).between(ano_inicio,ano_fim)]
    return df

def data_atual(df,coluna_ano,coluna_mes,ano_fim):
    data_atual = datetime.now()
    ano_hj = data_atual.year
    if ano_fim == 2023:
        numero_mes_hj = data_atual.month
        #df.loc[(df[coluna_ano] < ano_hj) | ((df[coluna_ano] == ano_hj) & (df[coluna_mes] < numero_mes_hj))]
        #df.loc[((df[coluna_ano] == ano_hj) & (df[coluna_mes] <= numero_mes_hj))]
        df.loc[(df[coluna_ano] < ano_hj) | ((df[coluna_ano] == ano_hj) & (df[coluna_mes] <= numero_mes_hj))]

    else:
        df.loc[(df[coluna_ano] < ano_hj) | ((df[coluna_ano] == ano_hj) & (df[coluna_mes] <= 12))]
    return df

def data_atual_incc(df,coluna_ano,coluna_mes,ano_fim):
    b = []
    data_atual = datetime.now()
    ano_hj = data_atual.year
    mes_hj = data_atual.month
    for index,row in df.iterrows():
            if (row[coluna_ano] < ano_hj) or (row[coluna_ano] == ano_hj and row[coluna_mes] < mes_hj):
                b.append(row)
            else:
                break
    df_new = pd.DataFrame(b)
    return df_new

def ano_mes(df,coluna_data):
    df['ano'] = df[coluna_data].dt.year
    df['mes'] = df[coluna_data].dt.month
    return df

df_ipca_parcial = df_ipca[['data','indiceMensal']]
df_ipca_parcial = df_ipca_parcial.rename(columns={'indiceMensal':'IPCA'})
ano_mes(df_ipca_parcial,'data')

df_igpm_parcial = df_igpm[['data','indiceMensal']]
df_igpm_parcial = df_igpm_parcial.rename(columns={'indiceMensal':'IGPM'})
ano_mes(df_igpm_parcial,'data')

def open_nav(url):

    try:
        # Start do simulador de navegador
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        print('Navegador aberto')
    
    except:
        
        desired_version = '114.0.5735.90'
    
        # Start do simulador de navegador
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(version=desired_version).install()))
        print('Navegador aberto')
    
    driver.get(url)
    
    sleep(1)
    
    html = bs(driver.page_source, "html.parser")
    tabela = html.find('div',{'align':'center'}).find('div',{'align':'center'})
    
    driver.quit()
    print('Navegador fechado')
    return tabela

def html_dados(tabela):
    cards = []
    colunas_df = ['A/M', 'JAN', 'FEV', 'MAR', 'ABR', 'MAI', 'JUN', 'JUL', 'AGO', 'SET', 'OUT', 'NOV', 'DEZ', 'ACUMULADO']
    for idx, i in enumerate(tabela.findAll('tr')):
        card = {}
        for jdx, j in enumerate(i.findAll('td')):
            if jdx < len(colunas_df):
                coluna = colunas_df[jdx]
                valor = j.get_text()
                card[coluna] = valor
        cards.append(card)
    return cards
    
def tratamento_cards(cards):
    for item in cards:
        for chave, valor in item.items():
            item[chave] = valor.strip()
    return cards
    
def tratamento(df,numero):
    meses_dict = {'JAN': '01', 'FEV': '02', 'MAR': '03', 'ABR': '04', 'MAI': '05', 'JUN': '06','JUL': '07', 'AGO': '08', 'SET': '09', 'OUT': '10', 'NOV': '11', 'DEZ': '12'}
    df = df.drop(df.index[0])
    df = df.reset_index(drop=True)
    df = df.drop(numero)
    df = df[df['A/M'].str.isnumeric()]
    df['A/M'] = pd.to_datetime(df['A/M'], format='%Y')
    df['A/M'] = df['A/M'].dt.year
    df = df.reset_index(drop=True)   
    df = df.drop('ACUMULADO',axis=1)
    df = df.melt(id_vars=['A/M'], var_name='mes', value_name='Valor')
    df['mes_numero'] = df['mes'].map(meses_dict)
    df = df.sort_values(by=['A/M','mes_numero'])
    df['Valor'] = df['Valor'].str.replace('%', '')
    df['Valor'] = df['Valor'].str.replace(',', '.')
    df['Valor'] = df['Valor'].str.replace(')', '')
    df['Valor'] = df['Valor'].str.replace('(', '')
    df['Valor'] = df['Valor'].replace(['', ' '], np.nan)
    df['Valor'] = df['Valor'].fillna(0.00)
    df['Valor'] = df['Valor'].apply(lambda x: -float(x[1:]) if isinstance(x, str) and x.startswith('-') else float(x))
    df['mes_numero'] = pd.to_numeric(df['mes_numero'], errors='coerce')
    return df

# Selecionando e clicando na caixa de seleção 
def imput_var(xpath,click,driver):
    imput_var = driver.find_element(by=By.XPATH, value=xpath)
    imput_var.click()
    sleep(2)
    var = driver.find_element(by=By.XPATH, value=click)
    var.click()
    sleep(2)
    return var

def gerar_heatmap_e_imagem(ano_inicio, ano_fim):

    url_2010_2023 = 'http://www.yahii.com.br/incc.html'

    tabela_2010_2023 = open_nav(url_2010_2023)

    cards_2010_2023 = html_dados(tabela_2010_2023)

    cards_2010_2023 = tratamento_cards(cards_2010_2023)

    df_incc_2010_2023 = pd.DataFrame(cards_2010_2023) 

    df_incc_2010_2023_acumulado = df_incc_2010_2023[['A/M','ACUMULADO']]

    df_incc_2010_2023 = tratamento(df_incc_2010_2023,20) # 20 index ultima linha desnecessária

    url_1990_2009 = 'http://www.yahii.com.br/incc1990a2009.html'

    tabela_1990_2009 = open_nav(url_1990_2009)

    cards_1990_2009 = html_dados(tabela_1990_2009)

    cards_1990_2009 = tratamento_cards(cards_1990_2009)

    df_incc_1990_2009 = pd.DataFrame(cards_1990_2009) 

    df_incc_1990_2009_acumulado = df_incc_1990_2009[['A/M','ACUMULADO']]

    df_incc_1990_2009 = tratamento(df_incc_1990_2009,20) # 20 index ultima linha desnecessária

    url_1944_1989 = 'http://www.yahii.com.br/incc44a89.html'

    tabela_1944_1989 = open_nav(url_1944_1989)

    cards_1944_1989 = html_dados(tabela_1944_1989)

    cards_1944_1989 = tratamento_cards(cards_1944_1989)

    df_incc_1944_1989 = pd.DataFrame(cards_1944_1989) 

    df_incc_1944_1989_acumulado = df_incc_1944_1989[['A/M','ACUMULADO']]

    df_incc_1944_1989.at[1, 'JAN'] = 0.00

    df_incc_1944_1989 = tratamento(df_incc_1944_1989,46) # 46 index ultima linha desnecessária

    df_incc = pd.concat([df_incc_1944_1989, df_incc_1990_2009, df_incc_2010_2023])
    df_incc = df_incc.reset_index(drop = True)

    url = 'https://www.fipe.org.br/pt-br/indices/ipc/#indice-mensal'

    try:
        # Start do simulador de navegador
        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        print('Navegador aberto')

    except:

        desired_version = '114.0.5735.90'

        # Start do simulador de navegador
        driver = webdriver.Chrome(service=Service(ChromeDriverManager(version=desired_version).install()))
        print('Navegador aberto')

    driver.get(url)

    sleep(1)

    # Selecionando o ano 
    imput_var('//*[@id="MensalAnoV_chosen"]/ul/li/input','//*[@id="MensalAnoV_chosen"]/div/ul/li[1]',driver)

    # Selecionando o mês
    imput_var('//*[@id="MensalMesV_chosen"]/ul/li/input','//*[@id="MensalMesV_chosen"]/div/ul/li[1]',driver)

    # Selecionando a categoria 
    imput_var('//*[@id="MensalCategoriaV_chosen"]/ul/li/input','//*[@id="MensalCategoriaV_chosen"]/div/ul/li[1]',driver)

    sleep(1)

    # Clicando o botão de pesquisa
    botao_pesq = driver.find_element(by=By.XPATH, value='//*[@id="buttonPesquisarMensalVIPC"]')
    botao_pesq.click()

    sleep(5)

    # Coletando o html com as tabelas desejadas
    html = bs(driver.page_source, "html.parser")
    tabelas = html.find('div',{'id':'resultadoMensalV'})

    # Coletando os anos das tabelas 
    a = tabelas.findAll('h3')
    anos = []
    for element in a:
        texto = element.get_text()
        if texto.isdigit():
            anos.append(texto)

    # Separando os html's em listas com os dados a serem trabalhados 
    cards = []
    tabela_results = tabelas.findAll('table',{'id':'tabela_results'})

    driver.quit()
    print('Navegador fechado')

    # Loop para obter os dados desejados dentro das listas de html's
    for tabela,ano in zip(tabela_results,anos):
        for k in tabela:
            card = {}
            for j in k.findAll('td'): 
                card['Ano'] = ano  # Adicionando a chave 'Ano' com o valor do ano atual
                if j['data-head'] == 'Mês':
                    mes_atual = j.get_text('data-head') # Get do mês 
                    card['Mês'] = mes_atual
                if j['data-head'] == 'Habit.':
                    card['Habit.'] = j.get_text('data-head') # Get do habit.
                if j['data-head'] == 'Aliment.':
                    card['Aliment.'] = j.get_text('data-head') # Get do aliment.
                if j['data-head'] == 'Transp.':
                    card['Transp.'] = j.get_text('data-head') # Get do mtransp.
                if j['data-head'] == 'Desp.':
                    card['Desp.'] = j.get_text('data-head') # Get do desp. 
                if j['data-head'] == 'Saúde':
                    card['Saúde'] = j.get_text('data-head') # Get do saúde 
                if j['data-head'] == 'Vest.':
                    card['Vest.'] = j.get_text('data-head') # Get do vest. 
                if j['data-head'] == 'Educ.':
                    card['Educ.'] = j.get_text('data-head') # Get do educ. 
                if j['data-head'] == 'Geral':
                    card['Geral'] = j.get_text('data-head') # Get do geral 

                # Append do dict dentro da lista antes que seja ressetada para procurar infos do próximo mês e ano
                if j['data-head'] == 'Geral':
                    cards.append(card) 
                    card = {}

    df_fipe = pd.DataFrame(cards)

    df_fipe = df_fipe.replace('%', '', regex=True)
    df_fipe = df_fipe.replace(',', '.', regex=True)
    df_fipe['Ano'] = pd.to_datetime(df_fipe['Ano'], format='%Y')
    df_fipe['Ano'] = df_fipe['Ano'].dt.year
    colunas = list(df_fipe.columns)

    meses_n_dict = {'jan': '01', 'fev': '02', 'mar': '03', 'abr': '04', 'mai': '05', 'jun': '06',
                  'jul': '07', 'ago': '08', 'set': '09', 'out': '10', 'nov': '11', 'dez': '12'}
    df_fipe['mes_numero'] = df_fipe['Mês'].map(meses_n_dict)
    df_fipe = df_fipe.sort_values(by=['Ano','mes_numero'])
    df_fipe['mes_numero'] = df_fipe['mes_numero'].astype(int)

    for i in colunas:
        if (i != 'Ano' and i != 'Mês'):
            df_fipe[i] = df_fipe[i].apply(lambda x: -float(x[1:]) if isinstance(x, str) and x.startswith('-') else float(x))

    # Dado mais antigo em comum 1995
    #ano_inicio = 1995
    #ano_fim = 2023

    df_ipca_parcial2 = entre_datas(df_ipca_parcial,'ano',ano_inicio,ano_fim)
    df_ipca_parcial3 = data_atual(df_ipca_parcial2,'ano','mes',ano_fim)

    df_igpm_parcial2 = entre_datas(df_igpm_parcial,'ano',ano_inicio,ano_fim)
    df_igpm_parcial3 = data_atual(df_igpm_parcial2,'ano','mes',ano_fim)

    df_ipca_parcial3 = df_ipca_parcial3.reset_index(drop=True)
    df_igpm_parcial3 = df_igpm_parcial3.reset_index(drop=True)

    #FIPE
    df_fipe_ano = entre_datas(df_fipe,'Ano',ano_inicio,ano_fim)
    df_fipe_ano = data_atual(df_fipe_ano,'Ano','mes_numero',ano_fim)
    df_fipe_ano = df_fipe_ano.reset_index(drop=True)

    #INCC
    df_incc_ano = entre_datas(df_incc,'A/M',ano_inicio,ano_fim)
    df_incc_ano = data_atual(df_incc_ano,'A/M','mes_numero',ano_fim)
    df_incc_ano = data_atual_incc(df_incc_ano,'A/M','mes_numero',ano_fim)
    df_incc_ano = df_incc_ano.reset_index(drop=True)
    df_incc_ano = df_incc_ano.rename(columns={'Valor':'INCC'})

    df_igpm_parcial3['ano'] = df_igpm_parcial3['ano'].astype(int)
    df_ipca_parcial3['ano'] = df_ipca_parcial3['ano'].astype(int)
    df_incc_ano['A/M'] = df_incc_ano['A/M'].astype(int)
    df_fipe_ano['Ano'] = df_fipe_ano['Ano'].astype(int)

    df_concat = pd.concat([df_igpm_parcial3,df_ipca_parcial3[['IPCA']],df_incc_ano[['INCC']],df_fipe_ano[['Habit.','Aliment.','Transp.','Desp.','Saúde','Vest.','Educ.','Geral']]], axis=1)

    correlation = df_concat[['IGPM','IPCA','INCC','Habit.','Aliment.','Transp.','Desp.','Saúde','Vest.','Educ.','Geral']].corr()
    correlation_plot = sn.heatmap(correlation, annot = True, fmt = ".1f", linewidths = .6)

    # Exibir o heatmap usando st.pyplot()
    #correlacao_figure = correlation_plot.get_figure()
    #correlacao_figure.savefig('correcalacao_inflacao.png')
    imagem_nome = f'heatmap_{ano_inicio}_{ano_fim}.png'
    correlation_plot.figure.savefig(imagem_nome)

    if os.path.exists(imagem_nome):
        st.image(imagem_nome)
    else:
        st.write('Erro ao carregar imagem')

st.title('Correlação entre IPCA, IGPM, INCC e tabela FIPE')

ano_inicio = st.number_input("Digite o ano de início:", min_value = 1995)
ano_fim = st.number_input("Digite o ano de fim:", max_value = datetime.now().year)

gerar_grafico = st.button('Gerar Heatmap')

if gerar_grafico:
    gerar_heatmap_e_imagem(ano_inicio,ano_fim)