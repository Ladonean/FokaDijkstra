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
3. Na początku dozwolony jest tylko punkt **12**.  
4. Dodawaj kolejne punkty (muszą być sąsiadami poprzedniego); trasa rysowana jest na żółto.  
5. Gdy w trasie pojawi się punkt **28**, gra się kończy – wyświetlony zostanie finalny widok z Twoją trasą (żółta) i najkrótszą (zielona), oraz podsumowanie (czas, łączna droga, lista punktów).
""")

st.markdown('<h2 id="wyzwanie">Wyzwanie</h2>', unsafe_allow_html=True)

############################
# Dane węzłów, nazwy
############################
# Uproszczona wersja – tylko kilka punktów, aby łatwiej debugować
punkty = {
    12: (465439, 724391),
    7: (474358.48, 724280.19),
    28: (496518, 721917),
    31: (472229.03, 727344.24),
    32: (476836.13, 720475)
}

node_names = {
    7: "Gdańsk Wrzeszcz",
    12: "Lotnisko",
    28: "Punkt Widokowy Sobieszewo Mewia Łacha",
    31: "Gdańsk Oliwa",
    32: "Gdańsk Śródmieście"
}

############################
# Budujemy graf
############################
G = nx.Graph()
for num, coord in punkty.items():
    G.add_node(num, pos=coord)

# Używamy oryginalnej funkcji obliczania odległości (km)
def euclidean_distance_km(p1, p2):
    return round(math.dist(p1, p2) / 1000, 2)

# Dla każdego punktu łączymy go z 3 najbliższymi (dla uproszczenia, u nas graf pełny)
for num, coord in punkty.items():
    for other, oc2 in punkty.items():
        if other != num:
            dval = euclidean_distance_km(coord, oc2)
            # Dodajemy krawędź tylko jeśli nie została dodana (graf nieskierowany)
            if not G.has_edge(num, other):
                G.add_edge(num, other, weight=dval)

# Krawędzie specjalne – (31,7) oraz (7,32) nie modyfikujemy
special_edges = [(31, 7), (7, 32)]
for (u, v) in special_edges:
    orig = euclidean_distance_km(punkty[u], punkty[v])
    half_w = round(orig * 0.5, 2)
    if G.has_edge(u, v):
        G[u][v]["weight"] = min(G[u][v]["weight"], half_w)
    else:
        G.add_edge(u, v, weight=half_w)

############################
# Konwersja współrzędnych
############################
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
    st.session_state["map_center"] = [54.0, 18.6]
if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 10
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "game_over" not in st.session_state:
    st.session_state["game_over"] = False
if "final_time" not in st.session_state:
    st.session_state["final_time"] = None
if "modifiers_assigned" not in st.session_state:
    st.session_state["modifiers_assigned"] = False
if "edge_mods" not in st.session_state:
    st.session_state["edge_mods"] = {}

#########################
# Mnożniki i kolory
#########################
EDGE_MULTIPLIERS = [0.4, 0.6, 0.8, 1.2, 1.4, 1.6]
COLOR_MAP = {
    0.4: "pink",
    0.6: "lightgreen",
    0.8: "lightblue",
    1.2: "orange",
    1.4: "red",
    1.6: "brown"
}

#########################
# Losowanie modyfikatorów (pomijamy specjalne krawędzie)
#########################
def assign_modifiers_once():
    all_edges = []
    for (u, v, data) in G.edges(data=True):
        if (u, v) in special_edges or (v, u) in special_edges:
            continue
        ed = tuple(sorted((u, v)))
        all_edges.append(ed)
    all_edges = list(set(all_edges))
    if len(all_edges) < 1:
        st.warning("Nie ma wystarczającej liczby krawędzi do losowania modyfikatorów.")
        return
    # Losujemy 1 lub więcej – tutaj wybieramy wszystkie, ale można zmienić na 6
    chosen = random.sample(all_edges, min(6, len(all_edges)))
    shuffled = EDGE_MULTIPLIERS[:]
    random.shuffle(shuffled)
    for i, ed in enumerate(chosen):
        mult = shuffled[i]
        color = COLOR_MAP[mult]
        a, b = ed
        old_w = G[a][b]["weight"]
        new_w = round(old_w * mult, 2)
        G[a][b]["weight"] = new_w
        if G.has_edge(b, a):
            G[b][a]["weight"] = new_w
        st.session_state["edge_mods"][ed] = (color, new_w)
        st.write(f"Krawędź {a}-{b}: {old_w} -> {new_w} (mnożnik: {mult})")
    st.session_state["modifiers_assigned"] = True
    st.write("Przypisane modyfikatory:", st.session_state["edge_mods"])
    st.write("Aktualne wagi w grafie:", [(u, v, G[u][v]["weight"]) for u, v in G.edges()])

#########################
# Pobieranie koloru i przeliczonej wagi (z grafu)
#########################
def get_edge_color_and_weight(u, v):
    ed = tuple(sorted((u, v)))
    if ed in st.session_state["edge_mods"]:
        (clr, new_w) = st.session_state["edge_mods"][ed]
        return (clr, G[u][v]["weight"])
    return ("gray", G[u][v]["weight"])

###########################################
# Niebieska trasa specjalna (31->...->7->...->32)
###########################################
# Ta trasa pozostaje bez modyfikatora
control_points_31_7_32 = [
    (472229.00, 727345.00),
    (472284.89, 726986.93),
    (472428.54, 726608.20),
    (472633.14, 726172.89),
    (473142.45, 725519.92),
    (473638.71, 724997.54),
    (474358.0, 724280.2),
    (475579.86, 723542.90),
    (475905.82, 723356.24),
    (476131.49, 723186.29),
    (476588.40, 722484.22),
    (476822.42, 722202.83),
    (476922.72, 721731.99),
    (476939.43, 721489.61),
    (476867.00, 720974.20),
    (476836.13, 720474.95)
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

# Dla specjalnej niebieskiej trasy wyświetlamy oryginalne odległości
def draw_single_line_31_7_32(fmap, pts_2180, node31_xy, node7_xy, node32_xy):
    latlon_list = [to_latlon(p) for p in pts_2180]
    folium.PolyLine(
        locations=latlon_list,
        color="blue",
        weight=4,
        dash_array="5,10"
    ).add_to(fmap)
    orig_31_7 = euclidean_distance_km(punkty[31], punkty[7])
    orig_7_32 = euclidean_distance_km(punkty[7], punkty[32])
    idx_7 = find_node_index_approx(pts_2180, node7_xy, label="7", tolerance=20.0)
    if idx_7 is not None:
        mid_idx_31_7 = idx_7 // 2
        latm, lonm = to_latlon(pts_2180[mid_idx_31_7])
        folium.Marker(
            [latm, lonm],
            icon=DivIcon(
                html=f"""<div style="font-size:14px;font-weight:bold;color:blue;">{orig_31_7}</div>"""
            )
        ).add_to(fmap)
        mid_idx_7_32 = (idx_7 + len(pts_2180) - 1) // 2
        latm, lonm = to_latlon(pts_2180[mid_idx_7_32])
        folium.Marker(
            [latm, lonm],
            icon=DivIcon(
                html=f"""<div style="font-size:14px;font-weight:bold;color:blue;">{orig_7_32}</div>"""
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
                html=f"""<div style="font-size:14px;font-weight:bold;color:{color};">{tooltip_text}</div>"""
            )
        ).add_to(final_map)
    for nd, (latn, lonn) in latlon_nodes.items():
        folium.Marker(
            location=[latn, lonn],
            tooltip=str(nd),
            icon=DivIcon(
                html=f"""
                <div style="text-align:center;">
                    <div style="background-color:red;color:white;border-radius:50%;width:24px;height:24px;
                                font-size:12pt;font-weight:bold;line-height:24px;margin:auto;">{nd}</div>
                </div>
                """
            )
        ).add_to(final_map)
    if st.session_state["route"]:
        coords_user = [latlon_nodes[n] for n in st.session_state["route"]]
        folium.PolyLine(
            locations=coords_user,
            color="yellow",
            weight=4,
            tooltip="Twoja trasa"
        ).add_to(final_map)
    if shortest_nodes:
        coords_short = [latlon_nodes[n] for n in shortest_nodes]
        folium.PolyLine(
            locations=coords_short,
            color="green",
            weight=5,
            tooltip="Najkrótsza (12->28)"
        ).add_to(final_map)
    # Rysujemy niebieską trasę specjalną (31->7->32)
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
                    html=f"""<div style="font-size:14px;font-weight:bold;color:{color};">{tooltip_text}</div>"""
                )
            ).add_to(main_map)
        for nd, (latn, lon_) in latlon_nodes.items():
            folium.Marker(
                location=[latn, lon_],
                tooltip=str(nd),
                icon=DivIcon(
                    html=f"""
                    <div style="text-align:center;">
                        <div style="background-color:red;color:white;border-radius:50%;width:24px;height:24px;
                                    font-size:12pt;font-weight:bold;line-height:24px;margin:auto;">{nd}</div>
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
                folium.PolyLine(coordsSP, color="green", weight=5, tooltip="Najkrótsza (12->28)").add_to(main_map)
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
                im.thumbnail((300,300))
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