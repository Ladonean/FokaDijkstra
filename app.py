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
import numpy as np

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
    27: "Plaża SObieszewo",
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
    return round(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) / 1000, 1)

# Tworzymy graf, w którym każdy węzeł łączy się z 3 najbliższymi
G = nx.Graph()
for num, coord in punkty.items():
    G.add_node(num, pos=coord)
for num, coord in punkty.items():
    dlist = []
    for other, other_coord in punkty.items():
        if other != num:
            distv = euclidean_distance_km(coord, other_coord)
            dlist.append((other, distv))
    dlist.sort(key=lambda x: x[1])
    for (onum, dval) in dlist[:3]:
        G.add_edge(num, onum, weight=dval)

# Dodajemy "specjalne" krawędzie 7->31 i 7->32 z wagą 0.5, ale z atrybutem `special=True`.
G.add_edge(7, 31, weight=0.5, special=True)
G.add_edge(7, 32, weight=0.5, special=True)

# Konwersja do EPSG:4326
transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
latlon_nodes = {}
for n, (x, y) in punkty.items():
    lon, lat = transformer.transform(x, y)
    latlon_nodes[n] = (lat, lon)

# Stan sesji
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
# Layout: kolumna mapa + kolumna info
############################
col_map, col_info = st.columns([2, 1])

with col_map:
    folium_map = folium.Map(
        location=st.session_state["map_center"],
        zoom_start=st.session_state["map_zoom"]
    )
    
    # Rysujemy "zwykłe" krawędzie – pomijając special=True
    for u, v, data in G.edges(data=True):
        if data.get("special", False):
            # Nie rysujemy "bezpośredniej" linii specjalnej
            continue
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        distv = data["weight"]
        folium.PolyLine(
            locations=[[lat1, lon1],[lat2, lon2]],
            color="gray",
            weight=2,
            tooltip=f"{distv:.1f} km"
        ).add_to(folium_map)
    
    # Rysujemy węzły (markery)
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
    
    # Rysujemy "specjalne" krawędzie jako niebieskie
    # (tylko jeśli istnieją w grafie)
    for (u,v) in [(7,31),(7,32)]:
        if G.has_edge(u,v):
            lat1, lon1 = latlon_nodes[u]
            lat2, lon2 = latlon_nodes[v]
            distv = G[u][v]["weight"]
            folium.PolyLine(
                locations=[[lat1, lon1],[lat2, lon2]],
                color="blue",
                weight=3,
                tooltip=f"{distv} km (przyspieszona)"
            ).add_to(folium_map)
    
    # Najkrótsza (zielona), jeśli show_shortest
    if st.session_state["show_shortest"]:
        sp_nodes = nx.shortest_path(G, 12, 28, weight="weight")
        coords_sp = [latlon_nodes[x] for x in sp_nodes]
        folium.PolyLine(
            locations=coords_sp,
            color="green",
            weight=5,
            tooltip="Najkrótsza (12->28)"
        ).add_to(folium_map)
    
    # Wyświetlamy mapę
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
            # Wyświetlamy obrazek
            b64 = images_base64[candidate_node]
            img_data = base64.b64decode(b64)
            img = Image.open(io.BytesIO(img_data))
            max_size = (400, 400)
            img.thumbnail(max_size)
            st.image(img, caption=f"{clicked_name} (ID: {candidate_node})")
            
            # Czy można dodać?
            last_node = st.session_state["route"][-1] if st.session_state["route"] else None
            allowed = True
            if last_node is not None:
                if candidate_node not in G.neighbors(last_node):
                    allowed = False
            
            if st.button("Wybierz punkt", key=f"btn_{candidate_node}", disabled=not allowed):
                if allowed:
                    if candidate_node not in st.session_state["route"]:
                        st.session_state["route"].append(candidate_node)
                        st.success(f"Dodano węzeł {candidate_node} ({clicked_name}) do trasy!")
                        # Ustaw nowe centrum i zoom
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
        st.write("Brak ścieżki między 12 a 28.")

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
