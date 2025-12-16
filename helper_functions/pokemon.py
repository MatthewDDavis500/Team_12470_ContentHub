def format_pokemon_data(data):
    image = data['sprites']['other']['official-artwork']['front_default']
    if not image:
        image = data['sprites']['front_default']

    formatted_data = {
        "img_Official Artwork": image,
        
        "Basic Info": {
            "Name": data['name'].capitalize(),
            "ID": f"#{data['id']}"
        },

        "Physical Traits": {
            "Height": f"{data['height'] / 10} m",
            "Weight": f"{data['weight'] / 10} kg"
        },

        "Combat Info": {
             "Types": ", ".join([t['type']['name'].title() for t in data['types']]),
             "Abilities": ", ".join([a['ability']['name'].replace('-', ' ').title() for a in data['abilities']])
        }
    }

    stats_dict = {}
    for s in data['stats']:
        stat_name = s['stat']['name'].replace('-', ' ').title()
        if stat_name == "Hp": stat_name = "HP"
        stats_dict[stat_name] = s['base_stat']
    
    formatted_data["Base Stats"] = stats_dict
    
    return formatted_data