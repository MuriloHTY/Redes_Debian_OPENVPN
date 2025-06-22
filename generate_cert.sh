#!/bin/bash

USER_NAME="$1"

if [ -z "$USER_NAME" ]; then
    echo "Erro: Nome de usuario nao fornecido."
    exit 1
fi

EASYRSA_DIR="/usr/share/easy-rsa"
CERTS_DEST_DIR="/etc/openvpn/client/$USER_NAME"
FINAL_ZIP_DEST_DIR="/home/userlinux/client_certs"

echo "Iniciando geracao de certificado para o usuario: $USER_NAME"

cd "$EASYRSA_DIR" || { echo "Erro: Nao foi possivel entrar em $EASYRSA_DIR. Verifique o caminho."; exit 1; }

echo "Gerando requisicao de certificado para $USER_NAME..."
printf "yes\n\n" | sudo ./easyrsa gen-req "$USER_NAME" nopass || {
    echo "Erro na geracao da requisicao para $USER_NAME. Saida Easy-RSA acima pode ter mais detalhes."
    exit 1
}
echo "Requisicao de certificado gerada."

echo "Assinando certificado para $USER_NAME..."
sudo -E EASYRSA_PASSPHRASE="123456" printf "yes\n" | sudo EASYRSA_BATCH=1 ./easyrsa sign-req client "$USER_NAME" || {
    echo "Erro na assinatura do certificado para $USER_NAME. Verifique a passphrase da CA e o estado da CA."
    exit 1
}
echo "Certificado assinado com sucesso."

echo "Copiando certificados para o diretorio do cliente ($CERTS_DEST_DIR)..."
sudo mkdir -p "$CERTS_DEST_DIR" || { echo "Erro ao criar diretorio de destino $CERTS_DEST_DIR. Verifique as permissoes."; exit 1; }

sudo cp "$EASYRSA_DIR"/pki/ca.crt "$CERTS_DEST_DIR"/ || { echo "Erro ao copiar ca.crt."; exit 1; }
sudo cp "$EASYRSA_DIR"/pki/issued/"$USER_NAME".crt "$CERTS_DEST_DIR"/ || { echo "Erro ao copiar $USER_NAME.crt."; exit 1; }
sudo cp "$EASYRSA_DIR"/pki/private/"$USER_NAME".key "$CERTS_DEST_DIR"/ || { echo "Erro ao copiar $USER_NAME.key."; exit 1; }
sudo cp "$EASYRSA_DIR"/pki/dh.pem "$CERTS_DEST_DIR"/ || { echo "Erro ao copiar dh.pem."; exit 1; }

echo "Certificados copiados para o diretorio do cliente."

cd "/etc/openvpn/client/" || { echo "Erro: Nao foi possivel entrar em /etc/openvpn/client/."; exit 1; }
echo "Criando arquivo ZIP para $USER_NAME..."

sudo mkdir -p "$FINAL_ZIP_DEST_DIR" || { echo "Erro: Nao foi possivel criar $FINAL_ZIP_DEST_DIR. Verifique as permissoes."; exit 1; }
sudo zip -r "$FINAL_ZIP_DEST_DIR"/"$USER_NAME".zip "$USER_NAME" || { echo "Erro ao criar ZIP. Verifique se o comando 'zip' esta instalado e se as permissoes estao corretas para o diretorio '$FINAL_ZIP_DEST_DIR'."; exit 1; }

echo "Arquivo ZIP gerado em $FINAL_ZIP_DEST_DIR/$USER_NAME.zip"
echo "Processo concluido para o usuario: $USER_NAME"
exit 0
