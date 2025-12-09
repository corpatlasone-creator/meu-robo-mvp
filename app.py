import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
# from webdriver_manager.chrome import ChromeDriverManager (Não vamos usar esse gerenciador na nuvem)
import time
import os
import shutil

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Meu Robô MVP", layout="centered")

st.title("🤖 Robô de Processamento")
st.write("O sistema está online! Faça o upload da planilha abaixo.")

# --- 2. FUNÇÃO DO ROBÔ (AJUSTADA PARA SERVIDOR) ---
def rodar_robo(caminho_do_arquivo):
    log_txt = ""
    
    # Opções do Chrome
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # --- AQUI ESTÁ O TRUQUE PARA O ERRO DA VERSÃO 143 ---
    # No servidor da nuvem, o Chrome e o Driver ficam nestas pastas específicas:
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")
    
    # Se você for rodar isso no seu PC (Windows), essa parte pode dar erro.
    # Mas para o servidor (Streamlit Cloud), isso resolve o conflito da versão 143.

    try:
        # Inicializa o driver apontando para os arquivos do sistema
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # --- LÓGICA DO ROBÔ ---
        st.info("Iniciando navegador oculto...")
        
        driver.get("https://www.google.com")
        titulo = driver.title
        st.write(f"Conexão com internet OK. Título do site acessado: {titulo}")
        
        # Lendo a planilha enviada
        df = pd.read_excel(caminho_do_arquivo)
        st.write(f"Li a planilha com sucesso! Ela tem {len(df)} linhas.")
        st.dataframe(df.head()) # Mostra as primeiras linhas da planilha na tela
        
        # Simulando processamento
        time.sleep(2)
        
        driver.quit()
        return "Processamento finalizado com sucesso!"

    except Exception as e:
        # Se der erro, tenta explicar melhor
        return f"Erro técnico: {e}"

# --- 3. INTERFACE VISUAL ---

arquivo_usuario = st.file_uploader("Selecione o arquivo .xlsx", type=["xlsx"])

if arquivo_usuario is not None:
    if st.button("Rodar Robô Agora"):
        
        with st.spinner('O robô está trabalhando... Aguarde.'):
            # Salva o arquivo temporariamente
            nome_arquivo_temp = f"temp_{arquivo_usuario.name}"
            with open(nome_arquivo_temp, "wb") as f:
                f.write(arquivo_usuario.getbuffer())
            
            # Chama o robô
            resultado = rodar_robo(nome_arquivo_temp)
            
            if "Erro" in resultado:
                st.error(resultado)
            else:
                st.success(resultado)
            
            # Limpeza
            if os.path.exists(nome_arquivo_temp):
                os.remove(nome_arquivo_temp)
