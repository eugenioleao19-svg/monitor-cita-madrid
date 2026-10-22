import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from playwright.sync_api import sync_playwright
import requests

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

def navegar_e_verificar():
    with sync_playwright() as p:
        # Lança o navegador automático em modo invisível (headless)
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # 1. Acessa a URL inicial
            page.goto(URL, timeout=30000)
            page.wait_for_timeout(2000)

            # 2. Clica em "SOLICITAR CITA" se essa opção estiver na primeira tela
            if page.is_visible("text=SOLICITAR CITA"):
                page.click("text=SOLICITAR CITA")
                page.wait_for_timeout(2000)

            # 3. Seleciona "Registro Civil de Getafe" no campo de seleção de centro
            # Procura pelo select do centro e escolhe a opção correspondente a Getafe
            select_centro = page.locator("select").nth(0)
            if select_centro.is_visible():
                select_centro.select_option(label="Registro Civil de Getafe")
                page.wait_for_timeout(1000)

            # 4. Seleciona "NACIONALIDAD V.S.P" no campo de serviço
            select_servicio = page.locator("select").nth(1)
            if select_servicio.is_visible():
                select_servicio.select_option(label="NACIONALIDAD V.S.P")
                page.wait_for_timeout(1000)

            # 5. Clica no botão "Continuar"
            if page.is_visible("text=Continuar") or page.is_visible("input[value='Continuar']"):
                page.click("text=Continuar")
                page.wait_for_timeout(3000)

            # 6. Avalia o conteúdo da página após clicar em Continuar
            conteudo = page.content()

            # Se passar da tela e não exibir a frase de falta de vagas
            indisponivel = (
                "No hay citas disponibles" in conteudo or 
                "En este momento no disponemos de citas" in conteudo
            )

            # Se avançou de tela (ex: aparece seleção de dia/hora ou dados pessoais)
            sucesso_avanco = (
                "Día y hora de la cita" in conteudo or 
                "Datos personales" in conteudo or 
                "Acciones" in conteudo
            )

            browser.close()

            if sucesso_avanco and not indisponivel:
                return True

        except Exception as e:
            print(f"Erro durante a navegação automática: {e}")
            try:
                browser.close()
            except:
                pass

        return False

tentativa = 1
print("A iniciar o monitoramento com navegação automática de formulário...")

enviar_alerta("🚀 Robô com navegação automática iniciado! A selecionar Getafe + Nacionalidad V.S.P de 5 em 5 minutos.")

while True:
    try:
        print(f"[Tentativa {tentativa}] A executar fluxo: Solicitar -> Getafe -> Nacionalidad V.S.P -> Continuar...")
        
        if navegar_e_verificar():
            for i in range(5):
                msg = f"🚨 VAGA ENCONTRADA EM GETAFE! 🚨\nO robô passou da seleção e encontrou datas disponíveis!\nAceda imediatamente: {URL}"
                enviar_alerta(msg)
                time.sleep(2)
            break
        else:
            print("Página de indisponibilidade/sem vagas após submeter formulário. Aguardando 5 minutos...")

    except Exception as e:
        print(f"Erro no ciclo: {e}")

    tentativa += 1
    time.sleep(300)
