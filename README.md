# Sobre a Aplicação
Esta aplicação web permite gerenciar usuários, redefinir senhas e gerar certificados VPN para os usuários.

# O que o usuário precisa fazer para rodar:
-Para rodar a aplicação, copie toda a pasta do projeto para o Debian onde deseja executar o sistema.

-É necessário criar e ativar um ambiente virtual Python (venv) para isolar as dependências do projeto.

-Certifique-se de que o Python e o gerenciador de pacotes pip estejam instalados no Debian.

-Dentro do ambiente virtual, instale as dependências necessárias usando o pip.

-É necessário instalar o EasyRSA para a assinatura dos certificados funcionar.

-Para o envio de e-mails, a aplicação utiliza o msmtp. Portanto você deve instalar o msmtp no Debian e configurar o arquivo ~/.msmtprc com os dados da conta Gmail.

-> É obrigatório ativar a verificação em duas etapas na conta Gmail e criar uma senha de app para que o envio dos e-mails funcione corretamente, essa senha será usada no arquivo msmtp para acessar a conta que enviará os e-mails.

# OBS: Esteja ciente que essa aplicação foi criada para fins academicos, portanto, tenha ciencia de usar uma conta teste ja que a aplicação precisará entrar na conta para enviar os e-mails de recuperação de senha dos usuários.

-Após as configurações, execute o arquivo app.py para iniciar a aplicação Flask.

-Acesse o sistema via navegador usando o IP da máquina Debian fornecido seguido da porta 5000, por exemplo: http://192.168.x.x:5000.

-Garanta que o usuário do Debian que está executando a aplicação tenha permissões para ler e escrever os arquivos do projeto, além de poder executar scripts necessários.

# Nota: Para baixar os certificados, é necessário informar a senha configurada durante o processo de instalação do EasyRSA diretamente no terminal debian (após clicar no botão Gerar Certificados VPN no front da aplicação), que protege as chaves privadas usadas na VPN. Após informada, será feito o donwload automaticamente no front da aplcação (navegador), basta pressionar ctrl+j para conferir.

-> O design utilizado para o front-end não foi desenvolvido inteiramente por mim. Este projeto não tem objetivos comerciais, de venda ou qualquer tipo de obtenção de dinheiro. Todo o desenvolvimento foi parte de um projeto acadêmico na Fatec Zona Leste.
