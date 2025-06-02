# Migration Recovery Instructions for FitBrainLab

Your `migrations/` directory is missing the required `env.py` and related Alembic files, which are necessary for Flask-Migrate to run database migrations.

## How to Fix

1. **Backup your migration scripts**
   - Move any custom migration scripts (like `add_week_columns.py`) to a safe location outside `migrations/`.

2. **Delete the `migrations/` folder**
   - You can do this with:
     ```
     rm -rf migrations
     ```

3. **Re-initialize migrations**
   - Run:
     ```
     flask db init
     ```
   - This will create a fresh `migrations/` folder with all required files (`env.py`, etc).

4. **Restore your migration scripts**
   - Move your custom migration scripts back into the new `migrations/versions/` directory.

5. **Stamp the current DB state (if needed)**
   - If your database schema is already up to date with your models, you may want to stamp it as current:
     ```
     flask db stamp head
     ```

6. **Run migrations**
   - Now you can run:
     ```
     flask db upgrade
     ```

## Notes
- Your `.env` file can remain in the main project directory; Flask-Migrate does not require it to be in `migrations/`.
- If you have a production database, always backup before running destructive operations.

---

If you want me to automate any of these steps, let me know!
