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
    return round(math.dist(p1, p2)/1000, 1)

G = nx.Graph()
for num, coord in punkty.items():
    G.add_node(num, pos=coord)

# Budowa 3 najbliższych
for num, coord in punkty.items():
    pairs = []
    for other, oc2 in punkty.items():
        if other != num:
            dval = euclidean_distance_km(coord, oc2)
            pairs.append((other,dval))
    pairs.sort(key=lambda x: x[1])
    for (o,distv) in pairs[:3]:
        G.add_edge(num, o, weight=distv)

# Krawędzie specjalne
special_edges = [(31, 7), (7, 32)]
for (u,v) in special_edges:
    orig = euclidean_distance_km(punkty[u], punkty[v])
    half_w = round(orig*0.5,1)
    if G.has_edge(u,v):
        G[u][v]["weight"] = min(G[u][v]["weight"], half_w)
    else:
        G.add_edge(u,v, weight=half_w)

transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
latlon_nodes={}
for n,(x,y) in punkty.items():
    lon,lat = transformer.transform(x,y)
    latlon_nodes[n] = (lat, lon)

def total_user_distance(rt):
    s=0
    for i in range(len(rt)-1):
        if G.has_edge(rt[i], rt[i+1]):
            s+= G[rt[i]][rt[i+1]]["weight"]
    return s

# Inicjalizacja
if "route" not in st.session_state:
    st.session_state["route"]=[]
if "map_center" not in st.session_state:
    clat = sum(v[0] for v in latlon_nodes.values())/len(latlon_nodes)
    clon = sum(v[1] for v in latlon_nodes.values())/len(latlon_nodes)
    st.session_state["map_center"]=[clat,clon]
if "map_zoom" not in st.session_state:
    st.session_state["map_zoom"]=12
if "start_time" not in st.session_state:
    st.session_state["start_time"]=None
if "show_shortest" not in st.session_state:
    st.session_state["show_shortest"]=False
if "game_over" not in st.session_state:
    st.session_state["game_over"]=False
if "final_time" not in st.session_state:
    st.session_state["final_time"]=None

# Nowe klucze:
# czy już przypisano modyfikatory:
if "modifiers_assigned" not in st.session_state:
    st.session_state["modifiers_assigned"]=False
# Słownik z krawędziami i ich kolorem:
# edge_modifiers[(u,v)] = { "multiplier": ..., "color": ...}
if "edge_modifiers" not in st.session_state:
    st.session_state["edge_modifiers"]={}

############################
# Mnożniki i kolory
############################
EDGE_MULTIPLIERS = [0.4, 0.6, 0.8, 1.2, 1.4, 1.6]
COLOR_MAP = {
    0.4: "pink",
    0.6: "lightgreen",
    0.8: "lightblue",
    1.2: "orange",
    1.4: "red",
    1.6: "brown"
}

##################################
# Procedura losowania 6 krawędzi
##################################
def assign_random_modifiers():
    # Znajdź WSZYSTKIE krawędzie (u,v) w G,
    # pominąć special_edges, jeśli nie chcesz ich modyfikować.
    all_edges = []
    for (u,v) in G.edges():
        if (u,v) in special_edges or (v,u) in special_edges:
            # Jeżeli NIE chcesz, by (31->7) i (7->32) były modyfikowane,
            # to odkomentuj ten continue
            continue
            pass
        # Pamiętaj, że nasz graf to undirected,
        # więc (v,u) == (u,v).
        # Na potrzeby unikalności weź tylko te, gdzie u<v
        if u<v:
            all_edges.append((u,v))
        else:
            all_edges.append((v,u))

    # Usuwamy duplikaty:
    all_edges = list(set(all_edges))
    # Wybieramy 6 losowych spośród nich (załóżmy, że jest >=6)
    chosen_edges = random.sample(all_edges, 6)
    # Mieszamy kolejność mnożników
    random.shuffle(EDGE_MULTIPLIERS)

    # Przypisujemy je krawędziom
    for i, edge in enumerate(chosen_edges):
        multiplier = EDGE_MULTIPLIERS[i]
        color = COLOR_MAP[multiplier]
        # Zmieniamy wagę w G
        (a,b)=edge
        old_w = G[a][b]["weight"]
        new_w = round(old_w * multiplier, 2)
        G[a][b]["weight"] = new_w
        # Dla spójności w undirected:
        # (b,a) to to samo
        if G.has_edge(b,a):
            G[b][a]["weight"] = new_w

        # Zapisujemy w st.session_state
        st.session_state["edge_modifiers"][edge]={"multiplier":multiplier, "color":color}
    # Ustawiamy flagę, że już przypisano
    st.session_state["modifiers_assigned"] = True


##################################
# Funkcja do rysowania krawędzi
##################################
def draw_edge(u,v):
    """
    Zwraca (color, distv) dla krawędzi (u,v),
    biorąc pod uwagę st.session_state["edge_modifiers"].
    """
    # W undirected definicja klucza
    edge_key = (u,v) if u<v else (v,u)
    distv = G[u][v]["weight"]
    # domyślnie "gray"
    color = "gray"

    # Jeżeli jest w edge_modifiers, bierz color stamtąd
    if edge_key in st.session_state["edge_modifiers"]:
        color = st.session_state["edge_modifiers"][edge_key]["color"]

    return color, distv

###########################################
# Rysowanie i logika
###########################################
def draw_single_line_31_7_32(*args, **kwargs):
    """
    Zostawiamy Twoją obecną implementację – 
    w niej nie ma nic do zmiany w kontekście multiplikatorów.
    """
    pass


##################################################
# (1) Gdy gra skończona (punkt 28)
##################################################
if st.session_state["game_over"]:
    if st.session_state["final_time"] is None and st.session_state["start_time"] is not None:
        st.session_state["final_time"] = time.time() - st.session_state["start_time"]
    final_time = st.session_state["final_time"]
    user_dist = total_user_distance(st.session_state["route"])
    user_route_labeled = [f"{x} ({node_names[x]})" for x in st.session_state["route"]]

    # Najkrótsza
    shortest_nodes = []
    shortest_dist = 0.0
    if nx.has_path(G, 12, 28):
        shortest_nodes = nx.shortest_path(G, 12, 28, weight="weight")
        for i in range(len(shortest_nodes) - 1):
            shortest_dist += G[shortest_nodes[i]][shortest_nodes[i+1]]["weight"]

    colL, colR = st.columns(2)
    with colL:
        st.subheader("Twoja trasa")
        st.write("Punkty:", user_route_labeled)
        if final_time is not None:
            st.write(f"Czas: {final_time:.1f} s")
        st.write(f"Łączna droga: {user_dist:.1f} km")

    with colR:
        st.subheader("Najkrótsza (12→28)")
        if shortest_nodes:
            lab_nodes = [f"{n} ({node_names[n]})" for n in shortest_nodes]
            st.write("Punkty:", lab_nodes)
            st.write(f"Łączna droga: {shortest_dist:.1f} km")
        else:
            st.write("Brak ścieżki w grafie :(")

    st.markdown("#### Finalna mapa:")
    final_map = folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])

    # Rysujemy krawędzie (biorąc pod uwagę modyfikatory)
    for u,v,data in G.edges(data=True):
        if (u,v) in special_edges or (v,u) in special_edges:
            continue
        color, distv = draw_edge(u,v)
        lat1,lon1= latlon_nodes[u]
        lat2,lon2= latlon_nodes[v]
        folium.PolyLine(
            locations=[[lat1,lon1],[lat2,lon2]],
            color=color,
            weight=2,
            tooltip=f"{distv} km"
        ).add_to(final_map)

        mid_lat=(lat1+lat2)/2
        mid_lon=(lon1+lon2)/2
        folium.Marker(
            [mid_lat, mid_lon],
            icon=DivIcon(
                html=f"""
                <div style="font-size:14px;font-weight:bold;color:black;">
                    {distv}
                </div>
                """
            )
        ).add_to(final_map)

    # Markery
    for nd,(la,lo) in latlon_nodes.items():
        folium.Marker(
            location=[la,lo],
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

    # Trasa użytkownika (żółta)
    if st.session_state["route"]:
        coords_user = [latlon_nodes[n] for n in st.session_state["route"]]
        folium.PolyLine(
            locations=coords_user,
            color="yellow",
            weight=4,
            tooltip="Twoja trasa"
        ).add_to(final_map)

    # Najkrótsza (zielona)
    if shortest_nodes:
        coords_shortest = [latlon_nodes[n] for n in shortest_nodes]
        folium.PolyLine(
            locations=coords_shortest,
            color="green",
            weight=5,
            tooltip="Najkrótsza (12->28)"
        ).add_to(final_map)

    # Jeśli chcesz rysować 31->7->32 (niebieska), z dwiema etykietami
    # (pomijam implementację – to Twój draw_single_line_31_7_32)

    st_folium(final_map, width=800, height=600)

    if st.button("Resetuj trasę"):
        # Reset
        st.session_state["route"]=[]
        st.session_state["start_time"]=None
        st.session_state["show_shortest"]=False
        st.session_state["game_over"]=False
        st.session_state["final_time"]=None
        st.session_state["modifiers_assigned"]=False
        st.session_state["edge_modifiers"]={}
        st.rerun()

else:
    ##################################################
    # Widok interaktywny
    ##################################################
    col_map,col_info = st.columns([2,1])
    with col_map:
        main_map=folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])

        # Rysujemy krawędzie – z modyfikatorami
        for u,v,data in G.edges(data=True):
            if (u,v) in special_edges or (v,u) in special_edges:
                continue
            color, distv = draw_edge(u,v)
            lat1,lon1= latlon_nodes[u]
            lat2,lon2= latlon_nodes[v]
            folium.PolyLine(
                locations=[[lat1,lon1],[lat2,lon2]],
                color=color,
                weight=2,
                tooltip=f"{distv} km"
            ).add_to(main_map)

            mlat=(lat1+lat2)/2
            mlon=(lon1+lon2)/2
            folium.Marker(
                [mlat,mlon],
                icon=DivIcon(
                    html=f"""
                    <div style="font-size:14px;font-weight:bold;color:black;">
                        {distv}
                    </div>
                    """
                )
            ).add_to(main_map)

        # Markery
        for nd,(la,lo) in latlon_nodes.items():
            folium.Marker(
                location=[la,lo],
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

        # Żółta trasa user
        if st.session_state["route"]:
            coords_user = [latlon_nodes[x] for x in st.session_state["route"]]
            folium.PolyLine(coords_user, color="yellow", weight=4).add_to(main_map)

        # Ewentualnie rysujesz 31->7->32 (niebieska)...

        # Najkrótsza (12->28) w trakcie – jeśli user ustawi
        if st.session_state["show_shortest"]:
            if nx.has_path(G,12,28):
                sp=nx.shortest_path(G,12,28,weight="weight")
                csp=[latlon_nodes[n] for n in sp]
                folium.PolyLine(csp, color="green", weight=5, tooltip="Najkrótsza").add_to(main_map)

        map_data=st_folium(main_map, width=800, height=600, returned_objects=["last_object_clicked_tooltip"])

    with col_info:
        st.subheader("Szczegóły punktu:")

        clicked_id=None
        if map_data and map_data.get("last_object_clicked_tooltip"):
            try:
                clicked_id=int(map_data["last_object_clicked_tooltip"])
            except ValueError:
                clicked_id=None

        if not st.session_state["route"]:
            st.write("Rozpocznij od kliknięcia na punkt **12**.")

        if clicked_id is not None:
            if clicked_id in node_names:
                # Wyświetlamy obrazek
                b64=images_base64[clicked_id]
                data_img=base64.b64decode(b64)
                im=Image.open(io.BytesIO(data_img))
                im.thumbnail((300,300))
                st.image(im)
                st.write(f"**{node_names[clicked_id]}** (ID: {clicked_id})")

                # Sprawdzamy, czy dozwolony
                if not st.session_state["route"]:
                    allowed=(clicked_id==12)
                else:
                    last_node=st.session_state["route"][-1]
                    allowed=(clicked_id in G.neighbors(last_node))

                if st.button("Wybierz punkt", key=f"btn_{clicked_id}", disabled=not allowed):
                    # Gdy user wybrał PIERWSZY raz 12, i jeszcze nie mamy modów
                    if (not st.session_state["route"]) and (clicked_id==12) and (not st.session_state["modifiers_assigned"]):
                        # Przypisz losowe modyfikatory
                        assign_random_modifiers()

                    if clicked_id not in st.session_state["route"]:
                        st.session_state["route"].append(clicked_id)
                        st.success(f"Dodano węzeł {clicked_id} ({node_names[clicked_id]}) do trasy!")

                        st.session_state["map_center"]=latlon_nodes[clicked_id]
                        st.session_state["map_zoom"]=13
                        if st.session_state["start_time"] is None:
                            st.session_state["start_time"]=time.time()

                        if clicked_id==28:
                            st.session_state["game_over"]=True
                        st.rerun()
                    else:
                        st.warning("Ten węzeł już jest w trasie.")
            else:
                st.warning("Kliknięto punkt spoza słownika węzłów.")
        else:
            st.write("Kliknij na czerwony znacznik, aby zobaczyć szczegóły.")

        # Wyświetlamy trasę
        if st.session_state["route"]:
            named_list=[f"{x} ({node_names[x]})" for x in st.session_state["route"]]
            st.write("Wybrane punkty (kolejność):", named_list)
            distv=total_user_distance(st.session_state["route"])
            st.write(f"Łączna droga: {distv:.1f} km")

        if st.session_state["start_time"] is not None and not st.session_state["game_over"]:
            elapsed=time.time()-st.session_state["start_time"]
            st.write(f"Czas od rozpoczęcia: {elapsed:.1f} s")

    if st.button("Resetuj trasę"):
        # Reset
        st.session_state["route"]=[]
        st.session_state["start_time"]=None
        st.session_state["show_shortest"]=False
        st.session_state["game_over"]=False
        st.session_state["final_time"]=None
        st.session_state["modifiers_assigned"]=False
        st.session_state["edge_modifiers"]={}
        st.rerun()

############################################################
# Teoria
############################################################
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
