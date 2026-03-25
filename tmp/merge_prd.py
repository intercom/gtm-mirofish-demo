#!/usr/bin/env python3
"""Merge all generated task parts into the existing PRD.json."""
import json
from pathlib import Path

# Load existing PRD
with open("PRD.json") as f:
    prd = json.load(f)

existing_count = len(prd["tasks"])
print(f"Existing tasks: {existing_count}")

# Load all parts
all_new_tasks = []
for part_file in sorted(Path("tmp").glob("tasks_*.json")):
    with open(part_file) as f:
        tasks = json.load(f)
    print(f"  {part_file.name}: {len(tasks)} tasks")
    all_new_tasks.extend(tasks)

print(f"Total new tasks: {len(all_new_tasks)}")

# Check for duplicate titles
titles = [t["title"] for t in prd["tasks"]] + [t["title"] for t in all_new_tasks]
dupes = [t for t in set(titles) if titles.count(t) > 1]
if dupes:
    print(f"\nWARNING: {len(dupes)} duplicate titles found:")
    for d in dupes[:5]:
        print(f"  - {d}")
else:
    print("No duplicate titles found.")

# Verify group coverage
new_groups = sorted(set(t["parallel_group"] for t in all_new_tasks))
print(f"\nNew groups: {new_groups[0]}-{new_groups[-1]}")
expected_groups = list(range(15, 96))
missing = [g for g in expected_groups if g not in new_groups]
if missing:
    print(f"WARNING: Missing groups: {missing}")
else:
    print("All groups 15-95 covered.")

# Group task counts
group_counts = {}
for t in all_new_tasks:
    g = t["parallel_group"]
    group_counts[g] = group_counts.get(g, 0) + 1
print("\nTasks per group:")
for g in sorted(group_counts.keys()):
    print(f"  Group {g:2d}: {group_counts[g]:2d} tasks")

# Merge
prd["tasks"].extend(all_new_tasks)
total = len(prd["tasks"])
print(f"\nTotal tasks in PRD: {total}")

# Write
with open("PRD.json", "w") as f:
    json.dump(prd, f, indent=2)
print(f"PRD.json written with {total} tasks.")
