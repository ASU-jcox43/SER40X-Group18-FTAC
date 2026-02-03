# Bylaw Dashboard

This project is a **municipality dashboard** for analyzing food truck friendliness scores across Canadian cities. It allows users to filter municipalities by business type, province, and minimum score, sort results, and view detailed information about each municipality.

---

## Features

- Filter municipalities by:
  - Business Type (Food Truck, Cottage Food, Catering)
  - Province
  - Minimum Friendliness Score
- Sort results by score (high to low, low to high)
- Click on a municipality to see:
  - Friendliness summary
  - Key requirements
  - Score breakdown
- Fully responsive dashboard layout

---

## Project Structure

dashboard/
│── index.html # Main dashboard page
│── style.css # CSS styling
│── script.js # JavaScript functionality
│── testdata/ # JSON data files for municipalities
│── assets/ # Logo and other images

## Running the Project

## Running the Project

Since this project uses **fetch()** to load JSON files, it must be run on a **local server** (cannot be opened directly in the browser as `file://`). You can use Python’s built-in HTTP server.

1. Open a terminal and navigate to the `dashboard/` folder:

```bash
cd path/to/dashboard

2. Start the Python HTTP server:
python3 -m http.server 8000

3. Open your browser and type in:
http://localhost:8000

4. Dashboard functionality should load. Click "Apply Filters", select sorting options and click muncipality rows to see detailed breakdowns.


Dependencies
None.
Works on modern browsers (Chrome, Firefox, Edge).