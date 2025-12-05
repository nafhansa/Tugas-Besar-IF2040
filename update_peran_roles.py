"""
Utility to turn the third column in Peran inserts into role categories (Lead/Co-Lead/Supporting/Antagonist/Cameo/Ensemble).
Only updates rows where the role column currently holds a placeholder (previously character names or 'Lead').
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Dict, Tuple

PROJECT_ROOT = Path(__file__).parent
SQL_PATH = PROJECT_ROOT / "IF2040_Milestone3_K1_G11.sql"

# Map specific (actor, title) pairs to role categories.
PAIR_ROLE_MAP: Dict[Tuple[str, str], str] = {
    # MCU & superheroes
    ("Robert Downey Jr.", "Iron Man"): "Lead",
    ("Robert Downey Jr.", "Iron Man 2"): "Lead",
    ("Robert Downey Jr.", "Iron Man 3"): "Lead",
    ("Robert Downey Jr.", "The Avengers"): "Lead",
    ("Chris Evans", "Avengers: Age of Ultron"): "Ensemble",
    ("Chris Hemsworth", "Avengers: Infinity War"): "Ensemble",
    ("Mark Ruffalo", "Avengers: Endgame"): "Ensemble",
    ("Chris Hemsworth", "Thor"): "Lead",
    ("Chris Hemsworth", "Thor: The Dark World"): "Lead",
    ("Chris Hemsworth", "Thor: Ragnarok"): "Lead",
    ("Chris Evans", "Captain America: The First Avenger"): "Lead",
    ("Chris Evans", "Captain America: The Winter Soldier"): "Lead",
    ("Chris Evans", "Captain America: Civil War"): "Lead",
    ("Chadwick Boseman", "Black Panther"): "Lead",
    ("Benedict Cumberbatch", "Doctor Strange"): "Lead",
    ("Benedict Cumberbatch", "Doctor Strange in the Multiverse of Madness"): "Lead",
    ("Tom Holland", "Spider-Man: Homecoming"): "Lead",
    ("Tom Holland", "Spider-Man: Far From Home"): "Lead",
    ("Tom Holland", "Spider-Man: No Way Home"): "Lead",
    ("Paul Rudd", "Ant-Man"): "Lead",
    ("Paul Rudd", "Ant-Man and the Wasp"): "Lead",
    ("Scarlett Johansson", "Black Widow"): "Lead",
    ("Simu Liu", "Shang-Chi and the Legend of the Ten Rings"): "Lead",
    ("Gemma Chan", "Eternals"): "Co-Lead",
    ("Brie Larson", "Captain Marvel"): "Lead",
    ("Letitia Wright", "Black Panther: Wakanda Forever"): "Lead",
    ("Chris Pratt", "Guardians of the Galaxy"): "Lead",
    ("Chris Pratt", "Guardians of the Galaxy Vol. 2"): "Lead",
    ("Chris Pratt", "Guardians of the Galaxy Vol. 3"): "Lead",
    ("Tom Hiddleston", "Loki"): "Lead",
    ("Elizabeth Olsen", "WandaVision"): "Lead",
    ("Jeremy Renner", "Hawkeye"): "Lead",
    ("Oscar Isaac", "Moon Knight"): "Lead",
    ("Tatiana Maslany", "She-Hulk: Attorney at Law"): "Lead",
    ("Anthony Mackie", "The Falcon and the Winter Soldier"): "Lead",
    ("Charlie Cox", "Daredevil"): "Lead",
    ("Krysten Ritter", "Jessica Jones"): "Lead",
    ("Jon Bernthal", "The Punisher"): "Lead",
    ("Clark Gregg", "Agents of S.H.I.E.L.D."): "Lead",
    ("Mike Colter", "Luke Cage"): "Lead",
    ("Finn Jones", "Iron Fist"): "Lead",
    ("Samuel L. Jackson", "Secret Invasion"): "Lead",
    ("Jeff Goldblum", "What If...?"): "Cameo",
    ("Ben McKenzie", "Gotham"): "Lead",
    ("Brenton Thwaites", "Titans"): "Lead",
    ("Brendan Fraser", "Doom Patrol"): "Lead",
    ("Stephen Amell", "Arrow"): "Lead",
    ("Grant Gustin", "The Flash"): "Lead",
    ("Caity Lotz", "DCs Legends of Tomorrow"): "Lead",
    ("Tom Welling", "Smallville"): "Lead",
    # Big franchises / films
    ("Leonardo DiCaprio", "Inception"): "Lead",
    ("Christian Bale", "The Dark Knight"): "Lead",
    ("Christian Bale", "The Dark Knight Rises"): "Lead",
    ("Christian Bale", "Batman Begins"): "Lead",
    ("Matthew McConaughey", "Interstellar"): "Lead",
    ("Fionn Whitehead", "Dunkirk"): "Co-Lead",
    ("John David Washington", "Tenet"): "Lead",
    ("Cillian Murphy", "Oppenheimer"): "Lead",
    ("Joaquin Phoenix", "Joker"): "Lead",
    ("Leonardo DiCaprio", "Titanic"): "Lead",
    ("Sam Worthington", "Avatar"): "Lead",
    ("Sam Worthington", "Avatar: The Way of Water"): "Lead",
    ("Keanu Reeves", "The Matrix"): "Lead",
    ("Keanu Reeves", "The Matrix Reloaded"): "Lead",
    ("Keanu Reeves", "The Matrix Revolutions"): "Lead",
    ("Keanu Reeves", "John Wick"): "Lead",
    ("Keanu Reeves", "John Wick: Chapter 2"): "Lead",
    ("Keanu Reeves", "John Wick: Chapter 3 - Parabellum"): "Lead",
    ("Keanu Reeves", "John Wick: Chapter 4"): "Lead",
    ("Tom Cruise", "Mission: Impossible"): "Lead",
    ("Tom Cruise", "Mission: Impossible - Fallout"): "Lead",
    ("Tom Cruise", "Top Gun"): "Lead",
    ("Tom Cruise", "Top Gun: Maverick"): "Lead",
    ("Russell Crowe", "Gladiator"): "Lead",
    ("Al Pacino", "The Godfather"): "Lead",
    ("Al Pacino", "The Godfather Part II"): "Lead",
    ("John Travolta", "Pulp Fiction"): "Co-Lead",
    ("Brad Pitt", "Fight Club"): "Co-Lead",
    ("Tom Hanks", "Forrest Gump"): "Lead",
    ("Tim Robbins", "The Shawshank Redemption"): "Lead",
    ("Song Kang-ho", "Parasite"): "Ensemble",
    ("Gong Yoo", "Train to Busan"): "Lead",
    ("Iko Uwais", "The Raid"): "Lead",
    ("Iko Uwais", "The Raid 2"): "Lead",
    ("Abimana Aryasatya", "Gundala"): "Lead",
    ("Pevita Pearce", "Sri Asih"): "Lead",
    ("Tara Basro", "Pengabdi Setan"): "Lead",
    ("Tara Basro", "Pengabdi Setan 2: Communion"): "Lead",
    ("Tissa Biani", "KKN di Desa Penari"): "Lead",
    ("Cut Mini", "Laskar Pelangi"): "Supporting",
    ("Reza Rahadian", "Habibie & Ainun"): "Lead",
    ("Iqbaal Ramadhan", "Dilan 1990"): "Lead",
    ("Iqbaal Ramadhan", "Dilan 1991"): "Lead",
    ("Iqbaal Ramadhan", "Milea: Suara dari Dilan"): "Lead",
    ("Dian Sastrowardoyo", "Ada Apa Dengan Cinta?"): "Lead",
    ("Dian Sastrowardoyo", "Ada Apa Dengan Cinta? 2"): "Lead",
    ("Ernest Prakasa", "Cek Toko Sebelah"): "Lead",
    ("Bene Dion", "Ngeri-Ngeri Sedap"): "Lead",
    ("Iqbaal Ramadhan", "Mencuri Raden Saleh"): "Lead",
    ("Abimana Aryasatya", "The Big 4"): "Lead",
    ("Tara Basro", "Perempuan Tanah Jahanam"): "Lead",
    ("Rio Dewanto", "Satu Suro"): "Lead",
    ("Chelsea Islan", "Sebelum Iblis Menjemput"): "Lead",
    ("Ario Bayu", "Ratu Ilmu Hitam"): "Lead",
    ("Luna Maya", "Suzanna: Bernapas dalam Kubur"): "Lead",
    ("Jun Ji-hyun", "My Sassy Girl"): "Lead",
    ("Choi Min-sik", "Oldboy"): "Lead",
    ("Song Kang-ho", "Memories of Murder"): "Lead",
    ("Steven Yeun", "Minari"): "Lead",
    ("Tang Wei", "Decision to Leave"): "Co-Lead",
    ("Song Kang-ho", "Broker"): "Co-Lead",
    ("Yoo Ah-in", "Burning"): "Lead",
    ("Ryu Seung-ryong", "Extreme Job"): "Lead",
    ("Jo Jung-suk", "Exit"): "Lead",
    ("Cha Tae-hyun", "Along With the Gods: The Two Worlds"): "Lead",
    ("Ha Jung-woo", "Along With the Gods: The Last 49 Days"): "Lead",
    ("Kwak Do-won", "The Wailing"): "Lead",
    ("Lee Byung-hun", "I Saw the Devil"): "Antagonist",
    ("Song Kang-ho", "A Taxi Driver"): "Lead",
    ("Ryu Seung-ryong", "Miracle in Cell No. 7"): "Lead",
    ("Daniel Radcliffe", "Harry Potter and the Sorcerers Stone"): "Lead",
    ("Daniel Radcliffe", "Harry Potter and the Chamber of Secrets"): "Lead",
    ("Daniel Radcliffe", "Harry Potter and the Prisoner of Azkaban"): "Lead",
    ("Daniel Radcliffe", "Harry Potter and the Goblet of Fire"): "Lead",
    ("Daniel Radcliffe", "Harry Potter and the Order of the Phoenix"): "Lead",
    ("Daniel Radcliffe", "Harry Potter and the Half-Blood Prince"): "Lead",
    ("Daniel Radcliffe", "Harry Potter and the Deathly Hallows: Part 1"): "Lead",
    ("Daniel Radcliffe", "Harry Potter and the Deathly Hallows: Part 2"): "Lead",
    ("Eddie Redmayne", "Fantastic Beasts and Where to Find Them"): "Lead",
    ("Eddie Redmayne", "Fantastic Beasts: The Crimes of Grindelwald"): "Lead",
    ("Eddie Redmayne", "Fantastic Beasts: The Secrets of Dumbledore"): "Lead",
    ("Elijah Wood", "The Lord of the Rings: The Fellowship of the Ring"): "Lead",
    ("Elijah Wood", "The Lord of the Rings: The Two Towers"): "Lead",
    ("Elijah Wood", "The Lord of the Rings: The Return of the King"): "Lead",
    ("Martin Freeman", "The Hobbit: An Unexpected Journey"): "Lead",
    ("Martin Freeman", "The Hobbit: The Desolation of Smaug"): "Lead",
    ("Martin Freeman", "The Hobbit: The Battle of the Five Armies"): "Lead",
    ("Johnny Depp", "Pirates of the Caribbean: The Curse of the Black Pearl"): "Lead",
    ("Johnny Depp", "Pirates of the Caribbean: Dead Mans Chest"): "Lead",
    ("Johnny Depp", "Pirates of the Caribbean: At Worlds End"): "Lead",
    ("Sam Neill", "Jurassic Park"): "Lead",
    ("Chris Pratt", "Jurassic World"): "Lead",
    ("Chris Pratt", "Jurassic World: Fallen Kingdom"): "Lead",
    ("Roy Scheider", "Jaws"): "Lead",
    ("Henry Thomas", "E.T. the Extra-Terrestrial"): "Lead",
    ("Michael J. Fox", "Back to the Future"): "Lead",
    ("Michael J. Fox", "Back to the Future Part II"): "Lead",
    ("Michael J. Fox", "Back to the Future Part III"): "Lead",
    ("Mark Hamill", "Star Wars: Episode IV - A New Hope"): "Lead",
    ("Mark Hamill", "Star Wars: Episode V - The Empire Strikes Back"): "Lead",
    ("Mark Hamill", "Star Wars: Episode VI - Return of the Jedi"): "Lead",
    ("Ewan McGregor", "Star Wars: Episode I - The Phantom Menace"): "Lead",
    ("Hayden Christensen", "Star Wars: Episode II - Attack of the Clones"): "Lead",
    ("Hayden Christensen", "Star Wars: Episode III - Revenge of the Sith"): "Lead",
    ("Yuto Uemura", "Tougen Anki"): "Lead",
    # Prestige and streaming series
    ("Bryan Cranston", "Breaking Bad"): "Lead",
    ("Bob Odenkirk", "Better Call Saul"): "Lead",
    ("Emilia Clarke", "Game of Thrones"): "Lead",
    ("Emma DArcy", "House of the Dragon"): "Lead",
    ("Millie Bobby Brown", "Stranger Things"): "Lead",
    ("Henry Cavill", "The Witcher"): "Lead",
    ("Pedro Pascal", "The Mandalorian"): "Lead",
    ("Pedro Pascal", "The Last of Us"): "Lead",
    ("Cillian Murphy", "Peaky Blinders"): "Lead",
    ("Benedict Cumberbatch", "Sherlock"): "Lead",
    ("Michael C. Hall", "Dexter"): "Lead",
    ("Claire Danes", "Homeland"): "Lead",
    ("Evan Rachel Wood", "Westworld"): "Lead",
    ("Matthew McConaughey", "True Detective"): "Lead",
    ("Karl Urban", "The Boys"): "Lead",
    ("Steven Yeun", "Invincible"): "Lead",
    ("Elliot Page", "The Umbrella Academy"): "Lead",
    ("Wagner Moura", "Narcos"): "Lead",
    ("Alvaro Morte", "Money Heist"): "Lead",
    ("Louis Hofmann", "Dark"): "Lead",
    ("Jared Harris", "Chernobyl"): "Lead",
    ("Aaron Paul", "Black Mirror"): "Co-Lead",
    ("Martin Freeman", "Fargo"): "Lead",
    ("Matthew Fox", "Lost"): "Lead",
    ("Wentworth Miller", "Prison Break"): "Lead",
    ("Kiefer Sutherland", "24"): "Lead",
    ("Steve Carell", "The Office"): "Lead",
    ("Jennifer Aniston", "Friends"): "Lead",
    ("Josh Radnor", "How I Met Your Mother"): "Lead",
    ("Jerry Seinfeld", "Seinfeld"): "Lead",
    ("Ed ONeill", "Modern Family"): "Ensemble",
    ("Andy Samberg", "Brooklyn Nine-Nine"): "Lead",
    ("Amy Poehler", "Parks and Recreation"): "Lead",
    ("Gabriel Macht", "Suits"): "Lead",
    ("Hugh Laurie", "House"): "Lead",
    ("Ellen Pompeo", "Greys Anatomy"): "Lead",
    ("William Petersen", "CSI: Crime Scene Investigation"): "Lead",
    ("Mark Harmon", "NCIS"): "Lead",
    ("Mandy Patinkin", "Criminal Minds"): "Lead",
    ("Mariska Hargitay", "Law & Order: Special Victims Unit"): "Lead",
    ("Jensen Ackles", "Supernatural"): "Lead",
    ("Steven Strait", "The Expanse"): "Lead",
    ("Edward James Olmos", "Battlestar Galactica"): "Lead",
    ("Nathan Fillion", "Firefly"): "Lead",
    ("Anna Torv", "Fringe"): "Lead",
    ("Andrew Lincoln", "The Walking Dead"): "Lead",
    ("Kim Dickens", "Fear the Walking Dead"): "Lead",
    ("Mads Mikkelsen", "Hannibal"): "Antagonist",
    ("Travis Fimmel", "Vikings"): "Lead",
    ("Sam Corlett", "Vikings: Valhalla"): "Lead",
    ("Toby Stephens", "Black Sails"): "Lead",
    ("Kevin McKidd", "Rome"): "Lead",
    ("Andy Whitfield", "Spartacus"): "Lead",
    ("Tyler Posey", "Teen Wolf"): "Lead",
    ("KJ Apa", "Riverdale"): "Lead",
    ("Tom Ellis", "Lucifer"): "Lead",
    ("Bae Doona", "Sense8"): "Lead",
    ("Rami Malek", "Mr. Robot"): "Lead",
    ("Olivia Colman", "The Crown"): "Lead",
    ("Elisabeth Moss", "The Handmaids Tale"): "Lead",
    ("Kevin Costner", "Yellowstone"): "Lead",
    ("Jason Bateman", "Ozark"): "Lead",
    ("Jon Hamm", "Mad Men"): "Lead",
    ("Steve Buscemi", "Boardwalk Empire"): "Lead",
    ("Kate Winslet", "Mare of Easttown"): "Lead",
    ("Brian Cox", "Succession"): "Lead",
    ("Adam Scott", "Severance"): "Lead",
    ("Diego Luna", "Andor"): "Lead",
    ("Ewan McGregor", "Obi-Wan Kenobi"): "Lead",
    ("Rosario Dawson", "Ahsoka"): "Lead",
    ("Sonequa Martin-Green", "Star Trek: Discovery"): "Lead",
    ("Patrick Stewart", "Star Trek: Picard"): "Lead",
    ("Freddie Highmore", "The Good Doctor"): "Lead",
    ("Milo Ventimiglia", "This Is Us"): "Co-Lead",
    ("Simon Baker", "The Mentalist"): "Lead",
    ("Jim Caviezel", "Person of Interest"): "Lead",
    ("Jonny Lee Miller", "Elementary"): "Lead",
    ("Dafne Keen", "His Dark Materials"): "Lead",
    ("Tom Sturridge", "The Sandman"): "Lead",
    ("Anthony Mackie", "Love, Death & Robots"): "Cameo",
    ("Hailee Steinfeld", "Arcane"): "Lead",
    ("Richard Armitage", "Castlevania"): "Lead",
    ("Jack De Sena", "The Dragon Prince"): "Lead",
    ("Zach Tyler Eisen", "Avatar: The Last Airbender"): "Lead",
    ("Janet Varney", "The Legend of Korra"): "Lead",
    ("Lee Jung-jae", "Squid Game"): "Lead",
    ("Ju Ji-hoon", "Kingdom"): "Lead",
    ("Hyun Bin", "Crash Landing on You"): "Lead",
    ("Gong Yoo", "Goblin"): "Lead",
    ("Song Joong-ki", "Descendants of the Sun"): "Lead",
    ("Park Seo-joon", "Itaewon Class"): "Lead",
    ("Song Joong-ki", "Vincenzo"): "Lead",
    ("Park Bo-gum", "Reply 1988"): "Ensemble",
    ("Lee Je-hoon", "Signal"): "Lead",
    ("Jo Jung-suk", "Hospital Playlist"): "Ensemble",
    ("Lee Sun-kyun", "My Mister"): "Lead",
    ("Park Ji-hu", "All of Us Are Dead"): "Co-Lead",
    ("Song Kang", "Sweet Home"): "Lead",
    ("Park Eun-bin", "Extraordinary Attorney Woo"): "Lead",
    ("Yoo Ah-in", "Hellbound"): "Lead",
    # Anime
    ("Yuki Kaji", "Attack on Titan"): "Lead",
    ("Junko Takeuchi", "Naruto"): "Lead",
    ("Junko Takeuchi", "Naruto Shippuden"): "Lead",
    ("Masakazu Morita", "Bleach"): "Lead",
    ("Mayumi Tanaka", "One Piece"): "Lead",
    ("Natsuki Hanae", "Demon Slayer"): "Lead",
    ("Junya Enoki", "Jujutsu Kaisen"): "Lead",
    ("Daiki Yamashita", "My Hero Academia"): "Lead",
    ("Romi Park", "Fullmetal Alchemist: Brotherhood"): "Lead",
    ("Mamoru Miyano", "Death Note"): "Antagonist",
    ("Megumi Han", "Hunter x Hunter"): "Lead",
    ("Kikunosuke Toya", "Chainsaw Man"): "Lead",
    ("Natsuki Hanae", "Tokyo Ghoul"): "Lead",
    ("Yoshitsugu Matsuoka", "Sword Art Online"): "Lead",
    ("Gakuto Kajiwara", "Black Clover"): "Lead",
    ("Tetsuya Kakihara", "Fairy Tail"): "Lead",
    ("Ayumu Murase", "Haikyuu!!"): "Lead",
    ("Kazuki Ura", "Blue Lock"): "Lead",
    ("Takuya Eguchi", "Spy x Family"): "Lead",
    ("Yusuke Kobayashi", "Dr. Stone"): "Lead",
    ("Setsuo Ito", "Mob Psycho 100"): "Lead",
    ("Yuto Uemura", "Vinland Saga"): "Lead",
    # Local series
    ("Reza Rahadian", "Layangan Putus"): "Lead",
    ("Dian Sastrowardoyo", "Gadis Kretek"): "Lead",
    ("Chelsea Islan", "Tira"): "Lead",
    ("Giorgino Abraham", "Turn On"): "Lead",
    ("Refal Hady", "Wedding Agreement The Series"): "Lead",
    ("Adhisty Zara", "Virgin The Series"): "Lead",
}

# Title-wide defaults when pair-specific mapping is missing.
TITLE_FALLBACK_MAP: Dict[str, str] = {
    "The Avengers": "Ensemble",
    "Avengers: Age of Ultron": "Ensemble",
    "Avengers: Infinity War": "Ensemble",
    "Avengers: Endgame": "Ensemble",
    "Guardians of the Galaxy": "Ensemble",
    "Guardians of the Galaxy Vol. 2": "Ensemble",
    "Guardians of the Galaxy Vol. 3": "Ensemble",
    "Harry Potter and the Sorcerers Stone": "Lead",
    "Harry Potter and the Chamber of Secrets": "Lead",
    "Harry Potter and the Prisoner of Azkaban": "Lead",
    "Harry Potter and the Goblet of Fire": "Lead",
    "Harry Potter and the Order of the Phoenix": "Lead",
    "Harry Potter and the Half-Blood Prince": "Lead",
    "Harry Potter and the Deathly Hallows: Part 1": "Lead",
    "Harry Potter and the Deathly Hallows: Part 2": "Lead",
    "Friends": "Ensemble",
    "Modern Family": "Ensemble",
    "Hospital Playlist": "Ensemble",
    "Money Heist": "Ensemble",
    "Parasite": "Ensemble",
}

ROLE_FALLBACK = ["Supporting", "Antagonist", "Co-Lead", "Cameo", "Ensemble"]

peran_pattern = re.compile(
    r"INSERT IGNORE INTO `Peran` VALUES \('(?P<actor>[^']*)'\s*,\s*'(?P<title>[^']*)'\s*,\s*'(?P<role>[^']*)'\);",
    re.MULTILINE,
)

def escape_sql(value: str) -> str:
    """Escape single quotes for SQL string literals."""
    return value.replace("'", "\\'")

def main() -> None:
    text = SQL_PATH.read_text(encoding="utf-8")
    total = 0
    updated = 0
    fallback_index = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal total, updated, fallback_index
        actor = match.group("actor")
        title = match.group("title")
        role = match.group("role")
        total += 1

        if role not in {"Lead", "Supporting", "Co-Lead", "Antagonist", "Cameo", "Ensemble"}:
            # Treat character names (or any other strings) as placeholders to be replaced.
            pass
        else:
            # Already a category, keep it.
            return match.group(0)

        mapped_role = PAIR_ROLE_MAP.get((actor, title))
        if mapped_role is None:
            mapped_role = TITLE_FALLBACK_MAP.get(title)

        if mapped_role is None:
            mapped_role = ROLE_FALLBACK[fallback_index % len(ROLE_FALLBACK)]
            fallback_index += 1

        updated += 1
        escaped_role = escape_sql(mapped_role)
        return f"INSERT IGNORE INTO `Peran` VALUES ('{actor}','{title}','{escaped_role}');"

    new_text = peran_pattern.sub(replace, text)

    if new_text == text:
        print("No changes applied.")
        return

    SQL_PATH.write_text(new_text, encoding="utf-8")
    print(f"Processed {total} Peran rows; updated {updated} placeholders.")


if __name__ == "__main__":
    main()
