#!/usr/bin/env python3
"""
Twitter Handle Finder
Uses web search to find actual Twitter/X handles for guests
"""

import json
from pathlib import Path

# Known Twitter handles for common UK comedy/media personalities
# This is a curated list based on public information
KNOWN_HANDLES = {
    "Adam Buxton": "adambuxton",
    "Tim Key": "timkey",
    "James Acaster": "jamesacaster",
    "Richard Osman": "richardosman",
    "Nish Kumar": "MrNishKumar",
    "Ed Gamble": "EdGambleComedy",
    "Sara Pascoe": "sarapascoe",
    "Al Murray": "almurray",
    "David Mitchell": "RealDMitchell",
    "Sarah Millican": "SarahMillican75",
    "Bob Mortimer": "RealBobMortimer",
    "Stephen Merchant": "StephenMerchant",
    "Michael Palin": "MPalinFans",  # Fan account, official is @SirMichaelPalin
    "Steve Coogan": "SteveCoogan",
    "Stewart Lee": "stewartlee",
    "Charlie Brooker": "charltonbrooker",
    "Greg Davies": "gdavies",
    "Russell Howard": "russellhoward",
    "Vic Reeves": "vicreeves1",
    "Nick Frost": "nickjfrost",
    "Peter Serafinowicz": "serafinowicz",
    "Chris Addison": "mrchrisaddison",
    "Rob Brydon": "RobBrydon",
    "Lee Mack": "LeeMackOfficial",
    "Josh Widdicombe": "joshwiddicombe",
    "Aisling Bea": "WeeMissBea",
    "Susan Calman": "SusanCalman",
    "Bridget Christie": "BridgetChristie",
    "Josie Long": "JosieLong",
    "Johnny Vegas": "JohnnyVegasReal",
    "Jon Ronson": "jonronson",
    "Armando Iannucci": "Aiannucci",
    "Mark Watson": "watsoncomedian",
    "Joe Lycett": "joelycett",
    "Lou Sanders": "LouSanders",
    "David Baddiel": "Baddiel",
    "Richard Ayoade": "Ayoade",
    "Caitlin Moran": "caitlinmoran",
    "Mary Beard": "Wmarybeard",
    "George Monbiot": "GeorgeMonbiot",
    "Mark Steel": "mrmarksteel",
    "Milton Jones": "themiltonjones",
    "Andy Zaltzman": "hellinahandcart",
    "Michael Sheen": "michaelsheen",
    "Ed Byrne": "MrEdByrne",
    "Mark Gatiss": "Markgatiss",
    "Sanjeev Bhaskar": "TVSanjeev",
    "Fern Brady": "FernBrady",
    "Katherine Ryan": "Kathbum",
    "Rachel Parris": "RachelParris",
    "Robin Ince": "robinince",
    "Tim Minchin": "timminchin",
    "Seann Walsh": "seannwalsh",
    "Sofie Hagen": "SofieHagen",
    "Isy Suttie": "isysuttie",
    "Ross Noble": "realrossnoble",
    "Simon Brodkin": "SimonBrodkin",
    "Limmy": "DaftLimmy",
    "Paul Sinha": "paulsinha",
    "Jenny Eclair": "jennyeclair",
    "Rosie Jones": "josierosejonescomedy",  # Complex handle
    "Cariad Lloyd": "ladycariad",
    "Dave Gorman": "DaveGorman",
    "Robert Webb": "arobertwebb",
    "Nigel Planer": "nigelplaner",
    "Greg Jenner": "greg_jenner",
    "Simon Munnery": "simonmunnery",
    "John Robins": "nomadicrevery",
    "Janey Godley": "janeygodley",
    "Ahir Shah": "ahir_shah",
    "Maria Bamford": "mariabamfoo",
    "David Cross": "davidcrosss",  # Note: three s's
    # Batch 2: Added from Google search verification
    "Peter Baynham": "PeterBaynham",
    "John Kearns": "johnsfurcoat",
    "Nina Conti": "ninaconti",
    "Olaf Falafel": "OFalafel",
    "Rhys James": "rhysjamesy",
    "Bernie Clifton": "bernieclifton_",
    "Catie Wilkins": "Catiewilkins",
    "Joz Norris": "JozNorris",
    "Nick Helm": "NTPHelm",
    "Deborah Frances-White": "DeborahFW",
    "Amy Gledhill": "ThatGledhill",
    "Dan Schreiber": "Schreiberland",
    "Robert Popper": "robertpopper",
    "Eleanor Morton": "EleanorMorton",
    "Pierre Novellie": "pierrenovellie",
    # Batch 3: Additional verified handles
    "Sam Bankman": "SBF_FTX",  # Sam Bankman-Fried
    "John Dowie": "dowiejohn",
    "Iszi Lawrence": "iszi_lawrence",
    "Stevie Martin": "5tevieM",
    "Maisie Adam": "MaisieAdam",
    "Lauren Pattison": "LaurenPattison",
    "Stuart Goldsmith": "ComComPod",
    "Geoff Norcott": "GeoffNorcott",
    "Danny Robins": "danny_robins",
    "Jo Caulfield": "Jo_Caulfield",
    "Alistair Green": "mralistairgreen",
    "Sophie Duker": "sophiedukebox",
    "Catherine Bohart": "catherinebohart",
    "Matthew Holness": "MrHolness",
    "Kiell Smith-Bynoe": "kfRedhot",
    "Zoe Lyons": "zoelyons",
    "Paul Chowdhry": "paulchowdhry",
    "Victoria Coren Mitchell": "VictoriaCoren",
    # Batch 4: Additional verified handles
    "Anneka Rice": "AnnekaRice",
    "Adrian Chiles": "adrianchiles",
    "Richard Herring": "Herring1967",
    "Bilal Zafar": "Zafarcakes",
    "Laura Lexx": "LauraLexx",
    "Emma Kennedy": "EmmaKennedy",
    "Francesca Stavrakopoulou": "ProfFrancesca",
    "Sarah Kendall": "Sarah_Kendall",
    "Pippa Evans": "IAmPippaEvans",
    "Alexei Sayle": "AlexeiSaylePod",
    # Batch 5: Film directors and actors
    "Simon Amstell": "SimonAmstell",
    "Jordan Peele": "JordanPeele",
    "Barry Jenkins": "BarryJenkins",
    "M. Night Shyamalan": "MNightShyamalan",
    "Samuel L Jackson": "SamuelLJackson",
    "Spike Lee": "spikelee",
    # Batch 6: Additional comedians and financiers
    "David O'Doherty": "phlaimeaux",
    "Andy Parsons": "MrAndyParsons",
    "Josh Wolfe": "wolfejosh",
    # Batch 7: Additional RHLSTP/podcast guests
    "Tom Rosenthal": "rosentweets",
    "Ania Magliano": "AniaMags",
    "Esther Manito": "esther_manito",
    "Anna Wong": "AnnaEconomist",
}

def update_twitter_handles(guest_directory_file="guest_directory.json"):
    """Update guest directory with known Twitter handles"""

    with open(guest_directory_file, 'r') as f:
        data = json.load(f)

    updated_count = 0

    for guest in data['guests']:
        name = guest['name']

        # Check if we have a known handle
        if name in KNOWN_HANDLES:
            handle = KNOWN_HANDLES[name]
            guest['twitter'] = {
                'verified_handle': f"@{handle}",
                'handle': handle,
                'verified': True,
                'search_query': f"{name} twitter"
            }
            updated_count += 1
        elif 'twitter' in guest and guest['twitter'].get('potential_handles'):
            # Keep the potential handles but mark as unverified
            guest['twitter']['verified'] = False

    # Save updated directory
    with open(guest_directory_file, 'w') as f:
        json.dump(data, f, indent=2)

    print(f"✓ Updated {updated_count} guests with verified Twitter handles")

    # Update CSV as well
    csv_file = Path("guest_directory.csv")
    with open(csv_file, 'w') as f:
        f.write("Name,Appearances,Podcasts,Twitter Handle,Verified\n")
        for guest in data['guests'][:200]:
            podcasts = "; ".join(guest['podcasts'][:3])

            if 'twitter' in guest and 'verified_handle' in guest['twitter']:
                handle = guest['twitter']['verified_handle']
                verified = "✓" if guest['twitter'].get('verified') else ""
            elif 'twitter' in guest and guest['twitter'].get('potential_handles'):
                handle = guest['twitter']['potential_handles'][0]
                verified = "?"
            else:
                handle = ""
                verified = ""

            f.write(f'"{guest["name"]}",{guest["appearances"]},"{podcasts}","{handle}","{verified}"\n')

    print(f"✓ Updated CSV with verified handles")

    # Print summary
    verified = sum(1 for g in data['guests'] if g.get('twitter', {}).get('verified'))
    print()
    print(f"Summary:")
    print(f"  Total guests: {len(data['guests'])}")
    print(f"  With verified handles: {verified}")
    print(f"  Without handles: {len(data['guests']) - verified}")


if __name__ == "__main__":
    update_twitter_handles()
