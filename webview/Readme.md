# Zip Project Deployer

This tool allows you to scan and deploy any Next.js project packaged in `.zip` format. It supports both typical folder structures and root-level projects inside zip archives.

---


## 🧩 Requirements

Make sure you have the following installed:

- **Python 3.7+**
- **Node.js** (preferably v16 or newer)
- **npm** (comes with Node.js)

---

## ✅ Install Python Dependencies

Install required Python packages using pip:

```bash
pip install selenium webdriver-manager
````

Or, using a `requirements.txt`:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Contents of `requirements.txt`:

```
selenium
webdriver-manager
```

---

## ✅ Node.js Project Dependencies

Each project is self-contained and will install its own dependencies during deployment:

```bash
npm install --legacy-peer-deps
```

You do **not** need to install anything globally.

---

## 🚀 How to Use

1. Make sure your zip files are placed in the `zip/` folder.
2. Run the script:

```bash
python deploy.py
```

3. You will see a list of zip files.
4. Enter the number of the zip you want to deploy.
5. The project will be:

   * Unzipped
   * Installed
   * Built
   * Started on [http://localhost:3000](http://localhost:3000)
6. Press `Ctrl+C` to stop the server and choose another zip.

---

## 📦 Optional: Use a Virtual Environment

It’s recommended to use a virtual environment for Python:

```bash
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

Then install requirements:

```bash
pip install -r requirements.txt
```

---

## 🛠 Troubleshooting

* Ensure each zip contains a valid Next.js project with a `package.json` file.
* The script detects the project root automatically. If there's only one folder after extraction, it will use that. Otherwise, it assumes the extracted directory is the root.
* Chrome must be installed for Selenium (ChromeDriver will be auto-managed).

---

## 📄 License

MIT License. Use at your own risk.


