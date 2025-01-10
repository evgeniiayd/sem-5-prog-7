import pytest
from fastapi.testclient import TestClient
from main import app, CurrenciesLst

# Создаем клиент для тестирования
client = TestClient(app)

# Инициализируем класс для хранения курсов валют
currencies_list = CurrenciesLst()


# Проверка статуса главной страницы
def test_get_main_page():
    """Тестирует доступность главной страницы"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Currency Observer" in response.text


# Проверка инициализации списка валют
def test_currencies_initialization():
    """Проверяет, что список валют инициализирован пустым словарем"""
    assert currencies_list.cur_lst == {}


# Проверка установки идентификаторов валют
def test_set_ids():
    """Тестирует установку идентификаторов валют"""
    currencies_list.set_ids(['R01235', 'R01239'])
    assert currencies_list._ids_lst == ['R01235', 'R01239']


# Проверка получения курсов валют
def test_get_currencies():
    """Проверяет получение курсов валют из API"""
    currencies_list.set_ids(['R01235', 'R01239'])
    currencies = currencies_list.get_currencies()
    assert 'Доллар США' in currencies  # Проверяем, что доллар США есть в списке
    assert 'Евро' in currencies  # Проверяем, что евро есть в списке


# Проверка корректности полученных данных
def test_currencies_data_format():
    """Проверяет формат данных, получаемых из API."""
    currencies_list.set_ids(['R01235', 'R01239'])
    currencies = currencies_list.get_currencies()
    for key, value in currencies.items():
        assert isinstance(key, str)  # Название валюты должно быть строкой
        assert isinstance(value, tuple)  # Значение должно быть кортежем

# Проверка на наличие валют с неверными ID
def test_invalid_currency_ids():
    """Проверяет, что происходит с неверными ID валют"""
    currencies_list.set_ids(['INVALID_ID'])
    currencies = currencies_list.get_currencies()
    assert 'INVALID_ID' in currencies
    assert currencies['INVALID_ID'] is None  # Ожидаем, что для неверного ID будет None

