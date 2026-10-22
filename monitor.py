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

threading.Thread(target=run_server, daemon=True).start()


# --- CONFIGURAÇÕES DO ROBÔ ---
URL_BASE = "https://gestiona7.madrid.org/ctac_cita/registro"

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

def executar_fluxo_getafe():
    session = requests.Session()
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": URL_BASE
    }

    try:
        # Step 1: Carregar a página de início (Solicitar Cita)
        res1 = session.get(URL_BASE, headers=headers, timeout=15)
        if res1.status_code != 200:
            return False

        # Step 2: Enviar a seleção de Registro Civil de Getafe + NACIONALIDAD V.S.P
        # Simula o clique no botão "Continuar"
        payload = {
            "rbtnCentro": "28067401",  # Código do centro Registro Civil de Getafe
            "sServicio": "NACIONALIDAD V.S.P",
            "btnContinuar": "Continuar"
        }

        res2 = session.post(URL_BASE, headers=headers, data=payload, timeout=15)
        conteudo = res2.text

        # Apenas considera sucesso SE a resposta contiver elementos da fase seguinte:
        # Passou para seleção de data/hora ou dados pessoais E não tem mensagem de indisponibilidade
        passou_de_fase = "Día y hora de la cita" in conteudo or "Datos personales" in conteudo
        tem_indisponibilidade = "No hay citas disponibles" in conteudo or "En este momento no disponemos de citas" in conteudo

        if passou_de_fase and not tem_indisponibilidade:
            return True

    except Exception as e:
        print(f"Erro ao executar o fluxo: {e}")

    return False

tentativa = 1
print("A iniciar o monitoramento com fluxo completo...")

enviar_alerta("🚀 Robô reconfigurado! Fluxo (Solicitar Cita -> Getafe -> Nacionalidad V.S.P -> Continuar) ativo de 5 em 5 minutos.")

while True:
    try:
        print(f"[Tentativa {tentativa}] A simular fluxo completo no portal...")

        if executar_fluxo_getafe():
            for i in range(5):
                msg = f"🚨 VAGA CONFIRMADA EM GETAFE! 🚨\nO robô passou por todas as telas e encontrou datas!\nAceda imediatamente: {URL_BASE}"
                enviar_alerta(msg)
                time.sleep(2)
            break
        else:
            print("Resultado: Indisponível/Sem vagas após o botão Continuar. Aguardando 5 minutos...")

    except Exception as e:
        print(f"Erro no ciclo: {e}")

    tentativa += 1
    time.sleep(300)
