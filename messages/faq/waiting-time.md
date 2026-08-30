+++
title = "Waiting Time"
threshold = 2.0

# Words that point at this topic. Matched on the word stem, so
# "ansøgning" also catches "ansøgningen" and "ansøgninger".
triggers = [
    "aika",
    "approx",
    "biðröð",
    "biðtími",
    "bíða",
    "bíður",
    "estimate",
    "harjoittelu",
    "jono",
    "kö",
    "kø",
    "odottaa",
    "odotusaika",
    "queue",
    "tid",
    "time",
    "training",
    "trening",
    "träning",
    "træning",
    "tími",
    "vente",
    "venter",
    "ventetid",
    "vänta",
    "väntar",
    "väntetid",
    "wait",
    "waiting",
    "þjálfun",
]

# Whole phrases, matched literally. They say far more than any single
# word does, so they are worth 2.0 each unless [weights] says otherwise.
phrases = [
    "how long",
    "how long is the wait",
    "hur lång tid",
    "hvor lang tid",
    "kuinka kauan",
    "waiting time",
]

# Anything not listed here is worth 1.0. Turn a word down when it is
# vague, or when another topic has a fair claim on it too.
[weights]
"biðtími" = 2.0
"odotusaika" = 2.0
"ventetid" = 2.0
"väntetid" = 2.0
"aika" = 0.3
"harjoittelu" = 0.5
"how long" = 1.5
"tid" = 0.3
"time" = 0.3
"training" = 0.5
"trening" = 0.5
"träning" = 0.5
"træning" = 0.5
"tími" = 0.3
"þjálfun" = 0.5
+++

## Waiting time in VATSIM Scandinavia
The waiting time for ATC Training varies by country. Generally, it may extend up to 12 months or follow the timing specified in your training confirmation email.

It's impossible to give you a queue number or exact estimate, because the training queue is dynamic and varies with a couple of factors such as:
- Mentor availability,
- Which rating a mentor can train,
- How long students take to complete their training,
- Other training types that may have higher priority.

*We recommend you to use the time while waiting to familiarize yourself with the VATSIM network, read through the training documents, and piloting skills are also very useful in your future training and understanding.*
