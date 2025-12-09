import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
import time
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Meu Robô MVP", layout="centered")

st.title("🤖 Robô de Processamento")
st.write("Faça upload da planilha, o robô vai processar e liberar o download.")

# --- 2. FUNÇÃO DO ROBÔ ---
def rodar_robo(caminho_entrada, caminho_saida):
    """
    Lê o arquivo de entrada, processa e salva no caminho_saida.
    Retorna (True, Mensagem) se der certo, ou (False, Erro) se falhar.
    """
    
    # Configuração BLINDADA para Nuvem (Linux)
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Caminhos fixos do servidor Streamlit Cloud
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        # --- AQUI É O TRABALHO DO ROBÔ ---
        st.info("O robô abriu o navegador oculto e começou...")

        # 1. Acessa um site (Simulação)
        driver.get("https://www.google.com")
        
        # 2. Lê a planilha que você subiu
        df = pd.read_excel(caminho_entrada)
        
        # 3. PROCESSAMENTO (Exemplo: Cria uma coluna nova)
        # Aqui você colocaria a lógica de preencher o site.
        # Por enquanto, vamos apenas marcar na planilha que o robô passou.
        df['Status_Robo'] = 'Processado com Sucesso'
        df['Data_Processamento'] = time.strftime("%d/%m/%Y %H:%M")
        
        time.sleep(1) # Simulando tempo de trabalho
        
        # 4. Salva a planilha nova (resultado)
        df.to_excel(caminho_saida, index=False)
        
        return True, "Processamento concluído! Baixe seu arquivo abaixo."

    except Exception as e:
        return False, f"Erro técnico no robô: {e}"
        
    finally:
        if driver:
            driver.quit()

# --- 3. INTERFACE VISUAL ---

arquivo_usuario = st.file_uploader("Selecione o arquivo .xlsx", type=["xlsx"])

if arquivo_usuario is not None:
    # Botão para iniciar
    if st.button("Rodar Robô Agora"):
        
        with st.spinner('O robô está trabalhando na nuvem...'):
            
            # Define nomes de arquivos temporários
            temp_entrada = f"temp_{arquivo_usuario.name}"
            temp_saida = "resultado_final.xlsx"
            
            # 1. Salva o arquivo que o usuário enviou
            with open(temp_entrada, "wb") as f:
                f.write(arquivo_usuario.getbuffer())
            
            # 2. Roda o robô
            sucesso, mensagem = rodar_robo(temp_entrada, temp_saida)
            
            # 3. Verifica o resultado
            if sucesso:
                st.success(mensagem)
                
                # 4. CRIA O BOTÃO DE DOWNLOAD
                with open(temp_saida, "rb") as file:
                    st.download_button(
                        label="📥 Baixar Planilha Processada",
                        data=file,
                        file_name="Lista_Processada.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error(mensagem)
            
            # Limpeza (opcional, remove o arquivo de entrada para não encher o servidor)
            if os.path.exists(temp_entrada):
                os.remove(temp_entrada)
