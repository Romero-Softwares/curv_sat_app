import json
from pathlib import Path
from datetime import datetime
import os
from typing import Dict
import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, FileResponse, JSONResponse

try:
    from .release_upload_endpoint import install_release_upload_endpoint
    from .sync_api import install_sync_api
except ImportError:
    from release_upload_endpoint import install_release_upload_endpoint
    from sync_api import install_sync_api

app = FastAPI(title='Politicas + FPS API')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_ASSETS_DIR = os.path.join(BASE_DIR, 'assets')
# Todo conteudo publico do servidor, incluindo os instaladores publicados,
# pertence a esta pasta. Nao use BASE_DIR como alternativa: isso separaria o
# arquivo enviado da raiz publica /download.
ASSETS_DIR = DEFAULT_ASSETS_DIR
JSON_DIR = Path(__file__).resolve().parent
VISITAS_JSON = JSON_DIR / "visitas.json"

# Instaladores recebidos em /api/releases/upload ficam disponíveis em
# /download/ASCC-System-X.Y.Z.exe no mesmo processo HTTP.
install_release_upload_endpoint(app, download_directory=Path(ASSETS_DIR))
install_sync_api(app)
# Salas WebSocket para sinalizacao P2P.
# Estrutura: { room_id: { client_id: websocket } }
rooms: Dict[str, Dict[str, WebSocket]] = {}

def carregar_html(arquivo: str) -> str:
    caminho = os.path.join(ASSETS_DIR, arquivo)
    try:
        if os.path.exists(caminho):
            with open(caminho, 'r', encoding='utf-8') as f:
                return f.read()
        return f"<h1>Erro 404</h1><p>Arquivo '{arquivo}' nao encontrado.</p>"
    except Exception as e:
        return f'<h1>Erro de Sistema</h1><p>{str(e)}</p>'


@app.get('/')
def raiz():
    return RedirectResponse(url='/site')


@app.get('/status', response_class=HTMLResponse)
def status():
    return (
        '<h1>Servidor ativo</h1>'
        '<p>Rotas: /site, /fps, /privacy, /politica_gcalc, /privacy-mtc, /politica-educ, /ws</p>'
    )

def ler_visitas():
    if VISITAS_JSON.exists():
        try:
            return json.loads(VISITAS_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            pass

    return {
        "total": 0,
        "ultima_visita": None
    }


def salvar_visitas(dados):
    VISITAS_JSON.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def incrementar_visita():
    dados = ler_visitas()
    dados["total"] = int(dados.get("total") or 0) + 1
    dados["ultima_visita"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    salvar_visitas(dados)
    print(f"Visitas ao site: {dados['total']}\nUltima visita: {dados['ultima_visita']}")
    return dados


@app.get("/site", response_class=HTMLResponse)
def rota_site():
    incrementar_visita()
    return carregar_html("site.html")
    
@app.get("/merotec-ia", response_class=HTMLResponse)
def rota_mtia():
    incrementar_visita()
    return carregar_html("mtia.html")


@app.get("/visitas.json")
def rota_visitas():
    dados = ler_visitas()
    return JSONResponse(
        content=dados,
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0"
        }
    )
        

@app.get('/politica_gcalc', response_class=HTMLResponse)
def rota_gcalc():
    return carregar_html('politica-gcalc.html')


@app.get('/privacy-mtc', response_class=HTMLResponse)
def rota_mtcprivacy():
    return carregar_html('privacy_mtccloud.html')


@app.get('/politica-educ', response_class=HTMLResponse)
def rota_educ():
    return carregar_html('privacy.html')


@app.get('/privacy', response_class=HTMLResponse)
def rota_privacy():
    return carregar_html('privacy.html')


@app.get('/fps', response_class=HTMLResponse)
def rota_fps():
    return carregar_html('fps.html')


@app.get('/fps.html', response_class=HTMLResponse)
def rota_fps_html():
    return carregar_html('fps.html')
    
@app.get('/manual-mtc-pt', response_class=FileResponse)
def rota_manual_mtc_pt(): 
    caminho = os.path.join(ASSETS_DIR, 'MTChart Pro v2-manual.pdf')
    if not os.path.exists(caminho): 
        return HTMLResponse( "<h1>Erro404</h1><p>PDF nao encontrado.</p>", status_code=404 )
    return FileResponse( caminho, media_type='application/pdf', filename='MTChart Pro v2-manual.pdf', headers={'Content-Disposition': 'inline; filename="MTChart Pro v2-manual.pdf"'} )


@app.websocket('/ws')
async def websocket_signaling(websocket: WebSocket):
    await websocket.accept()
    current_room = ''
    current_client_id = ''
    
    async def cleanup_peer(room_id: str, client_id: str, ws: WebSocket | None = None):
        peers = rooms.get(room_id)
        if not peers:
            return

        if ws is None:
            peers.pop(client_id, None)
        elif peers.get(client_id) is ws:
            peers.pop(client_id, None)

        if not peers:
            rooms.pop(room_id, None)

    try:
        while True:
            raw_message = await websocket.receive_text()

            try:
                message = json.loads(raw_message)
            except json.JSONDecodeError:
                await websocket.send_json({'type': 'error', 'message': 'Mensagem JSON invalida'})
                continue

            room_id = message.get('room') or current_room
            client_id = message.get('from') or current_client_id
            msg_type = message.get('type')

            if not room_id or not client_id:
                await websocket.send_json(
                    {'type': 'error', 'message': "Campos 'room' e 'from' sao obrigatorios"}
                )
                continue

            if msg_type == 'join':
                current_room = room_id
                current_client_id = client_id

                peers = rooms.setdefault(room_id, {})
                peers[client_id] = websocket

                join_notice = {'type': 'peer-joined', 'from': client_id}
                for peer_id, peer_ws in list(peers.items()):
                    if peer_id == client_id:
                        continue
                    try:
                        await peer_ws.send_json(join_notice)
                    except Exception:
                        await cleanup_peer(room_id, peer_id, peer_ws)
                continue

            peers = rooms.get(room_id)
            if not peers:
                continue

            target_id = message.get('to')
            if target_id:
                target_ws = peers.get(target_id)
                if target_ws and target_ws is not websocket:
                    try:
                        await target_ws.send_json(message)
                    except Exception:
                        await cleanup_peer(room_id, target_id, target_ws)
                continue

            for peer_id, peer_ws in list(peers.items()):
                if peer_id == client_id:
                    continue
                try:
                    await peer_ws.send_json(message)
                except Exception:
                    await cleanup_peer(room_id, peer_id, peer_ws)

    except WebSocketDisconnect:
        pass
    finally:
        if current_room and current_client_id:
            await cleanup_peer(current_room, current_client_id, websocket)

@app.get("/download/{nome_arquivo}")
def baixar_arquivo(nome_arquivo: str):
    pasta_assets = Path(ASSETS_DIR).resolve()
    caminho_arquivo = (pasta_assets / nome_arquivo).resolve()

    if (
        pasta_assets not in caminho_arquivo.parents
        or not caminho_arquivo.is_file()
        or caminho_arquivo.suffix.lower() != ".exe"
    ):
        raise HTTPException(status_code=404, detail="Arquivo não encontrado.")

    return FileResponse(
        path=caminho_arquivo,
        filename=caminho_arquivo.name,
        media_type="application/octet-stream",
    )

if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8550)
