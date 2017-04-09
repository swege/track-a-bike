#!/usr/bin/env python3
import os

from neo4j.v1 import GraphDatabase, basic_auth
import networkx as nx
from networkx.drawing.nx_pydot import write_dot
from matplotlib import pyplot as plt
from datetime import datetime, timedelta
from pprint import pprint

OUTPUT_DIRECTORY = os.path.join('graphviz', 'dot')

START_DATE = datetime.strptime('25.03.2017 00:00', '%d.%m.%Y %H:%M')
END_DATE = datetime.strptime('09.04.2017 00:00', '%d.%m.%Y %H:%M')
STEP = timedelta(hours=1)

def get_stations(session):
    result = session.run('MATCH (station:Station) RETURN station')
    return [x['station'] for x in result]

if __name__ == '__main__':
    if not os.path.exists(OUTPUT_DIRECTORY):
        os.makedirs(OUTPUT_DIRECTORY)
    driver = GraphDatabase.driver('bolt://localhost:7687', auth=basic_auth('neo4j', 'Eiqu3soh'))
    session = driver.session()
    stations = get_stations(session)
    min_lat = min(stations, key=lambda x: x['lat'])['lat']
    min_lng = min(stations, key=lambda x: x['lng'])['lng']
    max_lat = max(stations, key=lambda x: x['lat'])['lat']
    max_lng = max(stations, key=lambda x: x['lng'])['lng']
    for station in stations:
        name = station['name']
        lat = station['lat']
        lng = station['lng']
        x = (lat - min_lat) / (max_lat - min_lat)
        y = (lng - min_lng) / (max_lng - min_lng)
        # graph.add_node(station['name'], id=station['station_id'], lat=station['lat'], lng=station['lng'])

    date = START_DATE
    while date < END_DATE:
        print(date.strftime('%d.%m.%Y %H:%M'))
        graph = nx.MultiDiGraph()
        start = date
        end = (date + STEP)
        result = session.run("""
        MATCH (a:Station)-[r:BIKE_MOVED]->(b:Station)
        WHERE {start} <= r.timestamp_start < {end}
        RETURN a, r, b""", {'start': start.timestamp(), 'end': end.timestamp()})
        for record in result:
            station_a = record['a']['station_id']
            station_b = record['b']['station_id']
            bike_id = record['r']['bike_id']
            start_time = datetime.fromtimestamp(record['r']['timestamp_start']).strftime('%H\:%M')
            end_time = datetime.fromtimestamp(record['r']['timestamp_end']).strftime('%H\:%M')
            label = f'{start_time} -\n{end_time}'
            graph.add_edge(station_a, station_b, label=label)
            # graph.add_edge(station_a, station_b, label=bike_id)
        filename = f"{start.strftime('%Y-%m-%d_%H_%M')} - {end.strftime('%Y-%m-%d_%H_%M')}.dot"
        write_dot(graph, os.path.join(OUTPUT_DIRECTORY, filename))
        date = end
    # nx.drawing.draw(graph)
    # plt.show()