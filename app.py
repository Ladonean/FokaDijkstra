import streamlit as st
from streamlit_folium import st_folium
import folium
import math
import base64
import time
import os
import io
from PIL import Image
import networkx as nx
from folium import DivIcon
from pyproj import Transformer
import random  # DO LOSOWANIA
import csv

############################
# Ustawienia strony
############################
st.set_page_config(
    page_title="FOKA Algorytm Dijsktry",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    """
    <style>
    html { scroll-behavior: smooth; }
    </style>
    """,
    unsafe_allow_html=True
)

with st.sidebar:
    st.title("DijkstraFoka")
    st.subheader("Menu:")
    st.markdown(
        """
        - [Start](#start)
        - [Samouczek](#samouczek)
        - [Wyzwanie](#wyzwanie)
        - [Teoria](#teoria)
        - [Ranking](#ranking)
        """,
        unsafe_allow_html=True
    )

st.title("Hej! Twoim zadaniem jest znaleźć najkrószą trasę.")

st.markdown('<h2 id="start">Start</h2>', unsafe_allow_html=True)
st.markdown(
    "<h3 style='text-align: center; font-size:24px;'>Wylądowałeś w Gdańsku w Porcie Lotniczym (12). Musisz znaleźć pomnik wielkiego wieszcza oraz bohaterskich żołnierzy. Na koniec musisz znaleźć się w najbardziej wysuniętym na wschód punkcie Gdańska.</h3>", 
    unsafe_allow_html=True
)
st.markdown('<h2 id="samouczek">Samouczek</h2>', unsafe_allow_html=True)
st.write("""\
1. Kliknij **bezpośrednio na marker** (czerwone kółko z numerem), aby go wybrać.  
2. Obok mapy (w prawej kolumnie) pojawi się panel z obrazkiem, nazwą i przyciskiem „Wybierz punkt”.  
3. Na początku dozwolony jest tylko punkt **12**. Po jego wybraniu w Gdańsku wystąpią losowe korki bądź przyspieszenia – mnożniki te zmieniają odległości dróg. Przykładowo, krawędź z mnożnikiem **1.4** staje się 1.4 razy dłuższa, a krawędź z mnożnikiem **0.6** – skrócona.  
   - Kolory modyfikatorów odpowiadają następującym wartościom:  
     - **1.2**: pomarańczowy  
     - **1.4**: czerwony  
     - **1.6**: brązowy
     - **0.8**: jasny niebieski
     - **0.6**: jasny zielony
     - **0.4**: różowy
4. Dodawaj kolejne punkty (muszą być sąsiadami poprzedniego); trasa rysowana jest na żółto. 
5. W Gdańsku funkcjonuje Szybka Kolej Miejska (SKM). Trasa między punktami 31, 7 i 32 ma mnożnik 0.5 zawsze :)
6. Gdy w trasie pojawi się punkt **28**, gra się kończy – wyświetlony zostanie finalny widok z Twoją trasą (żółta) i najkrótszą (zielona) oraz podsumowanie: czas, łączna droga, lista punktów i ocena punktowa.  
   
   **System oceny:**  
   Twoja ocena obliczana jest według wzoru:  
   &nbsp;&nbsp;&nbsp;&nbsp;**Ocena = 100 · (najkrótsza_trasa / Twoja_trasa) · (60 / czas)**  
   Przy założeniu czasu bazowego 60 s, gdy Twoja trasa jest najkrótsza, uzyskujesz 100 punktów. Im dłuższa trasa lub większy czas, tym niższa ocena.
""")

st.markdown('<h2 id="wyzwanie">Wyzwanie</h2>', unsafe_allow_html=True)

############################
# Dane węzłów, nazwy, obrazki
############################
punkty = {
    1: (475268, 723118), 2: (472798, 716990), 3: (478390, 727009),
    4: (476650, 725153), 5: (476622, 721571), 6: (477554, 720574),
    7: (474358.48, 724280.19),
    8: (472297, 726195), 9: (465609, 730292),
    10: (474121, 727887), 11: (468217, 726296), 12: (465439, 724391),
    13: (465959, 719280), 14: (469257, 720007), 15: (473811, 717807),
    16: (475696, 717669), 17: (477650, 722680), 18: (483004, 720271),
    19: (474542, 720350), 20: (477733, 718819), 21: (475730, 715454),
    22: (470501, 722655), 23: (469834, 727580), 24: (472429, 720010),
    25: (482830, 723376), 26: (475686, 727888), 27: (490854, 720757),
    28: (496518, 721917), 29: (485721, 721588), 30: (495889, 718798),
    31: (472229.03, 727344.24),
    32: (476836.13, 720475)
}

node_names = {
    1: "Politechnika Gdańska",
    2: "Parkrun Gdańsk Południe",
    3: "Pomnik Obrońców Wybrzeża",
    4: "Bursztynowy",
    5: "Góra Gradowa",
    6: "Posejdon",
    7: "SKM Gdańsk Wrzeszcz",
    8: "Uniwersytet Gdański",
    9: "Parkrun Gdańsk Osowa",
    10: "Parkrun Gdańsk Regana",
    11: "Trójmiejski Park Krajobrazowy",
    12: "Port Lotniczy",
    13: "Las Otomiński",
    14: "Jezioro Jasień",
    15: "Kozacza Góra",
    16: "Park Oruński",
    17: "Stocznia Gdańska",
    18: "Rafineria Orlen",
    19: "Pomnik Mickiewicza",
    20: "Dwór Olszynka",
    21: "Park Ferberów",
    22: "Sanktuarium Matemblewo",
    23: "Gdańskie ZOO",
    24: "Zbiornik Łabędzia",
    25: "Plaża Stogi",
    26: "Molo Brzeźno",
    27: "Plaża Sobieszewo",
    28: "Punkt Widokowy Sobieszewo Mewia Łacha",
    29: "Marina Przełom",
    30: "Prom Świbno",
    31: "SKM Gdańsk Oliwa",
    32: "SKM Gdańsk Śródmieście"
}

def get_image_base64(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode()

images_base64 = {}
for n in punkty.keys():
    fname = f"img_{n}.png"
    if os.path.exists(fname):
        images_base64[n] = get_image_base64(fname)
    else:
        images_base64[n] = get_image_base64("img_placeholder.png")

def euclidean_distance_km(p1, p2):
    return round(math.dist(p1, p2) / 1000, 1)

################################
# Budujemy graf
################################
G = nx.Graph()
for num, coord in punkty.items():
    G.add_node(num, pos=coord)
for num, coord in punkty.items():
    pairs = []
    for other, oc2 in punkty.items():
        if other != num:
            dval = euclidean_distance_km(coord, oc2)
            pairs.append((other, dval))
    pairs.sort(key=lambda x: x[1])
    for (o, distv) in pairs[:3]:
        G.add_edge(num, o, weight=distv)
# Krawędzie specjalne – nie modyfikujemy ich
special_edges = [(31, 7), (7, 32)]
for (u, v) in special_edges:
    orig = euclidean_distance_km(punkty[u], punkty[v])
    half_w = round(orig * 0.5, 1)
    if G.has_edge(u, v):
        G[u][v]["weight"] = half_w
    else:
        G.add_edge(u, v, weight=half_w)

# Po ponownym zbudowaniu grafu sprawdzamy, czy modyfikatory już są przypisane
# Jeśli tak, przeliczamy wagi krawędzi na podstawie oryginalnych wartości
if st.session_state.get("modifiers_assigned", False):
    for ed, (color, mult) in st.session_state["edge_mods"].items():
        u, v = ed
        original_weight = euclidean_distance_km(punkty[u], punkty[v])
        new_weight = round(original_weight * mult, 2)
        if G.has_edge(u, v):
            G[u][v]["weight"] = new_weight
        if G.has_edge(v, u):
            G[v][u]["weight"] = new_weight

transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
latlon_nodes = {}
for n, (x, y) in punkty.items():
    lon, lat = transformer.transform(x, y)
    latlon_nodes[n] = (lat, lon)

def total_user_distance(rt):
    s = 0
    for i in range(len(rt) - 1):
        if G.has_edge(rt[i], rt[i+1]):
            s += G[rt[i]][rt[i+1]]["weight"]
    return s

############################
# Stan aplikacji
############################
if "route" not in st.session_state:
    st.session_state["route"] = []
if "map_center" not in st.session_state:
    clat = sum(v[0] for v in latlon_nodes.values()) / len(latlon_nodes)
    clon = sum(v[1] for v in latlon_nodes.values()) / len(latlon_nodes)
    st.session_state["map_center"] = [clat, clon]
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

# Klucze do modyfikatorów
if "modifiers_assigned" not in st.session_state:
    st.session_state["modifiers_assigned"] = False
if "edge_mods" not in st.session_state:
    st.session_state["edge_mods"] = {}

#########################
# Mnożniki i kolory
#########################
EDGE_MULTIPLIERS = [0.4, 0.6, 0.8, 1.2, 1.4, 1.6]
COLOR_MAP = {
    1.2: "orange",
    1.4: "red",
    1.6: "brown",
    0.8: "lightblue",
    0.6: "palegreen",
    0.4: "pink"
}

#########################
# Losowanie 6 krawędzi (tylko raz) – specjalne krawędzie (31,7) i (7,32) pomijamy
#########################
def assign_modifiers_once():
    all_edges = []
    for (u, v, data) in G.edges(data=True):
        if (u, v) in special_edges or (v, u) in special_edges:
            continue
        edge_key = tuple(sorted((u, v)))
        all_edges.append(edge_key)
    all_edges = list(set(all_edges))
    required_count = 12
    if len(all_edges) < required_count:
        st.warning(f"Nie ma wystarczającej liczby krawędzi do wylosowania {required_count}! Pomijam modyfikatory.")
        return
    chosen_edges = random.sample(all_edges, required_count)
    # Każdy modyfikator z EDGE_MULTIPLIERS wystąpi dokładnie 2 razy
    modifiers = EDGE_MULTIPLIERS * 2  
    random.shuffle(modifiers)
    for i, ed in enumerate(chosen_edges):
        mult = modifiers[i]
        color = COLOR_MAP[mult]
        (a, b) = ed
        oldw = G[a][b]["weight"]
        neww = round(oldw * mult, 2)
        G[a][b]["weight"] = neww
        if G.has_edge(b, a):
            G[b][a]["weight"] = neww
        st.session_state["edge_mods"][ed] = (color, mult)
    st.session_state["modifiers_assigned"] = True
    st.write("Przypisane modyfikatory:", st.session_state["edge_mods"])
#########################
# Rysowanie krawędzi – dla wyświetlania chcemy pokazać przeliczoną wartość
#########################
def get_edge_color_and_weight(u, v):
    ed = tuple(sorted((u, v)))
    # Pobieramy wartość z grafu – to już przeliczona wartość
    if ed in st.session_state["edge_mods"]:
        (clr, mul) = st.session_state["edge_mods"][ed]
        return (clr, G[u][v]["weight"])
    return ("gray", G[u][v]["weight"])

###########################################
# Niebieska trasa 31->...->7->...->32
###########################################
# Ta trasa pozostaje bez modyfikatora
control_points_31_7_32 = [
    (472229.00, 727345.00),   # przybliżenie 31
    (472284.89, 726986.93),
    (472428.54, 726608.20),
    (472633.14, 726172.89),
    (473142.45, 725519.92),
    (473638.71, 724997.54),
    (474358.0, 724280.2),      # węzeł 7 (przybliżenie)
    (475579.86, 723542.90),
    (475905.82, 723356.24),
    (476131.49, 723186.29),
    (476588.40, 722484.22),
    (476822.42, 722202.83),
    (476922.72, 721731.99),
    (476939.43, 721489.61),
    (476867.00, 720974.20),
    (476836.13, 720474.95)    # węzeł 32 (dokładny)
]

def dist2180(a, b):
    return math.dist(a, b)

def to_latlon(pt):
    lon, lat = transformer.transform(pt[0], pt[1])
    return (lat, lon)

def find_node_index_approx(points_2180, node_xy, label, tolerance=20.0):
    best_idx = None
    best_dist = None
    for i, pp in enumerate(points_2180):
        d = dist2180(pp, node_xy)
        if best_dist is None or d < best_dist:
            best_dist = d
            best_idx = i
    if best_dist is not None and best_dist <= tolerance:
        return best_idx
    else:
        st.warning(f"Nie znaleziono węzła {label}, minimalna odleglosc {best_dist:.2f}m > {tolerance}m.")
        return None

# Ta funkcja rysuje niebieską trasę – wyświetlamy oryginalne odległości dla specjalnych krawędzi
def draw_single_line_31_7_32(fmap, pts_2180, node31_xy, node7_xy, node32_xy):
    latlon_list = [to_latlon(p) for p in pts_2180]
    folium.PolyLine(
        locations=latlon_list,
        color="blue",
        weight=4,
        dash_array="5,10"
    ).add_to(fmap)
    # Wyświetlamy oryginalne odległości dla krawędzi (31,7) oraz (7,32)
    orig_31_7 = euclidean_distance_km(punkty[31], punkty[7])
    orig_7_32 = euclidean_distance_km(punkty[7], punkty[32])
    idx_7 = find_node_index_approx(pts_2180, node7_xy, label="7", tolerance=20.0)
    if idx_7 is not None:
        mid_idx_31_7 = idx_7 // 2
        latm, lonm = to_latlon(pts_2180[mid_idx_31_7])
        folium.Marker(
            [latm, lonm],
            icon=DivIcon(
                html=f"""
                <div style="font-size:16px;font-weight:bold;color:blue;">
                    {orig_31_7}
                </div>
                """
            )
        ).add_to(fmap)
        mid_idx_7_32 = (idx_7 + len(pts_2180) - 1) // 2
        latm, lonm = to_latlon(pts_2180[mid_idx_7_32])
        folium.Marker(
            [latm, lonm],
            icon=DivIcon(
                html=f"""
                <div style="font-size:16px;font-weight:bold;color:blue;">
                    {orig_7_32}
                </div>
                """
            )
        ).add_to(fmap)

###########################################
# LOGIKA APLIKACJI
###########################################
if st.session_state["game_over"]:
    if st.session_state["final_time"] is None and st.session_state["start_time"] is not None:
        st.session_state["final_time"] = time.time() - st.session_state["start_time"]
    final_time = st.session_state["final_time"]
    user_dist = total_user_distance(st.session_state["route"])
    route_named = [f"{r} ({node_names[r]})" for r in st.session_state["route"]]

    # Obliczanie najkrótszej trasy z wymaganymi punktami (3 i 19)
    route1, weight1 = None, float('inf')
    if nx.has_path(G, 12, 3) and nx.has_path(G, 3, 19) and nx.has_path(G, 19, 28):
        route1a = nx.shortest_path(G, 12, 3, weight="weight")
        route1b = nx.shortest_path(G, 3, 19, weight="weight")
        route1c = nx.shortest_path(G, 19, 28, weight="weight")
        # Łączymy trasy (pomijając duplikaty punktów)
        route1 = route1a + route1b[1:] + route1c[1:]
        weight1 = sum(G[route1[i]][route1[i+1]]["weight"] for i in range(len(route1)-1))

    route2, weight2 = None, float('inf')
    if nx.has_path(G, 12, 19) and nx.has_path(G, 19, 3) and nx.has_path(G, 3, 28):
        route2a = nx.shortest_path(G, 12, 19, weight="weight")
        route2b = nx.shortest_path(G, 19, 3, weight="weight")
        route2c = nx.shortest_path(G, 3, 28, weight="weight")
        route2 = route2a + route2b[1:] + route2c[1:]
        weight2 = sum(G[route2[i]][route2[i+1]]["weight"] for i in range(len(route2)-1))

    # Wybieramy trasę o mniejszej wadze
    if weight1 <= weight2:
        required_route = route1
        required_weight = weight1
    else:
        required_route = route2
        required_weight = weight2

    leftC, rightC = st.columns(2)
    with leftC:
        st.subheader("Twoja trasa")
        st.write("Punkty:", route_named)
        if final_time is not None:
            st.write(f"Czas: {final_time:.1f} s")
        st.write(f"Łączna droga: {user_dist:.1f} km")
        if user_dist > 0 and final_time > 0:
            baseline_time = 60.0  # przyjęty czas bazowy
            score = 100 * (required_weight / user_dist) * (baseline_time / final_time)
            # Jeśli użytkownik nie odwiedził wymaganych punktów 3 i 19, odejmujemy 25 punktów
            if 3 not in st.session_state["route"] or 19 not in st.session_state["route"]:
                score -= 25
                st.write("Nie odwiedzono wszystkich wymaganych punktów (3 i 19). Kara -25 punktów.")
            st.write(f"Ocena: {score} punktów")
    with rightC:
        st.subheader("Najkrótsza trasa (12→28 z punktami 3 i 19)")
        if required_route:
            srt = [f"{x} ({node_names[x]})" for x in required_route]
            st.write("Punkty:", srt)
            st.write(f"Łączna droga: {required_weight:.1f} km")
        else:
            st.write("Brak ścieżki spełniającej wymaganie (przez 3 i 19).")

    st.markdown("#### Finalna mapa:")
    final_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])
    # Rysujemy krawędzie – dla zmodyfikowanych wyświetlamy przeliczoną wartość
    for u, v, data in G.edges(data=True):
        if (u, v) in special_edges or (v, u) in special_edges:
            continue
        color, disp_w = get_edge_color_and_weight(u, v)
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        tooltip_text = f"{disp_w}"
        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color=color,
            weight=2,
            tooltip=tooltip_text
        ).add_to(final_map)
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        folium.Marker(
            [mid_lat, mid_lon],
            icon=DivIcon(
                html=f"""
                <div style="font-size:16px;font-weight:bold;color:black;">
                    {tooltip_text}
                </div>
                """
            )
        ).add_to(final_map)
    for nd, (latn, lonn) in latlon_nodes.items():
        folium.Marker(
            location=[latn, lonn],
            tooltip=str(nd),
            icon=DivIcon(
                html=f"""
                <div style="text-align:center;">
                    <div style="background-color:red;color:white;border-radius:50%;
                                width:24px;height:24px;font-size:12pt;font-weight:bold;
                                line-height:24px;margin:auto;">
                        {nd}
                    </div>
                </div>
                """
            )
        ).add_to(final_map)
    if st.session_state["route"]:
        coords_user = [latlon_nodes[n] for n in st.session_state["route"]]
        folium.PolyLine(
            locations=coords_user,
            color="yellow",
            weight=5,
            tooltip="Twoja trasa"
        ).add_to(final_map)
    if required_route:
        coords_short = [latlon_nodes[n] for n in required_route]
        folium.PolyLine(
            locations=coords_short,
            color="green",
            weight=5,
            tooltip="Najkrótsza (12→28 z punktami 3 i 19)"
        ).add_to(final_map)
    # Rysujemy niebieską trasę 31->7->32 – wyświetlamy oryginalne odległości, bo te krawędzie nie mają modyfikatora
    node7_xy = punkty[7]
    node31_xy = punkty[31]
    node32_xy = punkty[32]
    draw_single_line_31_7_32(final_map, control_points_31_7_32, node31_xy, node7_xy, node32_xy)
    st_folium(final_map, width=800, height=600)
    if st.button("Resetuj trasę"):
        st.session_state["route"] = []
        st.session_state["start_time"] = None
        st.session_state["show_shortest"] = False
        st.session_state["game_over"] = False
        st.session_state["final_time"] = None
        st.session_state["modifiers_assigned"] = False
        st.session_state["edge_mods"] = {}
        st.rerun()
else:
    # Widok interaktywny
    col_map, col_info = st.columns([2, 1])
    with col_map:
        main_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])
        for u, v, data in G.edges(data=True):
            if (u, v) in special_edges or (v, u) in special_edges:
                continue
            color, disp_w = get_edge_color_and_weight(u, v)
            lat1, lon1 = latlon_nodes[u]
            lat2, lon2 = latlon_nodes[v]
            tooltip_text = f"{disp_w}"
            folium.PolyLine(
                [[lat1, lon1], [lat2, lon2]],
                color=color,
                weight=4,
                tooltip=tooltip_text
            ).add_to(main_map)
            mlat = (lat1 + lat2) / 2
            mlon = (lon1 + lon2) / 2
            folium.Marker(
                [mlat, mlon],
                icon=DivIcon(
                    html=f"""
                    <div style="font-size:16px;font-weight:bold;color:black;">
                        {tooltip_text}
                    </div>
                    """
                )
            ).add_to(main_map)
        for nd, (latn, lon_) in latlon_nodes.items():
            folium.Marker(
                location=[latn, lon_],
                tooltip=str(nd),
                icon=DivIcon(
                    html=f"""
                    <div style="text-align:center;">
                        <div style="background-color:red;color:white;border-radius:50%;
                                    width:24px;height:24px;font-size:12pt;font-weight:bold;
                                    line-height:24px;margin:auto;">
                            {nd}
                        </div>
                    </div>
                    """
                )
            ).add_to(main_map)
        if st.session_state["route"]:
            coords_user = [latlon_nodes[x] for x in st.session_state["route"]]
            folium.PolyLine(coords_user, color="yellow", weight=4, tooltip="Twoja trasa").add_to(main_map)
        node7_xy = punkty[7]
        node31_xy = punkty[31]
        node32_xy = punkty[32]
        draw_single_line_31_7_32(main_map, control_points_31_7_32, node31_xy, node7_xy, node32_xy)
        if st.session_state["show_shortest"]:
            if nx.has_path(G, 12, 28):
                spn = nx.shortest_path(G, 12, 28, weight="weight")
                coordsSP = [latlon_nodes[x] for x in spn]
                folium.PolyLine(coordsSP, color="green", weight=4, tooltip="Najkrótsza (12->28)").add_to(main_map)
        map_data = st_folium(main_map, width=800, height=600, returned_objects=["last_object_clicked_tooltip"])
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
                b64 = images_base64[clicked_id]
                dataim = base64.b64decode(b64)
                im = Image.open(io.BytesIO(dataim))
                im.thumbnail((600, 400))
                st.image(im)
                st.write(f"**{node_names[clicked_id]}** (ID: {clicked_id})")
                if not st.session_state["route"]:
                    allowed = (clicked_id == 12)
                    if not allowed:
                        st.info("Musisz zacząć od węzła 12.")
                else:
                    last_node = st.session_state["route"][-1]
                    allowed = (clicked_id in G.neighbors(last_node))
                if st.button("Wybierz punkt", key=f"btn_{clicked_id}", disabled=not allowed):
                    # Jeśli to pierwszy ruch i punkt 12, przypisz modyfikatory
                    if not st.session_state["route"] and clicked_id == 12 and not st.session_state["modifiers_assigned"]:
                        assign_modifiers_once()
                    # Zawsze dodajemy kliknięty węzeł do trasy, nawet jeśli już wcześniej był odwiedzony
                    st.session_state["route"].append(clicked_id)
                    st.success(f"Dodano węzeł {clicked_id} ({node_names[clicked_id]}) do trasy!")
                    st.session_state["map_center"] = latlon_nodes[clicked_id]
                    if st.session_state["start_time"] is None:
                        st.session_state["start_time"] = time.time()
                    if clicked_id == 28:
                        st.session_state["game_over"] = True
                    st.rerun()

            else:
                st.warning("Kliknięto punkt spoza słownika węzłów.")
        else:
            st.write("Kliknij na czerwony znacznik, aby zobaczyć szczegóły.")
        if st.session_state["route"]:
            rlab = [f"{r} ({node_names[r]})" for r in st.session_state["route"]]
            st.write("Wybrane punkty (kolejność):", rlab)
            sdist = total_user_distance(st.session_state["route"])
            st.write(f"Łączna droga: {sdist:.1f} km")
        if st.session_state["start_time"] is not None and not st.session_state["game_over"]:
            elap = time.time() - st.session_state["start_time"]
            st.write(f"Czas od rozpoczęcia: {elap:.1f} s")
    if st.button("Resetuj trasę"):
        st.session_state["route"] = []
        st.session_state["start_time"] = None
        st.session_state["show_shortest"] = False
        st.session_state["game_over"] = False
        st.session_state["final_time"] = None
        st.session_state["modifiers_assigned"] = False
        st.session_state["edge_mods"] = {}
        st.rerun()

st.markdown('<h2 id="teoria">Teoria</h2>', unsafe_allow_html=True)
st.write("""\
Algorytm Dijkstry pozwala na wyznaczenie najkrótszej trasy w grafach, których krawędzie mają przypisane nieujemne wagi (np. odległości, koszty przejazdu). Graf składa się z wierzchołków (punktów) połączonych krawędziami, które reprezentują możliwe przejścia pomiędzy punktami. Każda krawędź posiada przypisaną wagę określającą koszt jej przebycia, np. długość drogi lub czas przejazdu. Algorytm ten zaczyna od ustalenia źródła, czyli punktu początkowego, i stopniowo odwiedza kolejne wierzchołki, wybierając zawsze najbliższy jeszcze nieodwiedzony punkt. Dzięki temu znajduje optymalną drogę do wszystkich osiągalnych punktów grafu.

W praktyce działanie algorytmu opiera się na przypisywaniu wszystkim wierzchołkom wstępnych odległości od źródła, przy czym odległość do źródła wynosi 0, a do pozostałych punktów – nieskończoność. Następnie, w każdym kroku wybierany jest wierzchołek z najmniejszą obecnie znaną odległością, a potem sprawdzani są jego bezpośredni sąsiedzi. Jeśli dotychczasowa droga do sąsiada jest dłuższa niż nowa proponowana trasa przez aktualny wierzchołek, odległość do tego sąsiada zostaje zaktualizowana. Proces ten powtarza się do momentu odwiedzenia wszystkich dostępnych punktów w grafie. W wyniku działania algorytmu znamy minimalne odległości od źródła do każdego punktu.

Algorytm Dijkstry znajduje szerokie zastosowanie w codziennym życiu, zwłaszcza w systemach nawigacyjnych, gdzie wyznacza optymalną trasę przejazdu dla użytkowników GPS. W sieciach komputerowych algorytm stosowany jest do przesyłania danych najkrótszą lub najszybszą drogą, dzięki czemu pakiety danych skutecznie docierają do celu. Algorytm jest także używany w logistyce, np. przy planowaniu tras dostaw, zarządzaniu flotą pojazdów czy optymalizacji transportu towarów. W grach komputerowych wykorzystywany jest do znajdowania optymalnej ścieżki dla postaci sterowanych przez komputer, które omijają przeszkody i przemieszczają się efektywnie w świecie gry.

Grafy, na których działa algorytm Dijkstry, można reprezentować na dwa popularne sposoby: za pomocą macierzy sąsiedztwa lub listy sąsiedztwa. Macierz sąsiedztwa to tablica, w której każda komórka określa wagę krawędzi łączącej odpowiednie wierzchołki; jeśli brak połączenia, komórka przyjmuje wartość nieskończoności. Lista sąsiedztwa natomiast zawiera dla każdego punktu grafu wykaz sąsiadujących z nim wierzchołków wraz z wagami prowadzących do nich krawędzi. Najkrótszą ścieżkę między dwoma punktami grafu definiuje się jako trasę o minimalnej sumie wag krawędzi łączących te punkty. Dzięki temu algorytm Dijkstry skutecznie znajduje optymalne rozwiązania w problemach opartych na analizie grafów.
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

#######################
# Sekcja Ranking
#######################
st.markdown('<h2 id="ranking">Ranking</h2>', unsafe_allow_html=True)
ranking_file = "ranking.csv"
# Utwórz plik rankingowy, jeśli nie istnieje
if not os.path.exists(ranking_file):
    with open(ranking_file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Email", "Punkty", "Czas", "Trasa"])

# Jeśli gra się zakończyła i użytkownik nie dodał jeszcze wyniku, pozwól na podanie e-maila
if st.session_state.get("game_over", False) and not st.session_state.get("ranking_submitted", False):
    st.markdown(
    "<h3 style='text-align: center; font-size:12px;'>Przy podaniu maila użytkownik wyraża zgodę na przetwarzanie danych osobowych przez [KN HEVELIUS] w celu wzięcia udziału w konkursie, zgodnie z Rozporządzeniem Parlamentu Europejskiego i Rady (UE) 2016/679 z dnia 27 kwietnia 2016 r. (RODO). Ma świadomość, że podanie danych jest dobrowolne oraz że przysługuje mu prawo do dostępu do danych, ich poprawiania, usunięcia oraz wycofania zgody w dowolnym momencie.</h3>", 
    unsafe_allow_html=True
    )
    user_email = st.text_input("Podaj swój e-mail, aby dodać swój wynik do rankingu:")
    if user_email:
        if "@" in user_email and user_email.endswith((".com", ".pl", ".net", ".org", ".edu")):
            if st.button("Dodaj do rankingu"):
                with open(ranking_file, "a", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([user_email, round(score, 1), round(final_time, 1), " -> ".join(map(str, st.session_state["route"]))])
                st.session_state["ranking_submitted"] = True
                st.success("Wynik dodany do rankingu!")
        else:
            st.error("Podaj poprawny adres e-mail (musi zawierać '@' oraz kończyć się .com, .pl, .net, .org lub .edu).")

# Wyświetl ranking
if os.path.exists(ranking_file):
    with open(ranking_file, "r", newline="") as f:
        reader = csv.DictReader(f)
        ranking_data = list(reader)
    if ranking_data:
        ranking_data = sorted(ranking_data, key=lambda x: float(x["Punkty"]), reverse=True)
        st.table(ranking_data)
    else:
        st.write("Ranking jest pusty.")

# Opcja administratora do czyszczenia rankingu
admin_pass = st.text_input("Podaj hasło administratora, aby wyczyścić ranking:", type="password")
if admin_pass == st.secrets.password:
    if st.button("Wyczyść ranking"):
        with open(ranking_file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Email", "Punkty", "Czas", "Trasa"])
        st.success("Ranking został wyczyszczony!")

st.markdown("""
<style>
.honorable {
    text-align: center;
    font-size: 28px;
    font-weight: bold;
    padding: 10px 20px;
    border: 3px solid #ff4081;
    border-radius: 15px;
    background: linear-gradient(90deg, #ff8a80, #ff80ab, #b388ff);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-shadow: 2px 2px 4px rgba(0,0,0,0.4);
    margin: 20px;
}
</style>
<h3 class="honorable">HONORABLE MENTION: Liwix, Martyszia, Szybka Kreska, Fifi, Basix, Idalix, Stefan</h3>
""", unsafe_allow_html=True)
