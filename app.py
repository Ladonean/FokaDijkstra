import streamlit as st
from streamlit_folium import st_folium
import folium
import math
import base64
import time
from pyproj import Transformer
import networkx as nx
from folium import DivIcon
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
st.markdown(
    """
    <style>
    html { scroll-behavior: smooth; }
    </style>
    """,
    unsafe_allow_html=True
)

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
# Nagłówki sekcji
############################
st.title("Zadanie: Najkrótsza droga od węzła 12 do 28")

# Sekcja 1: Start
st.markdown('<h2 id="start">Start</h2>', unsafe_allow_html=True)
st.write("Witamy w aplikacji! Aby rozpocząć, wybierz punkt **12** jako start.")

# Sekcja 2: Samouczek
st.markdown('<h2 id="samouczek">Samouczek</h2>', unsafe_allow_html=True)
st.write("""\
1. Kliknij **bezpośrednio na marker** (czerwone kółko z numerem), aby go wybrać.  
2. Obok mapy (w prawej kolumnie) pojawi się szczegółowy panel z obrazkiem, nazwą i przyciskiem „Wybierz punkt”.  
3. Na początku dozwolony jest tylko punkt **12**.  
4. Dodawaj kolejne punkty (muszą być sąsiadami poprzedniego); trasa rysowana jest na żółto.  
5. Gdy w trasie pojawi się punkt **28**, gra się kończy – wyświetlony zostanie finalny widok z trasą użytkownika (żółta) i najkrótszą trasą (zielona), oraz podsumowanie (czas, łączna droga, lista punktów).
""")

# Sekcja 3: Wyzwanie
st.markdown('<h2 id="wyzwanie">Wyzwanie</h2>', unsafe_allow_html=True)

############################
# Dane węzłów, nazwy, obrazki
############################
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
    31: (472229, 727344), 32: (476836, 720475)
}

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
    27: "Plaża Sobieszewo",
    28: "Punkt Widokowy Sobieszewo Mewia Łacha",
    29: "Marina Przełom",
    30: "Prom Świbno",
    31: "Gdańsk Oliwa",
    32: "Gdańsk Śródmieście"
}

# (3) Wczytanie i zakodowanie obrazków (base64)
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
    return round(math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2) / 1000, 1)

# Budowa grafu – każdy węzeł łączy się z 3 najbliższymi sąsiadami
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

# Dodajemy specjalne krawędzie (przyspieszone) między 31 a 7 oraz 7 a 32
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
# Funkcja globalna: całkowita droga użytkownika
############################
def total_user_distance(route):
    dsum = 0.0
    for i in range(len(route) - 1):
        u = route[i]
        v = route[i + 1]
        if G.has_edge(u, v):
            dsum += G[u][v]["weight"]
    return dsum

############################
# Inicjalizacja stanu sesji
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
if "game_over" not in st.session_state:
    st.session_state["game_over"] = False
if "final_time" not in st.session_state:
    st.session_state["final_time"] = None

############################
# Dodatkowa trasa przyspieszona (niebieska, przerywana)
############################
control_points = [
    (476836.13, 720474.95), (476867.00, 720974.20), (476939.43, 721489.61),
    (476922.72, 721731.99), (476822.42, 722202.83), (476588.40, 722484.22),
    (476131.49, 723186.29), (475905.82, 723356.24), (475579.86, 723542.90),
    (474625.15, 724115.93), (474358.48, 724280.19), (473638.71, 724997.54),
    (473142.45, 725519.92), (472633.14, 726172.89), (472428.54, 726608.20),
    (472284.89, 726986.93), (472229.03, 727344.24)
]
control_points_latlon = []
for pt in control_points:
    lon, lat = transformer.transform(pt[0], pt[1])
    control_points_latlon.append((lat, lon))

def compute_control_distance(points):
    total = 0.0
    for i in range(len(points) - 1):
        dx = points[i + 1][0] - points[i][0]
        dy = points[i + 1][1] - points[i][1]
        d = math.sqrt(dx**2 + dy**2) / 1000
        total += d
    return total * 0.5

control_distance = compute_control_distance(control_points)
control_distance_text = f"{control_distance:.1f} km"


############################################
# Najpierw wyświetlamy finalny widok, jeśli gra skończona
############################################
if st.session_state["game_over"]:
    # Ustal czas zakończenia
    if st.session_state["final_time"] is None and st.session_state["start_time"] is not None:
        st.session_state["final_time"] = time.time() - st.session_state["start_time"]
    final_time = st.session_state["final_time"]
    final_distance = total_user_distance(st.session_state["route"])
    final_route = [f"{n} ({node_names[n]})" for n in st.session_state["route"]]

    st.markdown("### Finalna trasa")
    st.write("Twoja trasa:", final_route)
    if final_time is not None:
        st.write("Czas:", f"{final_time:.1f} s")
    st.write("Łączna droga:", f"{final_distance:.1f} km")

    final_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])
    # Rysowanie krawędzi (pomijamy specjalne)
    for u, v, data in G.edges(data=True):
        if (u, v) in special_edges or (v, u) in special_edges:
            continue
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        distv = data["weight"]
        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color="gray",
            weight=2,
            tooltip=f"{distv} km"
        ).add_to(final_map)

    # Markery z ID w tooltipie
    for node_id, (latn, lonn) in latlon_nodes.items():
        folium.Marker(
            location=[latn, lonn],
            tooltip=str(node_id),
            icon=DivIcon(
                html=f"""
                <div style="text-align:center;">
                    <div style="background-color:red;color:white;border-radius:50%;
                                width:24px;height:24px;font-size:12pt;font-weight:bold;
                                line-height:24px;margin:auto;">
                        {node_id}
                    </div>
                </div>
                """
            )
        ).add_to(final_map)

    # Trasa użytkownika (żółta)
    if st.session_state["route"]:
        coords_route = [latlon_nodes[n] for n in st.session_state["route"]]
        folium.PolyLine(locations=coords_route, color="yellow", weight=4).add_to(final_map)

    # Najkrótsza (zielona)
    if nx.has_path(G, 12, 28):
        shortest_nodes = nx.shortest_path(G, 12, 28, weight="weight")
        coords_sp = [latlon_nodes[x] for x in shortest_nodes]
        folium.PolyLine(
            locations=coords_sp,
            color="green",
            weight=5,
            tooltip="Najkrótsza (12->28)"
        ).add_to(final_map)

    st.markdown("#### Finalna mapa:")
    st_folium(final_map, width=800, height=600)

    # Guzik resetu (np. żeby można było powtórzyć)
    if st.button("Resetuj trasę"):
        st.session_state["route"] = []
        st.session_state["start_time"] = None
        st.session_state["show_shortest"] = False
        st.session_state["game_over"] = False
        st.session_state["final_time"] = None
        st.experimental_rerun()

    st.stop()  # nie wyświetlaj nic więcej

############################################
# Jeżeli gra jeszcze trwa, to wyświetlamy interaktywną mapę
############################################
col_map, col_info = st.columns([2, 1])
with col_map:
    folium_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])

    # Krawędzie (pomijamy specjalne)
    for u, v, data in G.edges(data=True):
        if (u, v) in special_edges or (v, u) in special_edges:
            continue
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        distv = data["weight"]
        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color="gray",
            weight=2,
            tooltip=f"{distv} km"
        ).add_to(folium_map)

    # Markery z ID (liczbą) w tooltipie
    for node_id, (latn, lonn) in latlon_nodes.items():
        folium.Marker(
            location=[latn, lonn],
            tooltip=str(node_id),
            icon=DivIcon(
                html=f"""
                <div style="text-align:center;">
                    <div style="background-color:red;color:white;border-radius:50%;
                                width:24px;height:24px;font-size:12pt;font-weight:bold;
                                line-height:24px;margin:auto;">
                        {node_id}
                    </div>
                </div>
                """
            )
        ).add_to(folium_map)

    # Trasa użytkownika (żółta)
    if st.session_state["route"]:
        coords_route = [latlon_nodes[n] for n in st.session_state["route"]]
        folium.PolyLine(locations=coords_route, color="yellow", weight=4).add_to(folium_map)

    # Trasa kontrolna (niebieska, przerywana)
    folium.PolyLine(
        locations=control_points_latlon,
        color="blue",
        weight=4,
        dash_array="5,10",
        tooltip=f"Przyspieszona trasa: {control_distance_text}"
    ).add_to(folium_map)

    # Jeśli chcemy podejrzeć najkrótszą trasę (np. dopingowo)
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

    clicked_id = None
    if map_data and map_data.get("last_object_clicked_tooltip"):
        # Tooltip to teraz tekst, np. "12"
        clicked_id_str = map_data["last_object_clicked_tooltip"]
        try:
            clicked_id = int(clicked_id_str)
        except ValueError:
            clicked_id = None

    if not st.session_state["route"]:
        st.write("Rozpocznij od kliknięcia na punkt **12**.")

    if clicked_id is not None:
        # Mamy ID węzła
        candidate_node = clicked_id
        if candidate_node in node_names:
            # Wyświetlamy obrazek
            b64 = images_base64[candidate_node]
            img_data = base64.b64decode(b64)
            img = Image.open(io.BytesIO(img_data))
            max_size = (300, 300)
            img.thumbnail(max_size)
            st.image(img)

            st.write(f"**{node_names[candidate_node]}** (ID: {candidate_node})")

            # Sprawdzamy, czy punkt można dodać:
            if not st.session_state["route"]:
                # Start tylko węzeł 12
                allowed = (candidate_node == 12)
                if not allowed:
                    st.info("Musisz zacząć od węzła 12.")
            else:
                last_node = st.session_state["route"][-1]
                allowed = candidate_node in list(G.neighbors(last_node))

            if st.button("Wybierz punkt", key=f"btn_{candidate_node}", disabled=not allowed):
                if candidate_node not in st.session_state["route"]:
                    st.session_state["route"].append(candidate_node)
                    st.success(f"Dodano węzeł {candidate_node} ({node_names[candidate_node]}) do trasy!")

                    st.session_state["map_center"] = latlon_nodes[candidate_node]
                    st.session_state["map_zoom"] = 13

                    if st.session_state["start_time"] is None:
                        st.session_state["start_time"] = time.time()

                    # Sprawdzamy zakończenie
                    if candidate_node == 28:
                        st.session_state["game_over"] = True
                    st.experimental_rerun()
                else:
                    st.warning("Ten węzeł już jest w trasie.")
        else:
            st.write("Kliknąłeś punkt spoza słownika węzłów (błąd).")
    else:
        st.write("Kliknij na czerwony znacznik, aby zobaczyć szczegóły.")

    if st.session_state["route"]:
        named_route = [f"{n} ({node_names[n]})" for n in st.session_state["route"]]
        st.write("Wybrane punkty (kolejność):", named_route)
        st.write(f"Łączna droga: {total_user_distance(st.session_state['route']):.1f} km")
    else:
        st.write("Brak wybranych punktów.")

    # Czas od rozpoczęcia
    if st.session_state["start_time"] is not None:
        elapsed = time.time() - st.session_state["start_time"]
        st.write(f"Czas od rozpoczęcia: {elapsed:.1f} s")

if st.button("Resetuj trasę"):
    st.session_state["route"] = []
    st.session_state["start_time"] = None
    st.session_state["show_shortest"] = False
    st.session_state["game_over"] = False
    st.session_state["final_time"] = None
    st.experimental_rerun()

############################################
# Sekcja 4: Teoria (zawsze wyświetlana)
############################################
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
