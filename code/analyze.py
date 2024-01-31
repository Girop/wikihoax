from collect import ExternalPage, WikiPage
from pyvis.network import Network
import networkx as nx
import seaborn as sns
import matplotlib.pyplot as plt

MAX_WIKI = 150

def load_formated_data(filename: str) -> list[ExternalPage | WikiPage]:
    with open(filename, encoding='utf-8') as fp:
        data = [line.strip() for line in fp.readlines()]

    objs = []
    for line in data:
        obj = eval(line)
        objs.append(obj)
    return objs

# def pyvis_vis(blue_nodes, red_nodes):
#     net.add_nodes(blue_nodes, color=['blue' for _ in range(len(blue_nodes))])
#     # net.add_nodes(green_nodes, color=['green' for _ in range(len(green_nodes))])
#     net.add_nodes(red_nodes, color=['red' for _ in range(len(red_nodes))]) 
#    
#
#     net.repulsion(node_distance=200, spring_length=400, spring_strength=0.1)
#
#     net.show("net.html", notebook=False)


if __name__ == '__main__':
    extpages = load_formated_data("processed_pagedata.txt")
    wikis = load_formated_data("wikidata.txt")[:MAX_WIKI]

    net = Network(height='99vh', width='99vw', directed=True, cdn_resources='remote')
    blue_nodes = [] # Wiki nodes with references
    green_nodes = [] # Unseen wiki articles
    red_nodes = [] # Wiki sources
    
    for page in wikis:
        if page.name in green_nodes:
            green_nodes.remove(page.name) 

        blue_nodes.append(page.name)
        green_nodes.extend(page.wikipages)

    for page in extpages:
        red_nodes.append(page.name)
        for link in page.wikilinks:
            if link not in blue_nodes:
                green_nodes.append(link)


    print("Blue nodes: ", len(blue_nodes))
    print("Red nodes: ", len(red_nodes))
    # pyvis_vis(blue_nodes, red_nodes) 
    
    # net = nx.DiGraph() 
    
    for node in blue_nodes:
        net.add_node(node)

    for wiki in wikis:
        name = wiki.name
        for link in wiki.wikipages:
            try:
                net.add_edge(name, link)
            except:
                pass

        # for link in wiki.external_links:
        #     try:
        #         net.add_edge(name, link)
        #     except:
        #         pass
        
        # for page in extpages:
        #     name = page.name
        #     for link in page.wikilinks:
        #         try:
        #             net.add_edge(name, link)
        #         except:
        #             pass
    net.repulsion(node_distance=300, spring_strength=0.1, damping=0.0001)
    net.show("net.html", notebook=False)
    exit()
    # TODO
    # 
    
    plt.figure(figsize=(10, 6))
    ax = sns.barplot(x=node_names, y=sorted_degrees, palette="colorfulness")
    ax.set_ylabel("Stopień wchodzący wierzchołka", labelpad=20)
    plt.xticks(rotation=90)
    plt.tight_layout()

    plt.show()
