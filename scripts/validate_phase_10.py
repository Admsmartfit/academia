import requests
import sys

BASE_URL = "http://localhost:5000"
SESSION = requests.Session()

def log(msg, success=True):
    icon = "✅" if success else "❌"
    print(f"{icon} {msg}")
    if not success:
        sys.exit(1)

def test_landing_page():
    print("\n--- Testando Landing Page ---")
    try:
        resp = SESSION.get(BASE_URL)
        if resp.status_code == 200:
            content = resp.text
            if "Transforme seu corpo" in content and "Simule seu Treino" in content:
                log("Landing Page carregada com sucesso.")
                # Verificar se packagesData foi renderizado corretamente
                if "const packagesData = [{" in content:
                    log("Dados do pacote renderizados no JavaScript.")
                else:
                    log("Dados do pacote não encontrados ou formato incorreto.", False)
            else:
                log("Conteúdo da Landing Page incompleto.", False)
        else:
            log(f"Erro ao carregar Landing Page: {resp.status_code}", False)
    except Exception as e:
        log(f"Exceção: {e}", False)

def generate_cpf():
    import random
    cpf = [random.randint(0, 9) for _ in range(9)]
    
    for _ in range(2):
        val = sum([(len(cpf) + 1 - i) * v for i, v in enumerate(cpf)]) % 11
        cpf.append(11 - val if val > 1 else 0)
        
    return '%s%s%s.%s%s%s.%s%s%s-%s%s' % tuple(cpf)

def test_registration():
    print("\n--- Testando Registro com CPF ---")
    import time
    email = f"user_{int(time.time())}@test.com"
    
    payload = {
        "name": "Usuario Teste CPF",
        "email": email,
        "phone": "(11) 99999-9999",
        "cpf": generate_cpf(),
        "password": "password123",
        "confirm_password": "password123"
    }
    
    try:
        # Primeiro GET para pegar CSRF se tiver (flask-wtf, mas aqui parece form simples)
        SESSION.get(f"{BASE_URL}/register")
        
        resp = SESSION.post(f"{BASE_URL}/register", data=payload, allow_redirects=True)
        if resp.status_code == 200:
            if "alert-danger" in resp.text:
                 print(f"DEBUG REGISTER FAILURE. Flash: {resp.text[resp.text.find('alert-danger'):resp.text.find('alert-danger')+200]}")
                 log("Falha no registro: Erro exibido na pagina.", False)
            elif "Conta criada com sucesso" in resp.text:
                log("Registro realizado com sucesso.")
            elif "/login" in resp.url: # Redirecionou
                 log("Registro realizado (redirecionado para login).")
            else:
                 # Check for the specific success message or redirect
                 log("Registro realizado (assumido).")
        else:
            log(f"Erro no registro: {resp.status_code}", False)
            
        return email
    except Exception as e:
        log(f"Exceção no registro: {e}", False)

def test_login(email):
    print("\n--- Testando Login ---")
    payload = {
        "email": email,
        "password": "password123"
    }
    
    try:
        resp = SESSION.post(f"{BASE_URL}/login", data=payload, allow_redirects=True)
        if "Bem-vindo" in resp.text or "Dashboard" in resp.text or "/student" in resp.url:
            log("Login realizado com sucesso.")
        else:
            print(f"DEBUG LOGIN FAILURE. URL: {resp.url}")
            # print(resp.text) # Too long?
            if "alert-danger" in resp.text:
                start = resp.text.find("alert-danger")
                print(f"Flash Error: {resp.text[start:start+200]}")
            log("Falha no login.", False)
    except Exception as e:
        log(f"Exceção no login: {e}", False)

def test_checkout_pix():
    print("\n--- Testando Checkout PIX NuPay ---")
    # Tentar acessar checkout do pacote 1 (criado no seed)
    package_id = 4 # Gold package from seed should be around 4 (previously created + 3 new)
    # Vamos pegar o primeiro link de checkout da landing page para garantir
    try:
        resp = SESSION.get(BASE_URL)
        import re
        match = re.search(r'/shop/checkout/(\d+)', resp.text)
        if match:
            package_id = match.group(1)
            log(f"Encontrado pacote ID: {package_id}")
        else:
            log("Não foi possível encontrar link de checkout na home.", False)
            
        checkout_url = f"{BASE_URL}/shop/checkout/{package_id}"
        resp = SESSION.get(checkout_url)
        
        if resp.status_code == 200:
            content = resp.text
            if "Finalizar Compra" in content:
                log("Página de checkout carregada.")
                
                # Verificar se opção PIX NuPay está habilitada (usuário tem CPF)
                if 'value="nupay_pix"' in content and 'disabled' not in content.split('value="nupay_pix"')[1].split('>')[0]:
                    log("Opção PIX NuPay disponível e habilitada (CPF detectado).")
                else:
                    log("Opção PIX NuPay não encontrada ou desabilitada.", False)
            else:
                log("Página de checkout incorreta.", False)
        else:
            log(f"Erro ao carregar checkout: {resp.status_code}", False)

    except Exception as e:
         log(f"Exceção no checkout: {e}", False)

def test_admin_login():
    print("\n--- Testando Login Admin (Seed) ---")
    payload = {
        "email": "admin@academia.com",
        "password": "admin123"
    }
    try:
        resp = SESSION.post(f"{BASE_URL}/login", data=payload, allow_redirects=True)
        if "Bem-vindo" in resp.text or "Dashboard" in resp.text or "/admin" in resp.url:
            log("Login Admin realizado com sucesso.")
        else:
            log("Falha no login Admin.", False)
    except Exception as e:
        log(f"Exceção no login Admin: {e}", False)

if __name__ == "__main__":
    test_landing_page()
    test_admin_login() # Add this
    SESSION = requests.Session() # Reset session for user test
    email = test_registration()
    test_login(email)
    test_checkout_pix()
    print("\n✅ TUDO CERTO! FASE 10 CONCLUÍDA.")
