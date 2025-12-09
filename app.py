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

st.title("🤖 Robô Processador de Listas")
st.write("Faça upload da sua planilha 'Lista_Ouro'. O robô vai pesquisar item por item.")

# --- 2. FUNÇÃO DO ROBÔ ---
def rodar_robo(caminho_entrada, caminho_saida):
    """
    Lê a planilha, entra no site para cada linha, raspa dados e salva.
    """
    
    # --- CONFIGURAÇÃO BLINDADA PARA NUVEM (NÃO MEXA AQUI) ---
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Caminhos fixos do servidor Streamlit Cloud (Crucial para funcionar)
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    
    try:
        # Tenta carregar a planilha que você subiu
        df = pd.read_excel(caminho_entrada)
        
        # Cria uma lista vazia para guardar o que o robô encontrar
        lista_resultados = []

        # Inicia o navegador
        driver = webdriver.Chrome(service=service, options=chrome_options)
        st.info(f"Navegador iniciado! A planilha tem {len(df)} linhas para processar.")

        # Cria uma barra de progresso visual na tela
        barra_progresso = st.progress(0)
        
        # --- AQUI É O LOOP MÁGICO (O CORAÇÃO DO ROBÔ) ---
        # Para cada linha da planilha, ele vai fazer o seguinte:
        for index, row in df.iterrows():
            
            try:
                # Pega o valor da PRIMEIRA coluna da sua planilha (índice 0)
                # Se sua planilha tiver cabeçalho, ele ignora o cabeçalho automaticamente
                termo_pesquisa = str(row.iloc[0]) 
                
                # 1. Entra no site
                driver.get("https://www.google.com")
                
                # 2. Procura a barra de pesquisa e digita
                # (O 'name="q"' é o nome da barra de busca do Google)
                elemento_busca = driver.find_element(By.NAME, "q")
                elemento_busca.clear()
                elemento_busca.send_keys(termo_pesquisa)
                elemento_busca.send_keys(Keys.RETURN) # Aperta Enter
                
                # Espera um pouquinho para a página carregar (importante!)
                time.sleep(2)
                
                # 3. Tenta pegar uma informação da tela
                # (Aqui estamos pegando o texto 'Aproximadamente X resultados')
                try:
                    resultado = driver.find_element(By.ID, "result-stats").text
                except:
                    resultado = "Info não encontrada"
                
                # Adiciona o que achou na lista
                lista_resultados.append(resultado)
                
            except Exception as e:
                # Se der erro numa linha específica, ele não para tudo, apenas anota o erro
                lista_resultados.append(f"Erro nessa linha: {e}")
            
            # Atualiza a barra de progresso
            barra_progresso.progress((index + 1) / len(df))

        # --- FIM DO LOOP ---
        
        # Cria uma coluna nova na planilha chamada "Dados_Coletados"
        df['Dados_Coletados'] = lista_resultados
        
        # Salva o arquivo final
        df.to_excel(caminho_saida, index=False)
        
        return True, "Sucesso! O robô terminou de ler todas as linhas."

    except Exception as e:
        return False, f"Erro grave no sistema: {e}"
        
    finally:
        if driver:
            driver.quit()

# --- 3. INTERFACE VISUAL (BOTÕES E DOWNLOAD) ---

arquivo_usuario = st.file_uploader("Selecione o arquivo .xlsx", type=["xlsx"])

if arquivo_usuario is not None:
    if st.button("Rodar Robô Agora"):
        
        with st.spinner('O robô está trabalhando... Isso pode levar alguns minutos.'):
            
            # Define nomes temporários
            temp_entrada = f"temp_{arquivo_usuario.name}"
            temp_saida = "Relatorio_Final.xlsx"
            
            # Salva o arquivo no servidor
            with open(temp_entrada, "wb") as f:
                f.write(arquivo_usuario.getbuffer())
            
            # Chama a função
            sucesso, mensagem = rodar_robo(temp_entrada, temp_saida)
            
            if sucesso:
                st.success(mensagem)
                # Botão para baixar o resultado
                with open(temp_saida, "rb") as file:
                    st.download_button(
                        label="📥 BAIXAR PLANILHA PRONTA",
                        data=file,
                        file_name="Lista_Processada.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error(mensagem)
            
            # Limpeza
            if os.path.exists(temp_entrada):
                os.remove(temp_entrada)
