import concurrent.futures
from .registry import WIDGET_REGISTRY


# --- AUTH


def login_user(conn, username, password):
    cursor = conn.cursor(dictionary=True)
    query = "SELECT * FROM users WHERE username = %s AND password_hash = %s"
    cursor.execute(query, (username, password))
    return cursor.fetchone()


def signup_user(conn, username, password):
    cursor = conn.cursor()
    try:
        query = "INSERT INTO users (username, password_hash) VALUES (%s, %s)"
        cursor.execute(query, (username, password))
        conn.commit()
        return True
    except:
        return False


# --- SETTINGS (This section handles user-specific widget settings, including saving and retrieving them.)  ---


def get_widget_settings(conn, user_widget_id):
    """
    Fetches custom settings for a specific widget instance.
    Returns: {'city': 'Paris'}
    """
    cursor = conn.cursor()
    query = "SELECT setting_name, setting_value FROM user_widget_settings WHERE user_widget_id = %s"
    cursor.execute(query, (user_widget_id,))

    settings = {}
    for row in cursor.fetchall():
        settings[row[0]] = row[1]
    return settings


"""
    Saves form data into the settings table. Or at least it should. 
"""

def save_widget_settings(conn, user_widget_id, form_data):

    cursor = conn.cursor()
    # Clear old settings for this widget this should prevent duplicates
    cursor.execute(
        "DELETE FROM user_widget_settings WHERE user_widget_id = %s", (
            user_widget_id,)
    )

    # Inserts the new settings
    for key, value in form_data.items():
        if value and value.strip():
            cursor.execute(
                """
                INSERT INTO user_widget_settings (user_widget_id, setting_name, setting_value)
                VALUES (%s, %s, %s)
                """,
                (user_widget_id, key, value),
            )
    conn.commit()

"""
    Returns the required fields for a widget instance.
    Used to build the form dynamically.
"""
def get_widget_config_fields(conn, user_widget_id):

    cursor = conn.cursor()
    # This is to get the generic name (e.g., "Weather" or "Pokemon") this is basically the widget identifier name that was given when it was created in the registry
    query = """
        SELECT w.name 
        FROM user_widgets uw
        JOIN widgets w ON uw.widget_id = w.id
        WHERE uw.id = %s
    """
    cursor.execute(query, (user_widget_id,))
    result = cursor.fetchone()
    # No result means invalid widget instance id 
    if not result:
        return {}, {}

    name = result[0]
    registry_entry = WIDGET_REGISTRY.get(name)

    if not registry_entry:
        return {}, {}

    # Return (Widget Name, Config Dictionary)
    return name, registry_entry.get("config", {})


# --- DASHBOARD LOGIC (This wasn't working with settings in my earlier version, but there should be no problem now.) ---


# Returns a list of all available widget names
def get_available_widgets():
    return list(WIDGET_REGISTRY.keys())

# Adds a widget to a user's dashboard (if not already added) ---
def add_widget_to_user(conn, user_id, widget_name):
    cursor = conn.cursor()

    # This gets Widget ID from the name
    cursor.execute("SELECT id FROM widgets WHERE name = %s", (widget_name,))
    res = cursor.fetchone()
    if not res:
        return  # Widget name doesn't exist
    widget_id = res[0]

    # CHECK IF ALREADY EXISTS, I didn't have this earlier and it was causing duplicates
    # We look for a row that matches BOTH the user and the widget
    cursor.execute(
        """
        SELECT id FROM user_widgets 
        WHERE user_id = %s AND widget_id = %s """,
        (user_id, widget_id),
    )

    existing = cursor.fetchone()

    if existing:
        print(f"Skipping: User {user_id} already has {widget_name}")
        return 

    # Link to User (This actually adds the widget to the user's dashboard list)
    try:
        cursor.execute(
            "INSERT INTO user_widgets (user_id, widget_id) VALUES (%s, %s)",
            (user_id, widget_id),
        )
        conn.commit()
    except Exception as e:
        print(f"Error adding widget: {e}")


def get_user_dashboard(conn, user_id):
    cursor = conn.cursor()
    
    # FETCH ALL WIDGET METADATA FIRST 
    query = """
        SELECT uw.id, w.name 
        FROM user_widgets uw
        JOIN widgets w ON uw.widget_id = w.id
        WHERE uw.user_id = %s
    """
    cursor.execute(query, (user_id,))
    rows = cursor.fetchall()
    
    
    widget_tasks = []
    for row in rows:
        uw_id = row[0]
        name = row[1]
        if name in WIDGET_REGISTRY:
            # Get settings immediately
            settings = get_widget_settings(conn, uw_id)
            # Store the data we need to run the function later
            widget_tasks.append({
                "id": uw_id,
                "name": name,
                "settings": settings,
                "func": WIDGET_REGISTRY[name]['summary'],
                "has_settings": len(WIDGET_REGISTRY[name].get('config', {})) > 0
            })

    results = []
    
    def process_widget(task):
        try:
            summary_data = task['func'](task['settings'])
        except:
            summary_data = {"text": "Error", "image": ""}
            
        return {
            "id": task['id'],
            "name": task['name'],
            "summary": summary_data,
            "has_settings": task['has_settings']
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = list(executor.map(process_widget, widget_tasks))
        
    return results

# This gets the detailed data for a specific widget instance ---
def get_widget_detail_data(conn, instance_id):
    cursor = conn.cursor()
    query = """
        SELECT w.name 
        FROM user_widgets uw
        JOIN widgets w ON uw.widget_id = w.id
        WHERE uw.id = %s
        """
    cursor.execute(query, (instance_id,))
    res = cursor.fetchone()

    if res and res[0] in WIDGET_REGISTRY:
        name = res[0]
        # Fetch settings
        settings = get_widget_settings(conn, instance_id)
        # Pass to detail function
        return name, WIDGET_REGISTRY[name]["detail"](settings)

    return "Error", {}


def sync_widgets(conn):
    cursor = conn.cursor()
    for name in WIDGET_REGISTRY:
        cursor.execute("SELECT id FROM widgets WHERE name = %s", (name,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO widgets (name) VALUES (%s)", (name,))
    conn.commit()
