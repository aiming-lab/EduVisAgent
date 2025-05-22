import subprocess
import time
import os
import zipfile
import tempfile


def deploy_project(project_dir):
    print(f"[Deploy] Installing dependencies: {project_dir}")
    subprocess.run(["npm", "install", "--legacy-peer-deps"], cwd=project_dir, check=True)

    print("[Deploy] Building project...")
    subprocess.run(["npm", "run", "build"], cwd=project_dir, check=True)

    print("[Deploy] Starting server...")
    server = subprocess.Popen(["npm", "start"], cwd=project_dir)
    time.sleep(10)  # Wait for the server to start

    print("[Deploy] Project is running. You can access it at:")
    print("👉 http://localhost:3000")
    print("Press Ctrl+C to stop the server.")

    try:
        server.wait()
    except KeyboardInterrupt:
        print("\n[Deploy] Interrupt received. Stopping server...")
        server.terminate()


def extract_zip(zip_path, extract_to_dir):
    print(f"[Extract] Extracting {zip_path} to {extract_to_dir}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to_dir)


def find_all_zip_files(base_dir):
    zip_files = []
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file.endswith(".zip"):
                zip_files.append(os.path.join(root, file))
    return zip_files


def choose_and_deploy():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    zip_root = os.path.join(script_dir, "zip")

    if not os.path.exists(zip_root):
        print("The 'zip' folder was not found. Make sure it's in the same directory as this script.")
        return

    zip_files = find_all_zip_files(zip_root)

    if not zip_files:
        print("No .zip files found.")
        return

    while True:
        print("\nFound the following zip files:")
        for i, path in enumerate(zip_files):
            print(f"{i + 1}. {os.path.relpath(path, zip_root)}")

        choice = input("\nEnter the number of the zip to deploy (or 'q' to quit): ").strip()
        if choice.lower() == 'q':
            print("Exiting.")
            break

        if not choice.isdigit() or not (1 <= int(choice) <= len(zip_files)):
            print("Invalid input. Please enter a valid number.")
            continue

        selected_zip = zip_files[int(choice) - 1]

        with tempfile.TemporaryDirectory() as temp_dir:
            extract_zip(selected_zip, temp_dir)

            items = os.listdir(temp_dir)
            if not items:
                print(f"[Skip] {selected_zip} is empty after extraction.")
                continue

            subdirs = [item for item in items if os.path.isdir(os.path.join(temp_dir, item))]
            if len(subdirs) == 1:
                project_root = os.path.join(temp_dir, subdirs[0])
            else:
                project_root = temp_dir

            print(f"\n===============================")
            print(f" Deploying: {os.path.basename(selected_zip)}")
            print(f"===============================")
            try:
                deploy_project(project_root)
            except subprocess.CalledProcessError as e:
                print(f"[Error] Deployment failed: {e}")
            print(f"[Done] Project {os.path.basename(selected_zip)} has been deployed.\n")


if __name__ == "__main__":
    choose_and_deploy()
