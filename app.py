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
import random
import pandas as pd

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
st.markdown(
    """
    <style>
    html { scroll-behavior: smooth; }
    </style>
    """,
    unsafe_allow_html=True
)

############################
# Menu w sidebar
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
# Tytuł
############################
st.title("Zadanie: Najkrótsza droga od węzła 12 do 28")

st.markdown('<h2 id="start">Start</h2>', unsafe_allow_html=True)
st.write("Witamy w aplikacji! Aby rozpocząć, wybierz punkt **12** jako start.")

st.markdown('<h2 id="samouczek">Samouczek</h2>', unsafe_allow_html=True)
st.write("""\
1. Kliknij **bezpośrednio na marker** (czerwone kółko z numerem), aby go wybrać.  
2. Obok mapy (w prawej kolumnie) pojawi się panel z obrazkiem, nazwą i przyciskiem „Wybierz punkt”.  
3. Na początku dozwolony jest tylko punkt **12**.  
4. Dodawaj kolejne punkty (muszą być sąsiadami poprzedniego); trasa rysowana jest na żółto.  
5. Gdy w trasie pojawi się punkt **28**, gra się kończy – wyświetlony zostanie finalny widok z Twoją trasą (żółta) i najkrótszą (zielona), oraz podsumowanie.
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
# Tworzymy (globalnie) obiekt G,
# ale musimy go "resetować" za każdym rerunem
################################
def build_graph():
    G = nx.Graph()
    # Dodajemy węzły
    for num, coord in punkty.items():
        G.add_node(num, pos=coord)
    # Każdy węzeł łączy się z 3 najbliższymi
    for num, coord in punkty.items():
        pairs = []
        for other, oc2 in punkty.items():
            if other != num:
                dval = euclidean_distance_km(coord, oc2)
                pairs.append((other, dval))
        pairs.sort(key=lambda x: x[1])
        for (o, distv) in pairs[:3]:
            G.add_edge(num, o, weight=distv)
    # Krawędzie specjalne
    special_edges = [(31, 7), (7, 32)]
    for (u, v) in special_edges:
        orig = euclidean_distance_km(punkty[u], punkty[v])
        half_w = round(orig * 0.5, 1)
        if G.has_edge(u, v):
            G[u][v]["weight"] = min(G[u][v]["weight"], half_w)
        else:
            G.add_edge(u, v, weight=half_w)
    return G

#########################
# Funkcja re-aplikująca zapisane modyfikatory
# (żeby nie zniknęły po rerunie)
#########################
def apply_modifiers(G):
    # Odczytujemy z session_state["edge_mods"] i ponownie ustawiamy w G
    for ed, (color, new_w, mult) in st.session_state["edge_mods"].items():
        a, b = ed
        if G.has_edge(a, b):
            G[a][b]["weight"] = new_w
        if G.has_edge(b, a):
            G[b][a]["weight"] = new_w

#########################
# Budujemy graf i stosujemy modyfikatory
#########################
G = build_graph()
if "edge_mods" not in st.session_state:
    st.session_state["edge_mods"] = {}
if "modifiers_assigned" not in st.session_state:
    st.session_state["modifiers_assigned"] = False
if "mod_table" not in st.session_state:
    st.session_state["mod_table"] = []

# Po zbudowaniu grafu, re-aplikujemy modyfikatory
apply_modifiers(G)

def total_user_distance(route):
    s = 0
    for i in range(len(route)-1):
        if G.has_edge(route[i], route[i+1]):
            s += G[route[i]][route[i+1]]["weight"]
    return s

#########################
# Stan aplikacji
#########################
if "route" not in st.session_state:
    st.session_state["route"] = []
if "map_center" not in st.session_state:
    # obliczamy średnią, aby ustawić "centrum"
    center_lat = sum(v[0] for v in latlon_nodes.values()) / len(latlon_nodes)
    center_lon = sum(v[1] for v in latlon_nodes.values()) / len(latlon_nodes)
    st.session_state["map_center"] = [center_lat, center_lon]
if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"] = 12
if "start_time" not in st.session_state:
    st.session_state["start_time"] = None
if "game_over" not in st.session_state:
    st.session_state["game_over"] = False
if "final_time" not in st.session_state:
    st.session_state["final_time"] = None

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
special_edges = [(31, 7), (7, 32)]

#########################
# Funkcja do przypisywania
# i zapisywania w session_state
#########################
def assign_modifiers_once():
    all_edges = []
    for (u, v) in G.edges():
        ed = tuple(sorted((u, v)))
        if ed in special_edges:
            continue
        all_edges.append(ed)
    all_edges = list(set(all_edges))
    if len(all_edges) < 6:
        st.warning("Nie ma wystarczającej liczby krawędzi do wylosowania 6! Pomijam modyfikatory.")
        return

    chosen_6 = random.sample(all_edges, 6)
    shuffled = EDGE_MULTIPLIERS[:]
    random.shuffle(shuffled)

    # czyścimy starą tablicę
    st.session_state["mod_table"] = []

    for i, ed in enumerate(chosen_6):
        mult = shuffled[i]
        color = COLOR_MAP[mult]
        a, b = ed
        old_w = G[a][b]["weight"]
        new_w = round(old_w * mult, 2)
        G[a][b]["weight"] = new_w
        if G.has_edge(b, a):
            G[b][a]["weight"] = new_w
        # Zapisujemy w edge_mods: (color, new_w, mult)
        st.session_state["edge_mods"][ed] = (color, new_w, mult)

        # Dodajemy do tablicy, którą potem wyświetlamy
        st.session_state["mod_table"].append({
            "Krawędź": f"{a} - {b}",
            "Nazwa punktów": f"{node_names[a]} ↔ {node_names[b]}",
            "Bazowa odległość": old_w,
            "Mnożnik": mult,
            "Zmodyfikowana odległość": new_w,
            "Kolor": color
        })

    st.session_state["modifiers_assigned"] = True

#########################
# Pobieranie koloru i wagi
#########################
def get_edge_color_and_weight(u, v):
    ed = tuple(sorted((u, v)))
    if ed in st.session_state["edge_mods"]:
        color, new_w, mult = st.session_state["edge_mods"][ed]
        return (color, G[u][v]["weight"])
    else:
        return ("gray", G[u][v]["weight"])

#########################
# Rysowanie trasy specjalnej (31->7->32)
# - bez modyfikatora
#########################
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

def draw_single_line_31_7_32(fmap):
    latlon_list = [to_latlon(p) for p in control_points_31_7_32]
    folium.PolyLine(
        locations=latlon_list,
        color="blue",
        weight=4,
        dash_array="5,10"
    ).add_to(fmap)

    # oryginalne odległości 31->7 i 7->32
    orig_31_7 = euclidean_distance_km(punkty[31], punkty[7])
    orig_7_32 = euclidean_distance_km(punkty[7], punkty[32])
    # (dla uproszczenia nie markerujemy wszystkich segmentów – tylko w 2 miejscach)
    # ...

#########################
# Widok finalny
#########################
if st.session_state["game_over"]:
    if st.session_state["final_time"] is None and st.session_state["start_time"] is not None:
        st.session_state["final_time"] = time.time() - st.session_state["start_time"]
    final_time = st.session_state["final_time"]
    user_dist = total_user_distance(st.session_state["route"])
    route_named = [f"{n} ({node_names[n]})" for n in st.session_state["route"]]

    # Najkrótsza
    shortest_nodes = []
    shortest_dist = 0.0
    if nx.has_path(G, 12, 28):
        sp = nx.shortest_path(G, 12, 28, weight="weight")
        for i in range(len(sp) - 1):
            shortest_dist += G[sp[i]][sp[i+1]]["weight"]
        shortest_nodes = sp

    colL, colR = st.columns(2)
    with colL:
        st.subheader("Twoja trasa")
        st.write("Punkty:", route_named)
        if final_time is not None:
            st.write(f"Czas: {final_time:.1f} s")
        st.write(f"Łączna droga: {user_dist:.1f} km")

    with colR:
        st.subheader("Najkrótsza (12->28)")
        if shortest_nodes:
            srt = [f"{x} ({node_names[x]})" for x in shortest_nodes]
            st.write("Punkty:", srt)
            st.write(f"Łączna droga: {shortest_dist:.1f} km")
        else:
            st.write("Brak ścieżki w grafie.")

    st.markdown("#### Finalna mapa:")
    final_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])
    # Rysujemy wszystkie krawędzie
    for u, v in G.edges():
        if tuple(sorted((u, v))) in special_edges:
            continue
        color, disp_w = get_edge_color_and_weight(u, v)
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color=color,
            weight=2,
            tooltip=f"{disp_w}"
        ).add_to(final_map)

    # Markery
    for nd, (latn, lonn) in latlon_nodes.items():
        folium.Marker(
            location=[latn, lonn],
            tooltip=str(nd),
            icon=DivIcon(
                html=f"""<div style="text-align:center;">
                           <div style="background-color:red;color:white;border-radius:50%;width:24px;height:24px;
                           font-size:12pt;font-weight:bold;line-height:24px;margin:auto;">{nd}</div>
                           </div>"""
            )
        ).add_to(final_map)

    # Trasa user
    if st.session_state["route"]:
        coords_user = [latlon_nodes[x] for x in st.session_state["route"]]
        folium.PolyLine(coords_user, color="yellow", weight=4).add_to(final_map)

    # Najkrótsza
    if shortest_nodes:
        coords_short = [latlon_nodes[x] for x in shortest_nodes]
        folium.PolyLine(coords_short, color="green", weight=5, tooltip="Najkrótsza(12->28)").add_to(final_map)

    # Niebieska (31->7->32)
    draw_single_line_31_7_32(final_map)

    st_folium(final_map, width=800, height=600)

    # Pod mapą: Tabela modyfikatorów, jeśli są
    if st.session_state["modifiers_assigned"] and "mod_table" in st.session_state:
        st.subheader("Trasy z modyfikatorami (podsumowanie):")
        st.table(st.session_state["mod_table"])

    if st.button("Resetuj trasę"):
        st.session_state["route"] = []
        st.session_state["start_time"] = None
        st.session_state["game_over"] = False
        st.session_state["final_time"] = None
        st.session_state["modifiers_assigned"] = False
        st.session_state["edge_mods"] = {}
        st.session_state["mod_table"] = []
        st.session_state["show_shortest"] = False
        st.rerun()

#########################
# Widok interaktywny
#########################
else:
    col_map, col_info = st.columns([2, 1])
    with col_map:
        main_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])
        for u, v in G.edges():
            if tuple(sorted((u, v))) in special_edges:
                continue
            color, disp_w = get_edge_color_and_weight(u, v)
            lat1, lon1 = latlon_nodes[u]
            lat2, lon2 = latlon_nodes[v]
            folium.PolyLine(
                locations=[[lat1, lon1], [lat2, lon2]],
                color=color,
                weight=2,
                tooltip=f"{disp_w}"
            ).add_to(main_map)

        # Markery
        for nd, (latn, lonn) in latlon_nodes.items():
            folium.Marker(
                location=[latn, lonn],
                tooltip=str(nd),
                icon=DivIcon(
                    html=f"""<div style="text-align:center;">
                                <div style="background-color:red;color:white;border-radius:50%;width:24px;height:24px;
                                font-size:12pt;font-weight:bold;line-height:24px;margin:auto;">{nd}</div>
                             </div>"""
                )
            ).add_to(main_map)

        # Żółta user route
        if st.session_state["route"]:
            coords_user = [latlon_nodes[x] for x in st.session_state["route"]]
            folium.PolyLine(coords_user, color="yellow", weight=4).add_to(main_map)

        # Niebieska (31->7->32)
        draw_single_line_31_7_32(main_map)

        # Najkrótsza w trakcie?
        if st.session_state["show_shortest"]:
            if nx.has_path(G, 12, 28):
                spn = nx.shortest_path(G, 12, 28, weight="weight")
                coordsSP = [latlon_nodes[x] for x in spn]
                folium.PolyLine(coordsSP, color="green", weight=5, tooltip="Najkrótsza(12->28)").add_to(main_map)

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
                # Wyświetlamy obrazek i nazwę
                b64 = images_base64[clicked_id]
                dataim = base64.b64decode(b64)
                im = Image.open(io.BytesIO(dataim))
                im.thumbnail((300,300))
                st.image(im)
                st.write(f"**{node_names[clicked_id]}** (ID: {clicked_id})")

                # Czy można dodać
                if not st.session_state["route"]:
                    allowed = (clicked_id == 12)
                    if not allowed:
                        st.info("Musisz zacząć od węzła 12.")
                else:
                    last_node = st.session_state["route"][-1]
                    allowed = (clicked_id in G.neighbors(last_node))

                if st.button("Wybierz punkt", key=f"btn_{clicked_id}", disabled=not allowed):
                    # Gdy pierwszy wybór to 12 i brak modyfikatorów, wylosuj
                    if not st.session_state["route"] and clicked_id == 12 and not st.session_state["modifiers_assigned"]:
                        assign_modifiers_once()
                    # Dodajemy do trasy
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
            named_route = [f"{n} ({node_names[n]})" for n in st.session_state["route"]]
            st.write("Wybrane punkty (kolejność):", named_route)
            sdist = total_user_distance(st.session_state["route"])
            st.write(f"Łączna droga: {sdist:.1f} km")

        if st.session_state["start_time"] is not None and not st.session_state["game_over"]:
            elapsed = time.time() - st.session_state["start_time"]
            st.write(f"Czas od rozpoczęcia: {elapsed:.1f} s")

    if st.button("Resetuj trasę"):
        st.session_state["route"] = []
        st.session_state["start_time"] = None
        st.session_state["game_over"] = False
        st.session_state["final_time"] = None
        st.session_state["modifiers_assigned"] = False
        st.session_state["edge_mods"] = {}
        st.session_state["mod_table"] = []
        st.session_state["show_shortest"] = False
        st.rerun()

############################
# Sekcja Teoria
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
