import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
import time
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA (Deve ser a primeira coisa) ---
st.set_page_config(page_title="Meu Robô MVP", layout="centered")

st.title("🤖 Robô de Processamento")
st.write("O sistema está online! Faça o upload da planilha abaixo.")

# --- 2. FUNÇÃO DO ROBÔ (MODO FANTASMA) ---
def rodar_robo(caminho_do_arquivo):
    """
    Roda o Selenium em modo Headless (sem janela) para funcionar na nuvem.
    """
    log_txt = ""
    
    # Opções obrigatórias para servidor Linux
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    try:
        # Instala e inicia o Chrome
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # --- LÓGICA DO ROBÔ ---
        st.info("Iniciando navegador oculto...")
        
        # Exemplo: Acessa Google (substitua pelo seu site alvo)
        driver.get("https://www.google.com")
        titulo = driver.title
        st.write(f"Acessou o site: {titulo}")
        
        # Lendo a planilha enviada (Exemplo)
        df = pd.read_excel(caminho_do_arquivo)
        st.write(f"Li uma planilha com {len(df)} linhas.")
        
        # Simulando trabalho
        time.sleep(2)
        
        driver.quit()
        return "Processamento finalizado com sucesso!"

    except Exception as e:
        return f"Erro no robô: {e}"

# --- 3. INTERFACE VISUAL DO STREAMLIT ---

# Botão de Upload
arquivo_usuario = st.file_uploader("Selecione o arquivo .xlsx", type=["xlsx"])

if arquivo_usuario is not None:
    # Mostra um botão para iniciar
    if st.button("Rodar Robô Agora"):
        
        with st.spinner('O robô está trabalhando... Aguarde.'):
            # Salva o arquivo temporariamente para o robô ler
            nome_arquivo_temp = f"temp_{arquivo_usuario.name}"
            with open(nome_arquivo_temp, "wb") as f:
                f.write(arquivo_usuario.getbuffer())
            
            # Chama a função do robô
            resultado = rodar_robo(nome_arquivo_temp)
            
            # Mostra o resultado
            if "Erro" in resultado:
                st.error(resultado)
            else:
                st.success(resultado)
            
            # Limpeza: remove o arquivo temporário
            os.remove(nome_arquivo_temp)
