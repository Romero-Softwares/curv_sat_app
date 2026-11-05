# API de sincronização SQLite

O servidor FastAPI agora disponibiliza uma alternativa local às RPCs usadas no
Supabase. O contrato das rotas é o mesmo do cliente CurvSat atual:

- `POST /rest/v1/rpc/sync_curvsat_license`
- `POST /rest/v1/rpc/sync_curvsat_system_data`
- `GET /api/sync/health`

As duas RPCs recebem JSON e usam `p_license_hash` para isolar os dados de cada
organização. O hash é SHA-256 da chave de ativação, exatamente como no cliente.
O primeiro endpoint registra o heartbeat da licença; o segundo exige que ela
esteja ativa e faz merge por `updated_at`. Registros e relatórios removidos são
mantidos como marcadores compactos por sete dias e então são eliminados.

## Execução local

```powershell
.venv\Scripts\python.exe -m uvicorn server.routes:app --host 0.0.0.0 --port 8550
```

Por padrão, o banco é criado em `server/data/curvsat_sync.db`. Para gravá-lo em
outro local, configure `CURVSAT_SYNC_DB` antes de iniciar o processo:

```powershell
$env:CURVSAT_SYNC_DB = "D:\dados\curvsat-sync.db"
.venv\Scripts\python.exe -m uvicorn server.routes:app --host 0.0.0.0 --port 8550
```

Para uma instalação acessível na rede, defina também uma chave compartilhada.
Nesse caso, cada chamada deve enviar o cabeçalho `apikey` com o mesmo valor:

```powershell
$env:CURVSAT_SYNC_API_KEY = "gere-uma-chave-longa-e-aleatoria"
```

Sem essa variável a API permanece aberta, o que só é adequado para testes em
rede privada. O aplicativo cliente usa `https://merotec.online` como destino
padrão e também aceita `CURVSAT_SYNC_URL` para instalações privadas.

## Administração de licenças

O administrador pode consultar ou alterar o status diretamente no SQLite.
Mantenha o processo do servidor parado antes de editar manualmente o arquivo:

```sql
UPDATE curvsat_license_activations
SET status = 'suspended'
WHERE license_hash = '<hash-da-licenca>';
```

Os estados aceitos são `active`, `suspended` e `revoked`.
