import streamlit as st
from streamlit_folium import st_folium
import folium
import math
import base64
import time
from pyproj import Transformer
import networkx as nx
from folium import IFrame, Popup, Element
from folium.plugins import PolyLineTextPath

############################
# Zadanie: Znajdź najkrótszą trasę z węzła 12 do węzła 28
############################

st.write("Zadanie: Znajdź najkrótszą drogę od węzła 12 do węzła 28")
st.write("Twoim celem jest skonstruowanie trasy łączącej węzły, tak aby przejść z 12 do 28.")

# ---------------------------
# Dane – lista punktów (w metrach, EPSG:2180) – 30 punktów
# ---------------------------
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

############################
# Funkcja obliczająca odległość euklidesową w km (zaokrąglenie do 1 miejsca)
############################
def euclidean_distance_km(p1, p2):
    return round(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) / 1000, 1)

############################
# Budowa grafu w NetworkX – każdy węzeł łączy się z trzema najbliższymi
############################
G = nx.Graph()
for num, coord in punkty.items():
    G.add_node(num, pos=coord)
for num, coord in punkty.items():
    distances = []
    for other_num, other_coord in punkty.items():
        if other_num != num:
            d = euclidean_distance_km(coord, other_coord)
            distances.append((other_num, d))
    distances.sort(key=lambda x: x[1])
    nearest = distances[:3]
    for other_num, d in nearest:
        G.add_edge(num, other_num, weight=d)

############################
# Konwersja współrzędnych z EPSG:2180 do EPSG:4326 (lat, lon)
############################
transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
latlon_nodes = {}
for node, (x, y) in punkty.items():
    lon, lat = transformer.transform(x, y)
    latlon_nodes[node] = (lat, lon)

############################
# Funkcja obliczająca odległość (Haversine) w metrach
############################
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000
    from math import radians, sin, cos, sqrt, atan2
    dlat = radians(lat2 - lat1)
    dlon = radians(lat2 - lat1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

############################
# Wczytanie obrazka i kodowanie do base64
############################
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

image_base64 = get_image_base64("node_image.png")
image_html = f'<img src="data:image/png;base64,{image_base64}" width="100" height="200" style="object-fit:contain;">'

############################
# Inicjalizacja stanu sesji
############################
if "route" not in st.session_state:
    st.session_state.route = []
if "map_center" not in st.session_state:
    avg_lat = sum(lat for lat, lon in latlon_nodes.values()) / len(latlon_nodes)
    avg_lon = sum(lon for lat, lon in latlon_nodes.values()) / len(latlon_nodes)
    st.session_state.map_center = [avg_lat, avg_lon]
if "map_zoom" not in st.session_state:
    st.session_state.map_zoom = 12
if "start_time" not in st.session_state:
    st.session_state.start_time = None
# Dodajemy też zmienną do sterowania wyświetlaniem najkrótszej ścieżki
if "show_shortest" not in st.session_state:
    st.session_state.show_shortest = False

# Przycisk resetujący trasę
if st.button("Resetuj trasę"):
    st.session_state.route = []
    st.session_state.start_time = None
    st.session_state.show_shortest = False

############################
# Funkcja tworząca mapę Folium
############################
def create_map():
    # Tworzymy mapę w oparciu o zapamiętane centrum i zoom
    m = folium.Map(location=st.session_state.map_center, zoom_start=st.session_state.map_zoom)

    # Dodajemy krawędzie (graf) oraz etykiety – odległość na środku linii, pozioma
    for u, v, data in G.edges(data=True):
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        distance = data["weight"]
        line = folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color="gray",
            weight=2,
            tooltip=f"{distance} km"
        )
        line.add_to(m)
        mid_lat = (lat1 + lat2) / 2
        mid_lon = (lon1 + lon2) / 2
        distance_icon = folium.DivIcon(
            html=f"""
                <div style="
                    font-size: 16px; 
                    font-weight: bold; 
                    color: black;
                    padding: 2px 4px;
                    border-radius: 0px;
                    transform: rotate(0deg);
                    ">
                    {distance}
                </div>
            """
        )
        folium.Marker(location=[mid_lat, mid_lon], icon=distance_icon).add_to(m)

    # Dodajemy markery węzłów
    for node, (lat, lon) in latlon_nodes.items():
        popup_html = f"""
            <b>Node {node}</b><br>
            {image_html}
        """
        iframe = IFrame(html=popup_html, width=150, height=240)
        popup = Popup(iframe, max_width=150)
        marker_html = f"""
            <div style="text-align: center;">
              <div style="
                background-color: red;
                color: white;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                margin: auto;
                font-size: 12pt;
                font-weight: bold;
                line-height: 24px;">
                {node}
              </div>
            </div>
        """
        folium.Marker(
            location=[lat, lon],
            popup=popup,
            tooltip=f"Node {node}",
            icon=folium.DivIcon(html=marker_html)
        ).add_to(m)

    # Rysujemy trasę użytkownika (żółta)
    if st.session_state.route:
        route_coords = [latlon_nodes[node] for node in st.session_state.route]
        folium.PolyLine(
            locations=route_coords,
            color="yellow",
            weight=4
        ).add_to(m)

    # Jeżeli show_shortest == True, rysujemy najkrótszą trasę (12->28) na zielono
    if st.session_state.show_shortest:
        # Obliczamy najkrótszą trasę
        shortest_path_12_28 = nx.shortest_path(G, source=12, target=28, weight='weight')
        coords_sp = [latlon_nodes[node] for node in shortest_path_12_28]
        folium.PolyLine(
            locations=coords_sp,
            color="green",
            weight=5,
            tooltip="Najkrótsza ścieżka (12->28)"
        ).add_to(m)

    return m

############################
# Wyświetlamy mapę – zwracamy tylko "last_clicked"
############################
map_data = st_folium(create_map(), width=600, height=400, returned_objects=["last_clicked"])

############################
# Aktualizacja widoku mapy – tylko przy kliknięciu (centrum=klik, zoom=15)
############################
if map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lng = map_data["last_clicked"]["lng"]
    st.session_state.map_center = [clicked_lat, clicked_lng]
    st.session_state.map_zoom = 15

############################
# Rozpoczęcie licznika – przy pierwszym dodaniu węzła
############################
if st.session_state.route and st.session_state.start_time is None:
    st.session_state.start_time = time.time()

############################
# Wyświetlenie upływającego czasu
############################
if st.session_state.start_time is not None:
    elapsed = time.time() - st.session_state.start_time
    st.write(f"Elapsed time: {elapsed:.1f} seconds")

############################
# Obsługa kliknięcia – dodawanie węzła do trasy
############################
if map_data.get("last_clicked"):
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lng = map_data["last_clicked"]["lng"]
    threshold = 300  # 300 metrów
    snapped_node = None
    for node, (lat, lon) in latlon_nodes.items():
        dx = (lat - clicked_lat) * 111000
        dy = (lon - clicked_lng) * 111000
        d = math.sqrt(dx**2 + dy**2)
        if d < threshold:
            snapped_node = node
            break
    if snapped_node is not None:
        if st.session_state.route:
            last_node = st.session_state.route[-1]
            allowed_nodes = list(G.neighbors(last_node))
            if snapped_node in allowed_nodes:
                if snapped_node not in st.session_state.route:
                    st.session_state.route.append(snapped_node)
                    st.success(f"Dodano węzeł {snapped_node} do trasy")
            else:
                st.warning(f"Węzeł {snapped_node} nie jest powiązany z węzłem {last_node}")
        else:
            st.session_state.route.append(snapped_node)
            st.success(f"Dodano węzeł {snapped_node} do trasy")

############################
# Obliczanie łącznej drogi użytkownika
############################
def total_user_distance(route):
    dist = 0.0
    for i in range(len(route)-1):
        u = route[i]
        v = route[i+1]
        if G.has_edge(u, v):
            dist += G[u][v]["weight"]
    return dist

user_dist = total_user_distance(st.session_state.route)
st.write(f"Łączna droga użytkownika: {user_dist:.1f} km")

############################
# Wyświetlenie najkrótszej drogi z 12 do 28 (zielona linia), ale dopiero po dotarciu do 28
############################
if 28 in st.session_state.route:
    st.session_state.show_shortest = True
    # Obliczamy najkrótszą trasę
    if nx.has_path(G, 12, 28):
        shortest_path_12_28 = nx.shortest_path(G, 12, 28, weight='weight')
        st.write(f"Najkrótsza możliwa trasa (12 -> 28): {shortest_path_12_28}")
        shortest_length_12_28 = nx.shortest_path_length(G, 12, 28, weight='weight')
        st.write("\nGratulacje! Dotarłeś do węzła 28.")
        st.write(f"Najkrótsza możliwa trasa (12 -> 28) ma długość: {shortest_length_12_28:.1f} km")
    else:
        st.write("Brak ścieżki pomiędzy 12 a 28.")


st.write("Wybrana trasa użytkownika:", st.session_state.route)
