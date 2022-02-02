import numpy as np
from copy import deepcopy
import random
from dispatch_alg import LD
from math import radians,degrees, cos, sin, asin, sqrt, atan2
from config import *
from path import *
import time
import pickle
import osmnx as ox

def distance(coord_1, coord_2):
    lon1, lat1 = coord_1
    lon2, lat2 = coord_2
    lon1, lat1, lon2, lat2 = map(radians, [lon1, lat1, lon2, lat2])
    dlon = abs(lon2 - lon1)
    dlat = abs(lat2 - lat1)
    r = 6371

    alat = sin(dlat / 2) ** 2
    clat = 2 * atan2(alat**0.5, (1-alat)**0.5)
    lat_dis = clat * r * 1000

    alon = sin(dlon / 2) ** 2
    clon = 2 * atan2(alon ** 0.5, (1 - alon) ** 0.5)
    lon_dis = clon * r * 1000

    manhattan_dis = abs(lat_dis) + abs(lon_dis)

    return manhattan_dis

def distance_array(coord_1, coord_2):
    coord_1 = coord_1.astype(float)
    coord_2 = coord_2.astype(float)
    coord_1_array = np.radians(coord_1)
    coord_2_array = np.radians(coord_2)
    dlon = np.abs(coord_2_array[:, 0] - coord_1_array[:, 0])
    dlat = np.abs(coord_2_array[:, 1] - coord_1_array[:, 1])
    r = 6371

    alat = np.sin(dlat / 2) ** 2
    clat = 2 * np.arctan2(alat ** 0.5, (1 - alat) ** 0.5)
    lat_dis = clat * r * 1000

    alon = np.sin(dlon / 2) ** 2
    clon = 2 * np.arctan2(alon ** 0.5, (1 - alon) ** 0.5)
    lon_dis = clon * r * 1000

    manhattan_dis = np.abs(lat_dis) + np.abs(lon_dis)

    return manhattan_dis

# given origin and destination, return itenarary

# 在这里加入ra
def route_generation_array(origin_coord_array, dest_coord_array, mode = 'complete'):
    # origin_coord_list为 Kx2 的array，第一列为lng，第二列为lat；dest_coord_array同理
    # itinerary_node_list的每一项为一个list，包含了对应路线中的各个节点编号
    # itinerary_segment_dis_list的每一项为一个array，包含了对应路线中的各节点到相邻下一节点的距离
    # dis_array包含了各行程的总里程
    origin_node_list = get_nodeId_from_coordinate(origin_coord_array[:, 1], origin_coord_array[:, 0])
    dest_node_list = get_nodeId_from_coordinate(dest_coord_array[:, 1], dest_coord_array[:, 0])
    itinerary_node_list = []
    itinerary_segment_dis_list = []
    dis_array = []
    G = ox.graph_from_bbox(42 + 0.1,39 - 0.1, 69 - 0.1, 72 + 0.1, network_type='drive_service')
    if mode == 'complete':
        #返回完整itinerary
        itenerary_list = ox.distance.shortest_path(G, origin_node_list, dest_node_list, weight='length', cpus=16)
        dis_array = [2] * len(itenerary_list)
        itinerary_segment_dis_list = [2] * len(itenerary_list)
        # a toy example
        # for i in range(origin_coord_array.shape[0]):
        #     origin_lng = origin_coord_array[i, 0]
        #     if origin_lng == 0:
        #         itinerary_node = [0,1,2]
        #         itinerary_segment_dis = [1,1,0]
        #         dis = 2
        #     elif origin_lng == 1:
        #         itinerary_node = [2,3,0]
        #         itinerary_segment_dis = [1, 1, 0]
        #         dis = 2
            # itinerary_node_list.append(itinerary_node)
            # itinerary_segment_dis_list.append(itinerary_segment_dis)
            # dis_array.append(dis)
        # dis_array = np.array(dis_array)
    elif mode == 'drop_end':
        #对itineray node_list和itineray segment_time_list中的各个item，把末尾节点给drop掉

        # a toy example
        # for i in range(origin_coord_array.shape[0]):
        #     origin_lng = origin_coord_array[i, 0]
        #     if origin_lng == 0:
        #         itinerary_node = [0, 1]
        #         itinerary_segment_dis = [1, 1]
        #         dis = 2
        #     elif origin_lng == 1:
        #         itinerary_node = [2, 3]
        #         itinerary_segment_dis = [1, 1]
        #         dis = 2
            # itinerary_node_list.append(itinerary_node)
            # itinerary_segment_dis_list.append(itinerary_segment_dis)
            # dis_array.append(dis)
        # dis_array = np.array(dis_array)
        itenerary_list = ox.distance.shortest_path(G, origin_node_list, dest_node_list, weight='length', cpus=16)
        dis_array = [2] * len(itenerary_list)
        itinerary_segment_dis_list = [2] * len(itenerary_list)
    return itinerary_node_list, itinerary_segment_dis_list, dis_array

class GridSystem:
    def __init__(self, **kwargs):
        pass

    def load_data(self, data_path):
        self.df_zone_info = pickle.load(open(data_path + 'zone_info.pickle', 'rb'))
        self.num_grid = self.df_zone_info.shape[0]
        self.adj_mat = pickle.load(open(data_path + 'adj_matrix.pickle', 'rb'))

    def get_basics(self):
        #output: basic information about the grid network
        return self.num_grid

class road_network:
    def __init__(self, **kwargs):
        self.params = kwargs

    def load_data(self, data_path, file_name):
        # 路网格式：节点数字编号（从0开始），节点经度，节点纬度，所在grid id
        # columns = ['node_id', 'lng', 'lat', 'grid_id']
        self.df_road_network = pickle.load(open(data_path + file_name, 'rb'))
        self.df_road_network['grid_id'] = [0] * len(self.df_road_network)

    def generate_road_info(self):
        data = pd.read_csv(self.params['input_file_path'])
        lng_max = max(data['origin_lng'].max(), data['dest_lng'].max())
        lng_min = min(data['origin_lng'].min(), data['dest_lng'].min())
        lat_max = max(data['origin_lat'].max(), data['dest_lat'].max())
        lat_min = min(data['origin_lat'].min(), data['dest_lat'].min())
        center = ((lng_max + lng_min) / 2, (lat_max + lat_min) / 2)
        interval = max((lng_max - lng_min), (lat_max - lat_min)) / self.params['side']
        G = ox.graph_from_bbox(lat_max + 0.1, lat_min - 0.1, lng_min - 0.1, lng_max + 0.1, network_type='drive_service')
        gdf_nodes, gdf_edges = ox.graph_to_gdfs(G)
        nodelist = []
        lat_list = gdf_nodes['y'].tolist()
        lng_list = gdf_nodes['x'].tolist()
        result = pd.DataFrame()
        result['lat'] = lat_list
        result['lng'] = lng_list
        result['node_id'] = gdf_nodes.index.tolist()
        result['node_id'] = gdf_nodes.index.tolist()[:10]
        for i in range(len(result)):
            nodelist.append(get_zone(lat_list[i], lng_list[i], center, side, interval))
        result['grid_id'] = nodelist
        pickle.dump(result, open('./road_network_information' + '.pickle', 'wb'))


    def get_information_for_nodes(self, node_id_array):
        lng_array = self.df_road_network.loc[node_id_array, 'lng'].values
        lat_array = self.df_road_network.loc[node_id_array, 'lat'].values
        grid_id_array = self.df_road_network.loc[node_id_array, 'grid_id'].values
        return lng_array, lat_array, grid_id_array


def get_exponential_epsilons(initial_epsilon, final_epsilon, steps, decay=0.99, pre_steps=10):
    epsilons = []

    # pre randomness
    for i in range(0, pre_steps):
        epsilons.append(deepcopy(initial_epsilon))

    # decay randomness
    epsilon = initial_epsilon
    for i in range(pre_steps, steps):
        epsilon = max(final_epsilon, epsilon * decay)
        epsilons.append(deepcopy(epsilon))

    return np.array(epsilons)


def sample_all_drivers(driver_info, t_initial, t_end, driver_sample_ratio=1, driver_number_dist=''):
    #当前并无随机抽样司机；后期若需要，可设置抽样模块生成sampled_driver_info
    new_driver_info = deepcopy(driver_info)
    sampled_driver_info = new_driver_info
    sampled_driver_info['status'] = 3
    loc_con = sampled_driver_info['start_time'] <= t_initial
    sampled_driver_info.loc[loc_con, 'status'] = 0
    sampled_driver_info['target_loc_lng'] = sampled_driver_info['lng']
    sampled_driver_info['target_loc_lat'] = sampled_driver_info['lat']
    sampled_driver_info['target_grid_id'] = sampled_driver_info['grid_id']
    sampled_driver_info['remaining_time'] = 0
    sampled_driver_info['matched_order_id'] = 'None'
    sampled_driver_info['total_idle_time'] = 0
    sampled_driver_info['time_to_last_cruising'] = 0
    sampled_driver_info['current_road_node_index'] = 0
    sampled_driver_info['remaining_time_for_current_node'] = 0
    sampled_driver_info['itinerary_node_list'] = [[] for i in range(sampled_driver_info.shape[0])]
    sampled_driver_info['itinerary_segment_time_list'] = [[] for i in range(sampled_driver_info.shape[0])]

    return sampled_driver_info


def sample_request_num(t_mean, std, delta_t):
    """
    sample request num during delta t
    :param t_mean:
    :param std:
    :param delta_t:
    :return:
    """
    random_num = np.random.normal(t_mean, std, 1)[0] * (delta_t/100)
    random_int = random_num // 1
    random_reminder = random_num % 1

    rn = random.random()
    if rn < random_reminder:
        request_num = random_int + 1
    else:
        request_num = random_int
    return int(request_num)

# reposition，暂时先不定义
def reposition(eligible_driver_table, df_zone_info, adj_mat, mode):
    #需用到route_generation_array
    itinerary_node_list = []
    itinerary_segment_dis_list = []
    dis_array = np.array([])
    print(eligible_driver_table)
    # toy example
    coord_array = eligible_driver_table.loc[:, ['lng', 'lat']].values
    itinerary_node_list, itinerary_segment_dis_list, dis_array = route_generation_array(coord_array, coord_array)
    return itinerary_node_list, itinerary_segment_dis_list, dis_array

# cruising，暂时先不定义
def cruising(eligible_driver_table, df_zone_info, adj_mat, mode):
    #需用到route_generation_array
    itinerary_node_list = []
    itinerary_segment_dis_list = []
    dis_array = np.array([])

    # toy example
    coord_array = eligible_driver_table.loc[:, ['lng', 'lat']].values
    itinerary_node_list, itinerary_segment_dis_list, dis_array = route_generation_array(coord_array, coord_array)
    return itinerary_node_list, itinerary_segment_dis_list, dis_array


def order_dispatch(wait_requests, driver_table, maximal_pickup_distance = 950, dispatch_method = 'LD'):
    con_ready_to_dispatch = (driver_table['status'] == 0) | (driver_table['status'] == 4)
    idle_driver_table = driver_table[con_ready_to_dispatch]
    num_wait_request = wait_requests.shape[0]
    num_idle_driver = idle_driver_table.shape[0]
    matched_pair_actual_indexs = []
    matched_itinerary = []

    if num_wait_request > 0 and num_idle_driver > 0:
        if dispatch_method == 'LD':
            #generate order driver pairs and corresponding itinerary
            request_array = wait_requests.loc[:, ['origin_lng', 'origin_lat', 'order_id', 'weight']].values
            request_array = np.repeat(request_array, num_idle_driver, axis=0)
            driver_loc_array = idle_driver_table.loc[:, ['lng', 'lat', 'driver_id']].values
            driver_loc_array = np.tile(driver_loc_array, (num_wait_request, 1))
            itinerary_node_list, itinerary_segment_dis_list, dis_array = route_generation_array(request_array[:, :2], driver_loc_array[:, :2], mode='drop_end')
            flag = np.where(dis_array <= maximal_pickup_distance)[0]
            if len(flag) > 0:
                order_driver_pair = np.vstack([request_array[flag, 2], driver_loc_array[flag, 2], request_array[flag, 3], flag]).T
                order_driver_pair = order_driver_pair.tolist()
                matched_pair_actual_indexs = LD(order_driver_pair)

                itinerary_node_list_new = []
                itinerary_segment_dis_list_new = []
                dis_array_new = []
                for item in matched_pair_actual_indexs:
                    index = int(item[3])
                    itinerary_node_list_new.append(itinerary_node_list[index])
                    itinerary_segment_dis_list_new.append(itinerary_segment_dis_list[index])
                    dis_array_new.append(dis_array[index])
                matched_itinerary = [itinerary_node_list_new, itinerary_segment_dis_list_new, dis_array_new]

    return matched_pair_actual_indexs, matched_itinerary

def driver_online_offline_decision(driver_table, current_time):
    #注意pickup和delivery driver不应当下线
    new_driver_table = driver_table
    return new_driver_table


# define the function to get zone_id of segment node
def get_zone(lat, lng, center, side, interval):
    if lat < center[1]:
        i = math.floor(side / 2) - math.ceil((center[1] - lat) / interval)
    else:
        i = math.floor(side / 2) + math.ceil((lat - center[1]) / interval) - (1 - side % 2)

    if lng < center[0]:
        j = math.floor(side / 2) - math.ceil((center[0] - lng) / interval)
    else:
        j = math.floor(side / 2) + math.ceil((lng - center[0]) / interval) - (1 - side % 2)

    return i * side + j


def get_nodeId_from_coordinate(lat, lng):
    node_list = []
    for i in range(len(lat)):
        print("lat: ", lat[i], " lng: ", lng[i])
        G = ox.graph_from_bbox(lat[i] + 40 + 0.1, lat[i] + 40 - 0.1, lng[i] + 70 - 0.1, lng[i] + 70  + 0.1, network_type='drive_service')
        x = ox.distance.get_nearest_node(G, (lat[i] + 40, lng[i] + 70), method=None, return_dist=True)
        node_list.append(x)
    return node_list
#############################################################################




