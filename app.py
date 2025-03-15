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

st.markdown("""
    <style>
    html { scroll-behavior: smooth; }
    </style>
    """, unsafe_allow_html=True)

with st.sidebar:
    st.title("DijkstraFoka")
    st.subheader("Menu:")
    st.markdown("""
- [Start](#start)
- [Samouczek](#samouczek)
- [Wyzwanie](#wyzwanie)
- [Teoria](#teoria)
""", unsafe_allow_html=True)

############################
# Sekcje
############################
st.title("Zadanie: Najkrótsza droga od węzła 12 do 28")

st.markdown('<h2 id="start">Start</h2>', unsafe_allow_html=True)
st.write("Witamy w aplikacji! Tutaj możesz zacząć swoją przygodę...")

st.markdown('<h2 id="samouczek">Samouczek</h2>', unsafe_allow_html=True)
st.write("""\
1. Kliknij w rejon markera (a dokładnie – w przezroczyste koło wokół niego).
2. Wybrany węzeł pokaże się pod mapą jako kandydat. 
3. Kliknij przycisk „Wybierz punkt”, by dodać go do trasy.
4. Po dojściu do węzła 28 pojawi się zielona linia najkrótszej trasy.
""")

st.markdown('<h2 id="wyzwanie">Wyzwanie</h2>', unsafe_allow_html=True)

############################
# Dane
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

def get_image_base64(path):
    with open(path,"rb") as f:
        return base64.b64encode(f.read()).decode()

images_base64 = {}
for n in punkty.keys():
    fname = f"img{n}.png"
    if os.path.exists(fname):
        images_base64[n] = get_image_base64(fname)
    else:
        images_base64[n] = get_image_base64("img_placeholder.png")

############################
# Budowa grafu (3 najbliższe)
############################
G = nx.Graph()
for n in punkty:
    G.add_node(n)

def euclid_km(p1, p2):
    return round(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) / 1000, 1)

for n, coord in punkty.items():
    dists = []
    for on, ocoord in punkty.items():
        if on!=n:
            d = euclid_km(coord, ocoord)
            dists.append((on,d))
    dists.sort(key=lambda x:x[1])
    near3 = dists[:3]
    for (nn, dd) in near3:
        G.add_edge(n, nn, weight=dd)

############################
# Konwersja do lat/lng
############################
from pyproj import Transformer
transformer = Transformer.from_crs("EPSG:2180","EPSG:4326", always_xy=True)
latlon_nodes={}
for n, (x,y) in punkty.items():
    lon, lat=transformer.transform(x, y)
    latlon_nodes[n]= (lat, lon)

############################
# Stan sesji: route, candidate
############################
if "route" not in st.session_state:
    st.session_state.route = []
if "candidate_node" not in st.session_state:
    st.session_state.candidate_node = None
if "show_shortest" not in st.session_state:
    st.session_state.show_shortest=False
if "map_center" not in st.session_state:
    av_lat = sum( lat for (lat,_) in latlon_nodes.values())/len(latlon_nodes)
    av_lon = sum( lon for (_,lon) in latlon_nodes.values())/len(latlon_nodes)
    st.session_state.map_center=[av_lat,av_lon]
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom=12
if "start_time" not in st.session_state:
    st.session_state.start_time=None

############################
# Funkcja tworząca mapę
############################
def create_map():
    m=folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)

    # Krawędzie
    for u,v,data in G.edges(data=True):
        la1, lo1 = latlon_nodes[u]
        la2, lo2 = latlon_nodes[v]
        dist=data["weight"]
        folium.PolyLine(
            locations=[[la1,lo1],[la2,lo2]],
            color="gray",
            weight=2,
            tooltip=f"{dist} km"
        ).add_to(m)

        mid_la=(la1+la2)/2
        mid_lo=(lo1+lo2)/2
        folium.Marker(
            location=[mid_la, mid_lo],
            icon=folium.DivIcon(html=f"<div style='font-size:16px;font-weight:bold;'>{dist}</div>")
        ).add_to(m)

    # Markery + Circle
    for node,(la,lo) in latlon_nodes.items():

        # Dodaj Circle "przezroczysty" (np. radius=100)
        folium.Circle(
            location=[la, lo],
            radius=100,    # 100m
            color=None,    # brak obramowania
            fill=True,
            fill_opacity=0  # całkowicie przezroczysty
        ).add_to(m)
        
        nm=node_names.get(node, f"Node{node}")
        b64=images_base64[node]
        pop_html=f"""
        <img src="data:image/png;base64,{b64}" width="180" height="200" style="object-fit:cover;"><br>
        {nm}
        """
        ifr=IFrame(pop_html, width=215, height=235)
        pop=Popup(ifr, max_width=215)

        marker_html=f"""
        <div style="text-align:center;">
          <div style="background-color:red;color:white;border-radius:50%;width:24px;height:24px;margin:auto;font-size:12pt;font-weight:bold;line-height:24px;">
          {node}
          </div>
        </div>
        """
        folium.Marker(
            location=[la, lo],
            popup=pop,
            tooltip=nm,
            icon=folium.DivIcon(html=marker_html)
        ).add_to(m)


    # Trasa user (żółta)
    if st.session_state.route:
        coords=[latlon_nodes[n] for n in st.session_state.route]
        folium.PolyLine(coords, color="yellow", weight=4).add_to(m)

    # Najkrótsza 12->28 (zielona)
    if st.session_state.show_shortest:
        sp=nx.shortest_path(G,12,28,weight='weight')
        coords_sp=[latlon_nodes[x] for x in sp]
        folium.PolyLine(coords_sp, color="green", weight=5).add_to(m)

    return m

############################
# Rysujemy mapę
############################
map_data = st_folium(create_map(), width=800, height=500, returned_objects=["last_clicked"])

if map_data.get("last_clicked"):
    # Przesuwamy map_center
    latc=map_data["last_clicked"]["lat"]
    lngc=map_data["last_clicked"]["lng"]
    st.session_state.map_center=[latc,lngc]
    st.session_state.map_zoom=13

    # Sprawdzamy, który węzeł jest najbliżej, w promieniu 100m
    # bo user klika w "through Circle"
    threshold=100
    candidate=None
    best_dist=9999999
    for node,(la,lo) in latlon_nodes.items():
        dx=(la-latc)*111000
        dy=(lo-lngc)*111000
        d=math.sqrt(dx*dx+dy*dy)
        if d< threshold and d<best_dist:
            best_dist=d
            candidate=node
    if candidate is not None:
        st.session_state.candidate_node=candidate

############################
# Pod mapą: jeśli jest węzeł-kandydat, pokaż przycisk
############################
cand=st.session_state.candidate_node
if cand is not None:
    st.info(f"Kandydat: {cand} ({node_names[cand]}) w odległości ok. do 100m")
    if st.button("Wybierz punkt"):
        # Dodajemy do route
        if st.session_state.route:
            lastn=st.session_state.route[-1]
            allowed= list(G.neighbors(lastn))
            if cand in allowed:
                if cand not in st.session_state.route:
                    st.session_state.route.append(cand)
                    st.success(f"Dodano węzeł {cand} ({node_names[cand]}) do trasy")
            else:
                st.warning(f"Węzeł {cand} nie jest połączony z {lastn}!")
        else:
            st.session_state.route.append(cand)
            st.success(f"Dodano węzeł {cand} ({node_names[cand]}) do trasy")

############################
# Start licznika czasu
############################
if st.session_state.route and st.session_state.start_time is None:
    st.session_state.start_time=time.time()

if st.session_state.start_time is not None:
    elapsed=time.time()-st.session_state.start_time
    st.write(f"Elapsed time: {elapsed:.1f} s")

############################
# Reset
############################
if st.button("Resetuj trasę"):
    st.session_state.route=[]
    st.session_state.start_time=None
    st.session_state.show_shortest=False
    st.session_state.candidate_node=None

############################
# Długość
############################
def total_dist(route):
    s=0.0
    for i in range(len(route)-1):
        a=route[i]
        b=route[i+1]
        if G.has_edge(a,b):
            s+=G[a][b]["weight"]
    return s

dist_user= total_dist(st.session_state.route)
st.write(f"Łączna droga użytkownika: {dist_user:.1f} km")

############################
# Wypis nazwy węzłów w trasie
############################
route_names=[node_names[n] for n in st.session_state.route]
st.write("Wybrane punkty (kolejność):", route_names)

############################
# Jeśli węzeł 28 w trasie => green path
############################
if 28 in st.session_state.route:
    st.session_state.show_shortest=True
    if nx.has_path(G,12,28):
        sp=nx.shortest_path(G,12,28,weight='weight')
        csp=nx.shortest_path_length(G,12,28,weight='weight')
        st.write("Najkrótsza trasa (12->28):",sp)
        st.write("Gratulacje, dotarłeś do 28!")
        st.write(f"Jej długość = {csp:.1f} km")
    else:
        st.write("Brak ścieżki 12->28!")

st.markdown('<h2 id="teoria">Teoria</h2>',unsafe_allow_html=True)
st.write("""Algorytm Dijkstry - ...""")
