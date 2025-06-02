# Remote Diagnostics Automation Tool

A Streamlit web application to upload machine configuration files, run remote diagnostics concurrently on multiple machines, and view/export diagnostic results.

---

Features:

- Upload JSON machine configuration files via the sidebar.
- Parse and validate machine configurations.
- Create machine instances dynamically based on config.
- Run asynchronous diagnostics on all machines concurrently.
- Display detailed diagnostic results in a searchable, sortable table.
- Export diagnostic results as CSV for further analysis.

---

Installation:

1. Clone the repository:
   ```
   git clone [https://github.com/deepaksuthar40128/RemoteDx](https://github.com/deepaksuthar40128/RemoteDx)
   cd RemoteDx
   ```

2. Create and activate a virtual environment:
 ```
   python3 -m venv venv
   source venv/bin/activate
```

3. Install dependencies:
```
   pip install -r requirements.txt
```

4. Start app
   Run the Streamlit app:
```
   streamlit run app.py
```

---

Run Tests

```
python3 -m unittest discover
```

Steps:
1. Upload your machine configuration JSON file via the sidebar.
2. After successful parsing, click "Start Diagnostics".
3. Wait for the diagnostics to complete; results will show on the main page.
4. Export results as CSV using the "Download Results as CSV" button.

---

Configuration File Format:

The JSON config file should contain an array of machine configuration objects compatible with the diagnostics parser. Each config typically includes:
- name
- ip_address
- machine_type
- other diagnostic parameters
