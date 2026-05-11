# Configuration for Tabelog scraper

# List of Japanese chain restaurants to search for (with Japanese names)
CHAIN_RESTAURANTS = [
    "松屋",  # Matsuya
    "ケンタッキー",  # KFC
    "マクドナルド",  # McDonald's
    "吉野家",  # Yoshinoya
    "すき家",  # Sukiya
    "モスバーガー",  # MOS Burger
    "一蘭",  # Ichiran
    "一風堂",  # Ippudo
    "ココイチ",  # CoCo Ichibanya
    "なか卯",  # Nakau
    "はなまるうどん",  # Hanamaru Udon
    "丸亀製麺",  # Marugame Seimen
    "天丼てんや",  # Tendon Tenya
    "かつや",  # Katsuya
    "大戸屋",  # Ootoya
    "ラーメン横丁",  # Ramen Yokocho
    "王将",  # Ōshō
    "ガスト",  # Gusto
    "バーミヤン",  # Bamiyan
    "ジョナサン",  # Jonathan's
    "ステーキガスト",  # Steak Gusto
    "鳥貴族",  # Torikizoku
    "白木屋",  # Shiraki-ya
    "名代富士そば",  # Meishiro Fuji Soba
    "オタフク",  # Otafuku
    "ファーストキッチン", #first_kitchen
]

# Common English aliases. Values are the search terms Tabelog expects.
BRAND_ALIASES = {
    "mcdonalds": "マクドナルド",
    "mcdonald's": "マクドナルド",
    "mc donalds": "マクドナルド",
    "kfc": "ケンタッキー",
    "kentucky": "ケンタッキー",
    "wendy": "ウェンディーズ",
    "wendys": "ウェンディーズ",
    "wendy's": "ウェンディーズ",
    "matsuya": "松屋",
    "yoshinoya": "吉野家",
    "sukiya": "すき家",
    "mosburger": "モスバーガー",
    "mos burger": "モスバーガー",
    "ichiran": "一蘭",
    "ippudo": "一風堂",
    "coco ichibanya": "ココイチ",
    "nakau": "なか卯",
    "marugame": "丸亀製麺",
    "ootoya": "大戸屋",
    "gusto": "ガスト",
    "bamiyan": "バーミヤン",
    "jonathan's": "ジョナサン",
    "torikizoku": "鳥貴族",
    "seizariya": "サイゼリヤ",
    "first_kitchen": "ファーストキッチン",
    "lotteria": "ロッテリア",
}

BRAND_NAME_PATTERNS = {
    "マクドナルド": [
        "マクドナルド",
    ],
    "ケンタッキー": [
        "ケンタッキー",
        "ケンタッキーフライドチキン",
        "KFC",
    ],
    "ウェンディーズ": [
        "ウェンディーズ",
        "Wendy",
        "Wendy's",
    ],
    "モスバーガー": [
        "モスバーガー",
        "MOS BURGER",
        "MOS",
    ],
}

DEFAULT_BURGER_CHAINS = [
    "mcdonalds",
    "wendys",
    "kfc",
    "mosburger",
]
DEFAULT_TEISHOKU_CHAINS = [
    "sukiya",
    "nakau",
    "yoshinoya",
    "matsuya",
    "ootoya",
]

DEFAULT_FAMILY_CHAINS = [
    "seizariya",
    "gusto",
]
# Canonical Tokyo ward list for batch scraping. The first value is the
# command/output slug, the second is Tabelog's city code.
TOKYO_WARDS = [
    ("chiyoda-ku", "C13101"),
    ("chuo-ku", "C13102"),
    ("minato-ku", "C13103"),
    ("shinjuku-ku", "C13104"),
    ("bunkyo-ku", "C13105"),
    ("taito-ku", "C13106"),
    ("sumida-ku", "C13107"),
    ("koto-ku", "C13108"),
    ("shinagawa-ku", "C13109"),
    ("meguro-ku", "C13110"),
    ("ota-ku", "C13111"),
    ("setagaya-ku", "C13112"),
    ("shibuya-ku", "C13113"),
    ("nakano-ku", "C13114"),
    ("suginami-ku", "C13115"),
    ("toshima-ku", "C13116"),
    ("kita-ku", "C13117"),
    ("arakawa-ku", "C13118"),
    ("itabashi-ku", "C13119"),
    ("nerima-ku", "C13120"),
    ("adachi-ku", "C13121"),
    ("katsushika-ku", "C13122"),
    ("edogawa-ku", "C13123"),
]

# Tabelog city codes for Tokyo's 23 special wards.
TOKYO_LOCATIONS = {
    "chiyoda-ku": "C13101",
    "chiyoda": "C13101",
    "chuo-ku": "C13102",
    "chuo": "C13102",
    "minato-ku": "C13103",
    "minato": "C13103",
    "shinjuku-ku": "C13104",
    "shinjuku": "C13104",
    "bunkyo-ku": "C13105",
    "bunkyo": "C13105",
    "taito-ku": "C13106",
    "taito": "C13106",
    "sumida-ku": "C13107",
    "sumida": "C13107",
    "koto-ku": "C13108",
    "koto": "C13108",
    "shinagawa-ku": "C13109",
    "shinagawa": "C13109",
    "meguro-ku": "C13110",
    "meguro": "C13110",
    "ota-ku": "C13111",
    "ota": "C13111",
    "setagaya-ku": "C13112",
    "setagaya": "C13112",
    "shibuya-ku": "C13113",
    "shibuya": "C13113",
    "nakano-ku": "C13114",
    "nakano": "C13114",
    "suginami-ku": "C13115",
    "suginami": "C13115",
    "toshima-ku": "C13116",
    "toshima": "C13116",
    "kita-ku": "C13117",
    "kita": "C13117",
    "arakawa-ku": "C13118",
    "arakawa": "C13118",
    "itabashi-ku": "C13119",
    "itabashi": "C13119",
    "nerima-ku": "C13120",
    "nerima": "C13120",
    "adachi-ku": "C13121",
    "adachi": "C13121",
    "katsushika-ku": "C13122",
    "katsushika": "C13122",
    "edogawa-ku": "C13123",
    "edogawa": "C13123",
}

# Scraping settings
SCRAPE_SETTINGS = {
    "base_url": "https://tabelog.com/tokyo/{location_code}/rstLst/",
    "request_delay": 3,  # seconds between requests
    "timeout": 10,  # request timeout
    "max_pages": 60,  # max pages per chain search
    "headless": True,  # run browser headless
    "search_time": "1930",
    "party_size": "2",
}

# User agent for requests
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

# Output settings
OUTPUT_SETTINGS = {
    "data_dir": "data",
    "csv_file": "data/{stem}.csv",
    "json_file": "data/{stem}.json",
    "cache_dir": "cache",
}
