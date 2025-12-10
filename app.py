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
st.set_page_config(page_title="Robô Filtro OC 2025", layout="centered")

st.title("🛡️ Robô de Seleção (OC 2025 + 300k)")
st.markdown("""
**Regras de Aprovação do Robô:**
1. O processo deve ser do ano **2025** (Ex: ...48.2025.8.26...).
2. O valor deve ser **maior que R$ 300.000,00**.
""")

# --- 2. FUNÇÃO DO ROBÔ ---
def rodar_robo(caminho_entrada, caminho_saida):
    
    # --- CONFIGURAÇÃO BLINDADA PARA NUVEM ---
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")

    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    
    try:
        # Lê a planilha
        df_entrada = pd.read_excel(caminho_entrada)
        
        # Garante a coluna certa
        if "Processos" not in df_entrada.columns:
            coluna_alvo = df_entrada.columns[0]
        else:
            coluna_alvo = "Processos"
            
        lista_processos = df_entrada[coluna_alvo].astype(str).tolist()
        resultados = []

        # Inicia Driver
        driver = webdriver.Chrome(service=service, options=chrome_options)
        
        st.info(f"Aplicando filtro em {len(lista_processos)} processos...")
        barra_progresso = st.progress(0)
        
        # --- LOOP PELOS PROCESSOS ---
        for i, processo in enumerate(lista_processos):
            
            # Limpeza do número
            processo = processo.strip()
            
            dados_processo = {
                "Processo": processo,
                "Ano_Identificado": "N/D",
                "Valor_Numerico": 0.0,
                "Status": "AGUARDANDO"
            }

            # --- REGRA 1: VERIFICA SE É 2025 ANTES MESMO DE ENTRAR NO SITE ---
            # O número padrão CNJ tem o ano na 3ª parte: NNNNNNN-DD.AAAA.J.TR.OOOO
            # Ex: 1000872-48.2025.8.26.0100 -> O robô procura ".2025."
            eh_ano_25 = ".2025." in processo or "2025" in processo
            
            dados_processo["Ano_Identificado"] = "2025" if eh_ano_25 else "Outro"

            # Se NÃO for 2025, a gente já pode descartar ou marcar, mas
            # vamos entrar no site de qualquer jeito para pegar o valor e ter certeza?
            # Se você quiser economizar tempo, podemos pular os que não são 2025.
            # Vou deixar ele verificar todos para garantir o valor.

            try:
                driver.get("https://esaj.tjsp.jus.br/cpopg/open.do")
                
                # Quebra o número para preencher
                if "8.26" in processo:
                    parte_numero_ano = processo.split("8.26")[0].strip(".")
                    parte_foro = processo.split(".")[-1]
                else:
                    parte_numero_ano = processo
                    parte_foro = ""

                # Preenche e consulta
                driver.find_element(By.ID, "numeroDigitoAnoUnificado").clear()
                driver.find_element(By.ID, "numeroDigitoAnoUnificado").send_keys(parte_numero_ano)
                driver.find_element(By.ID, "foroNumeroUnificado").clear()
                driver.find_element(By.ID, "foroNumeroUnificado").send_keys(parte_foro)
                driver.find_element(By.ID, "botaoConsultarProcessos").click()

                # Tratamento de popup de seleção
                try:
                    lista = driver.find_elements(By.ID, "processoSelecionado")
                    if lista:
                        lista[0].click()
                        driver.find_element(By.ID, "botaoDetalhes").click()
                except: pass
                
                WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.ID, "tabelaTodasMovimentacoes")))
                
                # Expande detalhes
                try:
                    link = driver.find_element(By.ID, "linkMaisDetalhes")
                    if link.is_displayed(): link.click()
                except: pass

                # --- BUSCA VALOR ---
                valor_bruto = ""
                try:
                    elem = driver.find_element(By.ID, "valorAcaoProcesso")
                    valor_bruto = elem.get_attribute("textContent")
                except: pass

                # Limpeza do Valor (R$ 1.000,00 -> 1000.00)
                valor_limpo = "".join([c for c in valor_bruto if c.isdigit()])
                try: 
                    valor_float = float(valor_limpo) / 100 
                except: 
                    valor_float = 0.0

                # --- APLICAÇÃO DAS REGRAS FINAIS ---
                # Regra: Ano 2025 E Valor > 300.000
                
                if eh_ano_25 and valor_float > 300000:
                    status = "✅ APROVADO (OC 25 + >300k)"
                elif eh_ano_25 and valor_float <= 300000:
                    status = "❌ REPROVADO (OC 25 mas Valor Baixo)"
                else:
                    status = "❌ REPROVADO (Ano Incorreto)"

                # Salva os dados
                dados_processo["Valor_Numerico"] = valor_float
                dados_processo["Status"] = status

                # Pequena pausa
                time.sleep(0.5)

            except Exception as e:
                dados_processo["Status"] = f"Erro ao ler site"

            resultados.append(dados_processo)
            barra_progresso.progress((i + 1) / len(lista_processos))

        # --- FIM DO LOOP ---
        
        df_final = pd.DataFrame(resultados)
        
        # Filtra para o Excel final mostrar primeiro os APROVADOS
        df_final = df_final.sort_values(by="Valor_Numerico", ascending=False)
        
        df_final.to_excel(caminho_saida, index=False)
        return True, "Filtro concluído! Baixe a planilha classificada."

    except Exception as e:
        return False, f"Erro Crítico: {e}"
        
    finally:
        if driver:
            driver.quit()

# --- 3. INTERFACE VISUAL ---

arquivo_usuario = st.file_uploader("Suba a planilha com os Processos", type=["xlsx"])

if arquivo_usuario is not None:
    if st.button("🔍 Filtrar OC 25 > 300k"):
        
        with st.spinner('O robô está verificando ano e valores...'):
            temp_entrada = f"temp_{arquivo_usuario.name}"
            temp_saida = "Resultado_Filtro_OC25.xlsx"
            
            with open(temp_entrada, "wb") as f:
                f.write(arquivo_usuario.getbuffer())
            
            sucesso, mensagem = rodar_robo(temp_entrada, temp_saida)
            
            if sucesso:
                st.success(mensagem)
                with open(temp_saida, "rb") as file:
                    st.download_button(
                        label="📥 Baixar Planilha Filtrada",
                        data=file,
                        file_name="Processos_OC25_Filtrados.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
            else:
                st.error(mensagem)
            
            if os.path.exists(temp_entrada):
                os.remove(temp_entrada)
