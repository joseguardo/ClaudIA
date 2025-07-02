import os
import json
import time
import concurrent.futures
from tqdm import tqdm
from openai import OpenAI


def build_prompt(chunk_texts, max_chunks=5):
    sample = chunk_texts if len(chunk_texts) <= max_chunks else chunk_texts[:max_chunks]
    text_block = "\n\n".join(f"{i+1}. {c}" for i, c in enumerate(sample))

    return (
        "You are a legal assistant specialized in EPC (Engineering, Procurement and Construction) contracts.\n"
        "Below is a set of paragraphs grouped by semantic similarity, all extracted from the same contract.\n"
        "Please analyze their content and return a concise, single-line label that best summarizes the shared theme.\n\n"
        "**Label format rules:**\n"
        "- Use 2 to 6 words.\n"
        "- Use formal and specific legal language (e.g., 'Force Majeure Clauses', 'Warranty Obligations', 'Termination Terms').\n"
        "- Capitalize first letters (Title Case).\n"
        "- Do not use punctuation at the end.\n"
        "- Return only the label, no explanation.\n\n"
        "Here are the paragraphs:\n\n"
        f"{text_block}\n\n"
        "Label:"
    )

def process_single_group(group, buffer, client, model):
    """Process a single group to generate its title"""
    try:
        # Extract texts from the group indices
        texts = [buffer[i] for i in sorted(group)]
        prompt = build_prompt(texts)
        
        # API call
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": "You are an expert in finding semantic similarities in legal documents."},
                {"role": "user", "content": prompt}
            ],
        )
        
        # Return the result for this group
        return group, response.output_text
    except Exception as e:
        # Handle errors gracefully
        print(f"Error processing group {sorted(group)}: {e}")
        return group, f"Error: {str(e)}"
    
def generate_titles(neighbor_groups, client, buffer, model="o4-mini-2025-04-16", max_workers=10):
    """
    Generate titles only for groups with more than 5 chunks using multi-threading.
    
    Parameters:
    - neighbor_groups: List of sets/frozensets representing groups of indices
    - client: API client for model interaction
    - buffer: List of text chunks indexed by the indices in neighbor_groups
    - model: Model identifier to use
    - max_workers: Maximum number of threads to use
    
    Returns:
    - Dictionary mapping groups to their generated labels
    """
    group_labels = {}
    start_time = time.time()
    
    # Convert to frozensets
    frozen_groups = [
        group if isinstance(group, frozenset) else frozenset(group)
        for group in neighbor_groups
    ]
    
    # Filter groups with more than 1 chunks
    groups_to_label = [group for group in frozen_groups if len(group) > 1]
    skipped_groups = len(frozen_groups) - len(groups_to_label)
    
    print(f"Generating titles for {len(groups_to_label)} groups (>1 chunks). Skipped {skipped_groups} groups.")
    
    # Use thread pool
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_group = {
            executor.submit(process_single_group, group, buffer, client, model): group
            for group in groups_to_label
        }

        for future in tqdm(concurrent.futures.as_completed(future_to_group), total=len(groups_to_label), desc="Generating titles"):
            group = future_to_group[future]
            try:
                result_group, label = future.result()
                group_labels[result_group] = label
            except Exception as e:
                print(f"Error retrieving result for group {sorted(group)}: {e}")
    
    # Update semantic_groups.json
    try:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        file_path_semanticgroups = os.path.join(base_dir, 'semantic_groups.json')
        
        with open(file_path_semanticgroups, 'r', encoding='utf-8') as f:
            semantic_groups = json.load(f)
        
        for group_data in semantic_groups:
            indices_set = frozenset(group_data["indices"])
            if indices_set in group_labels:
                group_data["group_name"] = group_labels[indices_set]
            else:
                group_data["group_name"] = group_data.get("group_name", None)
        
        with open(file_path_semanticgroups, 'w', encoding='utf-8') as f:
            json.dump(semantic_groups, f, ensure_ascii=False, indent=2)
        
        print(f"Updated semantic_groups.json with {len(group_labels)} new labels.")
    
    except Exception as e:
        print(f"Error updating semantic_groups.json: {e}")
    
    # Summary
    elapsed_time = time.time() - start_time
    print(f"Title generation complete. {len(group_labels)} groups labeled in {elapsed_time:.2f} seconds.")
    print(f"Average time per group: {elapsed_time / max(1, len(group_labels)):.2f} seconds")
    
    # Debug print
    for group, label in group_labels.items():
        print(f"({sorted(group)}, {label})")
    
    return group_labels
