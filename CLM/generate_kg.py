import json
import numpy as np
from pyvis.network import Network
from generate_embeddings import get_embedding


def generate_kgraph(relations, meta_labels, client, group_labels, save_path="kgraph.html"):
    """
    Generate a knowledge graph visualization that includes all semantic groups,
    including those containing only a single chunk ("loneliners").
    
    Parameters:
    - relations: dict, relationships between groups {group_a: {group_b: relation_type, ...}, ...}
    - meta_labels: dict, metadata for chunks with group information
    - client: client for generating embeddings
    - group_labels: dict, additional information about groups (optional)
    - save_path: str, path to save the HTML visualization
    """
    # 1. Collect all unique groups from relations and meta_labels
    unique_groups = set()
    
    # Add groups from relations
    for group_a, related_groups in relations.items():
        unique_groups.add(group_a)
        for group_b in related_groups:
            unique_groups.add(group_b)
    
    # Add ALL groups from meta_labels, including loneliners
    for chunk_id, data in meta_labels.items():
        if "meta" in data and "groups_related" in data["meta"]:
            for group in data["meta"]["groups_related"]:
                unique_groups.add(group)
    
    print(f"Found {len(unique_groups)} unique groups, including loneliners")
    
    # 2. Calculate embeddings for each group
    group_embeddings = {}
    for group_name in unique_groups:
        embedding = get_embedding(group_name, client)
        group_embeddings[group_name] = embedding
    
    # 3. Compile chunks that belong to each group
    group_chunks = {group: [] for group in unique_groups}
    for chunk_id, data in meta_labels.items():
        if "meta" in data and "groups_related" in data["meta"]:
            for group in data["meta"]["groups_related"]:
                if group in group_chunks:
                    group_chunks[group].append(chunk_id)
    
    # Count how many loneliners we have (groups with only one chunk)
    loneliner_count = sum(1 for group, chunks in group_chunks.items() if len(chunks) == 1)
    print(f"Found {loneliner_count} loneliner groups (groups with only one chunk)")
    
    # 4. Create PyVis network
    net = Network(
        height="750px",
        width="100%",
        directed=True,
        notebook=False,
        cdn_resources="remote"
    )
    
    # Configure network options with special settings for loneliners
    net.toggle_physics(True)
    net.set_options("""
    {
        "nodes": {
            "font": {
                "size": 14,
                "strokeWidth": 3
            }
        },
        "edges": {
            "color": {"inherit": "both"},
            "font": {"size": 10},
            "smooth": {"type": "dynamic"}
        },
        "physics": {
            "hierarchicalRepulsion": {
                "centralGravity": 0.0,
                "springLength": 120,
                "springConstant": 0.01,
                "nodeDistance": 150,
                "damping": 0.09
            },
            "solver": "hierarchicalRepulsion"
        },
        "layout": {
            "improvedLayout": true
        }
    }
    """)
    
    # 5. Add nodes directly to PyVis - including loneliners
    added_nodes = set()  # Track which nodes have been added
    
    for group_name in unique_groups:
        try:
            # Get chunks associated with this group
            chunk_ids = group_chunks.get(group_name, [])
            
            # Create tooltip with chunk information
            tooltip = f"<b>Group: {group_name}</b><br>Chunks: {len(chunk_ids)}"
            if len(chunk_ids) > 0:
                # Add chunk IDs to the tooltip (limit to avoid huge tooltips)
                sample_chunks = chunk_ids[:5]
                tooltip += f"<br>Sample IDs: {', '.join(map(str, sample_chunks))}"
                if len(chunk_ids) > 5:
                    tooltip += f" (+ {len(chunk_ids) - 5} more)"
            
            # Node size based on number of chunks - make sure loneliners aren't too small
            size = max(15, 10 + len(chunk_ids) * 2)
            
            # Different shape and color treatment for loneliners vs multi-chunk groups
            is_loneliner = len(chunk_ids) == 1
            
            # Color scheme: loneliners get their own color group to distinguish them
            if is_loneliner:
                color_id = 0  # Special color group for loneliners
                shape = "triangle"  # Different shape for loneliners
            else:
                # For multi-chunk groups, use hash-based coloring for diversity
                color_id = (hash(group_name) % 19) + 1  # 1-19 range (keep 0 for loneliners)
                shape = "dot"  # Regular shape for normal groups
            
            # Add the node with appropriate styling
            net.add_node(
                group_name,
                label=group_name,
                title=tooltip,
                value=size,
                group=color_id,
                shape=shape,
                physics=True,  # Enable physics for better layout
                borderWidth=2,
                borderWidthSelected=4
            )
            
            added_nodes.add(group_name)
            
            # Track different types of nodes
            node_type = "loneliner" if is_loneliner else "multi-chunk"
            print(f"Added {node_type} node: {group_name} with {len(chunk_ids)} chunks")
            
        except Exception as e:
            print(f"Error adding node '{group_name}': {e}")
    
    # 6. Add edges from the relations dictionary
    edge_count = 0
    
    for group_a, related_groups in relations.items():
        if group_a not in added_nodes:
            print(f"Warning: Source node '{group_a}' was not added to the graph")
            continue
            
        for group_b, relation_type in related_groups.items():
            if group_b not in added_nodes:
                print(f"Warning: Target node '{group_b}' was not added to the graph")
                continue
                
            try:
                # Add the edge
                net.add_edge(
                    group_a,
                    group_b,
                    title=relation_type,
                    label=relation_type,
                    arrows="to",
                    smooth={"enabled": True, "type": "dynamic"}
                )
                edge_count += 1
                
            except Exception as e:
                print(f"Error adding edge '{group_a}' -> '{group_b}': {e}")
    
    # 7. Connect loneliners to related groups based on semantic similarity
    # This is optional but helps integrate loneliners into the graph structure
    loneliner_edge_count = 0
    
    # Identify loneliners
    loneliners = [group for group, chunks in group_chunks.items() if len(chunks) == 1]
    
    # For each loneliner, try to find connections to other groups based on 
    # chunk co-occurrence in the meta_labels
    for loneliner in loneliners:
        loneliner_chunks = group_chunks[loneliner]
        if not loneliner_chunks:
            continue
        
        # Get the single chunk ID for this loneliner
        chunk_id = loneliner_chunks[0]
        
        # Find other groups that share this chunk
        if chunk_id in meta_labels and "meta" in meta_labels[chunk_id] and "groups_related" in meta_labels[chunk_id]["meta"]:
            related_groups = meta_labels[chunk_id]["meta"]["groups_related"]
            
            # Connect to other groups (not self)
            for related_group in related_groups:
                if related_group != loneliner and related_group in added_nodes:
                    try:
                        # Add edge from loneliner to related group with "part of" relationship
                        net.add_edge(
                            loneliner,
                            related_group,
                            title="part of",
                            label="part of",
                            arrows="to",
                            dashes=True,  # Use dashed line for these implicit relations
                            color={"color": "#cccccc"}  # Light gray to distinguish from explicit relations
                        )
                        loneliner_edge_count += 1
                    except Exception as e:
                        print(f"Error adding loneliner edge '{loneliner}' -> '{related_group}': {e}")
    
    print(f"Added {edge_count} explicit edges and {loneliner_edge_count} implicit loneliner connections")
    
    # 8. Save the graph
    try:
        net.save_graph(save_path)
        print(f"Knowledge graph saved as '{save_path}'")
    except Exception as e:
        print(f"Error saving graph: {e}")
        # Try a simpler save as fallback
        try:
            simple_path = "simple_" + save_path
            net.save_graph(simple_path, local=True)
            print(f"Saved simplified graph as '{simple_path}'")
        except Exception as e2:
            print(f"Failed to save graph: {e2}")
    
    # Return the results
    return {
        "network": net,
        "group_embeddings": group_embeddings,
        "nodes_added": len(added_nodes),
        "edges_added": edge_count + loneliner_edge_count,
        "loneliner_count": loneliner_count
    }
