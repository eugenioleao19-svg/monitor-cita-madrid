import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SERVIDOR WEB SECUNDÁRIO (Para manter a conta Free do Render ativa) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot de monitorizacao ativo!")

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

# Inicia o servidor web em segundo plano
threading.Thread(target=run_server, daemon=True).start()


# --- CONFIGURAÇÕES DO ROBÔ ---
URL = "https://gestiona7.madrid.org/ctac_cita/registro#"

# COLOCA AQUI OS TEUS DADOS REAIS ENTRE AS ASPAS:
TELEGRAM_TOKEN = "8772689124:AAHVK1i6dYQDbPvWVUTuB6yI3QQpANrd1L8"
TELEGRAM_CHAT_ID = "8908857291"

def enviar_alerta(mensagem):
    if TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, json={"chat_id": TELEGRAM_CHAT_ID, "text": mensagem})
        except Exception as e:
            print(f"Erro ao enviar aviso: {e}")

def tentar_avancar_pagina():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://gestiona7.madrid.org/ctac_cita/registro"
    }
    
    try:
        # Passo 1: Obter a página inicial
        resposta = session.get(URL, headers=headers, timeout=15)
        if resposta.status_code != 200:
            return False

        # Passo 2: Simular o envio do formulário de Getafe / Nacionalidade para "Continuar"
        dados_formulario = {
            "rbtnCentro": "28067401",
            "sServicio": "NACIONALIDAD V.S.P",
            "btnContinuar": "Continuar"
        }
        
        resposta_post = session.post(URL, headers=headers, data=dados_formulario, timeout=15)
        conteudo = resposta_post.text
        
        # O robô só considera sucesso SE PASSAR da página inicial de selección/indisponibilidad
        if "Acciones" in conteudo or "Día y hora de la cita" in conteudo or "Seleccione la operación" not in conteudo:
            if "No hay citas disponibles" not in conteudo:
                return True
                
    except Exception as e:
        print(f"Erro na tentativa de avanço: {e}")
        
    return False

tentativa = 1
print("A iniciar o monitoramento focado em transpor a tela de citas...")

# Mensagem inicial de arranque
enviar_alerta("🚀 Robô configurado! A monitorizar e a tentar passar da tela de Getafe de 5 em 5 minutos.")

while True:
    try:
        print(f"[Tentativa {tentativa}] A tentar avançar no portal de Getafe...")
        
        if tentar_avancar_pagina():
            # Sucesso! Conseguiu passar da página. Dispara alertas repetidos para o Telegram.
            for i in range(10):
                msg = f"🚨 SUCESSO ABSOLUTO (Aviso {i+1}/10) 🚨\nO robô conseguiu PASSAR da página de indisponibilidade!\nAceda imediatamente: {URL}"
                enviar_alerta(msg)
                time.sleep(2)
            break # Termina o ciclo para te dar total liberdade de agendamento
        else:
            print("Ainda bloqueado na tela inicial / sem vagas. A aguardar 5 minutos...")
            
    except Exception as e:
        print(f"Erro no ciclo: {e}")
    
    tentativa += 1
    # Pausa de 5 minutos (300 segundos) entre cada verificação
    time.sleep(300)
