# Publicar atualizacoes

O aplicativo consulta o manifesto publico no GitHub ao iniciar. A publicacao de
uma nova versao e feita pelo atalho `publicar_atualizacao.cmd`.

## Fonte unica e fluxo completo

`curvsat/core/version.py` e a fonte unica da versao instalada. A tela **Sobre o
sistema** le esse mesmo valor em tempo de execucao; portanto, ela nao possui
nenhuma versao fixa para ser alterada manualmente.

O publicador e a unica forma normal de mudar uma versao. Para uma versao
`X.Y.Z`, ele mantem sincronizados:

1. `curvsat/core/version.py` (versao exibida e enviada pelo aplicativo);
2. `update_manifest.json` (versao, notas e URL publica);
3. `packaging/ASCC System.spec` e `packaging/pyinstaller-params.txt` (nome do pacote);
4. `dist/ASCC-System-X.Y.Z.exe` (instalador gerado);
5. `update_manifest.json` assinado localmente, incluindo nome, tamanho e SHA-256 do executável;
6. commit `Publica atualizacao X.Y.Z` e tag Git `vX.Y.Z`.

Antes de mudar qualquer arquivo, o roteiro verifica que a versao atual ja esta
coerente em todos esses arquivos, que a nova versao e maior e que a tag nao
existe localmente nem no remoto. Ele tambem executa os testes automatizados.
Isso impede publicar um manifesto, pacote ou tag com versoes diferentes.

## Servidor integrado, upload direto

O endpoint de upload ja esta integrado em `server/routes.py` e e implementado
em `server/release_upload_endpoint.py`:

```text
PUT /api/releases/upload
```

O instalador e gravado de forma atomica em `server/assets/` e fica disponivel
em `/download/ASCC-System-X.Y.Z.exe`.

Nao ha token, IP autorizado ou variavel de ambiente para configurar. Copie os
arquivos do servidor e reinicie o servico Python: o endpoint recebe o arquivo
enviado pelo publicador e o grava em `assets/`.

E no bloco do Nginx que encaminha para a aplicacao:

```nginx
client_max_body_size 500m;
```

Reinicie o servico. Neste projeto, `.release.env` e opcional: as URLs de upload
e download ja estao definidas no publicador.

## Publicar uma versao

Abra `publicar_atualizacao.cmd`, informe a versao (por exemplo, `1.0.2`) e as
notas que aparecerao ao usuario. O roteiro:

1. valida a versao, o estado rastreado do Git, a tag e a coerencia atual;
2. executa os testes automatizados;
3. atualiza os quatro arquivos de versao e confere a nova coerencia;
4. gera e confere `dist/ASCC-System-X.Y.Z.exe`;
5. envia o executavel ao endpoint;
6. cria o commit, a tag `vX.Y.Z` e envia ambos ao GitHub.

Se a compilacao ou o upload falhar, os arquivos de versao sao restaurados e
nenhum commit e feito. O manifesto so e enviado ao GitHub depois que o
instalador for aceito pelo servidor. Nao edite versao, manifesto, `.spec` ou
parametros de compilacao manualmente entre publicacoes: o roteiro bloqueia
qualquer divergencia encontrada.

## Assinatura local verificável

O publicador cria uma assinatura **Ed25519** do manifesto depois do build. A
assinatura inclui os metadados do instalador (`name`, `size` e `sha256`), e o
aplicativo aceita atualização somente quando ela confere com a chave pública
incorporada. Assim, uma alteração no manifesto ou no executável é detectada
antes da distribuição.

A chave privada local fica em
`licensing/release_signing_private_key.json`, ignorada pelo Git. Ela já foi
gerada neste ambiente. Faça uma cópia criptografada e restrita dessa chave:
perdê-la impede assinar novas versões; expô-la permite falsificar releases.
Não a inclua em instaladores, commits ou backups públicos.

Para conferir manualmente uma release já publicada:

```powershell
.venv\Scripts\python.exe -m curvsat.tools.release_signing verify `
  --manifest update_manifest.json `
  --artifact dist\ASCC-System-X.Y.Z.exe
```

Essa assinatura é própria do CurvSat e serve para integridade/autoria entre os
componentes do produto. Ela não é uma assinatura Authenticode: o Windows só
remove a desconfiança nativa para certificados encadeados a uma CA confiável ou
para pacotes MSIX distribuídos pela Microsoft Store. Certificado autoassinado
continua adequado apenas para teste ou parque corporativo controlado.

Para automacao por terminal:

```powershell
.venv\Scripts\python.exe release_update.py 1.0.2 --notes "Melhorias e correcoes."
```

Use `--dry-run` para validar nomes e URLs sem alterar arquivos. `--skip-tests`
fica reservado para diagnostico; a publicacao normal sempre executa os testes.
Use `--no-push` somente para revisar um commit local: enquanto ele nao for
enviado, o instalador ja estara no servidor, mas os clientes ainda nao receberao
o manifesto da nova versao.
