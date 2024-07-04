import folium
import matplotlib.colors as mcolors
import pandas as pd

# Lista singleton para almacenar los puntos. Se borran al reiniciar el servicio
points = []


# Función para agregar puntos iniciales a la lista singleton
def add_points():
    # Leer el archivo CSV
    df = pd.read_csv('csv/weatherWithCoordsImputed.csv')
    df = df[df['Location'] != 'MountGinini']
    df_avg_temp = df.groupby('Location').agg(
        Latitud=('Latitud', 'mean'),
        Longitud=('Longitud', 'mean'),
        AvgMaxTemp=('MaxTemp', 'mean')
    ).reset_index()
    df_avg_temp['AvgMaxTemp'] = df_avg_temp['AvgMaxTemp'].round(1)
    min_avg_temp = df_avg_temp['AvgMaxTemp'].min()
    max_avg_temp = df_avg_temp['AvgMaxTemp'].max()
    df_avg_temp['TempNorm'] = df_avg_temp['AvgMaxTemp'].apply(
        lambda x: (x - min_avg_temp) / (max_avg_temp - min_avg_temp))

    # Limpiar la lista singleton y agregar nuevos puntos
    points.clear()
    for _, row in df_avg_temp.iterrows():
        points.append({
            'Latitud': row['Latitud'],
            'Longitud': row['Longitud'],
            'Location': row['Location'],
            'AvgMaxTemp': row['AvgMaxTemp'],
            'TempNorm': row['TempNorm']
        })


# Función para agregar un nuevo punto a la lista singleton
def add_new_point(location, latitud, longitud, temp_max):
    if points:
        min_temp = min(points, key=lambda x: x['AvgMaxTemp'])['AvgMaxTemp']
        max_temp = max(points, key=lambda x: x['AvgMaxTemp'])['AvgMaxTemp']
    else:
        min_temp = temp_max
        max_temp = temp_max

    temp_norm = (temp_max - min_temp) / (
                max_temp - min_temp) if max_temp != min_temp else 0.5

    points.append({
        'Latitud': latitud,
        'Longitud': longitud,
        'Location': location,
        'AvgMaxTemp': temp_max,
        'TempNorm': temp_norm
    })


# Función para crear el mapa
def create_map():
    # Crear el mapa centrado en el centro de la primera ciudad de la lista
    if points:
        map_center = [points[0]['Latitud'], points[0]['Longitud']]
    else:
        map_center = [0, 0]  # Fallback center if points list is empty

    m = folium.Map(location=map_center, zoom_start=4, scrollWheelZoom=False)

    # Definir una función para obtener colores basados en la temperatura normalizada
    colormap = mcolors.LinearSegmentedColormap.from_list("temp_map",
                                                         ["blue", "green",
                                                          "yellow", "red"])

    # Agregar los marcadores coloreados al mapa desde la lista singleton
    for point in points:
        color = mcolors.to_hex(colormap(point['TempNorm']))
        folium.CircleMarker(
            location=[point['Latitud'], point['Longitud']],
            radius=10,
            popup=f"{point['Location']}: {point['AvgMaxTemp']}°C",
            color=color,
            fill=True,
            fill_color=color
        ).add_to(m)

    # Guardar el mapa en un archivo HTML
    map_html = 'templates/map.html'
    m.save(map_html)


# Inicializar los puntos y crear el mapa
add_points()
create_map()
