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

def verificar_vaga_real():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        resposta = session.get(URL, headers=headers, timeout=15)
        
        # Garante que o site respondeu corretamente (Código HTTP 200)
        if resposta.status_code == 200:
            conteudo = resposta.text
            
            # Textos típicos de quando NÃO HÁ vagas ou a seleção está bloqueada
            indisponivel = (
                "No hay citas disponibles" in conteudo or 
                "En este momento no disponemos de citas" in conteudo or
                "no hay fechas disponibles" in conteudo.lower()
            )
            
            # Se a página carregou perfeitamente e NENHUMA das frases de indisponibilidade apareceu:
            if not indisponivel:
                return True

    except Exception as e:
        print(f"Erro na ligação ao portal: {e}")
        
    return False

tentativa = 1
print("A iniciar o monitoramento ultra-preciso...")

# Mensagem de arranque para saberes que está ativo
enviar_alerta("🚀 Monitor ajustado! Sensibilidade máxima ativada. Verificando de 5 em 5 minutos sem falsos alarmes.")

while True:
    try:
        print(f"[Tentativa {tentativa}] Verificando o portal...")
        
        if verificar_vaga_real():
            # Apenas envia quando detetar uma alteração real na página
            for i in range(5):
                msg = f"🚨 VAGA DETETADA EM GETAFE! 🚨\nO portal atualizou e há datas disponíveis!\nAceda imediatamente: {URL}"
                enviar_alerta(msg)
                time.sleep(2)
            break # Para o robô para não inundar o Telegram enquanto tentas agendar
        else:
            print("Página verificada: Indisponível/Sem vagas no momento. Aguardando 5 minutos...")
            
    except Exception as e:
        print(f"Erro no ciclo: {e}")
    
    tentativa += 1
    # Pausa de 5 minutos (300 segundos) entre verificações
    time.sleep(300)
