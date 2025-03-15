import streamlit as st
from streamlit_folium import st_folium
import folium
import math
import base64
import time
from pyproj import Transformer
import networkx as nx
from folium import IFrame, Popup, Element
import os

############################
# Ustawienia strony
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
# Sekcje: Start, Samouczek, Wyzwanie, Teoria
############################
st.title("Zadanie: Najkrótsza droga od węzła 12 do 28")

# Sekcja 1: Start
st.markdown('<h2 id="start">Start</h2>', unsafe_allow_html=True)
st.write("Witamy w aplikacji! Tutaj możesz zacząć swoją przygodę z wyszukiwaniem najkrótszej trasy od węzła 12 do 28.")

# Sekcja 2: Samouczek
st.markdown('<h2 id="samouczek">Samouczek</h2>', unsafe_allow_html=True)
st.write("""\
1. Kliknij **dokładnie** w marker węzła (nie obok), aby zobaczyć jego popup.
2. W panelu Streamlit pojawi się komunikat i przycisk „Wybierz punkt”.
3. Po kliknięciu przycisku węzeł zostanie dodany do Twojej trasy (jeśli dozwolone jest połączenie z poprzednim).
4. Trasa jest rysowana na żółto. Po dojściu do węzła 28 ujrzysz najkrótszą możliwą (zieloną) ścieżkę w grafie.
5. Odległość w km wyświetlana jest na środku każdej szarej krawędzi.
6. Czas liczony jest od momentu pierwszego dodanego węzła.
""")

# Sekcja 3: Wyzwanie
st.markdown('<h2 id="wyzwanie">Wyzwanie</h2>', unsafe_allow_html=True)

############################
# Dane węzłów + nazwy
############################
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

############################
# Funkcja licząca odległość euklidesową (w km)
############################
def euclidean_distance_km(p1, p2):
    return round(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) / 1000, 1)

############################
# Budowa grafu (nieskierowany) - 3 najbliższych
############################
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
    for (other, distv) in nearest:
        G.add_edge(num, other, weight=distv)

############################
# Konwersja EPSG:2180 -> EPSG:4326
############################
from pyproj import Transformer
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
# create_map
############################
def create_map():
    m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)

    # Rysujemy krawędzie
    for u, v, data in G.edges(data=True):
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        distance = data["weight"]

        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color="gray",
            weight=2,
            tooltip=f"{distance} km"
        ).add_to(m)

        # Etykieta odległości na środku
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        dist_icon = folium.DivIcon(
            html=f"""
            <div style="
                font-size: 14px;
                font-weight: bold;
                color: black;
                padding: 2px 4px;">
                {distance}
            </div>"""
        )
        folium.Marker(location=[mid_lat, mid_lon], icon=dist_icon).add_to(m)

    # Markery węzłów
    for node, (lat, lon) in latlon_nodes.items():
        name = node_names.get(node, f"Node {node}")
        # popup tekstowy
        popup_html = f"Węzeł: {node}<br>{name}"
        # tooltip = name
        marker_html = f"""
        <div style="text-align:center;">
          <div style="
            background-color: red;
            color: white;
            border-radius: 50%;
            width: 24px;
            height: 24px;
            margin:auto;
            font-size:12pt;
            font-weight:bold;
            line-height:24px;">
            {node}
          </div>
        </div>
        """

        folium.Marker(
            location=[lat, lon],
            popup=popup_html,
            tooltip=name,
            icon=folium.DivIcon(html=marker_html)
        ).add_to(m)

    # Żółta linia - trasa user
    if st.session_state.route:
        coords_route = [latlon_nodes[n] for n in st.session_state.route]
        folium.PolyLine(
            locations=coords_route,
            color="yellow",
            weight=4
        ).add_to(m)

    # Zielona - najkrótsza 12->28
    if st.session_state.show_shortest:
        if nx.has_path(G, 12, 28):
            sp_nodes = nx.shortest_path(G, 12, 28, weight='weight')
            coords_sp = [latlon_nodes[n] for n in sp_nodes]
            folium.PolyLine(
                locations=coords_sp,
                color="green",
                weight=5,
                tooltip="Najkrótsza ścieżka (12->28)"
            ).add_to(m)

    return m

############################
# Wyświetlamy mapę
############################
map_data = st_folium(create_map(), width=800, height=500, returned_objects=["last_clicked"])

############################
# Rozpoznanie węzła - tylko przy kliknięciu EXACTLY w marker
############################
clicked_node = None
if map_data and map_data["last_clicked"]:
    clat = map_data["last_clicked"]["lat"]
    clng = map_data["last_clicked"]["lng"]
    # sprawdzamy, czy (clat, clng) pasuje do któregoś węzła (z drobną tolerancją)
    eps = 1e-7
    for n, (nlat, nlng) in latlon_nodes.items():
        if abs(nlat - clat) < eps and abs(nlng - clng) < eps:
            clicked_node = n
            break

if clicked_node is not None:
    st.info(f"Kliknięto w węzeł {clicked_node} ({node_names[clicked_node]})")
    # dopiero po wciśnięciu przycisku "Wybierz punkt" dodaj do trasy
    if st.button("Wybierz punkt"):
        # logika "dodaj węzeł do route"
        if st.session_state.route:
            last_node = st.session_state.route[-1]
            neighbors = list(G.neighbors(last_node))
            if clicked_node in neighbors:
                if clicked_node not in st.session_state.route:
                    st.session_state.route.append(clicked_node)
                    st.success(f"Dodano węzeł {clicked_node} ({node_names[clicked_node]}) do trasy")
            else:
                st.warning(f"Węzeł {clicked_node} nie jest powiązany z węzłem {last_node}")
        else:
            st.session_state.route.append(clicked_node)
            st.success(f"Dodano węzeł {clicked_node} ({node_names[clicked_node]}) do trasy")

############################
# Rozpoczęcie licznika czasu
############################
if st.session_state.route and st.session_state.start_time is None:
    st.session_state.start_time = time.time()

if st.session_state.start_time is not None:
    elapsed = time.time() - st.session_state.start_time
    st.write(f"Elapsed time: {elapsed:.1f} seconds")

############################
# Przyciski
############################
if st.button("Resetuj trasę"):
    st.session_state.route = []
    st.session_state.start_time = None
    st.session_state.show_shortest = False

############################
# Liczenie łącznej drogi
############################
def total_user_distance(route):
    dist_sum = 0.0
    for i in range(len(route)-1):
        u = route[i]
        v = route[i+1]
        if G.has_edge(u, v):
            dist_sum += G[u][v]["weight"]
    return dist_sum

dist_user = total_user_distance(st.session_state.route)
st.write(f"Łączna droga użytkownika: {dist_user:.1f} km")

# Wybrane punkty
named_route = [f"{node}({node_names[node]})" for node in st.session_state.route]
st.write(f"Wybrane węzły (kolejność): {named_route}")

############################
# Gdy dojdziemy do 28, odkrywamy najkrótszą
############################
if 28 in st.session_state.route:
    st.session_state.show_shortest = True
    if nx.has_path(G, 12, 28):
        sp = nx.shortest_path(G, 12, 28, weight='weight')
        cost_sp = nx.shortest_path_length(G, 12, 28, weight='weight')
        st.write(f"Najkrótsza ścieżka (12->28): {sp}")
        st.write(f"Długość: {cost_sp:.1f} km")
    else:
        st.write("Brak ścieżki 12->28 w tym grafie.")

############################
# Sekcja 4: Teoria
############################
st.markdown('<h2 id="teoria">Teoria</h2>', unsafe_allow_html=True)
st.write("Tutaj opisujemy algorytm Dijkstry itp.")

# Przykład przycisku do wyświetlenia gifa
if st.button("Pokaż animację algorytmu Dijkstry"):
    st.image("dijkstra_steps.gif", caption="Przykładowy przebieg algorytmu Dijkstry.")
