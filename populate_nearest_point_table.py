import osmnx
import math
import boto3
from decouple import config

BLOCK_SIZE = 0.01

def main():
    G = osmnx.load_graphml('./graph.graphml')
    dynamo_client = boto3.client('dynamodb', 
        aws_access_key_id=config('AWSAccessKeyId'), 
        aws_secret_access_key=config('AWSSecretKey')
    )

    min_x = 180
    max_x = -180
    min_y = 180
    max_y = -180
    for node_id in G.nodes:
        # print(node_id)
        # print(G.nodes[node_id])
        # print(G.nodes[node_id]["x"], G.nodes[node_id]["y"])
        if(G.nodes[node_id]["x"] < min_x):
            min_x = G.nodes[node_id]["x"]
        if(G.nodes[node_id]["x"] > max_x):
            max_x = G.nodes[node_id]["x"]

        if(G.nodes[node_id]["y"] < min_y):
            min_y = G.nodes[node_id]["y"]
        if(G.nodes[node_id]["y"] > max_y):
            max_y = G.nodes[node_id]["y"]
    print(min_x, min_y, max_x, max_y)

    lowest_cap_x = math.floor(min_x * 100) / 100
    highest_cap_x = math.ceil(max_x * 100) / 100

    lowest_cap_y = math.floor(min_y * 100) / 100
    highest_cap_y = math.ceil(max_y * 100) / 100

    print(lowest_cap_x, lowest_cap_y, highest_cap_x, highest_cap_y)

    # set 0.01*0.01 blocks
    num_x_blocks = round((highest_cap_x - lowest_cap_x)/BLOCK_SIZE)
    num_y_blocks = round((highest_cap_y - lowest_cap_y)/BLOCK_SIZE)

    print(num_x_blocks, num_y_blocks) 

    list_region = []
    for _ in range(num_x_blocks * num_y_blocks):
        list_region.append(0)

    for node_id in G.nodes:
        x = G.nodes[node_id]["x"]
        y = G.nodes[node_id]["y"]

        x_val = math.floor((x - lowest_cap_x) / BLOCK_SIZE)
        y_val = math.floor((y - lowest_cap_y) / BLOCK_SIZE)

        region_id = x_val + y_val * num_x_blocks
        print(G.nodes[node_id]["x"], G.nodes[node_id]["y"], region_id)

        list_region[region_id] += 1
        response = dynamo_client.put_item(
            TableName='table_find_nearest_point',
            Item={
                "region_id": {"N": str(region_id)},
                "node_id": {"N": str(node_id)},
                "x": {"N": str(x)},
                "y": {"N": str(y)},
            },
        )
    
    for node_id in G.nodes:
        x = G.nodes[node_id]["x"]
        y = G.nodes[node_id]["y"]

        response = dynamo_client.put_item(
            TableName='table_node',
            Item={
                "node_id": {"N": str(node_id)},
                "x": {"N": str(x)},
                "y": {"N": str(y)},
            },
        )

    for edge_id in G.edges:
        print(G.edges[edge_id])
        length = G.edges[edge_id]['length']
        print(length)
        speed_kph = G.edges[edge_id]['speed_kph']
        print(speed_kph)
        edge_tuple = '(' + str(edge_id[0])+', '+str(edge_id[1])+', '+str(edge_id[2])+')'
        print(edge_tuple)
        geometry = []
        if "geometry" in G.edges[edge_id]:
            print(list(G.edges[edge_id]['geometry'].coords)) 
            for item in list(G.edges[edge_id]['geometry'].coords):
                d = {}
                d["S"] = '(' + str(item[0])+', '+str(item[1])+')'
                geometry.append(d)
        print(geometry)
        response = dynamo_client.put_item(
            TableName='table_edges',
            Item={
                "src_node_id": {"N": str(edge_id[0])},
                "edge_tuple": {"S": edge_tuple },
                "length": {"N": str(G.edges[edge_id]['length'])},
                "speed_kph": {"N": str(G.edges[edge_id]['speed_kph'])},
                "current_speed": {"N": str(G.edges[edge_id]['speed_kph'])},
                "geometry": {"L": geometry},
            },
        )
    
    # for i in range(num_x_blocks * num_y_blocks):
    #     print("region id", i, "has", list_region[i], "nodes")


if __name__ == "__main__":
    main()