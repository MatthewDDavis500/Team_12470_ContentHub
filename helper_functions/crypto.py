def format_crypto_data(data):
    price = float(data['data']['amount'])
    currency = data['data']['currency']
    base = data['data']['base']

    logo_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Bitcoin.svg/128px-Bitcoin.svg.png"

    formatted_data = {
        "img_Logo": logo_url,

        "Market Data": {
            "Current Price": f"${price:,.2f}",
            "Currency": currency,
            "Asset Code": base
        },
        "Asset Information": {
            "Name": "Bitcoin",
            "Category": "Cryptocurrency",
            "Provider": "Coinbase Public API"
        }
    }

    return formatted_data