import json

parent_file = "test_api_parent_collection.json"
category_files = [
    ("Organizations", "test_api_organizations.json"),
    ("Users", "test_api_users.json"),
    ("Profiles", "test_api_profiles.json"),
    ("Batch Operations", "test_api_batch.json"),
    ("Statistics", "test_api_stats.json"),
    ("Advanced Search", "test_api_search.json"),
    ("Health & Version", "test_api_health_version.json"),
]

with open(parent_file, "r") as f:
    parent = json.load(f)

merged_items = []
for folder_name, filename in category_files:
    with open(filename, "r") as f:
        data = json.load(f)
    merged_items.append({
        "name": folder_name,
        "description": data.get("description", ""),
        "item": data["item"]
    })

parent["item"] = merged_items

with open("test_api_merged_collection.json", "w") as f:
    json.dump(parent, f, indent=2)

print("Merged collection written to test_api_merged_collection.json") 