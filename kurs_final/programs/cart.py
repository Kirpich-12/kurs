
import webbrowser
import pandas as pd
import folium
import os
from folium.plugins import HeatMap
from folium.plugins import MarkerCluster

from update_data import get_data
from models import Link, BankBranch



class DataLoader:
    """Получение данных напрямую из update_data.py"""
    
    def __init__(self, currency: Link):
        self.currency = currency
    
    def load_data(self) -> pd.DataFrame:
        """Запрашивает данные через парсер/кэш и возвращает DataFrame"""
<<<<<<< HEAD
        print(f"[INFO] Получение данных для {self.currency.name}...")

        raw_data = get_data(self.currency)

        data = []
        for branch in raw_data:
            buy_rate = None
            sell_rate = None

            for rate in branch.exchange_rates:
                if rate.curr_to == "byn":
                    buy_rate = rate.rate
                elif rate.curr_from == "byn":
                    sell_rate = rate.rate

            if buy_rate and sell_rate:
                data.append({
                    "address": branch.address,
                    "bank_name": str(branch.bank_org),
                    "sell_course": float(sell_rate),
                    "buy_course": float(buy_rate),
                    "lat": float(branch.coords.lat),
                    "lon": float(branch.coords.lon)
                })

        df = pd.DataFrame(data)
        print(f"[INFO] Данные успешно загружены. Найдено отделений: {len(df)}")
        return df
=======
        branches = get_data(self.currency)
        return self._convert_to_dataframe(branches)

    def _convert_to_dataframe(self, branches: list[BankBranch]) -> pd.DataFrame:
        records = []
        for branch in branches:
            record = {
                "branch_id": branch.id,
                "bank_name": branch.bank_org.name,
                "address": branch.address,
                "lon": branch.coords.lon,
                "lat": branch.coords.lat,
                "buy_course": None,
                "sell_course": None,
            }

            # Маппим курсы: парсер передает buy_course как BYN->USD, sell_course как USD->BYN
            for rate in branch.exchange_rates:
                if rate.curr_from.value == "byn" and rate.curr_to.value == "usd":
                    record["buy_course"] = float(rate.rate)
                elif rate.curr_from.value == "usd" and rate.curr_to.value == "byn":
                    record["sell_course"] = float(rate.rate)

            records.append(record)

        df = pd.DataFrame(records)

        if df["buy_course"].isna().all():
            raise ValueError(f"No buy_course (BYN->USD) rates found. Available branches: {len(df)}. Check if parser returned data with correct exchange rates.")

        return df.dropna(subset=["buy_course"])
>>>>>>> 42866260137d211fe9799273af3835200a16db6b

class DataProcessor:
    """Обработка трансформаций и вычислений данных"""
    
    @staticmethod
    def compute_weight(df: pd.DataFrame) -> pd.DataFrame:
        """Вычисление веса: более низкий курс = более высокое влияние"""
        df_copy = df.copy()

        if "buy_course" not in df_copy.columns:
            raise ValueError("Column 'buy_course' not found in dataframe. Check if exchange rates are being parsed correctly.")

        df_copy["weight_raw"] = 1 / df_copy["buy_course"]

        min_w, max_w = df_copy["weight_raw"].min(), df_copy["weight_raw"].max()
        df_copy["weight"] = (df_copy["weight_raw"] - min_w) / (max_w - min_w + 1e-6)
        df_copy["weight"] = df_copy["weight"] ** 2.5

        return df_copy
    
    @staticmethod
    def get_color(course: float, min_c: float, max_c: float) -> str:
        """Возвращает цвет на основе курса: зеленый = лучший, красный = худший"""
        norm = (course - min_c) / (max_c - min_c + 1e-6)
        norm = norm ** 2

        if norm < 0.33:
            return "green"
        elif norm < 0.66:
            return "orange"
        return "red"


class MapBuilder:
    """Построение карты folium со всеми слоями"""
    
    def __init__(self, center: tuple, zoom: int):
        self.center = center
        self.zoom = zoom
        self.map = folium.Map(location=center, zoom_start=zoom)
    
    def add_heatmap(self, df: pd.DataFrame) -> "MapBuilder":
        """Добавление слоя тепловой карты"""
        heat_data = df[["lat", "lon", "weight"]].values.tolist()
        HeatMap(
            heat_data,
            radius=20,
            blur=15,
            min_opacity=0.3,
            max_zoom=18
        ).add_to(self.map)
        return self
    
    def add_markers(self, df: pd.DataFrame) -> "MapBuilder":
        """Добавление кластеризованных маркеров с цветами на основе курсов"""
        cluster = MarkerCluster(
            disableClusteringAtZoom=15,
            spiderfyOnMaxZoom=True,
            zoomToBoundsOnClick=True,
            showCoverageOnHover=False
        ).add_to(self.map)

        min_c = df["buy_course"].min()
        max_c = df["buy_course"].max()

        for _, row in df.iterrows():
            color = DataProcessor.get_color(row["buy_course"], min_c, max_c)
            popup = self._create_popup(row)

            folium.CircleMarker(
                location=[row["lat"], row["lon"]],
                radius=8,
                color=color,
                fill=True,
                fill_opacity=0.88,
                weight=2,
                popup=folium.Popup(popup, max_width=300),
            ).add_to(cluster)
        
        return self
    
<<<<<<< HEAD
    def add_best_buy_marker(self, df: pd.DataFrame) -> "MapBuilder":
        """Добавление маркера для лучшей покупки (минимальный курс покупки)"""
        best = df.loc[df["buy_course"].idxmin()]
        popup = f"💰 <b>ЛУЧШАЯ ПОКУПКА</b><br><b>{best['bank_name']}</b><br>Курс: {best['buy_course']}<br>{best['address']}"

        folium.Marker(
            location=[best["lat"], best["lon"]],
            icon=folium.Icon(color="green", icon="arrow-down", prefix="fa"),
            popup=popup
        ).add_to(self.map)

        return self

    def add_best_sell_marker(self, df: pd.DataFrame) -> "MapBuilder":
        """Добавление маркера для лучшей продажи (максимальный курс продажи)"""
        best = df.loc[df["sell_course"].idxmax()]
        popup = f"📈 <b>ЛУЧШАЯ ПРОДАЖА</b><br><b>{best['bank_name']}</b><br>Курс: {best['sell_course']}<br>{best['address']}"

        folium.Marker(
            location=[best["lat"], best["lon"]],
            icon=folium.Icon(color="blue", icon="arrow-up", prefix="fa"),
            popup=popup
=======
    def add_best_rate_marker(self, df: pd.DataFrame) -> "MapBuilder":
        """Добавление звездных маркеров для лучшего курса покупки и продажи"""
        best_buy = df.loc[df["buy_course"].idxmin()]
        popup_buy = f"★ <b>ЛУЧШАЯ ПОКУПКА</b><br><b>{best_buy['bank_name']}</b><br>Курс: {best_buy['buy_course']}<br>{best_buy['address']}"

        folium.Marker(
            location=[best_buy["lat"], best_buy["lon"]],
            icon=folium.Icon(color="green", icon="star", prefix="fa"),
            popup=popup_buy
        ).add_to(self.map)

        best_sell = df.loc[df["sell_course"].idxmax()]
        popup_sell = f"★ <b>ЛУЧШАЯ ПРОДАЖА</b><br><b>{best_sell['bank_name']}</b><br>Курс: {best_sell['sell_course']}<br>{best_sell['address']}"

        folium.Marker(
            location=[best_sell["lat"], best_sell["lon"]],
            icon=folium.Icon(color="blue", icon="star", prefix="fa"),
            popup=popup_sell
>>>>>>> 42866260137d211fe9799273af3835200a16db6b
        ).add_to(self.map)

        return self
    
    def save(self, filename: str) -> str:
        """Сохранение карты в HTML файл"""
        self.map.save(filename)
        print(f"[OK] Карта сохранена: {filename}")
        return filename
    
    @staticmethod
    def _create_popup(row) -> str:
        """Создание HTML всплывающего окна для маркера"""
        return f"""
        <b>{row['bank_name']}</b><br>
        <b>{row['address']}</b><br>
            Курс покупки: {row['buy_course']}<br>
            Курс продажи: {row['sell_course']}<br>
        """


class ExchangeMap:
    """Основной класс для создания интерактивной карты курсов обмена"""
    
    # Теперь передаем валюту (Link), а не путь к CSV файлу
    def __init__(self, currency: Link = Link.USD, 
                 city_center: tuple = (53.904, 27.5616), 
                 zoom: int = 12):
        self.currency = currency
        self.city_center = city_center
        self.zoom = zoom
        self.df = None
        
        self.data_loader = DataLoader(self.currency)
        self.map_builder = MapBuilder(city_center, zoom)
    
    def build(self) -> "ExchangeMap":
        """Построение полной карты со всеми слоями"""
        self.df = self.data_loader.load_data()
        self.df = DataProcessor.compute_weight(self.df)

        self.map_builder.add_heatmap(self.df)
        self.map_builder.add_markers(self.df)
        self.map_builder.add_best_buy_marker(self.df)
        self.map_builder.add_best_sell_marker(self.df)

        return self
    
    def save_and_open(self, filename: str = "generated_heatmap.html") -> None:
        """Сохранение карты и открытие в браузере"""
        filepath = self.map_builder.save(filename)
        
        try:
            # os остался только для поиска абсолютного пути к сгенерированному HTML-файлу
            webbrowser.open('file://' + os.path.realpath(filepath))
        except Exception as e:
            print(f"[WARNING] Не удалось открыть браузер: {e}")


if __name__ == "__main__":
    # Для теста генерируем карту для USD
    map_builder = ExchangeMap(currency=Link.USD)
    map_builder.build()
    map_builder.save_and_open()