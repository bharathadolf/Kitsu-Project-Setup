import os
import gazu

# -------------------------------
# CONFIG
# -------------------------------
KITSU_HOST = "http://192.100.0.112/api"
EMAIL = "adolfbharath@gmail.com"
PASSWORD = "Bharath@2026"

BASE_BUILD_PATH = "D:/PROJECTS"   # change to studio root

# -------------------------------
# LOGIN
# -------------------------------
gazu.set_host(KITSU_HOST)
gazu.log_in(EMAIL, PASSWORD)
print("✅ Login successful\n")

# -------------------------------
# 1️⃣ LIST ALL PROJECTS
# -------------------------------
projects = gazu.project.all_projects()

print("📂 Available Projects:")
print("-" * 30)
for p in projects:
    print(f"• {p['name']}")

# -------------------------------
# 2️⃣ USER SELECTS PROJECT
# -------------------------------
project_name = input("\nEnter project name: ").strip()

project = gazu.project.get_project_by_name(project_name)
if not project:
    raise RuntimeError(f"❌ Project '{project_name}' not found")

print(f"\n✅ Selected Project: {project['name']}")

# -------------------------------
# 3️⃣ MODE SELECTION
# -------------------------------
print("\nChoose mode:")
print("1) Sequence")
print("2) Asset")

mode = input("Enter choice (1 or 2): ").strip()

# ======================================================
# SEQUENCE MODE
# ======================================================
if mode == "1":
    sequences = gazu.shot.all_sequences_for_project(project)

    if not sequences:
        print("❌ No sequences found in this project")
        exit()

    print("\n🎬 Sequences:")
    for i, seq in enumerate(sequences, start=1):
        print(f"{i}) {seq['name']}")

    seq_choice = int(input("\nSelect sequence number: "))
    sequence = sequences[seq_choice - 1]

    print(f"\n✅ Selected Sequence: {sequence['name']}")

    # -------------------------------
    # 4️⃣ LIST SHOTS FOR SEQUENCE
    # -------------------------------
    shots = gazu.shot.all_shots_for_sequence(sequence)

    if not shots:
        print("❌ No shots found in this sequence")
        exit()

    print(f"\n🎯 Shots in {sequence['name']}:")
    print("-" * 30)
    for shot in shots:
        print(f"• {shot['name']}")

    # -------------------------------
    # 5️⃣ (OPTIONAL) CREATE SHOT BUILD FOLDERS
    # -------------------------------
    create = input("\nCreate shot build folders? (y/n): ").lower()

    if create == "y":
        for shot in shots:
            shot_path = os.path.join(
                BASE_BUILD_PATH,
                project["name"],
                "shots",
                sequence["name"],
                shot["name"]
            )
            os.makedirs(shot_path, exist_ok=True)
            print(f"📁 Created: {shot_path}")

# ======================================================
# ASSET MODE
# ======================================================
elif mode == "2":
    assets = gazu.asset.all_assets_for_project(project)

    if not assets:
        print("❌ No assets found in this project")
        exit()

    print("\n🧱 Assets:")
    print("-" * 30)
    for asset in assets:
        print(f"• {asset['name']}")

else:
    print("❌ Invalid option")
