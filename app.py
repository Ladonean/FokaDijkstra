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
import os

############################
# Ustawienia strony: tytuł, tryb szerokości, stan paska bocznego itp.
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
            """, unsafe_allow_html=True)

############################
# Sekcje: Start, Samouczek, Wyzwanie, Teoria
############################
st.title("Zadanie: Najkrótsza droga od węzła 12 do 28")

# Sekcja 1: Start
st.markdown('<h2 id="start">Start</h2>', unsafe_allow_html=True)
st.write("Witamy w aplikacji! Tutaj możesz zacząć swoją przygodę z wyszukiwaniem najkrótszej trasy od węzła 12 do 28.")

# Sekcja 2: Samouczek
st.markdown('<h2 id="samouczek">Samouczek</h2>', unsafe_allow_html=True)
st.write("""\
1. Kliknij blisko węzła na mapie, by wybrać kolejne węzły trasy, kliknij na węzeł żeby zobaczyć co się tam znajduje :)
2. Trasa jest rysowana na żółto.
3. Po dodaniu węzła 28 pojawi się zielona linia – najkrótsza możliwa ścieżka z 12 do 28.
4. Odległość w km wyświetlana jest na środku każdej szarej krawędzi.
5. Czas liczony jest od momentu pierwszego dodanego węzła.""")

# Sekcja 3: Wyzwanie (Właściwa mapa i logika)
st.markdown('<h2 id="wyzwanie">Wyzwanie</h2>', unsafe_allow_html=True)

############################
# Dane węzłów + nazwy + obrazy
############################

# (1) Węzły (EPSG:2180)
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

# (2) Nazwy węzłów
node_names = {
    1: "PG",
    2: "Parkrun Gdańsk Południe",
    3: "Pomnik Obrońców Wybrzeża",
    4: "Bursztynowy",
    5: "Góra Gradowa",
    6: "Posejdon",
    7: "Galeria Bałtycka",
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
    30: "Prom Świbno"
}

# (3) Funkcja do wczytania i zakodowania obrazka w base64
def get_image_base64(path):
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# (4) Mapujemy każdy węzeł => plik obrazka np. "img1.png", "img2.png" itd.
images_base64 = {}
for node_id in punkty.keys():
    image_filename = f"img{node_id}.png"  # np. nazwa pliku dla węzła 1 to "img1.png"
    if os.path.exists(image_filename):
        images_base64[node_id] = get_image_base64(image_filename)
    else:
        # jeśli nie istnieje plik, można wstawić placeholder
        images_base64[node_id] = get_image_base64("img_placeholder.png")  # lub pominąć

############################
# Funkcja licząca odległość euklidesową (km)
############################
def euclidean_distance_km(p1, p2):
    return round(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) / 1000, 1)

############################
# Budowa grafu w NetworkX
############################
G = nx.Graph()
for num, coord in punkty.items():
    G.add_node(num, pos=coord)

for num, coord in punkty.items():
    distances = []
    for other_num, other_coord in punkty.items():
        if other_num != num:
            d = euclidean_distance_km(coord, other_coord)
            distances.append((other_num, d))
    distances.sort(key=lambda x: x[1])
    nearest = distances[:3]
    for other_num, dist_val in nearest:
        G.add_edge(num, other_num, weight=dist_val)

############################
# Konwersja EPSG:2180 → EPSG:4326
############################
transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
latlon_nodes = {}
for node, (x, y) in punkty.items():
    lon, lat = transformer.transform(x, y)
    latlon_nodes[node] = (lat, lon)

############################
# Stan sesji (route, center, zoom, start_time, show_shortest)
############################
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
if "show_shortest" not in st.session_state:
    st.session_state.show_shortest = False

############################
# Definicja mapy
############################
def create_map():
    m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)

    # Rysujemy krawędzie + odległość na środku
    for u, v, data in G.edges(data=True):
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        distance = data["weight"]
        
        # Linia
        line = folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color="gray",
            weight=2,
            tooltip=f"{distance} km"
        )
        line.add_to(m)

        # Środek
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        distance_icon = folium.DivIcon(
            html=f"""
                <div style="
                    font-size: 16px;
                    font-weight: bold;
                    color: black;
                    padding: 2px 4px;
                    border-radius: 0px;
                ">
                    {distance}
                </div>
            """
        )
        folium.Marker(location=[mid_lat, mid_lon], icon=distance_icon).add_to(m)

    # Rysujemy węzły (markery)
    for node, (lat, lon) in latlon_nodes.items():
        # 1) nazwa węzła
        name = node_names.get(node, f"Node {node}")
        
        # 2) pobieramy zakodowany obrazek
        img64 = images_base64[node]
        
        # 3) budujemy HTML do popupu
        popup_html = f"""
            <img src="data:image/png;base64,{img64}" width="180" height="200" style="object-fit:cover;"><br>
            {name}<br>
        """
        iframe = IFrame(html=popup_html, width=215, height=235)
        popup = Popup(iframe, max_width=215)

        # Wyświetlany numer w kółku
        marker_html = f"""
            <div style="text-align: center;">
              <div style="
                background-color: red;
                color: white;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                margin: auto;
                font-size: 12pt;
                font-weight: bold;
                line-height: 24px;">
                {node}
              </div>
            </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=popup,
            tooltip=name,
            icon=folium.DivIcon(html=marker_html)
        ).add_to(m)
    
    # Trasa użytkownika (żółta)
    if st.session_state.route:
        coords_route = [latlon_nodes[n] for n in st.session_state.route]
        folium.PolyLine(locations=coords_route, color="yellow", weight=4).add_to(m)

    # Najkrótsza (12->28) (zielona)
    if st.session_state.show_shortest:
        shortest_path_12_28 = nx.shortest_path(G, source=12, target=28, weight='weight')
        coords_sp = [latlon_nodes[n] for n in shortest_path_12_28]
        folium.PolyLine(
            locations=coords_sp,
            color="green",
            weight=5,
            tooltip="Najkrótsza ścieżka (12->28)"
        ).add_to(m)

    return m

############################
# Wyświetlenie mapy
############################
map_data = st_folium(create_map(), width=800, height=500, returned_objects=["last_clicked"])

# Kliknięcie -> center + zoom
if map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lng = map_data["last_clicked"]["lng"]
    st.session_state.map_center = [clicked_lat, clicked_lng]
    st.session_state.map_zoom = 13.5

############################
# Dodawanie węzła do trasy
############################
if map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lng = map_data["last_clicked"]["lng"]
    threshold = 400
    snapped_node = None
    for node, (lat, lon) in latlon_nodes.items():
        dx = (lat - clicked_lat) * 111000
        dy = (lon - clicked_lng) * 111000
        d = math.sqrt(dx**2 + dy**2)
        if d < threshold:
            snapped_node = node
            break
    if snapped_node is not None:
        if st.session_state.route:
            last_node = st.session_state.route[-1]
            allowed_nodes = list(G.neighbors(last_node))
            if snapped_node in allowed_nodes:
                if snapped_node not in st.session_state.route:
                    st.session_state.route.append(snapped_node)
                    st.success(f"Dodano węzeł {snapped_node} ({node_names[snapped_node]}) do trasy")
            else:
                st.warning(f"Węzeł {snapped_node} nie jest powiązany z węzłem {last_node}")
        else:
            st.session_state.route.append(snapped_node)
            st.success(f"Dodano węzeł {snapped_node} ({node_names[snapped_node]}) do trasy")

############################
# Rozpoczęcie licznika
############################
if st.session_state.route and st.session_state.start_time is None:
    st.session_state.start_time = time.time()

if st.session_state.start_time is not None:
    elapsed = time.time() - st.session_state.start_time
    st.write(f"Elapsed time: {elapsed:.1f} seconds")

############################
# Przycisk reset
############################
if st.button("Resetuj trasę"):
    st.session_state.route = []
    st.session_state.start_time = None
    st.session_state.show_shortest = False

############################
# Liczenie łącznej drogi
############################
def total_user_distance(route):
    dist = 0.0
    for i in range(len(route)-1):
        u = route[i]
        v = route[i+1]
        if G.has_edge(u, v):
            dist += G[u][v]["weight"]
    return dist

user_dist = total_user_distance(st.session_state.route)
st.write(f"Łączna droga użytkownika: {user_dist:.1f} km")

############################
# Wybrana trasa (nazwy)
############################
named_route = [node_names[n] for n in st.session_state.route]
st.write(f"Wybrane punkty użytkownika (kolejność): {named_route}")

############################
# Najkrótsza droga (12 -> 28) po dotarciu
############################
if 28 in st.session_state.route:
    st.session_state.show_shortest = True
    if nx.has_path(G, 12, 28):
        shortest_path_12_28 = nx.shortest_path(G, 12, 28, weight='weight')
        st.write(f"Najkrótsza możliwa trasa (12 -> 28): {shortest_path_12_28}")
        shortest_length_12_28 = nx.shortest_path_length(G, 12, 28, weight='weight')
        st.write("\nGratulacje! Dotarłeś do węzła 28.")
        st.write(f"Najkrótsza możliwa trasa (12 -> 28) ma długość: {shortest_length_12_28:.1f} km")
    else:
        st.write("Brak ścieżki pomiędzy 12 a 28.")

############################
# Sekcja 4: Teoria
############################
st.markdown('<h2 id="teoria">Teoria</h2>', unsafe_allow_html=True)

st.write("""Algorytm Dijkstry wyznacza najkrótszą ścieżkę w grafie o nieujemnych wagach.
Możesz myśleć o nim jak o szukaniu najtańszej trasy na mapie: węzły to miasta, a wagi krawędzi to długości dróg.
""")

st.write("""
**Zastosowania**  

Nawigacja:  
Znajdowanie najszybszej trasy w systemach GPS.  

Sieci komputerowe:  
Protokół OSPF używa Dijkstry do trasowania pakietów.  

Transport i logistyka:  
Optymalizacja kosztów przewozu w firmach kurierskich.  

Gry i robotyka:  
Wytyczanie drogi postaciom w grach lub robotom w terenie.
""")

if st.button("Pokaż animację algorytmu Dijkstry"):
    st.image("dijkstra_steps.gif", caption="Przykładowy przebieg algorytmu Dijkstry.")


