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

def verificar_vaga():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resposta = session.get(URL, headers=headers, timeout=15)
        if resposta.status_code == 200:
            conteudo = resposta.text
            # Se a página mudou e já não mostra a mensagem clássica de indisponível
            if "No hay citas disponibles" not in conteudo and "Elección del servicio" not in conteudo:
                return True
    except Exception as e:
        print(f"Erro na verificação: {e}")
        
    return False

tentativa = 1
print("A iniciar o monitoramento contínuo...")

# Mensagem inicial de arranque
enviar_alerta("🚀 Robô de Getafe configurado! A verificar vagas de 5 em 5 minutos com alertas repetidos.")

while True:
    try:
        print(f"[Tentativa {tentativa}] Verificando o Portal de Justiça (Getafe)...")
        
        if verificar_vaga():
            # Dispara alertas repetidos para o Telegram chamar a atenção
            for i in range(5):
                msg = f"🚨 ALERTA DE CITA (Tentativa {i+1}) 🚨\nVagas detetadas ou alteração no portal!\nAceda imediatamente: {URL}"
                enviar_alerta(msg)
                time.sleep(2)
        else:
            print("Sem vagas no momento. A aguardar 5 minutos para a próxima verificação...")
            
    except Exception as e:
        print(f"Erro no ciclo: {e}")
    
    tentativa += 1
    # Pausa exata de 5 minutos (300 segundos) entre cada verificação
    time.sleep(300)
