import json
from typing import List, Dict, Any, Union
from datetime import datetime
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
def generate_contractual_calendar_html(
    calendar_data: Union[List[Dict[str, Any]], str],
    output_file: str = "contractual_calendar.html",
    title: str = "Contractual Calendar Dashboard",
    subtitle: str = "Project Timeline Management & Compliance Tracking"
) -> str:
    """
    Generate an interactive HTML dashboard from contractual calendar JSON data.
    
    Args:
        calendar_data: List of dictionaries containing calendar items, or JSON string
        output_file: Output HTML file path (optional)
        title: Main title for the dashboard
        subtitle: Subtitle text for the dashboard
        
    Returns:
        str: Generated HTML content
        
    Example:
        # From list of dictionaries
        calendar_items = [
            {
                "type": "Deadline",
                "name": "Project Completion",
                "deadline": "2024-12-31",
                "description": "Final project delivery date",
                "clause_reference": "Section 5.1"
            }
        ]
        html_content = generate_contractual_calendar_html(calendar_items)
        
        # From JSON file
        with open('calendar.json', 'r') as f:
            calendar_data = f.read()
        html_content = generate_contractual_calendar_html(calendar_data)
    """
    
    # Parse input data
    if isinstance(calendar_data, str):
        try:
            parsed_data = json.loads(calendar_data)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON string provided: {e}")
    elif isinstance(calendar_data, list):
        parsed_data = calendar_data
    else:
        raise TypeError("calendar_data must be a list of dictionaries or a JSON string")
    
    # Filter out items with errors or invalid data
    valid_items = []
    for item in parsed_data:
        if isinstance(item, dict) and not item.get('error') and item.get('name'):
            # Ensure required fields have default values
            cleaned_item = {
                'type': item.get('type', 'Other'),
                'name': item.get('name', 'Unnamed Item'),
                'deadline': item.get('deadline', ''),
                'relative_to_notice': item.get('relative_to_notice', ''),
                'description': item.get('description', ''),
                'clause_reference': item.get('clause_reference', ''),
                'source_citations': item.get('source_citations', [])
            }
            valid_items.append(cleaned_item)
    
    # Convert data to JavaScript format
    js_data = json.dumps(valid_items, indent=2, ensure_ascii=False)
    
    # Generate timestamp
    generation_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # HTML template
    html_template = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <meta name="generator" content="Contractual Calendar Generator">
    <meta name="generated" content="{generation_time}">
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
            background: rgba(255, 255, 255, 0.95);
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            overflow: hidden;
        }}
        
        .header {{
            background: linear-gradient(135deg, #2c3e50 0%, #3498db 100%);
            color: white;
            padding: 30px;
            text-align: center;
            position: relative;
            overflow: hidden;
        }}
        
        .header::before {{
            content: '';
            position: absolute;
            top: -50%;
            left: -50%;
            width: 200%;
            height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 70%);
            animation: shimmer 4s ease-in-out infinite;
        }}
        
        @keyframes shimmer {{
            0%, 100% {{ transform: translateX(-100%) translateY(-100%) rotate(45deg); }}
            50% {{ transform: translateX(100%) translateY(100%) rotate(45deg); }}
        }}
        
        .header h1 {{
            font-size: 2.5rem;
            margin-bottom: 10px;
            position: relative;
            z-index: 1;
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
            position: relative;
            z-index: 1;
        }}
        
        .generation-info {{
            font-size: 0.8rem;
            opacity: 0.7;
            margin-top: 10px;
            position: relative;
            z-index: 1;
        }}
        
        .filters {{
            padding: 20px 30px;
            background: #f8f9fa;
            border-bottom: 1px solid #e9ecef;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            align-items: center;
        }}
        
        .filter-group {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        
        .filter-label {{
            font-weight: 600;
            color: #495057;
        }}
        
        .filter-select {{
            padding: 8px 12px;
            border: 2px solid #dee2e6;
            border-radius: 8px;
            background: white;
            font-size: 14px;
            transition: all 0.3s ease;
        }}
        
        .filter-select:focus {{
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }}
        
        .search-box {{
            flex: 1;
            min-width: 250px;
            padding: 10px 15px;
            border: 2px solid #dee2e6;
            border-radius: 25px;
            font-size: 14px;
            transition: all 0.3s ease;
        }}
        
        .search-box:focus {{
            outline: none;
            border-color: #3498db;
            box-shadow: 0 0 0 3px rgba(52, 152, 219, 0.1);
        }}
        
        .content {{
            padding: 30px;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        
        .stat-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            border-radius: 15px;
            text-align: center;
            transform: translateY(0);
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .stat-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.2), transparent);
            transition: left 0.5s;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.15);
        }}
        
        .stat-card:hover::before {{
            left: 100%;
        }}
        
        .stat-number {{
            font-size: 2rem;
            font-weight: bold;
            margin-bottom: 5px;
        }}
        
        .stat-label {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        .items-grid {{
            display: grid;
            gap: 20px;
        }}
        
        .item-card {{
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.08);
            border-left: 5px solid #3498db;
            transition: all 0.3s ease;
            position: relative;
            overflow: hidden;
        }}
        
        .item-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.12);
        }}
        
        .item-card.deadline {{
            border-left-color: #e74c3c;
        }}
        
        .item-card.milestone {{
            border-left-color: #f39c12;
        }}
        
        .item-card.entitlement {{
            border-left-color: #27ae60;
        }}
        
        .item-header {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-bottom: 15px;
            gap: 15px;
        }}
        
        .item-title {{
            font-size: 1.3rem;
            font-weight: 600;
            color: #2c3e50;
            flex: 1;
        }}
        
        .item-type {{
            padding: 5px 12px;
            border-radius: 20px;
            font-size: 0.8rem;
            font-weight: 600;
            text-transform: uppercase;
            flex-shrink: 0;
        }}
        
        .item-type.deadline {{
            background: rgba(231, 76, 60, 0.1);
            color: #e74c3c;
        }}
        
        .item-type.milestone {{
            background: rgba(243, 156, 18, 0.1);
            color: #f39c12;
        }}
        
        .item-type.entitlement {{
            background: rgba(39, 174, 96, 0.1);
            color: #27ae60;
        }}
        
        .item-type.other {{
            background: rgba(108, 117, 125, 0.1);
            color: #6c757d;
        }}
        
        .item-details {{
            display: grid;
            gap: 10px;
            margin-bottom: 15px;
        }}
        
        .detail-row {{
            display: flex;
            align-items: flex-start;
            gap: 10px;
        }}
        
        .detail-label {{
            font-weight: 600;
            color: #495057;
            min-width: 100px;
            font-size: 0.9rem;
        }}
        
        .detail-value {{
            color: #6c757d;
            flex: 1;
            font-size: 0.9rem;
            line-height: 1.4;
        }}
        
        .deadline-date {{
            background: #f8f9fa;
            padding: 8px 12px;
            border-radius: 8px;
            font-weight: 600;
            color: #495057;
        }}
        
        .clause-reference {{
            background: rgba(52, 152, 219, 0.1);
            color: #3498db;
            padding: 4px 8px;
            border-radius: 5px;
            font-size: 0.8rem;
            font-weight: 500;
        }}
        
        .no-results {{
            text-align: center;
            padding: 40px;
            color: #6c757d;
        }}
        
        .hidden {{
            display: none !important;
        }}
        
        .export-buttons {{
            margin-bottom: 20px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        
        .export-btn {{
            padding: 8px 16px;
            background: #3498db;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.3s ease;
        }}
        
        .export-btn:hover {{
            background: #2980b9;
        }}
        
        @media (max-width: 768px) {{
            .filters {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .filter-group {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .search-box {{
                min-width: auto;
            }}
            
            .item-header {{
                flex-direction: column;
                align-items: stretch;
            }}
            
            .item-type {{
                align-self: flex-start;
            }}
            
            .export-buttons {{
                flex-direction: column;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>{subtitle}</p>
            <div class="generation-info">Generated on {generation_time}</div>
        </div>
        
        <div class="filters">
            <div class="filter-group">
                <span class="filter-label">Type:</span>
                <select class="filter-select" id="typeFilter">
                    <option value="">All Types</option>
                    <option value="Deadline">Deadlines</option>
                    <option value="Milestone">Milestones</option>
                    <option value="Entitlement">Entitlements</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            
            <input type="text" class="search-box" id="searchBox" placeholder="Search by name, description, or clause reference...">
        </div>
        
        <div class="content">
            <div class="export-buttons">
                <button class="export-btn" onclick="exportToJSON()">Export to JSON</button>
                <button class="export-btn" onclick="exportToCSV()">Export to CSV</button>
                <button class="export-btn" onclick="printDashboard()">Print Dashboard</button>
            </div>
            
            <div class="stats" id="stats">
                <!-- Stats will be populated by JavaScript -->
            </div>
            
            <div class="items-grid" id="itemsGrid">
                <!-- Items will be populated by JavaScript -->
            </div>
            
            <div class="no-results hidden" id="noResults">
                <h3>No items found</h3>
                <p>Try adjusting your filters or search terms</p>
            </div>
        </div>
    </div>

    <script>
        const contractualData = {js_data};
        let filteredData = [...contractualData];

        function updateStats() {{
            const stats = {{
                total: filteredData.length,
                deadlines: filteredData.filter(item => item.type === 'Deadline').length,
                milestones: filteredData.filter(item => item.type === 'Milestone').length,
                entitlements: filteredData.filter(item => item.type === 'Entitlement').length
            }};

            document.getElementById('stats').innerHTML = `
                <div class="stat-card">
                    <div class="stat-number">${{stats.total}}</div>
                    <div class="stat-label">Total Items</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${{stats.deadlines}}</div>
                    <div class="stat-label">Deadlines</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${{stats.milestones}}</div>
                    <div class="stat-label">Milestones</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${{stats.entitlements}}</div>
                    <div class="stat-label">Entitlements</div>
                </div>
            `;
        }}

        function renderItems() {{
            const grid = document.getElementById('itemsGrid');
            const noResults = document.getElementById('noResults');

            if (filteredData.length === 0) {{
                grid.classList.add('hidden');
                noResults.classList.remove('hidden');
                return;
            }}

            grid.classList.remove('hidden');
            noResults.classList.add('hidden');

            grid.innerHTML = filteredData.map(item => `
                <div class="item-card ${{item.type.toLowerCase()}}">
                    <div class="item-header">
                        <h3 class="item-title">${{item.name || 'Unnamed Item'}}</h3>
                        <span class="item-type ${{item.type.toLowerCase()}}">${{item.type}}</span>
                    </div>
                    <div class="item-details">
                        ${{item.deadline ? `
                            <div class="detail-row">
                                <span class="detail-label">Deadline:</span>
                                <span class="detail-value">
                                    <span class="deadline-date">${{item.deadline}}</span>
                                </span>
                            </div>
                        ` : ''}}
                        ${{item.relative_to_notice ? `
                            <div class="detail-row">
                                <span class="detail-label">Relative to:</span>
                                <span class="detail-value">${{item.relative_to_notice}}</span>
                            </div>
                        ` : ''}}
                        ${{item.description ? `
                            <div class="detail-row">
                                <span class="detail-label">Description:</span>
                                <span class="detail-value">${{item.description}}</span>
                            </div>
                        ` : ''}}
                        ${{item.clause_reference ? `
                            <div class="detail-row">
                                <span class="detail-label">Reference:</span>
                                <span class="detail-value">
                                    <span class="clause-reference">${{item.clause_reference}}</span>
                                </span>
                            </div>
                        ` : ''}}
                    </div>
                </div>
            `).join('');
        }}

        function filterData() {{
            const typeFilter = document.getElementById('typeFilter').value;
            const searchTerm = document.getElementById('searchBox').value.toLowerCase();

            filteredData = contractualData.filter(item => {{
                const matchesType = !typeFilter || item.type === typeFilter;
                const matchesSearch = !searchTerm || 
                    (item.name && item.name.toLowerCase().includes(searchTerm)) ||
                    (item.description && item.description.toLowerCase().includes(searchTerm)) ||
                    (item.clause_reference && item.clause_reference.toLowerCase().includes(searchTerm)) ||
                    (item.deadline && item.deadline.toLowerCase().includes(searchTerm));

                return matchesType && matchesSearch;
            }});

            updateStats();
            renderItems();
        }}

        function exportToJSON() {{
            const dataStr = JSON.stringify(filteredData, null, 2);
            const dataBlob = new Blob([dataStr], {{type: 'application/json'}});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'contractual_calendar_export.json';
            link.click();
            URL.revokeObjectURL(url);
        }}

        function exportToCSV() {{
            const headers = ['Type', 'Name', 'Deadline', 'Relative to Notice', 'Description', 'Clause Reference'];
            const csvContent = [
                headers.join(','),
                ...filteredData.map(item => [
                    `"${{item.type || ''}}"`,
                    `"${{(item.name || '').replace(/"/g, '""')}}"`,
                    `"${{item.deadline || ''}}"`,
                    `"${{item.relative_to_notice || ''}}"`,
                    `"${{(item.description || '').replace(/"/g, '""')}}"`,
                    `"${{item.clause_reference || ''}}"`
                ].join(','))
            ].join('\\n');
            
            const dataBlob = new Blob([csvContent], {{type: 'text/csv'}});
            const url = URL.createObjectURL(dataBlob);
            const link = document.createElement('a');
            link.href = url;
            link.download = 'contractual_calendar_export.csv';
            link.click();
            URL.revokeObjectURL(url);
        }}

        function printDashboard() {{
            window.print();
        }}

        // Event listeners
        document.getElementById('typeFilter').addEventListener('change', filterData);
        document.getElementById('searchBox').addEventListener('input', filterData);

        // Initial render
        filterData();
    </script>
</body>
</html>'''

    # Save to file if output_file is provided
    if output_file:
        try:
            output_file = os.path.join(BASE_DIR, output_file)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_template)
            print(f"HTML dashboard generated successfully: {output_file}")
        except IOError as e:
            print(f"Warning: Could not write to file {output_file}: {e}")
    
    return html_template


def load_calendar_from_file(file_path: str) -> List[Dict[str, Any]]:
    """
    Load calendar data from a JSON file.
    
    Args:
        file_path: Path to the JSON file
        
    Returns:
        List of calendar items
        
    Raises:
        FileNotFoundError: If file doesn't exist
        json.JSONDecodeError: If file contains invalid JSON
    """
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(BASE_DIR, file_path)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


# Example usage and demonstration
if __name__ == "__main__":
    # Example 1: Basic usage with sample data

    # Example 2: Loading from JSON file (commented out as file may not exist)
    try:
        calendar_data = load_calendar_from_file("generated_calendar.json")
        html_content = generate_contractual_calendar_html(calendar_data)
    except FileNotFoundError:
        print("Calendar JSON file not found")
