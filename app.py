import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import time
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Meu Robô MVP", layout="centered")

st.title("🤖 Robô de Processamento")
st.write("Faça upload da planilha para iniciar a raspagem de dados.")

# --- 2. FUNÇÃO DO ROBÔ (LÓGICA REAL) ---
def rodar_robo(caminho_entrada, caminho_saida):
    """
    Lê a planilha, entra no site para cada linha, raspa dados e salva.
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
        # Tenta carregar a planilha
        df = pd.read_excel(caminho_entrada)
        
        # Cria uma lista para salvar os resultados
        resultados_raspados = []

        # Inicia o navegador
        driver = webdriver.Chrome(service=service, options=chrome_options)
        st.info(f"Navegador iniciado. Processando {len(df)} itens...")

        # --- LOOP: PERCORRE CADA LINHA DA PLANILHA ---
        # ATENÇÃO: Verifique se sua planilha tem a coluna certa. 
        # Aqui estou assumindo que a coluna de busca se chama 'Termo_Busca' ou é a primeira coluna.
        # Se não tiver cabeçalho, usamos a primeira coluna.
        
        # Barra de progresso visual
        barra_progresso = st.progress(0)
        
        for index, row in df.iterrows():
            try:
                # Pega o valor da primeira coluna para pesquisar (ajuste se necessário)
                termo_para_pesquisar = str(row.iloc[0]) 
                
                # 1. Acessa o Google
                driver.get("https://www.google.com")
                
                # 2. Encontra a barra de pesquisa
                # (O ID ou Name pode mudar, 'q' costuma ser o padrão do Google)
                search_box = driver.find_element(By.NAME, "q")
                
                # 3. Digita e dá Enter
                search_box.clear()
                search_box.send_keys(termo_para_pesquisar)
                search_box.send_keys(Keys.RETURN)
                
                # Espera carregar um pouco
                time.sleep(2)
                
                # 4. RASPAGE (Exemplo: Pegar o título do primeiro resultado ou o número de resultados)
                # Vamos pegar o elemento que mostra "Aproximadamente X resultados"
                try:
                    stats = driver.find_element(By.ID, "result-stats").text
                except:
                    stats = "Não encontrado"
                
                # Salva na lista
                resultados_raspados.append(stats)
                
            except Exception as e_linha:
                resultados_raspados.append(f"Erro na linha: {e_linha}")
            
            # Atualiza barra de progresso
            barra_progresso.progress((index + 1) / len(df))

        # --- FIM DO LOOP ---
        
        # Adiciona os resultados numa nova coluna na planilha
        df['Resultado_Raspagem'] = resultados_raspados
        
        # Salva o arquivo final
        df.to_excel(caminho_saida, index=False)
        
        return True, "Processamento concluído com sucesso!"

    except Exception as e:
        return False, f"Erro grave no robô: {e}"
        
    finally:
        if driver:
            driver.quit()

# --- 3. INTERFACE VISUAL ---

arquivo_usuario = st.file_uploader("Selecione o arquivo .xlsx", type=["xlsx"])

if arquivo_usuario is not None:
    if st.button("Rodar Robô Agora"):
        
        with st.spinner('O robô está navegando e coletando dados...'):
            
            temp_entrada = f"temp_{arquivo_usuario.name}"
            temp_saida = "resultado_final.xlsx"
            
            with open(temp_entrada, "wb") as f:
                f.write(arquivo_usuario.getbuffer())
            
            sucesso, mensagem = rodar_robo(temp_entrada, temp_saida)
            
            if sucesso:
                st.success(mensagem)
                with open(temp_saida, "rb") as file:
                    st.download_button(
                        label="📥 Baixar Planilha Completa",
                        data=file,
                        file_name="Resultado_Raspagem.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error(mensagem)
            
            if os.path.exists(temp_entrada):
                os.remove(temp_entrada)
