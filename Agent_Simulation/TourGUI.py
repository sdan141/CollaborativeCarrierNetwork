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
import random
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib.widgets import RadioButtons
from CalculateTour import get_optimal_tour, create_tour_data

def show_tour(carriers):
    """Display the tour for carriers.

    Args:
        carriers (list of CarrierAgents): A list of carrier agents to be displayed.
    """
    fig, ax = plt.subplots()
    plt.subplots_adjust(left=0.3)
    
    carrier_selector_ax = plt.axes([0.05, 0.7, 0.15, 0.15])
    carrier_labels = ['All Carriers'] + ['Carrier ' + str(i) for i in range(1, len(carriers))]
    carrier_selector = RadioButtons(carrier_selector_ax, carrier_labels)
    carrier_selector.on_clicked(lambda label: handle_button_click(label, carriers, ax))

    show_all_carriers(carriers, ax)
    plt.show() 

def handle_button_click(label, carriers, ax):
    """Handle button click by updating the plot based on the label.

    Args:
        label (str): The label associated with the button clicked.
        carriers (list of CarrierAgents): A list of carrier agents to be displayed.
        ax (AxesSubplot): The subplot to draw the graph on.
    """
    ax.clear()
    
    if label == 'All Carriers':
        show_all_carriers(carriers, ax)
        return
    
    for i in range(1, len(carriers)):
        if label == 'Carrier ' + str(i):
            draw_graph(carriers[i], 'red',  ax)
            return

def show_all_carriers(carriers, ax):
    """Display all carriers on the plot with distinct colors.

    Args:
        carriers (list of CarrierAgents): A list of carrier agents to be displayed.
        ax (AxesSubplot): The subplot to draw the graph on.
    """
    for i in range(1, len(carriers)):
        # Generate a random color for this carrier
        color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
        draw_graph(carriers[i], color,  ax)

def draw_graph(carrier, color, ax):
    """Draw a graph representing carrier routes on a plot.

    Args:
        carrier (CarrierAgent): The carrier agent containing locations and deliveries.
        color (str): The color to use for drawing the graph.
        ax (AxesSubplot): The subplot to draw the graph on.
    """
    random_locations = carrier.locations
    random_deliveries = carrier.deliveries
    
    locations = {f'{i}': loc for i, loc in enumerate(random_locations)}
    data = create_tour_data(random_locations, random_deliveries)
    tours = get_optimal_tour(data)
    Graph = nx.DiGraph()

    # Add nodes
    for loc, coords in locations.items():
        Graph.add_node(loc, pos=coords)

    # Add edges
    for i in range(len(tours) - 1):
        Graph.add_edge(tours[i], tours[i + 1], color=color)

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