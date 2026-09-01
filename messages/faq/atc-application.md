+++
title = "ATC Application"
threshold = 2.0

# Words that point at this topic. Matched on the word stem, so
# "ansøgning" also catches "ansøgningen" and "ansøgninger".
triggers = [
    "ansöka",
    "ansökan",
    "ansöker",
    "ansøge",
    "ansøgning",
    "application",
    "apply",
    "atc",
    "become",
    "bli",
    "blive",
    "controller",
    "flugumferðarstjóri",
    "flygeleder",
    "flygledare",
    "haen",
    "hakea",
    "hakemus",
    "harjoittelu",
    "koulutus",
    "lennonjohtaja",
    "menntun",
    "sækist",
    "sækja",
    "søke",
    "søker",
    "søknad",
    "train",
    "trained",
    "training",
    "trening",
    "träning",
    "træning",
    "tulla",
    "umsókn",
    "utbildning",
    "verða",
    "þjálfun",
]

# Whole phrases, matched literally. They say far more than any single
# word does, so they are worth 2.0 each unless [weights] says otherwise.
phrases = [
    "apply for training",
    "become a controller",
    "become an atc",
    "bli flygeleder",
    "bli flygledare",
    "blive flyveleder",
    "how do i apply",
    "start training",
]

# Anything not listed here is worth 1.0. Turn a word down when it is
# vague, or when another topic has a fair claim on it too.
[weights]
"become" = 0.5
"bli" = 0.5
"blive" = 0.5
"harjoittelu" = 0.5
"train" = 0.5
"trained" = 0.5
"training" = 0.5
"trening" = 0.5
"träning" = 0.5
"træning" = 0.5
"tulla" = 0.5
"verða" = 0.5
"þjálfun" = 0.5
+++

## How to become a controller in VATSIM Scandinavia

1. Go to our training system [Control Center](https://cc.vatsim-scandinavia.org/).
2. Read the information in the "Request Training" section on your right.
3. Follow instructions accordingly to apply for your training.

**Do you have questions regarding the details of the training?**
Here are some documents detailing how our training works in each country:
- [Denmark](https://wiki.vatsim-scandinavia.org/books/training-department)
- [Finland](https://wiki.vatsim-scandinavia.org/books/getting-started)
- [Iceland](https://wiki.vatsim-scandinavia.org/books/training-documents/page/faq)
- [Norway](https://wiki.vatsim-scandinavia.org/books/training-curriculum/chapter/local-training-policy)
- [Sweden](https://wiki.vatsim-scandinavia.org/books/training-in-sweden)

**Have you recently transferred?**
Log out and back in to refresh your associated division.
