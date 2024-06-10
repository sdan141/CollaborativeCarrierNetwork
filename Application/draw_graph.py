"""Visualizes tours of carriers with a GUI

This module provides functions for visualizing carrier routes on a plot.
The GUI can handle button clicks by redrawing the plot based on the clicked label.

Functions:
    show_tour(carriers): 
        Display the tour of carriers with a GUI.
        
    handle_button_click(label, carriers, ax): 
        Handle radio button click event by updating the plot based on the label.
        
    show_all_carriers(carriers, ax):
        Display all carriers on the plot with distinct colors.
    
    draw_graph(carrier, color, ax): 
        Draw a graph for a carrier tour with selected color.
"""
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons

def show_tour(locations, tour_calculation):
    # Adjust the figure size by setting the figsize parameter
    fig, ax = plt.subplots() 

    random_locations = locations
    tour = tour_calculation
    color = "#D26466"
    
    location_nodes = {f'{i}': loc for i, loc in enumerate(random_locations)}
    Graph = nx.DiGraph()

    # Add nodes
    for loc, coords in location_nodes.items():
        Graph.add_node(loc, pos=coords)

    # Add edges
    for i in range(len(tour) - 1):
        Graph.add_edge(tour[i], tour[i + 1], color=color)

    # Draw graph
    pos = nx.get_node_attributes(Graph, 'pos')

    # Remove the axis borders and ticks
    ax.axis('off')

    # Create labels: "+" and "-" for the nodes, "pX" and "dX" below the nodes
    node_labels = {}
    p_count = 1
    d_count = 1
    for idx, node in enumerate(Graph.nodes()):
        if idx == 0:
            node_labels[node] = "D"
        else:
            if idx % 2 != 0:
                node_labels[node] = f"P{d_count}" # "({coords[0]:.2f}, {coords[1]:.2f})"
                coords = pos[node]
                p_count += 1
            else:
                node_labels[node] = f"D{d_count}" # "({coords[0]:.2f}, {coords[1]:.2f})"
                coords = pos[node]
                d_count += 1

    # Draw nodes
    for idx, (u, v, d) in enumerate(Graph.edges(data=True)):
        node_shape = 's' if u == '0' else 'o'  # Square for the first node, circle for others
        nx.draw_networkx_nodes(Graph, pos, nodelist=[u], node_size=400, node_color=color, ax=ax, node_shape=node_shape)
        nx.draw_networkx_nodes(Graph, pos, nodelist=[v], node_size=400, node_color=color, ax=ax, node_shape='o')

    # Draw edges
    nx.draw_networkx_edges(Graph, pos, width=2, arrows='reverse', edge_color=color, ax=ax)

    # Draw node labels
    nx.draw_networkx_labels(Graph, pos, node_labels, font_size=10, font_weight='bold', ax=ax)

    # Use tight layout to minimize padding
    plt.tight_layout(pad=0)
    
    ax.figure.canvas.draw()

    return fig
    # plt.show()




    

    