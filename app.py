import os
import subprocess
import json
from flask import Flask, render_template, request, redirect, url_for, send_file, flash, session, make_response

app = Flask(__name__)
app.secret_key = b'AlunoFatec'

GENERATE_CERT_SCRIPT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'generate_cert.sh')
CLIENT_CERTS_ZIP_DIR = '/home/userlinux/client_certs'
USERS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'users.json')
TOKENS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tokens.json')

def load_users():
    if not os.path.exists(USERS_FILE):
        return []
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def enviar_email_redefinicao(username, token):
    users = load_users()
    destinatario = None

    for user in users:
        if user['username'] == username:
            destinatario = user.get('email')
            break

    if not destinatario:
        print("Usuario nao encontrado no users.json.")
        return False

    assunto = "Link para redefinir sua senha"
    corpo = f"Acesse o link para redefinir sua senha: http://{get_local_ip()}:5000/redefiniu?id={token}"

    comando = f'echo "{corpo}" | mail -s "{assunto}" {destinatario}'
    resultado = subprocess.run(comando, shell=True)

    return resultado.returncode == 0

def get_local_ip():
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(('10.255.255.255', 1))
        IP = s.getsockname()[0]
    except Exception:
        IP = '127.0.0.1'
    finally:
        s.close()
    return IP

def verify_credentials(username, password):
    users = load_users()
    for user in users:
        if user['username'] == username and user['password'] == password:
            return user
    return None

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['username']
        senha = request.form['password']

        user = verify_credentials(usuario, senha)
        if user:
            try:
                with open('acessos.json', 'r') as f:
                    acessos = json.load(f)
            except:
                acessos = {}

            acesso_permitido = acessos.get(usuario, False)
            
            if acesso_permitido is True or usuario == 'admin':
                session['user'] = user['username']

                if usuario == 'admin' and senha == '123':
                    return redirect(url_for('admin_index'))
                else:
                    return redirect(url_for('dashboard'))
            else:
                flash('Acesso negado, fale com o administrador.', 'error')
                return render_template('login.html')
        else:
            flash('Usuario ou senha incorretos.', 'error')
            return render_template('login.html')

    return render_template('login.html')

@app.route('/redefinir', methods=['GET', 'POST'])
def redefinir():
    if request.method == 'POST':
        username = request.form.get('username')

        token = os.urandom(16).hex()
        try:
            with open(TOKENS_FILE, 'r') as f:
                tokens = json.load(f)
        except:
            tokens = {}

        tokens[token] = {
            'username': username,
            'used': False
        }

        with open(TOKENS_FILE, 'w') as f:
            json.dump(tokens, f, indent=4)

        sucesso = enviar_email_redefinicao(username, token)

        if sucesso:
            flash('Um email com um link foi enviado para sua caixa de entrada.', 'success')
        else:
            flash('Erro ao enviar o email de redefinicao.', 'error')

        return redirect(url_for('redefinir'))

    return render_template('redefinir.html')

@app.route('/redefiniu', methods=['GET', 'POST'])
def redefiniu():
    token = request.args.get('id') if request.method == 'GET' else request.form.get('token')

    with open(TOKENS_FILE, 'r') as f:
        tokens = json.load(f)

    if token not in tokens or tokens[token].get('used'):
        flash('Link invalido ou expirado.', 'error')
        return redirect(url_for('login'))

    username = tokens[token]['username']

    if request.method == 'POST':
        nova_senha = request.form.get('newpass')
        nova_senha2 = request.form.get('newpass2')

        if nova_senha != nova_senha2:
            flash('As senhas nao coincidem.', 'error')
            return render_template('redefiniu.html', token=token)

        with open(USERS_FILE, 'r+') as f:
            usuarios = json.load(f)
            for user in usuarios:
                if user['username'] == username:
                    user['password'] = nova_senha
                    break
            f.seek(0)
            json.dump(usuarios, f, indent=4)
            f.truncate()

        tokens[token]['used'] = True
        with open(TOKENS_FILE, 'w') as f:
            json.dump(tokens, f, indent=4)

        flash('Senha redefinida com sucesso.', 'success')
        return redirect(url_for('login'))

    return render_template('redefiniu.html', token=token)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        flash('Voce precisa fazer login primeiro.', 'error')
        return redirect(url_for('login'))
    usuario = session['user']
    response = make_response(render_template('index.html', user=usuario))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/gerar_e_baixar_certificado', methods=['POST'])
def gerar_e_baixar_certificado():
    if 'user' not in session:
        flash('Sessao expirada, por favor faca login novamente.', 'error')
        return redirect(url_for('login'))

    username = session['user']
    try:
        result = subprocess.run(['sudo', GENERATE_CERT_SCRIPT, username],
                                capture_output=True, text=True, check=True)
        print("STDOUT do script:", result.stdout)
        print("STDERR do script:", result.stderr)
        flash("Certificados para {} gerados e empacotados com sucesso!".format(username), 'success')

    except subprocess.CalledProcessError as e:
        print("Erro ao executar script (codigo {}): {}".format(e.returncode, e))
        print("STDOUT do script (erro):", e.stdout)
        print("STDERR do script (erro):", e.stderr)
        flash("Erro ao gerar certificados para {}. Detalhes: {}".format(username, e.stderr), 'error')
        return redirect(url_for('dashboard'))
    except Exception as e:
        print("Erro inesperado ao chamar o script:", e)
        flash("Erro inesperado ao gerar certificados: {}".format(e), 'error')
        return redirect(url_for('dashboard'))

    zip_filename = "{}.zip".format(username)
    zip_filepath = os.path.join(CLIENT_CERTS_ZIP_DIR, zip_filename)

    if os.path.exists(zip_filepath):
        return send_file(zip_filepath, as_attachment=True, download_name=zip_filename)
    else:
        print("Erro: Arquivo ZIP '{}' nao encontrado apos execucao do script.".format(zip_filepath))
        flash("Erro: Arquivo ZIP para '{}' nao foi encontrado. Por favor, tente novamente ou verifique os logs do servidor.".format(username), 'error')
        return redirect(url_for('dashboard'))

@app.route('/admin')
def admin_index():
    if 'user' not in session or session['user'] != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('login'))
    
    usuarios = load_users()
    return render_template('indexadm.html', user='Admin', usuarios=usuarios)

@app.route('/adicionar_usuario', methods=['POST'])
def adicionar_usuario():
    if 'user' not in session or session['user'] != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('login'))

    username = request.form.get('username').strip()
    email = request.form.get('email').strip()
    password = request.form.get('password')
    is_admin = 'admin' in request.form

    if not username or not email or not password:
        flash('Todos os campos devem ser preenchidos.', 'error')
        return redirect(url_for('admin_index'))

    usuarios = load_users()

    if any(u['username'] == username for u in usuarios):
        flash('Usuario ja existe.', 'error')
        return redirect(url_for('admin_index'))

    novo_usuario = {
        'username': username,
        'email': email,
        'password': password,
        'admin': is_admin
    }
    usuarios.append(novo_usuario)

    with open(USERS_FILE, 'w') as f:
        json.dump(usuarios, f, indent=4)

    try:
        with open('acessos.json', 'r') as f:
            acessos = json.load(f)
    except:
        acessos = {}

    acessos.pop('liberados', None)
    acessos.pop('revogados', None)

    acessos[username] = False

    with open('acessos.json', 'w') as f:
        json.dump(acessos, f, indent=4)

    flash('Usuario adicionado!', 'success')
    return redirect(url_for('admin_index'))

@app.route('/excluir_usuarios', methods=['POST'])
def excluir_usuarios():
    if 'user' not in session or session['user'] != 'admin':
        flash('Acesso negado.', 'error')
        return redirect(url_for('login'))

    usuarios_selecionados = request.form.getlist('usuarios_selecionados')

    if not usuarios_selecionados:
        flash('Nenhum usuario selecionado.', 'error')
        return redirect(url_for('admin_index'))

    users = load_users()

    users_filtrados = [u for u in users if u['username'] not in usuarios_selecionados]

    with open(USERS_FILE, 'w') as f:
        json.dump(users_filtrados, f, indent=4)

    try:
        with open('acessos.json', 'r') as f:
            acessos = json.load(f)
    except:
        acessos = {}

    for usuario in usuarios_selecionados:
        if usuario in acessos:
            acessos.pop(usuario)

    with open('acessos.json', 'w') as f:
        json.dump(acessos, f, indent=4)

    flash("Usuarios selecionados excluidos!", "success")
    return redirect(url_for('admin_index'))

@app.route('/liberar_acessos', methods=['POST'])
def liberar_acessos():
    usernames = request.form.getlist('usuarios_selecionados')
    
    if not usernames:
        flash("Nenhum usuario selecionado", "error")
        return redirect(url_for('admin_index'))

    try:
        with open('acessos.json', 'r') as f:
            acessos = json.load(f)
        
        for username in usernames:
            acessos[username] = True
        
        with open('acessos.json', 'w') as f:
            json.dump(acessos, f, indent=2)

        flash("Acessos liberados!", "success")
    except Exception as e:
        flash(f"Erro ao liberar acessos: {e}", "error")
    
    return redirect(url_for('admin_index'))

@app.route('/revogar_acessos', methods=['POST'])
def revogar_acessos():
    usernames = request.form.getlist('usuarios_selecionados')
    if not usernames:
        flash('Nenhum usuario selecionado.', 'error')
        return redirect(url_for('admin_index'))

    try:
        with open('acessos.json', 'r') as f:
            acessos = json.load(f)

        for username in usernames:
            acessos[username] = False

        with open('acessos.json', 'w') as f:
            json.dump(acessos, f, indent=2)

        flash('Acessos revogados!', 'success')
    except Exception as e:
        flash(f"Erro ao revogar acessos: {e}", 'error')

    return redirect(url_for('admin_index'))

if __name__ == '__main__':
    os.makedirs(CLIENT_CERTS_ZIP_DIR, exist_ok=True)
    app.run(debug=True, host='0.0.0.0', port=5000)
