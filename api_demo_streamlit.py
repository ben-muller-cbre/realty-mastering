import requests
import streamlit as st
import pandas as pd
from geopy.geocoders import Nominatim
import geopandas as gpd

# api_base_url = 'http://127.0.0.1:10100'
api_base_url = 'https://r28nn0w9v0.execute-api.us-east-1.amazonaws.com/default'

def reset_coords():
    st.session_state["address"] = "Blue Cross Blue Shield Tower, 300 E Randolph St, Chicago, IL 60601, USA"
    st.session_state["lat"] = "41.88504625046071"
    st.session_state["lon"] = "-87.6198346251189"

def geocode():
    address = st.session_state['address']
    locator = Nominatim(user_agent="realty_geocoder", timeout=10)
    location = locator.geocode(address)
    return location

def get_realty(lat,lon,closest=False):
    if closest:
        closeststr = '&closest=True'
    else:
        closeststr = ''
    r = requests.get(f"{api_base_url}/realty?lat={lat}&lon={lon}{closeststr}")
    return r.json()

if 'location' not in st.session_state:
    st.session_state['location'] = None

find_existing_realty, create_realty = st.tabs(['Get Realty','Create Realty'])

with find_existing_realty:
    with st.expander("Geocode Address", expanded=False):
        address = st.text_input('Address', value='Blue Cross Blue Shield Tower, 300 E Randolph St, Chicago, IL 60601, USA', key='address')
        col1, col2, _ = st.columns([2,2,5])
        with col1:
            if st.button('Geocode'):
                st.session_state["location"] = geocode()
        with col2:
            closest = st.checkbox('Closest')

        if st.session_state['location'] is not None:
            st.write(st.session_state["location"])
            st.write(st.session_state["location"][1])
            st.session_state["lat"] = str(st.session_state["location"][1][0])
            st.session_state["lon"] = str(st.session_state["location"][1][1])



    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        lat = st.text_input('Latitude', value="41.88504625046071", key='lat')
    with col2:
        lon = st.text_input('Longitude', value="-87.6198346251189", key='lon')
    with col3:
        st.button('Reset to example', on_click=reset_coords, use_container_width=True)





    data = get_realty(lat,lon,closest)

    st.write(data)
    if data != 'No realty exists at this location, to create one call POST /create_realty':
        popup = data['Realty_ID']
    else:
        popup = None

    with st.expander("Show map", expanded=True):

        # mapdata = pd.DataFrame({'lat':[float(lat)], 'lon':[float(lon)]})
        # st.map(mapdata, zoom=13)

        import folium

        from streamlit_folium import st_folium

        # center on Liberty Bell, add marker
        m = folium.Map(location=[float(lat), float(lon)], zoom_start=16)
        folium.Marker(
            [float(lat), float(lon)], popup=popup
        ).add_to(m)
        if data != 'No realty exists at this location, to create one call POST /create_realty':
            folium.Marker(
                [data['centroid'][1], data['centroid'][0]], popup=popup, icon=folium.Icon(color='red', icon='home')
            ).add_to(m)
        realty_gdf = gpd.read_file('draft realtyID table-api.geojson')
        geo_j = realty_gdf.to_json()
        folium.GeoJson(data=geo_j,
                       style_function=lambda x: {'fillColor': 'orange'}).add_to(m)

        # call to render Folium map in Streamlit
        st_data = st_folium(m, width=725)
        last_click = st_data['last_clicked']
        if last_click:
            st.write(last_click)
            # reset_coords()
            # st.session_state.lat = str(last_click['lat'])
            # st.session_state["lon"] = str(last_click['lng'])
        
with create_realty:
    address = st.text_input('Address', value='Blue Cross Blue Shield Tower, 300 E Randolph St, Chicago, IL 60601, USA', key='address_create')
    col1, col2, col3 = st.columns([2,2,1])
    with col1:
        lat = st.text_input('Latitude', value=st.session_state["lat"], key='lat_create')
    with col2:
        lon = st.text_input('Longitude', value=st.session_state["lon"], key='lon_create')
    def create_realty(lat,lon):
        payload = {'lat':lat,'lon':lon}
        r = requests.post(
            f'{api_base_url}/create_realty',
            json=payload
        )
        st.write(r.text)
        st.write(gpd.read_file('draft realtyID table-api.geojson'))
    if st.button('Create Realty'):
        create_realty(float(st.session_state["lat"]), float(st.session_state["lon"]))
    if st.button('Reset Realty Table'):
        realty_gdf = gpd.read_file('draft realtyID table.geojson')
        realty_gdf.to_file('draft realtyID table-api.geojson',driver='GeoJSON')
        st.write(realty_gdf)