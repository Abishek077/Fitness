# Abishek Peak Transformation Dashboard V2

This V2 uses the uploaded HTML as the visual base: dark black/gray background, orange accent, hero profile, tab navigation, rounded cards, daily checklist, workout/diet/progress sections and charts. The Canva-specific SDK code was removed and replaced with the existing Flask + MySQL backend.

## Run
1. Run `schema.sql` in MySQL Workbench.
2. Open terminal in this folder.
3. `python -m venv .venv`
4. `.venv\Scripts\activate`
5. `pip install -r requirements.txt`
6. Set `MYSQL_PASSWORD` to your MySQL password.
7. `python app.py`
8. Open `http://127.0.0.1:5000`

The dashboard stores daily checkboxes, steps, weight, calories and notes in MySQL and provides weekly CSV/PDF export.
