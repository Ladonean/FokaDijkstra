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

for num, coord in punkty.items():
    # 3 najbliższe
    pairs = []
    for other, oc2 in punkty.items():
        if other != num:
            dval = euclidean_distance_km(coord, oc2)
            pairs.append((other,dval))
    pairs.sort(key=lambda x: x[1])
    for (o,distv) in pairs[:3]:
        G.add_edge(num, o, weight=distv)

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

###########################################
# LISTA 31->...->7->...->32 (EPSG:2180)
###########################################
control_points_31_7_32 = [
    (472229.00, 727345.00),   # w przybliżeniu 31 (472229.03,727344.24)
    (473000.00, 726800.00),
    (473800.00, 725500.00),
    (474358.0, 724280.2),     # węzeł 7 w przybliżeniu
    (475500.00, 722500.00),
    (476000.00, 721500.00),
    (476836.13, 720474.95)    # węzeł 32 (dokładny)
]

def dist2180(a, b):
    return math.dist(a,b)

def to_latlon(xy):
    lon, lat = transformer.transform(xy[0], xy[1])
    return (lat, lon)

def find_node_index_approx(points_2180, node_xy, label, tolerance=20.0):
    """
    Znajduje index w points_2180 najbliższy node_xy (EPSG:2180).
    Jeżeli jest bliżej niż 'tolerance' m, zwraca index.
    W przeciwnym razie None + ostrzeżenie.
    """
    best_idx = None
    best_dist = None
    for i,pt in enumerate(points_2180):
        d = dist2180(pt, node_xy)
        if (best_dist is None) or (d<best_dist):
            best_dist=d
            best_idx=i
    if best_dist is not None and best_dist<=tolerance:
        return best_idx
    else:
        st.warning(f"Nie znaleziono węzła {label} - min odległość {best_dist:.2f} m > {tolerance} m.")
        return None

def draw_single_line_31_7_32(fmap, points_2180, node_31, node_7, node_32):
    """
    Rysuje jedną polilinię przerywaną 31->...->7->...->32
    i wstawia dwie etykiety: 31->7 i 7->32.
    Korzysta z find_node_index_approx() aby dopasować węzeł 7.
    """
    latlon_list = [to_latlon(p) for p in points_2180]
    # Jedna przerywana
    folium.PolyLine(
        locations=latlon_list,
        color="blue",
        weight=4,
        dash_array="5,10",
        tooltip="31->7->32"
    ).add_to(fmap)

    # Szukamy index 7
    idx_7 = find_node_index_approx(points_2180, node_7, label="7", tolerance=20.0)
    if idx_7 is None:
        return

    # Liczymy dystans
    dist_31_7 = 0.0
    for i in range(idx_7):
        dist_31_7 += dist2180(points_2180[i], points_2180[i+1])
    dist_7_32 = 0.0
    for i in range(idx_7, len(points_2180)-1):
        dist_7_32 += dist2180(points_2180[i], points_2180[i+1])

    # Etykieta w "środku" sublisty 31->7
    mid_31_7 = idx_7//2
    lat_mid1, lon_mid1 = to_latlon(points_2180[mid_31_7])
    folium.Marker(
        [lat_mid1, lon_mid1],
        icon=DivIcon(
            html=f"""
            <div style="font-size:14px;font-weight:bold;color:blue;background-color:white;padding:3px;border-radius:5px;">
                {dist_31_7/1000:.1f} km (31->7)
            </div>
            """
        )
    ).add_to(fmap)

    # Etykieta w "środku" sublisty 7->32
    mid_7_32 = (idx_7 + len(points_2180)-1)//2
    lat_mid2, lon_mid2 = to_latlon(points_2180[mid_7_32])
    folium.Marker(
        [lat_mid2, lon_mid2],
        icon=DivIcon(
            html=f"""
            <div style="font-size:14px;font-weight:bold;color:blue;background-color:white;padding:3px;border-radius:5px;">
                {dist_7_32/1000:.1f} km (7->32)
            </div>
            """
        )
    ).add_to(fmap)

############################
# GRA - final i interaktywny
############################
if st.session_state["game_over"]:
    # final
    if st.session_state["final_time"] is None and st.session_state["start_time"] is not None:
        st.session_state["final_time"] = time.time() - st.session_state["start_time"]
    final_time = st.session_state["final_time"]
    user_dist = total_user_distance(st.session_state["route"])
    user_route_labeled = [f"{r} ({node_names[r]})" for r in st.session_state["route"]]

    shortest_nodes=[]
    shortest_dist=0
    if nx.has_path(G,12,28):
        sh=nx.shortest_path(G,12,28,weight="weight")
        for i in range(len(sh)-1):
            shortest_dist+= G[sh[i]][sh[i+1]]["weight"]
        shortest_nodes=sh

    leftC,rightC=st.columns(2)
    with leftC:
        st.subheader("Twoja trasa")
        st.write("Punkty:", user_route_labeled)
        if final_time is not None:
            st.write(f"Czas: {final_time:.1f} s")
        st.write(f"Łączna droga: {user_dist:.1f} km")
    with rightC:
        st.subheader("Najkrótsza (12->28)")
        if shortest_nodes:
            st.write("Punkty:", [f"{x} ({node_names[x]})" for x in shortest_nodes])
            st.write(f"Łączna droga: {shortest_dist:.1f} km")
        else:
            st.write("Brak ścieżki w grafie.")

    st.write("#### Finalna mapa:")
    final_map = folium.Map(
        location=st.session_state["map_center"],
        zoom_start=st.session_state["map_zoom"]
    )

    # Szare
    for u,v,data in G.edges(data=True):
        if (u,v) in special_edges or (v,u) in special_edges:
            continue
        lat1,lon1=latlon_nodes[u]
        lat2,lon2=latlon_nodes[v]
        distv=data["weight"]
        folium.PolyLine([[lat1,lon1],[lat2,lon2]], color="gray", weight=2, tooltip=f"{distv} km").add_to(final_map)
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
        ).add_to(final_map)

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

    # Żółta user
    if st.session_state["route"]:
        cu=[latlon_nodes[x] for x in st.session_state["route"]]
        folium.PolyLine(cu, color="yellow", weight=4).add_to(final_map)

    # Najkrótsza
    if shortest_nodes:
        csp=[latlon_nodes[n] for n in shortest_nodes]
        folium.PolyLine(csp, color="green", weight=5, tooltip="Najkrótsza(12->28)").add_to(final_map)

    # Rysujemy jedną line 31->...->7->...->32
    node7_xy = punkty[7]
    node31_xy= punkty[31]
    node32_xy= punkty[32]
    draw_single_line_31_7_32(final_map, control_points_31_7_32, node31_xy, node7_xy, node32_xy)

    st_folium(final_map, width=800, height=600)

    if st.button("Resetuj trasę"):
        st.session_state["route"]=[]
        st.session_state["start_time"]=None
        st.session_state["show_shortest"]=False
        st.session_state["game_over"]=False
        st.session_state["final_time"]=None
        st.experimental_rerun()

else:
    # Interaktywny
    col_map, col_info= st.columns([2,1])
    with col_map:
        main_map=folium.Map(location=st.session_state["map_center"], zoom_start=st.session_state["map_zoom"])
        for u,v,data in G.edges(data=True):
            if (u,v) in special_edges or (v,u) in special_edges:
                continue
            lat1,lon1=latlon_nodes[u]
            lat2,lon2=latlon_nodes[v]
            distv=data["weight"]
            folium.PolyLine([[lat1,lon1],[lat2,lon2]], color="gray", weight=2, tooltip=f"{distv} km").add_to(main_map)
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

        # Markery węzłów
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

        # Trasa user (yellow)
        if st.session_state["route"]:
            uu=[latlon_nodes[x] for x in st.session_state["route"]]
            folium.PolyLine(uu, color="yellow", weight=4).add_to(main_map)

        # Niebieska: 31->7->32
        node7_xy = punkty[7]
        node31_xy= punkty[31]
        node32_xy= punkty[32]
        draw_single_line_31_7_32(main_map, control_points_31_7_32, node31_xy, node7_xy, node32_xy)

        # Najkrótsza w trakcie?
        if st.session_state["show_shortest"]:
            if nx.has_path(G,12,28):
                path_nodes=nx.shortest_path(G,12,28,weight="weight")
                csp=[latlon_nodes[x] for x in path_nodes]
                folium.PolyLine(csp, color="green", weight=5, tooltip="Najkrótsza(12->28)").add_to(main_map)

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
                b64img=images_base64[clicked_id]
                dataimg=base64.b64decode(b64img)
                im=Image.open(io.BytesIO(dataimg))
                im.thumbnail((300,300))
                st.image(im)
                st.write(f"**{node_names[clicked_id]}** (ID: {clicked_id})")

                if not st.session_state["route"]:
                    allowed=(clicked_id==12)
                    if not allowed:
                        st.info("Musisz zacząć od węzła 12.")
                else:
                    last_node=st.session_state["route"][-1]
                    allowed=(clicked_id in G.neighbors(last_node))

                if st.button("Wybierz punkt", key=f"btn_{clicked_id}", disabled=not allowed):
                    if clicked_id not in st.session_state["route"]:
                        st.session_state["route"].append(clicked_id)
                        st.success(f"Dodano węzeł {clicked_id} ({node_names[clicked_id]}) do trasy!")
                        st.session_state["map_center"]=latlon_nodes[clicked_id]
                        st.session_state["map_zoom"]=13
                        if st.session_state["start_time"] is None:
                            st.session_state["start_time"]=time.time()
                        if clicked_id==28:
                            st.session_state["game_over"]=True
                        st.experimental_rerun()
                    else:
                        st.warning("Ten węzeł już jest w trasie.")
            else:
                st.warning("Kliknięto punkt spoza słownika węzłów.")
        else:
            st.write("Kliknij na czerwony znacznik, aby zobaczyć szczegóły.")

        if st.session_state["route"]:
            rlab=[f"{r} ({node_names[r]})" for r in st.session_state["route"]]
            st.write("Wybrane punkty (kolejność):", rlab)
            sdist=total_user_distance(st.session_state["route"])
            st.write(f"Łączna droga: {sdist:.1f} km")

        if st.session_state["start_time"] is not None and not st.session_state["game_over"]:
            elap=time.time()-st.session_state["start_time"]
            st.write(f"Czas od rozpoczęcia: {elap:.1f} s")

    if st.button("Resetuj trasę"):
        st.session_state["route"]=[]
        st.session_state["start_time"]=None
        st.session_state["show_shortest"]=False
        st.session_state["game_over"]=False
        st.session_state["final_time"]=None
        st.experimental_rerun()

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
