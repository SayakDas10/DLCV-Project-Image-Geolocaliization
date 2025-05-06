import pandas as pd
import numpy as np
import geopandas as gpd

import matplotlib.pyplot as plt

def main():
    df = pd.read_csv("labelled_points.csv")
    print(df.shape)
    print(len(set(df['polygon_label'])))
    gdf = gpd.read_file("output_polygons.shp")
    gdf.plot()
    plt.show()
    
if __name__ == "__main__":
    main()