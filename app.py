import streamlit as st
from streamlit_folium import st_folium
import folium
import math
import base64
from pyproj import Transformer
import networkx as nx
from folium import IFrame, Popup, Element

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

# ---------------------------
# Funkcja licząca odległość euklidesową w km (zaokrąglenie do 1 miejsca po przecinku)
# ---------------------------
def euclidean_distance_km(p1, p2):
    return round(math.sqrt((p1[0]-p2[0])**2 + (p1[1]-p2[1])**2) / 1000, 1)

# ---------------------------
# Budowa grafu w NetworkX – łączymy każdy węzeł z trzema najbliższymi
# ---------------------------
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

# ---------------------------
# Konwersja współrzędnych z EPSG:2180 do EPSG:4326 (lat, lon)
# ---------------------------
transformer = Transformer.from_crs("EPSG:2180", "EPSG:4326", always_xy=True)
latlon_nodes = {}
for node, (x, y) in punkty.items():
    lon, lat = transformer.transform(x, y)
    latlon_nodes[node] = (lat, lon)  # Folium oczekuje [lat, lon]

# ---------------------------
# Funkcja obliczająca odległość (Haversine) w metrach
# ---------------------------
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371000  # Promień Ziemi w metrach
    from math import radians, sin, cos, sqrt, atan2
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

# ---------------------------
# Wczytanie obrazka i kodowanie do base64
# ---------------------------
def get_image_base64(image_path):
    with open(image_path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# Zakładamy, że mamy obrazek "node_image.png" w tym samym folderze
image_base64 = get_image_base64("node_image.png")
# Ustawiamy obrazek o maksymalnych wymiarach 100 x 200 pikseli
image_html = f'<img src="data:image/png;base64,{image_base64}" width="100" height="200" style="object-fit:contain;">'

# ---------------------------
# Inicjalizacja stanu sesji dla trasy
# ---------------------------
if "route" not in st.session_state:
    st.session_state.route = []
if st.button("Resetuj trasę"):
    st.session_state.route = []

# ---------------------------
# Funkcja tworząca mapę Folium
# ---------------------------
def create_map():
    avg_lat = sum(lat for lat, lon in latlon_nodes.values()) / len(latlon_nodes)
    avg_lon = sum(lon for lat, lon in latlon_nodes.values()) / len(latlon_nodes)
    m = folium.Map(location=[avg_lat, avg_lon], zoom_start=12)

    # Dodajemy krawędzie (graf)
    for u, v, data in G.edges(data=True):
        lat1, lon1 = latlon_nodes[u]
        lat2, lon2 = latlon_nodes[v]
        distance = data["weight"]
        folium.PolyLine(
            locations=[[lat1, lon1], [lat2, lon2]],
            color="gray",
            weight=2,
            tooltip=f"{distance} km"
        ).add_to(m)

    # Dodajemy markery – z popupem, który zawiera tekst i obrazek.
    for node, (lat, lon) in latlon_nodes.items():
        popup_html = f"""
            <b>Node {node}</b><br>
            {image_html}
        """
        iframe = IFrame(html=popup_html, width=150, height=240)
        popup = Popup(iframe, max_width=120)
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

    # Jeśli trasa jest zdefiniowana, rysujemy żółtą linię
    if st.session_state.route:
        route_coords = [latlon_nodes[node] for node in st.session_state.route if node in latlon_nodes]
        folium.PolyLine(
            locations=route_coords,
            color="yellow",
            weight=4
        ).add_to(m)

    return m

# Streamlit tytuł
st.title("Znajdź najkrótszą trasę")
# Wyświetlamy mapę przy użyciu streamlit-folium
#map_data = st_folium(create_map(), width=400, height=300, returned_objects=["last_clicked"])
map_data = st_folium(create_map(), width=1000, height=600, returned_objects=["last_clicked"])
# Dodajemy obsługę kliknięć – dodawanie węzła do trasy, gdy kliknięcie jest blisko punktu
if map_data["last_clicked"]:
    clicked_lat = map_data["last_clicked"]["lat"]
    clicked_lng = map_data["last_clicked"]["lng"]
    threshold = 300  # 50 metrów
    snapped_node = None
    for node, (lat, lon) in latlon_nodes.items():
        d = haversine_distance(clicked_lat, clicked_lng, lat, lon)
        if d < threshold:
            snapped_node = node
            break
    if snapped_node is not None:
        # Jeśli trasa nie jest pusta, sprawdzamy, czy nowy węzeł należy do 3 najbliższych od ostatniego węzła
        if st.session_state.route:
            last_node = st.session_state.route[-1]
            distances = []
            for other_num, other_coord in punkty.items():
                if other_num != last_node:
                    d_val = euclidean_distance_km(punkty[last_node], other_coord)
                    distances.append((other_num, d_val))
            distances.sort(key=lambda x: x[1])
            allowed_nodes = [t[0] for t in distances[:3]]
            if snapped_node in allowed_nodes:
                if snapped_node not in st.session_state.route:
                    st.session_state.route.append(snapped_node)
                    st.success(f"Dodano węzeł {snapped_node} do trasy")
            else:
                st.warning(
                    f"Węzeł {snapped_node} nie jest jednym z 3 najbliższych węzłów do węzła {last_node}. "
                    f"Dozwolone: {allowed_nodes}"
                )
        else:
            st.session_state.route.append(snapped_node)
            st.success(f"Dodano węzeł {snapped_node} do trasy")

st.write("Wybrana trasa:", st.session_state.route)
