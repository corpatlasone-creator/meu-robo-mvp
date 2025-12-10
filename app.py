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
import re

# --- 1. CONFIGURAÇÃO DA PÁGINA ---
st.set_page_config(page_title="Garimpeiro TJSP 2025", layout="centered")

st.title("⛏️ Robô Garimpeiro TJSP (2025)")
st.markdown("""
**Modo 100% Autônomo:**
O robô vai **GERAR** números de processos sequenciais do ano de 2025, verificar se existem e filtrar os valores altos.
""")

# --- 2. FUNÇÃO MATEMÁTICA (CRIA O NÚMERO VÁLIDO) ---
def calcular_digito_cnj(numero_sequencial, ano, orgao=8, tribunal=26, foro=100):
    """
    Calcula os dígitos verificadores (DD) conforme regra do CNJ (Módulo 97).
    Ex: Para 1000872, ano 2025 -> Retorna o número completo com traço.
    """
    # Formato CNJ: NNNNNNN-DD.AAAA.J.TR.OOOO
    # A fórmula coloca tudo num numerão só e faz MOD 97
    numero_base = f"{int(numero_sequencial):07d}{ano}{orgao:01d}{tribunal:02d}{foro:04d}00"
    numero_int = int(numero_base)
    resto = numero_int % 97
    digito = 98 - resto
    
    return f"{int(numero_sequencial):07d}-{digito:02d}.{ano}.{orgao}.{tribunal}.{foro:04d}"

# --- 3. FUNÇÃO DO ROBÔ ---
def rodar_garimpo(inicio_seq, quantidade, foro_id):
    
    # --- CONFIGURAÇÃO NUVEM ---
    chrome_options = Options()
    chrome_options.add_argument("--headless=new") 
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    
    chrome_options.binary_location = "/usr/bin/chromium"
    service = Service("/usr/bin/chromedriver")

    driver = None
    resultados = []
    
    try:
        driver = webdriver.Chrome(service=service, options=chrome_options)
        wait = WebDriverWait(driver, 3) # Espera curta para ser rápido
        
        st.info(f"Gerando lista de {quantidade} números a partir do sequencial {inicio_seq}...")
        barra_progresso = st.progress(0)
        
        # --- LOOP DE GERAÇÃO E TESTE ---
        for i in range(quantidade):
            
            # 1. GERA O NÚMERO
            seq_atual = inicio_seq + i
            processo_gerado = calcular_digito_cnj(seq_atual, 2025, foro=int(foro_id))
            
            dados = {
                "Processo": processo_gerado,
                "Status_Site": "Não verificado",
                "Valor": 0.0,
                "Resultado": "DESCARTADO"
            }

            try:
                driver.get("https://esaj.tjsp.jus.br/cpopg/open.do")
                
                # Quebra para preencher (Redundância necessária para o site)
                parte_numero = processo_gerado.split("-")[0]
                parte_digito = processo_gerado.split("-")[1].split(".")[0]
                parte_foro_str = str(foro_id)

                # Preenche campos
                campo_num = driver.find_element(By.ID, "numeroDigitoAnoUnificado")
                campo_num.clear()
                # Digita NNNNNNNDD2025 (O campo aceita tudo junto)
                campo_num.send_keys(f"{parte_numero}{parte_digito}2025")
                
                campo_foro = driver.find_element(By.ID, "foroNumeroUnificado")
                campo_foro.clear()
                campo_foro.send_keys(parte_foro_str)
                
                driver.find_element(By.ID, "botaoConsultarProcessos").click()

                # --- VERIFICA SE O PROCESSO EXISTE ---
                # Se aparecer mensagem de erro, o processo ainda não foi distribuído
                try:
                    msg = driver.find_element(By.ID, "mensagemRetorno").text
                    if "Não existem" in msg:
                        dados["Status_Site"] = "INEXISTENTE (Vago)"
                        resultados.append(dados)
                        barra_progresso.progress((i + 1) / quantidade)
                        continue # Pula para o próximo
                except:
                    pass # Se não tem erro, o processo existe!

                # Clica se for lista
                try:
                    lista = driver.find_elements(By.ID, "processoSelecionado")
                    if lista:
                        lista[0].click()
                        driver.find_element(By.ID, "botaoDetalhes").click()
                except: pass
                
                # Espera carregar
                wait.until(EC.presence_of_element_located((By.ID, "tabelaTodasMovimentacoes")))
                dados["Status_Site"] = "ATIVO"

                # --- LÊ O VALOR ---
                texto_pagina = driver.find_element(By.TAG_NAME, "body").text
                valor_bruto = "0"
                
                if "Valor da ação:" in texto_pagina:
                    inicio = texto_pagina.find("Valor da ação:") + 14
                    fim = texto_pagina.find("\n", inicio)
                    valor_bruto = texto_pagina[inicio:fim]

                # Limpa valor
                valor_limpo = "".join([c for c in valor_bruto if c.isdigit()])
                try:
                    valor_float = float(valor_limpo) / 100
                except:
                    valor_float = 0.0
                
                dados["Valor"] = valor_float

                # --- FILTRO DE OURO (> 300k) ---
                if valor_float > 300000:
                    dados["Resultado"] = "✅ ACHAMOS OURO!"
                else:
                    dados["Resultado"] = "Valor Baixo"

            except Exception as e:
                dados["Status_Site"] = "Erro de Leitura"
            
            resultados.append(dados)
            barra_progresso.progress((i + 1) / quantidade)
            
            # Pequena pausa
            time.sleep(0.5)

        # --- FIM ---
        df_final = pd.DataFrame(resultados)
        
        # Filtra para salvar só o que existe (opcional)
        # df_final = df_final[df_final["Status_Site"] == "ATIVO"]
        
        df_final = df_final.sort_values(by="Valor", ascending=False)
        return df_final

    except Exception as e:
        st.error(f"Erro Crítico: {e}")
        return pd.DataFrame()
        
    finally:
        if driver:
            driver.quit()

# --- 4. INTERFACE DE COMANDO ---

col1, col2 = st.columns(2)
with col1:
    inicio = st.number_input("Começar do Nº Sequencial:", min_value=1, value=1000000, step=1)
    st.caption("Ex: 1000000 (para gerar 1000000-xx.2025...)")

with col2:
    qtd = st.number_input("Quantos investigar?", min_value=1, max_value=50, value=10)
    st.caption("Recomendado: 10 a 20 por vez para não bloquear.")

foro = st.text_input("Código do Foro (Padrão SP Capital = 0100)", value="0100")

if st.button("⛏️ Iniciar Garimpo"):
    with st.spinner(f"O robô está gerando números de 2025 e testando no Foro {foro}..."):
        
        df_resultado = rodar_garimpo(inicio, qtd, foro)
        
        if not df_resultado.empty:
            st.success("Varredura concluída!")
            st.dataframe(df_resultado)
            
            # Botão Download
            csv = df_resultado.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Baixar Relatório",
                data=csv,
                file_name="Garimpo_TJSP.csv",
                mime="text/csv",
            )
        else:
            st.warning("Nenhum dado foi coletado ou ocorreu um erro.")
