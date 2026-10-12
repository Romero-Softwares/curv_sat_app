# Sincronizacao de licenca e dados do sistema

## Licenca compartilhada

Execute `migrations/20261011_create_license_sync.sql` no SQL Editor do projeto
Supabase antes de distribuir a versao com sincronizacao em nuvem.

A migracao cria a tabela com RLS ativo e libera somente a funcao RPC estrita
necessaria ao aplicativo. A chave publishable do executavel nao tem acesso
direto a tabela.

A chave de ativacao pertence a organizacao. A mesma chave deve ser ativada em
cada computador autorizado; o servidor identifica a licenca pelo hash da
propria chave, e nunca pela instalacao Windows. Para suspender ou revogar a
licenca, altere `status` para `suspended` ou `revoked` na linha correspondente
em `curvsat_license_activations`. Nunca distribua uma chave `sb_secret_`.

Se o SQL Editor informar que encontrou uma tabela legada sem `license_hash`,
use a versao atual deste arquivo e execute o script completo novamente. A
migracao renomeia a tabela antiga para
`curvsat_license_activations_legacy_20261011`, sem apagar os registros, e cria
a nova tabela. Os computadores com uma chave de ativacao valida recriam a
licenca compartilhada automaticamente no primeiro sincronismo.

## Dados do sistema

O proximo conjunto de tabelas deve sincronizar configuracoes, cadastros de PN,
curvas salvas e historico de relatorios usando a mesma identidade de licenca.
Assim, o segundo computador autorizado podera abrir os dados que o primeiro
enviou. Ate essas tabelas e o fluxo de envio/recebimento serem adicionados, os
arquivos `configuracoes.json` e `dados_pn.db` continuam locais ao Windows.
