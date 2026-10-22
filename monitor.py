import time
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler

# --- SERVIDOR WEB SECUNDÁRIO (Necessário para a conta Free do Render) ---
class SimpleHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"Bot de monitorizacao ativo!")

def run_server():
    server = HTTPServer(('0.0.0.0', 10000), SimpleHandler)
    server.serve_forever()

# Inicia o servidor web em segundo plano para o Render não dar erro
threading.Thread(target=run_server, daemon=True).start()


# --- CONFIGURAÇÕES DO ROBÔ ---
URL = "https://gestiona7.madrid.org/ctac_cita/registro#"


# ==============================================================================
# 🚨 ***SUBSTITUI APENAS O QUE ESTÁ DENTRO DAS ASPAS ABAIXO*** 🚨
# ==============================================================================

TELEGRAM_TOKEN = "8772689124:AAHVK1i6dYQDbPvWVUTuB6yI3QQpANrd1L8"
TELEGRAM_CHAT_ID = "8908857291"

# ==============================================================================


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
    
    resposta = session.get(URL, headers=headers, timeout=15)
    
    if resposta.status_code == 200:
        conteudo = resposta.text
        if "No hay citas disponibles" not in conteudo and "Elección del servicio" not in conteudo:
            return True
    return False

tentativa = 1
print("A iniciar o monitoramento de vagas...")

# Alerta de boas-vindas no Telegram assim que o robô liga
enviar_alerta("🚀 Robô do Render iniciado com sucesso! A monitorizar vagas no Portal de Justiça 24/7.")

while True:
    try:
        print(f"[Tentativa {tentativa}] Verificando o Portal de Justiça...")
        if verificar_vaga():
            msg = f"🚨 ATENÇÃO: Mudança detetada no portal de citas!\nAceda imediatamente: {URL}"
            print(msg)
            enviar_alerta(msg)
            break
        else:
            print("Sem vagas no momento. Aguardando próximo ciclo...")
    except Exception as e:
        print(f"Erro na verificação: {e}")
    
    tentativa += 1
    time.sleep(60)
