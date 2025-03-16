import streamlit as st
from streamlit_folium import st_folium
import folium
import math
import base64
import time
from pyproj import Transformer
import networkx as nx
from folium import DivIcon, IFrame, Popup
import os
from PIL import Image
import io

############################
# Ustawienia strony (Streamlit)
############################
st.set_page_config(
    page_title="Mapa Zadanie: 12 → 28",
    layout="wide",
    initial_sidebar_state="expanded"
)

############################
# CSS dla płynnego przewijania
############################
st.markdown("""
    <style>
    html { scroll-behavior: smooth; }
    </style>
    """, unsafe_allow_html=True)

############################
# Menu w sidebarze
############################
with st.sidebar:
    st.title("DijkstraFoka")
    st.subheader("Menu:")
    st.markdown(
        """
        - [Start](#start)
        - [Samouczek](#samouczek)
        - [Wyzwanie](#wyzwanie)
        - [Teoria](#teoria)
        """,
        unsafe_allow_html=True
    )

############################
# Sekcje nagłówkowe
############################
st.title("Zadanie: Najkrótsza droga od węzła 12 do 28")

# Sekcja 1: Start
st.markdown('<h2 id="start">Start</h2>', unsafe_allow_html=True)
st.write("Witamy w aplikacji! Tutaj możesz zacząć swoją przygodę z wyszukiwaniem najkrótszej trasy od węzła 12 do 28.")

# Sekcja 2: Samouczek
st.markdown('<h2 id="samouczek">Samouczek</h2>', unsafe_allow_html=True)
st.write("""\
1. Kliknij **bezpośrednio na marker** (kółko z numerem), by go wybrać.  
2. Obok mapy (w prawej kolumnie) pojawi się szczegółowy opis i przycisk „Wybierz punkt”.  
3. Punkty można dodawać do trasy, jeśli łączą się z poprzednim wybranym (graf używa 3 najbliższych sąsiadów).  
4. Po dodaniu węzła 28 automatycznie pojawi się (na żółto) wybrana trasa oraz (na zielono) najkrótsza możliwa ścieżka.  
5. Odległości (w km) widoczne są na środku każdej szarej krawędzi, a czas liczony jest od momentu wybrania pierwszego punktu.
""")

# Sekcja 3: Wyzwanie
st.markdown('<h2 id="wyzwanie">Wyzwanie</h2>', unsafe_allow_html=True)

############################
# Dane węzłów + nazwy + obrazki
############################
# (1) Węzły (EPSG:2180)
punkty = {
    1: (475268, 723118), 2: (472798, 716990), 3: (478390, 727009),
    4: (476650, 725153), 5: (476622, 721571), 6: (477554, 720574),
    7: (474358, 724280), 8: (472297, 726195), 9: (465609, 730292),
    10: (474121, 727887), 11: (468217, 726296), 12: (465439, 724391),
    13: (465959, 719280), 14: (469257, 720007), 15: (473811, 717807),
    16: (475696, 717669), 17: (477528, 723238), 18: (483004, 720271),
    19: (474542, 720350), 20: (477733, 718819), 21: (475730, 715454),
    22: (470501, 722655), 23: (469834, 727580), 24: (472429, 720010),
    25: (482830, 723376), 26: (475686, 727888), 27: (490854, 720757),
    28: (496518, 721917), 29: (485721, 721588), 30: (495889, 718798),
    31: (472229, 727344), 32: (476836, 720475)  # dodatkowe punkty
}

# (2) Nazwy węzłów
node_names = {
    1: "PG",
    2: "Parkrun Gdańsk Południe",
    3: "Pomnik Obrońców Wybrzeża",
    4: "Bursztynowy",
    5: "Góra Gradowa",
    6: "Posejdon",
    7: "Gdańsk Wrzeszcz",
    8: "UG",
    9: "Parkrun Gdańsk Osowa",
    10: "Parkrun Gdańsk Regana",
    11: "Trójmiejski Park Krajobrazowy",
    12: "Lotnisko",
    13: "Las Otomiński",
    14: "Jezioro Jasień",
    15: "Kozacza Góra",
    16: "Park Oruński",
    17: "Stocznia Remontowa",
    18: "Rafineria",
    19: "Pomnik Mickiewicza",
    20: "Dwór Olszynka",
    21: "Park Ferberów",
    22: "Sanktuarium Matemblewo",
    23: "ZOO",
    24: "Zbiornik Łabędzia",
    25: "Plaża Stogi",
    26: "Molo Brzeźno",
    27: "Plaża SObieszewo",
    28: "Punkt Widokowy Sobieszewo Mewia Łacha",
    29: "Marina Przełom",
    30: "Prom Świbno",
    31: "Gdańsk Oliwa",
    32: "Gdańsk Śródmieście"
}

# (3) Funkcja do wczytania i zakodowania obrazka w base64
def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

images_base64 = {}
for n in punkty.keys():
    fname = f"img{n}.png"
    if os.path.exists(fname):
        images_base64[n] = get_image_base64(fname)
    else:
        images_base64[n] = get_image_base64("img_placeholder.png")

def euclidean_distance_km(p1, p2):
    return round(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) / 1000, 1)

# Budowa grafu (3 najbliższych sąsiadów)
G = nx.Graph()
for num, coord in punkty.items():
    G.add_node(num, pos=coord)
for num, coord in punkty.items():
    distances = []
    for other_num, other_coord in punkty.items():
        if other_num != num:
            dval = euclidean_distance_km(coord, other_coord)
            distances.append((other_num, dval))
    distances.sort(key=lambda x: x[1])
    nearest = distances[:3]
    for (onum, distv) in nearest:
        G.add_edge(num, onum, weight=distv)

# Dodajemy dodatkowe (specjalne) krawędzie między 31 a 7 oraz 7 a 32
# Te krawędzie są "przyspieszone": waga = EuclideanDistance * 0.5
special_edges = [(31, 7), (7, 32)]
for u, v in special_edges:
    special_weight = euclidean_distance_km(punkty[u], punkty[v]) * 0.5
    if G.has_edge(u, v):
        G[u][v]["weight"] = min(G[u][v]["weight"], special_weight)
    else:
        G.add_edge(u, v, weight=special_weight)

# Konwersja EPSG:2180 -> EPSG:4326
transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
latlon_nodes = {}
for n, (x, y) in punkty.items():
    lon, lat = transformer.transform(x, y)
    latlon_nodes[n] = (lat, lon)

############################
# Stan sesji
############################
if "route" not in st.session_state:
    st.session_state["route"] = []
if "map_center" not in st.session_state:
    center_lat = sum(v[0] for v in latlon_nodes.values()) / len(latlon_nodes)
    center_lon = sum(v[1] for v in latlon_nodes.values()) / len(latlon_nodes)
    st.session_state["map_center"] = [center_lat, center_lon]
if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 12
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "show_shortest" not in st.session_state:
    st.session_state["show_shortest"] = False

############################
# Dodatkowa trasa przyspieszona przez kontrolne punkty
############################
control_points = [
    (476836.13, 720474.95),
    (476867.00, 720974.20),
    (476939.43, 721489.61),
    (476922.72, 721731.99),
    (476822.42, 722202.83),
    (476588.40, 722484.22),
    (476131.49, 723186.29),
    (475905.82, 723356.24),
    (475579.86, 723542.90),
    (474625.15, 724115.93),
    (474358.48, 724280.19),
    (473638.71, 724997.54),
    (473142.45, 725519.92),
    (472633.14, 726172.89),
    (472428.54, 726608.20),
    (472284.89, 726986.93),
    (472229.03, 727344.24)
]
control_points_latlon = []
for pt in control_points:
    lon, lat = transformer.transform(pt[0], pt[1])
    control_points_latlon.append((lat, lon))
def compute_control_distance(points):
    total = 0.0
    for i in range(len(points)-1):
        dx = points[i+1][0] - points[i][0]
        dy = points[i+1][1] - points[i][1]
        d = math.sqrt(dx**2 + dy**2) / 1000  # w km
        total += d
    return total * 0.5
control_distance = compute_control_distance(control_points)
control_distance_text = f"{control_distance:.1f} km"

############################
# Layout: 2 kolumny: mapa (col_map) i panel informacyjny (col_info)
############################
col_map, col_info = st.columns([2, 1])

with col_map:
    folium_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])
    # Krawędzie (szare) oraz etykiety
    for u, v, data in G.edges(data=True):
        if (u, v) in special_edges or (v, u) in special_edges:
            continue  # specjalne krawędzie nie rysujemy
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        distv = data["weight"]
        line = folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color="gray",
            weight=2,
            tooltip=f"{distv} km"
        )
        line.add_to(folium_map)
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        dist_icon = DivIcon(
            html=f"""
            <div style="font-size:14px;font-weight:bold;color:black;">
                {distv}
            </div>
            """
        )
        folium.Marker([mid_lat, mid_lon], icon=dist_icon).add_to(folium_map)
    
    # Markery węzłów (bez popupów, używamy tooltipów)
    for node in latlon_nodes:
        latn, lonn = latlon_nodes[node]
        nm = node_names[node]
        folium.Marker(
            location=[latn, lonn],
            tooltip=nm,
            icon=DivIcon(html=f"""
            <div style="text-align:center;">
                <div style="background-color:red;color:white;border-radius:50%;
                            width:24px;height:24px;font-size:12pt;font-weight:bold;
                            line-height:24px;margin:auto;">
                {node}
                </div>
            </div>
            """)
        ).add_to(folium_map)
    
    # Trasa użytkownika (żółta)
    if st.session_state["route"]:
        coords_route = [latlon_nodes[n] for n in st.session_state["route"]]
        folium.PolyLine(locations=coords_route, color="yellow", weight=4).add_to(folium_map)
    
    # Rysujemy specjalną trasę przez punkty kontrolne (niebieska, przerywana)
    folium.PolyLine(
        locations=control_points_latlon,
        color="blue",
        weight=4,
        dash_array="5,10",
        tooltip=f"Przyspieszona trasa: {control_distance_text}"
    ).add_to(folium_map)
    
    # Najkrótsza trasa (zielona) – jeśli show_shortest
    if st.session_state["show_shortest"]:
        sp_nodes = nx.shortest_path(G, 12, 28, weight="weight")
        coords_sp = [latlon_nodes[x] for x in sp_nodes]
        folium.PolyLine(
            locations=coords_sp,
            color="green",
            weight=5,
            tooltip="Najkrótsza (12->28)"
        ).add_to(folium_map)
    
    map_data = st_folium(
        folium_map,
        width=800,
        height=600,
        returned_objects=["last_object_clicked_tooltip"]
    )

with col_info:
    st.subheader("Szczegóły punktu:")
    clicked_name = None
    if map_data and map_data.get("last_object_clicked_tooltip"):
        clicked_name = map_data["last_object_clicked_tooltip"]
    if clicked_name:
        candidate_node = None
        for k, v in node_names.items():
            if v == clicked_name:
                candidate_node = k
                break
        if candidate_node is not None:
            # Wyświetlamy obrazek – skalowany do maksymalnie 300x300 pikseli
            b64 = images_base64[candidate_node]
            img_data = base64.b64decode(b64)
            img = Image.open(io.BytesIO(img_data))
            max_size = (300, 300)
            img.thumbnail(max_size)
            st.image(img)
            st.write(f"**{clicked_name}** (ID: {candidate_node})")
            # Sprawdzamy, czy punkt można dodać (musi być sąsiadem ostatniego wybranego)
            last_node = st.session_state["route"][-1] if st.session_state["route"] else None
            allowed = True
            if last_node is not None:
                if candidate_node not in list(G.neighbors(last_node)):
                    allowed = False
            if st.button("Wybierz punkt", key=f"btn_{candidate_node}", disabled=not allowed):
                if allowed:
                    if candidate_node not in st.session_state["route"]:
                        st.session_state["route"].append(candidate_node)
                        st.success(f"Dodano węzeł {candidate_node} ({clicked_name}) do trasy!")
                        # Aktualizacja mapy: wycentruj i przybliż na wybranym punkcie
                        st.session_state["map_center"] = latlon_nodes[candidate_node]
                        st.session_state["map_zoom"] = 13
                        st.rerun()
                    else:
                        st.warning("Ten węzeł już jest w trasie.")
                else:
                    st.warning("Nie można dodać – punkt nie jest sąsiadem ostatniego węzła.")
        else:
            st.write("Nie znaleziono punktu o tej nazwie.")
    else:
        st.write("Kliknij na marker, aby zobaczyć szczegóły.")
    
    if st.session_state["route"]:
        named_route = [f"{n} ({node_names[n]})" for n in st.session_state["route"]]
        st.write("Wybrane punkty użytkownika (kolejność):", named_route)
    else:
        st.write("Brak wybranych punktów.")
    
    def total_user_distance(route):
        dsum = 0.0
        for i in range(len(route)-1):
            u = route[i]
            v = route[i+1]
            if G.has_edge(u, v):
                dsum += G[u][v]["weight"]
        return dsum
    user_dist = total_user_distance(st.session_state["route"])
    st.write(f"Łączna droga użytkownika: {user_dist:.1f} km")

############################
# Pomiar czasu
############################
if st.session_state["route"] and st.session_state["start_time"] is None:
    st.session_state["start_time"] = time.time()
if st.session_state["start_time"] is not None:
    elapsed = time.time() - st.session_state["start_time"]
    st.write(f"Czas od rozpoczęcia trasy: {elapsed:.1f} s")

############################
# Przycisk reset
############################
if st.button("Resetuj trasę"):
    st.session_state["route"] = []
    st.session_state["start_time"] = None
    st.session_state["show_shortest"] = False
    st.rerun()

############################
# Najkrótsza trasa (zielona) – po dotarciu do węzła 28
############################
if 28 in st.session_state["route"]:
    st.session_state["show_shortest"] = True
    if nx.has_path(G, 12, 28):
        shortest_nodes = nx.shortest_path(G, 12, 28, weight='weight')
        shortest_len = nx.shortest_path_length(G, 12, 28, weight='weight')
        st.write(f"Najkrótsza możliwa trasa (12 -> 28): {shortest_nodes}")
        st.write(f"Długość najkrótszej trasy: {shortest_len:.1f} km")
        st.success("Gratulacje, dotarłeś do węzła 28!")
        st.rerun()
    else:
        st.write("Brak ścieżki pomiędzy 12 a 28.")

############################
# Sekcja 4: Teoria
############################
st.markdown('<h2 id="teoria">Teoria</h2>', unsafe_allow_html=True)
st.write("""\
Algorytm Dijkstry wyznacza najkrótszą ścieżkę w grafie o nieujemnych wagach.
Możesz myśleć o nim jak o szukaniu najtańszej trasy na mapie:
- **węzły** to miasta,
- **krawędzie** to drogi,
- **waga** to długość/odległość.
""")
st.write("""\
**Zastosowania**  

- Nawigacja (GPS)  
- Sieci komputerowe (protokół OSPF)  
- Transport i logistyka  
- Gry i robotyka  
""")
if st.button("Pokaż animację algorytmu Dijkstry"):
    if os.path.exists("dijkstra_steps.gif"):
        st.image("dijkstra_steps.gif", caption="Przykładowy przebieg algorytmu Dijkstry.")
    else:
        st.warning("Brak pliku dijkstra_steps.gif w katalogu.")
