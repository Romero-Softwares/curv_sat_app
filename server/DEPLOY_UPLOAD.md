# Implantacao do upload de atualizacoes

Este diretorio e o pacote que deve ser levado para a maquina que hospeda
`merotec.online`. O executavel enviado pelo publicador e gravado diretamente
em `assets/` ao lado de `routes.py` e servido por:

```text
https://merotec.online/download/ASCC-System-X.Y.Z.exe
```

## Arquivos a atualizar no servidor

Copie para o diretorio da aplicacao FastAPI remota:

```text
server/routes.py
server/release_upload_endpoint.py
```

Mantenha o diretorio remoto `assets/` existente; ele e o destino dos
instaladores. O usuario que executa o processo Python precisa ter permissao de
leitura e escrita nesse diretorio.

## Publicacao direta

Nao ha token, IP autorizado ou variavel de ambiente para configurar. Depois de
copiar os dois arquivos e reiniciar o servico Python, o endpoint recebe o
instalador diretamente e o salva em `assets/`. No projeto publicador, basta
executar `publicar_atualizacao.cmd` e informar a versao e as notas.

## Proxy reverso

Se `merotec.online` usa Nginx, o bloco que encaminha a aplicacao deve aceitar
o tamanho do instalador e substituir qualquer IP informado pelo cliente:

```nginx
client_max_body_size 500m;
proxy_set_header X-Forwarded-For $remote_addr;
```

O metodo `PUT` deve ser repassado sem filtros para `/api/releases/upload`.

## Verificacao apos a implantacao

Na maquina publicadora, com `.release.env` configurado, execute:

```powershell
.venv\Scripts\python.exe release_update.py 1.0.2 --notes "Teste de publicacao" --no-build --no-push
```

O comando deve receber `201 Created`. O arquivo deve aparecer no diretorio
remoto `assets/` e responder em
`/download/ASCC-System-1.0.2.exe`. Use uma versao ainda nao publicada; o
publicador sempre exige que o executavel correspondente exista em `dist/`.
