+++
title = "Visiting/Transfer"
threshold = 1.0

# Words that point at this topic. Matched on the word stem, so
# "ansøgning" also catches "ansøgningen" and "ansøgninger".
triggers = [
    "besöka",
    "besöker",
    "besøg",
    "besøge",
    "besøger",
    "besøke",
    "besøker",
    "flutningar",
    "flutningur",
    "flytja",
    "flytta",
    "flyttar",
    "flytte",
    "flytter",
    "flytur",
    "heimsækir",
    "heimsækja",
    "overføre",
    "overfører",
    "overføring",
    "overføringer",
    "overførsel",
    "overførsler",
    "siirrot",
    "siirto",
    "siirtyä",
    "siirtää",
    "skipta",
    "skiptir",
    "transfer",
    "transfers",
    "vierailee",
    "vierailla",
    "visiting",
    "överför",
    "överföra",
    "överföring",
    "överföringar",
]

# Whole phrases, matched literally. They say far more than any single
# word does, so they are worth 2.0 each unless [weights] says otherwise.
phrases = [
    "move my account",
    "transfer to",
    "visiting controller",
]

# Anything not listed here is worth 1.0. Turn a word down when it is
# vague, or when another topic has a fair claim on it too.
[weights]
+++

## Visiting or transferring to VATSIM Scandinavia

### Transfer your account
If you wish to move your account to VATSIM Scandinavia, [follow this step-by-step transfer instruction.](https://wiki.vatsim-scandinavia.org/books/getting-started)

### Become a visiting controller
If you want to control as a visitor, [read our visiting and transfer policy.](https://wiki.vatsim-scandinavia.org/books/training-documents/page/transfer-and-visiting-policy-in-vatsim-scandinavia)
