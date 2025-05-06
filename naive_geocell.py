import pandas as pd
from s2sphere import LatLng, CellId, Cell
import folium

def extract_long_lat(dataframe):
    return dataframe[['id', 'latitude', 'longitude']]


def adaptive_geocells(df, max_points=100, max_level=16):
    df = df.copy()
    df['level'] = 8  
    df['level'] = df['level'].astype(int)
    df['cell'] = df.apply(lambda x: CellId.from_lat_lng(
        LatLng.from_degrees(x['latitude'], x['longitude'])).parent(int(x['level'])).to_token(), axis=1)
    
    # Iteratively split dense cells
    for _ in range(max_level - 8):
        # Count points per cell
        counts = df.groupby('cell').size().reset_index(name='count')
        dense_cells = counts[counts['count'] > max_points]['cell'].tolist()
        
        if not dense_cells:
            break
            
        mask = df['cell'].isin(dense_cells)
        df.loc[mask, 'level'] += 1
        df.loc[mask, 'cell'] = df[mask].apply(
            lambda x: CellId.from_lat_lng(LatLng.from_degrees(x['latitude'], x['longitude']))
            .parent(x['level']).to_token(), axis=1)
    return df

def get_cell_boundary(cell_token):
    """Get polygon coordinates for a cell token"""
    cell = Cell(CellId.from_token(cell_token))
    rect = cell.get_rect_bound()
    return [
        [rect.lo().lat().degrees, rect.lo().lng().degrees],
        [rect.hi().lat().degrees, rect.lo().lng().degrees],
        [rect.hi().lat().degrees, rect.hi().lng().degrees],
        [rect.lo().lat().degrees, rect.hi().lng().degrees]
    ]


def main():
    test_df = pd.read_csv('test.csv')
    longLatDf = extract_long_lat(test_df)
    processedDf = adaptive_geocells(longLatDf[['latitude', 'longitude']], max_points=500)
    # print(processedDf[:5])
    
    # Create map centered on data
    m = folium.Map(location=[0, 0], zoom_start=2)

    for cell_token, group in processedDf.groupby('cell'):
        count = len(group)
        boundary = get_cell_boundary(cell_token)
        
        folium.Polygon(
            locations=boundary,
            color='blue',
            weight=1,
            fill=True,
            fill_color='YlOrRd' if count > 50 else 'BuPu',
            fill_opacity=0.6,
            popup=f"Points: {count}\nLevel: {group['level'].iloc[0]}"
        ).add_to(m)

    m.save('adaptive_geocells.html')

if __name__ == "__main__":
    main()
