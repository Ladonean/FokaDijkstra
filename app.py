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

############################
# Ustawienia strony
############################
st.set_page_config(
    page_title="Mapa Zadanie: 12 → 28",
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
        """,
        unsafe_allow_html=True
    )

st.title("Zadanie: Najkrótsza droga od węzła 12 do 28")

st.markdown('<h2 id="start">Start</h2>', unsafe_allow_html=True)
st.write("Witamy w aplikacji! Aby rozpocząć, wybierz punkt **12** jako start.")

st.markdown('<h2 id="samouczek">Samouczek</h2>', unsafe_allow_html=True)
st.write("""\
1. Kliknij **bezpośrednio na marker** (czerwone kółko z numerem), aby go wybrać.  
2. Obok mapy (w prawej kolumnie) pojawi się panel z obrazkiem, nazwą i przyciskiem „Wybierz punkt”.  
3. Na początku dozwolony jest tylko punkt **12**. Po jego wybraniu losowo przypisywane są modyfikatory do wybranych krawędzi – mnożniki te zmieniają odległości dróg. Przykładowo, krawędź z mnożnikiem **1.4** staje się 1.4 razy dłuższa, a krawędź z mnożnikiem **0.6** jest skrócona.  
   - Kolory modyfikatorów odpowiadają następującym wartościom:  
     - **1.2**: pomarańczowy  
     - **1.4**: czerwony  
     - **1.6**: brązowy/bordowy  
     - **0.8**: niebieski  
     - **0.6**: zielony (odcień jaśniejszy niż zielony trasy najszybszej)  
     - **0.4**: różowy (średni odcień)  
4. Dodawaj kolejne punkty (muszą być sąsiadami poprzedniego); trasa rysowana jest na żółto.  
5. Gdy w trasie pojawi się punkt **28**, gra się kończy – wyświetlony zostanie finalny widok z Twoją trasą (żółta) i najkrótszą (zielona) oraz podsumowanie: czas, łączna droga, lista punktów i ocena punktowa.
""")

st.markdown('<h2 id="wyzwanie">Wyzwanie</h2>', unsafe_allow_html=True)

############################
# Dane węzłów, nazwy, obrazki
############################
punkty = {
    1: (475268, 723118), 2: (472798, 716990), 3: (478390, 727009),
    4: (476650, 725153), 5: (476622, 721571), 6: (477554, 720574),
    7: (474358.48, 724280.19),
    8: (472331, 725750), 9: (465609, 730292),
    10: (474121, 727887), 11: (468217, 726296), 12: (465439, 724391),
    13: (465959, 719280), 14: (469257, 720007), 15: (473811, 717807),
    16: (475696, 717669), 17: (477528, 723238), 18: (483004, 720271),
    19: (474542, 720350), 20: (477733, 718819), 21: (475730, 715454),
    22: (470501, 722655), 23: (469834, 727580), 24: (472429, 720010),
    25: (482830, 723376), 26: (475686, 727888), 27: (490854, 720757),
    28: (496518, 721917), 29: (485721, 721588), 30: (495889, 718798),
    31: (472229.03, 727344.24),
    32: (476836.13, 720475)
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
    half_w = round(orig * 0.6, 1)
    if G.has_edge(u, v):
        G[u][v]["weight"] = min(G[u][v]["weight"], half_w)
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
    0.8: "ligthblue",
    0.6: "palegreen",
    0.4: "pink"
}

#########################
# Losowanie 12 krawędzi (tylko raz) – specjalne krawędzie (31,7) i (7,32) pomijamy
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
        weight=5,
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
                <div style="font-size:16px;font-weight:bold;color:black;">
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
                <div style="font-size:16px;font-weight:bold;color:black;">
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

    shortest_nodes = []
    shortest_dist = 0.0
    if nx.has_path(G, 12, 28):
        sp = nx.shortest_path(G, 12, 28, weight="weight")
        for i in range(len(sp) - 1):
            shortest_dist += G[sp[i]][sp[i+1]]["weight"]
        shortest_nodes = sp

    leftC, rightC = st.columns(2)
    with leftC:
        st.subheader("Twoja trasa")
        st.write("Punkty:", route_named)
        if final_time is not None:
            st.write(f"Czas: {final_time:.1f} s")
        st.write(f"Łączna droga: {user_dist:.1f} km")
        if user_dist > 0 and final_time > 0:
            # Przykładowy system punktacji:
            # Jeśli trasa użytkownika jest równa najkrótszej, a czas równy bazowemu (60s) → 100 punktów.
            # Dłuższa trasa i/lub dłuższy czas skutkuje niższą oceną.
            baseline_time = 60.0  # przyjęty czas bazowy
            score = round(100 * (shortest_dist / user_dist) * (baseline_time / final_time))
            st.write(f"Ocena: {score} punktów")
    with rightC:
        st.subheader("Najkrótsza (12→28)")
        if shortest_nodes:
            srt = [f"{x} ({node_names[x]})" for x in shortest_nodes]
            st.write("Punkty:", srt)
            st.write(f"Łączna droga: {shortest_dist:.1f} km")
        else:
            st.write("Brak ścieżki w grafie.")

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
            weight=5,
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
    if shortest_nodes:
        coords_short = [latlon_nodes[n] for n in shortest_nodes]
        folium.PolyLine(
            locations=coords_short,
            color="en",
            weight=5,
            tooltip="Najkrótsza (12->28)"
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
                weight=3,
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
                folium.PolyLine(coordsSP, color="en", weight=5, tooltip="Najkrótsza (12->28)").add_to(main_map)
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
                im.thumbnail((300, 300))
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
                    if not st.session_state["route"] and clicked_id == 12 and not st.session_state["modifiers_assigned"]:
                        assign_modifiers_once()
                    if clicked_id not in st.session_state["route"]:
                        st.session_state["route"].append(clicked_id)
                        st.success(f"Dodano węzeł {clicked_id} ({node_names[clicked_id]}) do trasy!")
                        st.session_state["map_center"] = latlon_nodes[clicked_id]
                        st.session_state["map_zoom"] = 13
                        if st.session_state["start_time"] is None:
                            st.session_state["start_time"] = time.time()
                        if clicked_id == 28:
                            st.session_state["game_over"] = True
                        st.rerun()
                    else:
                        st.warning("Ten węzeł już jest w trasie.")
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
