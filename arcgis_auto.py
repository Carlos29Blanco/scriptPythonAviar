# import modules
import arcgis
from arcgis.gis import GIS
from IPython.display import clear_output,display
import ipywidgets as widgets
from arcgis import features
import csv
from arcgis.geoanalytics import manage_data
from arcgis.features import FeatureLayer
import urllib.request
import io
import requests
import pandas as pd
import os
from os import path
from io import StringIO
from arcgis import geometry #use geometry module to project Long,Lat to X and Y
from copy import deepcopy
from datetime import datetime, timedelta, date
import numpy as np
from dateutil.relativedelta import relativedelta, MO

username='CAHFS_UMN'
password='CAHFSVPMCVMUMN2022'

gis = GIS("https://umn.maps.arcgis.com/home/index.html", username, password)

#Descarga de datos portal de la FAO de los ultimos 4 meses
#https://europe-west1-fao-empres-re.cloudfunctions.net/getEventsInfluenzaAvian?start_date=2021-07-22&end_date=2021-10-22&serotype=all&diagnosis_status=confirmed&animal_type=all
# url = 'https://us-central1-fao-empres-re.cloudfunctions.net/getEventsASF'

today = date.today()
today_str = str(today)
past_months = str(today + relativedelta(months=-1))
# today_str = '2015-01-01'
# past_months = '2013-01-01'

# today = date.today()
# today_str = '2003-01-01'
# past_months = '2002-01-01'

start_url = 'https://europe-west1-fao-empres-re.cloudfunctions.net/getEventsInfluenzaAvian?start_date='
start_date = past_months
m_url = '&end_date='
end_date = today_str
end_url = '&serotype=all&diagnosis_status=confirmed&animal_type=all'

url = start_url+start_date+m_url+end_date+end_url

datos= urllib.request.urlopen(url)
datos=pd.read_csv(StringIO(bytearray(datos.read()).decode("utf-8")),encoding=("ISO-8859-1"))

# Añadir "NULL" a los datos vacios
datos = datos.fillna('NULL')

# #Filtro para quedarnos con la primera palabra en el campo de species
datos['species'] = datos['species'].apply(lambda x: x.split(',')[0])


#redondear lat y lon para solucionar problema a la hora de subir el csv a Portal
datos['lat'] = datos['lat'].apply(lambda x: np.round(x, decimals=2))
datos['lon'] = datos['lon'].apply(lambda x: np.round(x, decimals=2))

datosCO = pd.DataFrame(data=datos)

#Frame to CSV y lectura
datos.to_csv('aviar_actual.csv',index=False, header=True, )
# df = pd.read_csv('hASF2021.csv', sep=";")
df = pd.read_csv('aviar_actual.csv', sep='\r')

rutaCsv='aviar_actual.csv'
inputRuta=path.abspath(rutaCsv)

item_properties = {
    'title': 'aviar_actual',
    'tags': 'cvs',
    'overwrite': 'True'
    }


csv_item = gis.content.add(item_properties, inputRuta, folder = "aviar")
csv_id = csv_item.id

csv_lyr = csv_item.publish(overwrite = True, item_id = csv_id)

historico_id = "7823a0b7da024b60bd21cd963e7ef4a1"
historico_item = gis.content.get(historico_id)

# #Eliminar datos de los ultimos 1 meses en adelante
feature_historico =  gis.content.get(historico_id).layers[0]

today = date.today()
today_str = str(today)
past_months_str = str(today + relativedelta(months=-1))

f1 = 'report_date >= TIMESTAMP'
f2 = '\''
f3 = past_months_str
f4 = '\''

filtro = f1+f2+f3+f4

historico_fset = feature_historico.query(where = filtro)

all_features = historico_fset.features

for a in historico_fset:
    delete_oid = a.attributes.get('objectid')
#     print(delete_oid)
    feature_historico.delete_features(where= "objectid = " + str(delete_oid))


# Añadir los nuevos registros desde el 2020-01-01
feature_item = csv_lyr.id
# feature_item

feature_table =  gis.content.get(feature_item).layers[0]
# feature_table
historico_flayer = gis.content.get(historico_id).layers[0]
# historico_flayer

historico_fset = feature_table.query()

len(historico_fset.features)

all_features = historico_fset.features

# all_features

historico_flayer.edit_features(adds = all_features)

#Eliminar capa csv_id y feature_id

csv_delete = gis.content.get(csv_id)
csv_delete.delete()
print(csv_delete)

feature_id = csv_lyr.id
feature_delete = gis.content.get(feature_id)
feature_delete.delete()

