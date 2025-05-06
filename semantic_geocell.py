import geopandas as gpd
import pandas as pd
import numpy as np
from shapely.geometry import Polygon
from scipy.spatial import ConvexHull
from hilbertcurve.hilbertcurve import HilbertCurve
import urllib.request
import zipfile
import os


if not os.path.exists('ne_110m_admin_0_countries.zip'):
    url = 'https://naciscdn.org/naturalearth/110m/cultural/ne_110m_admin_0_countries.zip'
    urllib.request.urlretrieve(url, 'ne_110m_admin_0_countries.zip')
    with zipfile.ZipFile('ne_110m_admin_0_countries.zip', 'r') as zip_ref:
        zip_ref.extractall('ne_countries')


world = gpd.read_file('ne_countries/ne_110m_admin_0_countries.shp')
land = world[world['CONTINENT'] != 'Antarctica']


def extract_long_lat(dataframe):
    return dataframe[['id', 'latitude', 'longitude']]



df = pd.read_csv('test.csv') 
df = extract_long_lat(df)
gdf_points = gpd.GeoDataFrame(
    df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326"
)


n_per_polygon = 100 
k = len(gdf_points) // n_per_polygon

n_bits = 10
hilbert_curve = HilbertCurve(n_bits, 2)
gdf_points['hilbert'] = gdf_points.apply(
    lambda row: hilbert_curve.distance_from_point([
        int((row['longitude'] + 180) / 360 * (2**n_bits - 1)),
        int((row['latitude'] + 90) / 180 * (2**n_bits - 1))
    ]), axis=1
)
gdf_points_sorted = gdf_points.sort_values('hilbert').reset_index(drop=True)
gdf_points_sorted['cluster'] = np.arange(len(gdf_points_sorted)) // n_per_polygon


polygons = []
for cluster_id in gdf_points_sorted['cluster'].unique():
    cluster_points = gdf_points_sorted[gdf_points_sorted['cluster'] == cluster_id]
    if len(cluster_points) < 3: continue
    coords = np.array([[p.x, p.y] for p in cluster_points.geometry])
    try:
        hull = ConvexHull(coords)
        polygon = Polygon(coords[hull.vertices])
        polygons.append(polygon)
    except: pass

gdf_polygons = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326")
land = land.to_crs(gdf_polygons.crs)
gdf_polygons_clipped = gpd.overlay(gdf_polygons, land, how='intersection')
gdf_polygons_clipped['label'] = range(1, len(gdf_polygons_clipped) + 1)

gdf_labeled = gpd.sjoin(
    gdf_points[['geometry']], 
    gdf_polygons_clipped[['label', 'geometry']], 
    how='left', 
    predicate='within'
)

df = df.merge(gdf_labeled['label'].reset_index(), left_index=True, right_on='index')
df = df.rename(columns={'label': 'polygon_label'}).drop(columns='index')


df['polygon_label'] = df['polygon_label'].fillna(0).astype(int)

gdf_polygons_clipped.to_file('output_polygons.shp')
df.to_csv("labelled_points.csv")