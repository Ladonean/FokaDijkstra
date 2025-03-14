import streamlit as st
from streamlit_folium import st_folium
import folium
import math
import base64
import time
from pyproj import Transformer
import networkx as nx
from folium import IFrame, Popup, Element
from folium.plugins import PolyLineTextPath

# ---------------------------
# Dane – lista punktów (w metrach, EPSG:2180) – 30 punktów
# ---------------------------
punkty = {
    1: (475268, 723118), 2: (472798, 716990), 3: (478390, 727009),
    4: (476650, 725153), 5: (476622, 721571), 6: (477554, 720574),
    7: (474066, 724361), 8: (472297, 726195), 9: (465609, 730292),
    10: (474121, 727887), 11: (468217, 726296), 12: (465439, 724391),
    13: (465959, 719280), 14: (469257, 720007), 15: (473811, 717807),
    16: (475696, 717669), 17: (477528, 723238), 18: (483004, 720271),
    19: (474542, 720350), 20: (477733, 718819), 21: (475730, 715454),
    22: (470501, 722655), 23: (469834, 727580), 24: (472429, 720010),
    25: (482830, 723376), 26: (475686, 727888), 27: (490854, 720757),
    28: (496518, 721917), 29: (485721, 721588), 30: (495889, 718798)
}

# ---------------------------
# Konwersja współrzędnych z EPSG:2180 do EPSG:4326 (lat, lon)
# ---------------------------
transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
latlon_nodes = {}
for node, (x, y) in punkty.items():
    lon, lat = transformer.transform(x, y)
    latlon_nodes[node] = (lat, lon)

# ---------------------------
# Inicjalizacja stanu sesji: trasy, widoku mapy, start_time
# ---------------------------
if "route" not in st.session_state:
    st.session_state.route = []
if "map_center" not in st.session_state:
    avg_lat = sum(lat for lat, lon in latlon_nodes.values()) / len(latlon_nodes)
    avg_lon = sum(lon for lat, lon in latlon_nodes.values()) / len(latlon_nodes)
    st.session_state.map_center = [avg_lat, avg_lon]
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 12
if "start_time" not in st.session_state:
    st.session_state.start_time = None

if st.button("Resetuj trasę"):
    st.session_state.route = []
    st.session_state.start_time = None

# ---------------------------
# Funkcja tworząca mapę Folium
# ---------------------------
def create_map():
    m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)

    # Dodajemy markery dla węzłów
    for node, (lat, lon) in latlon_nodes.items():
        folium.Marker(location=[lat, lon], tooltip=f"Node {node}").add_to(m)
    
    # Rysujemy trasę (żółta linia) jeśli zdefiniowano
    if st.session_state.route:
        route_coords = [latlon_nodes[node] for node in st.session_state.route if node in latlon_nodes]
        folium.PolyLine(locations=route_coords, color="yellow", weight=4).add_to(m)
    
    return m

# Wyświetlamy mapę – zwracamy "last_clicked"
map_data = st_folium(create_map(), width=1000, height=600, returned_objects=["last_clicked"])

# Aktualizacja widoku mapy – tylko przy kliknięciu (centrowanie na klikniętym węźle, zoom stały)
if map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lng = map_data["last_clicked"]["lng"]
    st.session_state.map_center = [clicked_lat, clicked_lng]
    st.session_state.map_zoom = 15  # Stały poziom zoom po kliknięciu

# Obsługa kliknięcia – dodawanie węzła do trasy, gdy kliknięcie jest blisko punktu
if map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lng = map_data["last_clicked"]["lng"]
    threshold = 300  # 300 metrów
    snapped_node = None
    for node, (lat, lon) in latlon_nodes.items():
        d = math.sqrt((lat - clicked_lat) ** 2 + (lon - clicked_lng) ** 2) * 111000  # Przeliczenie stopni na metry
        if d < threshold:
            snapped_node = node
            break
    if snapped_node is not None:
        if snapped_node not in st.session_state.route:
            st.session_state.route.append(snapped_node)
            st.success(f"Dodano węzeł {snapped_node} do trasy")

# Wyświetlenie wybranej trasy
st.write("Wybrana trasa:", st.session_state.route)
