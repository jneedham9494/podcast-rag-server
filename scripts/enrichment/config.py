"""
Configuration constants for transcript enrichment.
"""

from typing import Dict, List

# Known hosts/speakers per podcast
KNOWN_SPEAKERS: Dict[str, Dict] = {
    'TRUE ANON TRUTH FEED': {
        'hosts': ['Brace Belden', 'Liz Franczak'],
        'producer': 'Yung Chomsky',
        'aliases': {
            'brace': 'Brace Belden',
            'liz': 'Liz Franczak',
            'chomsky': 'Yung Chomsky',
            'young chomsky': 'Yung Chomsky',
        }
    },
    'Chapo Trap House': {
        'hosts': [
            'Will Menaker', 'Matt Christman', 'Felix Biederman',
            "Amber A'Lee Frost", 'Virgil Texas'
        ],
        'aliases': {
            'will': 'Will Menaker',
            'matt': 'Matt Christman',
            'felix': 'Felix Biederman',
            'amber': "Amber A'Lee Frost",
        }
    },
    'The Adam Friedland Show Podcast': {
        'hosts': ['Adam Friedland', 'Nick Mullen'],
        'aliases': {
            'adam': 'Adam Friedland',
            'nick': 'Nick Mullen',
        }
    },
    'Blowback': {
        'hosts': ['Brendan James', 'Noah Kulwin'],
        'aliases': {
            'brendan': 'Brendan James',
            'noah': 'Noah Kulwin',
        }
    },
    'Hello Internet': {
        'hosts': ['CGP Grey', 'Brady Haran'],
        'aliases': {
            'grey': 'CGP Grey',
            'brady': 'Brady Haran',
        }
    },
    'Multipolarity': {
        'hosts': ['Marshall Kosloff', 'Justin Ling'],
        'aliases': {}
    },
    'RHLSTP with Richard Herring': {
        'hosts': ['Richard Herring'],
        'aliases': {
            'richard': 'Richard Herring',
        }
    },
    'The Louis Theroux Podcast': {
        'hosts': ['Louis Theroux'],
        'aliases': {
            'louis': 'Louis Theroux',
        }
    },
}

# Topic taxonomy for classification
TOPIC_TAXONOMY: List[str] = [
    "US Politics",
    "International Politics",
    "Media & Journalism",
    "History",
    "Conspiracy Theories",
    "Technology",
    "Economics & Finance",
    "Crime & Justice",
    "Culture & Entertainment",
    "Science",
    "Health",
    "Religion",
    "Military & Intelligence",
    "Environment",
    "Sports",
    "Personal Stories",
]
