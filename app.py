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
2. Obok mapy (w prawej kolumnie) pojawi się panel z obrazkiem, nazwą i przyciskiem „Wybierz punkt”.  
3. Na początku dozwolony jest tylko punkt **12**.  
4. Dodawaj kolejne punkty (muszą być sąsiadami poprzedniego); trasa rysowana jest na żółto.  
5. Gdy w trasie pojawi się punkt **28**, gra się kończy – wyświetlony zostanie finalny widok z Twoją trasą (żółta) i najkrótszą (zielona), oraz podsumowanie (czas, łączna droga, lista punktów).
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
    """Zwraca odległość euklidesową w km."""
    return round(math.dist(p1, p2) / 1000, 1)

# Budowa grafu – każdy węzeł łączy się z 3 najbliższymi sąsiadami
import networkx as nx
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

# Krawędzie specjalne (0.5)
special_edges = [(31, 7), (7, 32)]
for u, v in special_edges:
    dist_orig = euclidean_distance_km(punkty[u], punkty[v])
    half_weight = round(dist_orig * 0.5, 1)
    if G.has_edge(u, v):
        G[u][v]["weight"] = min(G[u][v]["weight"], half_weight)
    else:
        G.add_edge(u, v, weight=half_weight)

# Konwersja EPSG:2180 -> EPSG:4326
from pyproj import Transformer
transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)

latlon_nodes = {}
for n, (x, y) in punkty.items():
    lon, lat = transformer.transform(x, y)
    latlon_nodes[n] = (lat, lon)

############################
# Funkcja do wyliczania długości trasy użytkownika
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
# Niebieska trasa "kontrolna" (z segmentami)
############################
control_points = [
    (476836.13, 720474.95), (476867.00, 720974.20), (476939.43, 721489.61),
    (476922.72, 721731.99), (476822.42, 722202.83), (476588.40, 722484.22),
    (476131.49, 723186.29), (475905.82, 723356.24), (475579.86, 723542.90),
    (474625.15, 724115.93), (474358.48, 724280.19), (473638.71, 724997.54),
    (473142.45, 725519.92), (472633.14, 726172.89), (472428.54, 726608.20),
    (472284.89, 726986.93), (472229.03, 727344.24)
]

def transform_2180_4326(xy):
    lon, lat = transformer.transform(xy[0], xy[1])
    return (lat, lon)

control_points_latlon = [transform_2180_4326(pt) for pt in control_points]

def distance_latlon(a, b):
    """Dystans w km między dwoma parami (lat, lon)."""
    return round(math.dist(a, b) / 1000, 2)

def draw_control_route(folium_map):
    """
    Rysuje standardową niebieską trasę przerywaną przez `control_points`,
    z etykietą segmentów w środku.
    """
    for i in range(len(control_points_latlon) - 1):
        lat1, lon1 = control_points_latlon[i]
        lat2, lon2 = control_points_latlon[i+1]
        distv = distance_latlon((lat1, lon1), (lat2, lon2))
        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color="blue",
            weight=4,
            dash_array="5,10",
            tooltip=f"{distv} km (kontrolny)"
        ).add_to(folium_map)
        # Etykieta na środku
        mid_lat = (lat1 + lat2)/2
        mid_lon = (lon1 + lon2)/2
        dist_icon = DivIcon(
            html=f"""
            <div style="font-size:14px;font-weight:bold;color:blue;">
                {distv}
            </div>
            """
        )
        folium.Marker([mid_lat, mid_lon], icon=dist_icon).add_to(folium_map)

############################
# Dwa osobne łuki: 31->7 i 7->32 w kolorze niebieskim
############################
def draw_arc_31_7(map_obj):
    """
    Rysuje łuk (31->7) w kolorze niebieskim, przerywanym,
    z jedną etykietą odległości na środku.
    """
    dist_31_7 = euclidean_distance_km(punkty[31], punkty[7])
    lat31, lon31 = latlon_nodes[31]
    lat7, lon7 = latlon_nodes[7]
    # Rysujemy odcinek
    folium.PolyLine(
        locations=[[lat31, lon31], [lat7, lon7]],
        color="blue",
        weight=4,
        dash_array="5,10",
        tooltip=f"{dist_31_7} km (31->7)"
    ).add_to(map_obj)
    # Etykieta
    mid_lat = (lat31 + lat7)/2
    mid_lon = (lon31 + lon7)/2
    dist_icon = DivIcon(
        html=f"""
        <div style="font-size:14px;font-weight:bold;color:blue;background-color:white;padding:2px;border-radius:3px;">
            {dist_31_7:.1f}
        </div>
        """
    )
    folium.Marker([mid_lat, mid_lon], icon=dist_icon).add_to(map_obj)

def draw_arc_7_32(map_obj):
    """
    Rysuje łuk (7->32) w kolorze niebieskim, przerywanym,
    z jedną etykietą odległości na środku.
    """
    dist_7_32 = euclidean_distance_km(punkty[7], punkty[32])
    lat7, lon7 = latlon_nodes[7]
    lat32, lon32 = latlon_nodes[32]
    # Rysujemy odcinek
    folium.PolyLine(
        locations=[[lat7, lon7], [lat32, lon32]],
        color="blue",
        weight=4,
        dash_array="5,10",
        tooltip=f"{dist_7_32} km (7->32)"
    ).add_to(map_obj)
    # Etykieta
    mid_lat = (lat7 + lat32)/2
    mid_lon = (lon7 + lon32)/2
    dist_icon = DivIcon(
        html=f"""
        <div style="font-size:14px;font-weight:bold;color:blue;background-color:white;padding:2px;border-radius:3px;">
            {dist_7_32:.1f}
        </div>
        """
    )
    folium.Marker([mid_lat, mid_lon], icon=dist_icon).add_to(map_obj)


###########################################################################
# FINALNY WIDOK (punkt 28 osiągnięty)
###########################################################################
if st.session_state["game_over"]:
    # Czas
    if st.session_state["final_time"] is None and st.session_state["start_time"] is not None:
        st.session_state["final_time"] = time.time() - st.session_state["start_time"]
    final_time = st.session_state["final_time"]
    final_distance = total_user_distance(st.session_state["route"])
    final_route = [f"{n} ({node_names[n]})" for n in st.session_state["route"]]

    # Najkrótsza
    shortest_nodes = []
    shortest_distance = 0.0
    if nx.has_path(G, 12, 28):
        shortest_nodes = nx.shortest_path(G, 12, 28, weight="weight")
        for i in range(len(shortest_nodes) - 1):
            u = shortest_nodes[i]
            v = shortest_nodes[i+1]
            shortest_distance += G[u][v]["weight"]

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Twoja trasa")
        st.write("Punkty:", final_route)
        if final_time is not None:
            st.write("Czas:", f"{final_time:.1f} s")
        st.write(f"Łączna droga: {final_distance:.1f} km")

    with col2:
        st.subheader("Najkrótsza (12→28)")
        if shortest_nodes:
            lab_nodes = [f"{n} ({node_names[n]})" for n in shortest_nodes]
            st.write("Punkty:", lab_nodes)
            st.write(f"Łączna droga: {shortest_distance:.1f} km")
        else:
            st.write("Brak ścieżki w grafie.")

    st.markdown("#### Finalna mapa:")
    final_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])

    # Rysujemy krawędzie (szare), pomijając special_edges
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
        # Etykieta na środku
        mid_lat = (lat1 + lat2)/2
        mid_lon = (lon1 + lon2)/2
        dist_icon = DivIcon(
            html=f"""
            <div style="font-size:14px;font-weight:bold;color:black;">
                {distv}
            </div>
            """
        )
        folium.Marker([mid_lat, mid_lon], icon=dist_icon).add_to(final_map)

    # Markery
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

    # Żółta trasa użytkownika
    if st.session_state["route"]:
        coords_user = [latlon_nodes[n] for n in st.session_state["route"]]
        folium.PolyLine(
            locations=coords_user,
            color="yellow",
            weight=4
        ).add_to(final_map)

    # Zielona najkrótsza
    if shortest_nodes:
        coords_shortest = [latlon_nodes[n] for n in shortest_nodes]
        folium.PolyLine(
            locations=coords_shortest,
            color="green",
            weight=5,
            tooltip="Najkrótsza (12->28)"
        ).add_to(final_map)

    # 1) Standardowa trasa kontrolna (po `control_points`)
    draw_control_route(final_map)
    # 2) Dwa osobne łuki: 31->7 i 7->32, z jedną etykietą na środku
    draw_arc_31_7(final_map)
    draw_arc_7_32(final_map)

    st_folium(final_map, width=800, height=600)

    if st.button("Resetuj trasę"):
        st.session_state["route"] = []
        st.session_state["start_time"] = None
        st.session_state["show_shortest"] = False
        st.session_state["game_over"] = False
        st.session_state["final_time"] = None
        st.experimental_rerun()

else:
    ###########################################################################
    # Widok interaktywny (gra jeszcze trwa)
    ###########################################################################
    col_map, col_info = st.columns([2, 1])
    with col_map:
        folium_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])

        # Rysujemy krawędzie szare, pomijając special_edges (31->7, 7->32)
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

            mid_lat = (lat1 + lat2)/2
            mid_lon = (lon1 + lon2)/2
            dist_icon = DivIcon(
                html=f"""
                <div style="font-size:14px;font-weight:bold;color:black;">
                    {distv}
                </div>
                """
            )
            folium.Marker([mid_lat, mid_lon], icon=dist_icon).add_to(folium_map)

        # Markery węzłów
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

        # Żółta trasa użytkownika
        if st.session_state["route"]:
            coords_user_route = [latlon_nodes[n] for n in st.session_state["route"]]
            folium.PolyLine(
                locations=coords_user_route,
                color="yellow",
                weight=4
            ).add_to(folium_map)

        # Standardowa niebieska trasa kontrolna
        draw_control_route(folium_map)
        # Dwa osobne łuki: 31->7 i 7->32
        draw_arc_31_7(folium_map)
        draw_arc_7_32(folium_map)

        # Opcjonalnie pokazujemy najkrótszą w trakcie, jeśli user ustawi show_shortest
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
            try:
                clicked_id = int(map_data["last_object_clicked_tooltip"])
            except ValueError:
                clicked_id = None

        if not st.session_state["route"]:
            st.write("Rozpocznij od kliknięcia na punkt **12**.")

        if clicked_id is not None:
            if clicked_id in node_names:
                # Wyświetlamy obrazek
                b64 = images_base64[clicked_id]
                img_data = base64.b64decode(b64)
                img = Image.open(io.BytesIO(img_data))
                max_size = (300, 300)
                img.thumbnail(max_size)
                st.image(img)

                st.write(f"**{node_names[clicked_id]}** (ID: {clicked_id})")

                # Czy można dodać
                if not st.session_state["route"]:
                    allowed = (clicked_id == 12)
                    if not allowed:
                        st.info("Musisz zacząć od węzła 12.")
                else:
                    last_node = st.session_state["route"][-1]
                    allowed = clicked_id in list(G.neighbors(last_node))

                if st.button("Wybierz punkt", key=f"btn_{clicked_id}", disabled=not allowed):
                    if clicked_id not in st.session_state["route"]:
                        st.session_state["route"].append(clicked_id)
                        st.success(f"Dodano węzeł {clicked_id} ({node_names[clicked_id]}) do trasy!")

                        st.session_state["map_center"] = latlon_nodes[clicked_id]
                        st.session_state["map_zoom"] = 13

                        if st.session_state["start_time"] is None:
                            st.session_state["start_time"] = time.time()

                        if clicked_id == 28:
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
            dist_val = total_user_distance(st.session_state["route"])
            st.write(f"Łączna droga: {dist_val:.1f} km")

        if st.session_state["start_time"] is not None and not st.session_state["game_over"]:
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
