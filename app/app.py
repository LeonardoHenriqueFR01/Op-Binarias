import telegram
from telegram.ext import Updater, CommandHandler
import yfinance as yf
import numpy as np
import schedule
import time
from datetime import datetime, timedelta
from dotenv import load_dotenv
import os
import random


# Carregar variáveis do arquivo .env
load_dotenv()

TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
CHAT_ID = "5936851416"

# Inicializa o bot
bot = telegram.Bot(token=TOKEN)

# Lista de ativos a serem monitorados
ativos = ["EURUSD=X", "GBPUSD=X", "USDJPY=X", "BTC-USD", "ETH-USD"]

# Armazena as negociações ativas
negociacoes_ativas = []

# Função para simular o resultado da negociação (ganha ou perdida)
def resultado_negociacao():
    """Simula o resultado da negociação (ganha ou perdida)"""
    return random.choice(["ganha", "perdida"])

def calcular_rsi(precos, periodo=14):
    """Calcula o RSI manualmente"""
    if len(precos) < periodo:
        return None

    ganhos = np.diff(precos)
    ganhos_positivos = np.where(ganhos > 0, ganhos, 0)
    perdas_negativas = np.where(ganhos < 0, -ganhos, 0)

    media_ganhos = np.mean(ganhos_positivos[:periodo])
    media_perdas = np.mean(perdas_negativas[:periodo])

    if media_perdas == 0:
        return 100  # RSI máximo
    rs = media_ganhos / media_perdas
    return 100 - (100 / (1 + rs))


def obter_sinal():
    global negociacoes_ativas
    try:
        mensagem = "🔍 **Analisando mercados...**\n"

        # Limita a análise para apenas duas negociações abertas
        if len(negociacoes_ativas) >= 2:
            mensagem += "⚠️ Já há 2 negociações ativas. Aguardando encerramento...\n"
            bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
            return

        for ativo in ativos:
            if len(negociacoes_ativas) >= 2:
                break  # Para quando atingir o limite de 2 negociações
            
            dados = yf.Ticker(ativo).history(period="1d", interval="1m")
            
            if dados.empty:
                mensagem += f"⚠️ Não foi possível obter os dados de {ativo}.\n"
                continue

            fechamento = dados["Close"].values
            rsi = calcular_rsi(fechamento, periodo=14)

            if rsi is None:
                mensagem += f"⚠️ Poucos dados para calcular o RSI de {ativo}.\n"
                continue

            agora = datetime.now()
            saida = agora + timedelta(minutes=10)
            agora_str = agora.strftime("%Y-%m-%d %H:%M:%S")
            saida_str = saida.strftime("%Y-%m-%d %H:%M:%S")

            # Verifica sinais de compra/venda
            if rsi < 30:
                mensagem += f"✅ **SINAL DE COMPRA** ({ativo}): RSI = {rsi:.2f} 📈\n🕐 Entrada: {agora_str} | Saída: {saida_str}\n"
                negociacoes_ativas.append({"ativo": ativo, "tipo": "compra", "entrada": agora_str, "saida": saida_str})
            elif rsi > 70:
                mensagem += f"❌ **SINAL DE VENDA** ({ativo}): RSI = {rsi:.2f} 📉\n🕐 Entrada: {agora_str} | Saída: {saida_str}\n"
                negociacoes_ativas.append({"ativo": ativo, "tipo": "venda", "entrada": agora_str, "saida": saida_str})
            else:
                mensagem += f"⏳ Nenhum sinal para {ativo}. RSI = {rsi:.2f}\n"
        
        bot.send_message(chat_id=CHAT_ID, text=mensagem, parse_mode="Markdown")
    
    except Exception as e:
        bot.send_message(chat_id=CHAT_ID, text=f"⚠️ **Erro ao obter sinais:** {e}")


def fechar_negociacoes():
    """Simula o encerramento das negociações após um tempo"""
    global negociacoes_ativas
    if negociacoes_ativas:
        negociacao = negociacoes_ativas.pop(0)  # Fecha a negociação mais antiga
        resultado = resultado_negociacao()  # Simula o resultado da negociação
        mensagem = f"📉 **Negociação encerrada** ({negociacao['ativo']} - {negociacao['tipo']})\n"
        mensagem += f"🕐 Entrada: {negociacao['entrada']} | Saída: {negociacao['saida']}\n"
        mensagem += f"💥 Resultado: **{resultado.upper()}**"
        bot.send_message(chat_id=CHAT_ID, text=mensagem)


# Agendar execução a cada 5 minutos
schedule.every(5).minutes.do(obter_sinal)
schedule.every(10).minutes.do(fechar_negociacoes)  # Fecha negociações a cada 10 min

bot.send_message(chat_id=CHAT_ID, text="📡 **Bot de sinais iniciado!**")
obter_sinal()  # Executa a primeira vez

while True:
    schedule.run_pending()
    time.sleep(1)
