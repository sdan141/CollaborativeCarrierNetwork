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
    fig, ax = plt.subplots()
    plt.subplots_adjust(left=0.3)

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

    # Draw nodes
    for idx, (u, v, d) in enumerate(Graph.edges(data=True)):
        node_shape = 's' if idx == 0 else 'o'  # Square for the first node, circle for others
        nx.draw_networkx_nodes(Graph, pos, nodelist=[u], node_size=300, node_color=color, ax=ax, node_shape=node_shape)
        nx.draw_networkx_nodes(Graph, pos, nodelist=[v], node_size=300, node_color=color, ax=ax, node_shape='o')

    # Draw edges
    nx.draw_networkx_edges(Graph, pos, width=2, arrows=True, edge_color=color, ax=ax)

    # Draw node labels
    nx.draw_networkx_labels(Graph, pos, font_size=10, font_weight='bold', ax=ax)
    
    ax.figure.canvas.draw()

    return fig
    # plt.show() 


    

    