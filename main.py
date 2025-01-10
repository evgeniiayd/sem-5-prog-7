import datetime
import time
import requests
from xml.etree import ElementTree as ET
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any
import uuid  # Для генерации уникальных идентификаторов клиентов

app = FastAPI()


# Класс для хранения курсов валют
class CurrenciesLst:
    def __init__(self):
        self.cur_lst: dict = {}
        self._ids_lst: list = []

    def set_ids(self, ids_lst):
        self._ids_lst = ids_lst

    def get_currencies(self) -> list:
        """Запрашивает курсы валют из API Центробанка России."""
        cur_res_str = requests.get('http://www.cbr.ru/scripts/XML_daily.asp')
        result = []

        root = ET.fromstring(cur_res_str.content)
        valutes = root.findall("Valute")
        double_of_ids = self._ids_lst.copy()

        for _v in valutes:
            valute_id = _v.get('ID')
            if str(valute_id) in double_of_ids:
                valute_cur_name = _v.find('Name').text
                valute_cur_val = _v.find('Value').text.replace(',', '.')
                valute_nominal = int(_v.find('Nominal').text)
                valute_charcode = _v.find('CharCode').text
                if valute_nominal != 1:
                    self.cur_lst[valute_cur_name] = (valute_charcode, valute_cur_val, valute_nominal)
                else:
                    self.cur_lst[valute_cur_name] = (valute_charcode, valute_cur_val)
                double_of_ids.remove(str(valute_id))

        for id in double_of_ids:
            self.cur_lst[f'{id}'] = None

        return self.cur_lst


currencies_list = CurrenciesLst()
currencies_list.set_ids(['R01235', 'R01239'])  # Пример ID валют (USD, EUR)

# Хранит активные веб-сокеты и их идентификаторы
active_connections: List[Dict[str, Any]] = []


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    client_id = str(uuid.uuid4())  # Генерируем уникальный идентификатор клиента
    count = 1
    await websocket.accept()
    active_connections.append({"websocket": websocket, "id": client_id})

    try:
        while True:
            # Отправляем обновления каждые 10 секунд
            time.sleep(10)
            count += 1
            currencies = currencies_list.get_currencies()
            cur_time = str(datetime.datetime.now())
            for connection in active_connections:
                await connection["websocket"].send_json({"client_id": client_id, "currencies": currencies,
                                                         "last_updated": cur_time})
    except WebSocketDisconnect:
        active_connections.remove(next(conn for conn in active_connections if conn["websocket"] == websocket))


@app.get("/")
async def get():
    return HTMLResponse(content=html_content(), status_code=200)


def html_content():
    return """
    <!DOCTYPE html>
    <html>
        <head>
            <title>Currency Observer</title>
            <script>
                const ws = new WebSocket("ws://localhost:8000/ws");
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    document.getElementById("currencies").innerText = JSON.stringify(data.currencies, null, 2);
                    document.getElementById("client-id").innerText = "Client ID: " + data.client_id;
                    document.getElementById("last-updated").innerText = "Last Updated: " + data.last_updated;
                };
            </script>
        </head>
        <body>
            <h1>Currency Observer</h1>
            <div id="client-id"></div>
            <div id="last-updated"></div>
            <pre id="currencies"></pre>
        </body>
    </html>
    """


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
