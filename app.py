import streamlit as st
import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import os

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Robô TJSP - Avaliação", layout="centered")

st.title("⚖️ Robô de Triagem TJSP")
st.markdown("""
**Instruções:**
1. Suba uma planilha Excel (.xlsx).
2. A planilha **DEVE** ter uma coluna chamada **"Processos"**.
3. O robô vai verificar valores acima de R$ 250k.
""")

# --- 2. FUNÇÃO DO ROBÔ (A LÓGICA DO SEU VS CODE ADAPTADA) ---
def rodar_robo(caminho_entrada, caminho_saida):
    
    # --- CONFIGURAÇÃO BLINDADA PARA NUVEM ---
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    # Caminhos do servidor Streamlit Cloud
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    
    try:
        # Lê a planilha
        df_entrada = pd.read_excel(caminho_entrada)
        
        # Verifica se a coluna existe
        if "Processos" not in df_entrada.columns:
            # Tenta ser inteligente: se não achar "Processos", pega a primeira coluna
            coluna_alvo = df_entrada.columns[0]
            st.warning(f"Aviso: Não achei a coluna 'Processos'. Usando a coluna '{coluna_alvo}' como base.")
        else:
            coluna_alvo = "Processos"
            
        lista_processos = df_entrada[coluna_alvo].astype(str).tolist()
        resultados = []

        # Inicia Driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        st.info(f"Iniciando triagem de {len(lista_processos)} processos no TJSP...")
        barra_progresso = st.progress(0)
        
        # --- LOOP PELOS PROCESSOS ---
        for i, processo in enumerate(lista_processos):
            
            dados_processo = {
                "Processo": processo,
                "Valor_Bruto": "N/D",
                "Valor_Numerico": 0.0,
                "Status": "ERRO/NÃO ENCONTRADO"
            }

            try:
                # Limpeza básica do número para evitar espaços
                processo = processo.strip()
                
                driver.get("https://esaj.tjsp.jus.br/cpopg/open.do")
                
                # --- SUA LÓGICA DE TRATAMENTO DO NÚMERO ---
                # Exemplo: 1000872-48.2023.8.26.0100
                if "8.26" in processo:
                    parte_numero_ano = processo.split("8.26")[0].strip(".")
                    parte_foro = processo.split(".")[-1]
                else:
                    # Caso o número venha formatado diferente, tenta uma contingência simples
                    parte_numero_ano = processo # Tenta jogar inteiro se falhar o split
                    parte_foro = ""

                # Preenche os campos
                driver.find_element(By.ID, "numeroDigitoAnoUnificado").clear()
                driver.find_element(By.ID, "numeroDigitoAnoUnificado").send_keys(parte_numero_ano)
                
                driver.find_element(By.ID, "foroNumeroUnificado").clear()
                driver.find_element(By.ID, "foroNumeroUnificado").send_keys(parte_foro)
                
                driver.find_element(By.ID, "botaoConsultarProcessos").click()

                # --- TRATAMENTO DE LISTA (SE HOUVER DUPLICIDADE) ---
                try:
                    lista = driver.find_elements(By.ID, "processoSelecionado")
                    if lista:
                        lista[0].click()
                        driver.find_element(By.ID, "botaoDetalhes").click()
                except:
                    pass
                
                # Espera tabela carregar
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "tabelaTodasMovimentacoes")))

                # --- EXPANDIR DETALHES ---
                try:
                    link = driver.find_element(By.ID, "linkMaisDetalhes")
                    if link.is_displayed():
                        link.click()
                except:
                    pass

                # --- BUSCA VALOR ---
                valor_bruto = ""
                # Tentativa 1: Pelo ID direto
                try:
                    elem = driver.find_element(By.ID, "valorAcaoProcesso")
                    valor_bruto = elem.get_attribute("textContent")
                except:
                    pass

                # Tentativa 2: Varredura no texto (Backup)
                if "R$" not in valor_bruto:
                    conteudo = driver.find_element(By.TAG_NAME, "body").text
                    if "Valor da ação:" in conteudo:
                        inicio = conteudo.find("Valor da ação:") + 14
                        fim = conteudo.find("\n", inicio)
                        valor_bruto = conteudo[inicio:fim]

                # --- LIMPEZA MATEMÁTICA ---
                # Remove tudo que não é dígito para converter
                valor_limpo = "".join([c for c in valor_bruto if c.isdigit()])
                
                try: 
                    # Divide por 100 para ajustar os centavos
                    valor_float = float(valor_limpo) / 100 
                except: 
                    valor_float = 0.0

                # --- REGRA DE NEGÓCIO (> 250 mil) ---
                status = "DESCARTAR"
                if valor_float > 250000:
                    status = "POTENCIAL COMPRA 💰"

                # Salva os dados
                dados_processo["Valor_Bruto"] = valor_bruto.strip()
                dados_processo["Valor_Numerico"] = valor_float
                dados_processo["Status"] = status

                # Pausa de segurança suave
                time.sleep(1)

            except Exception as e:
                # Se falhar, registra o erro mas continua o loop
                dados_processo["Status"] = f"Falha na leitura: {str(e)[:50]}..."

            resultados.append(dados_processo)
            
            # Atualiza barra
            barra_progresso.progress((i + 1) / len(lista_processos))

        # --- FIM DO LOOP ---
        
        # Cria DataFrame final
        df_final = pd.DataFrame(resultados)
        df_final.to_excel(caminho_saida, index=False)
        
        return True, "Análise concluída com sucesso!"

    except Exception as e:
        return False, f"Erro Crítico: {e}"
        
    finally:
        if driver:
            driver.quit()

# --- 3. INTERFACE VISUAL ---

arquivo_usuario = st.file_uploader("Selecione sua planilha de processos (.xlsx)", type=["xlsx"])

if arquivo_usuario is not None:
    if st.button("🔍 Iniciar Varredura TJSP"):
        
        with st.spinner('O robô está trabalhando no TJSP...'):
            temp_entrada = f"temp_{arquivo_usuario.name}"
            temp_saida = "Relatorio_Final_Auto.xlsx"
            
            with open(temp_entrada, "wb") as f:
                f.write(arquivo_usuario.getbuffer())
            
            sucesso, mensagem = rodar_robo(temp_entrada, temp_saida)
            
            if sucesso:
                st.success(mensagem)
                st.balloons() # Um efeito visual de comemoração
                with open(temp_saida, "rb") as file:
                    st.download_button(
                        label="📥 Baixar Relatório (Potenciais Compras)",
                        data=file,
                        file_name="Relatorio_Final_TJ.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error(mensagem)
            
            if os.path.exists(temp_entrada):
                os.remove(temp_entrada)
