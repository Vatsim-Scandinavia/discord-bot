from helpers.config import config
import discord


async def send_faq_embed(channel, user_mention, topic, description):
    await channel.send(
        f"{user_mention} I believe you're asking about {topic}:"
    )
    embed = discord.Embed(description=description, color=discord.Color(0x43C6E7))
    await channel.send(embed=embed)


faq_triggers = {
    'ATC Application': {
        'triggers': {
            # EN
            'application',
            'apply',
            'atc',
            'become',
            'controller',
            'train',
            'training',
            # DK
            'ansøgning',
            'ansøge',
            'blive',
            'flygeleder',
            'træning',
            # NO
            'søknad',
            'søke',
            'søker',
            'bli',
            'flygeleder',
            'trening',
            # SE
            'ansökan',
            'ansöka',
            'ansöker',
            'bli',
            'flygledare',
            'utbildning',
            'träning',
            # FI
            'hakemus',
            'hakea',
            'haen',
            'lennonjohtaja',
            'harjoittelu',
            'koulutus',
            'tulla',
            # IS
            'umsókn',
            'sækja',
            'sækist',
            'flugumferðarstjóri',
            'þjálfun',
            'verða',
            'menntun',
        },
        'tolerance': 2,
    },
    'Visiting/Transfer': {
        'triggers': {
            # EN
            'transfer',
            'visiting',
            # DK
            'besøg',
            'besøge',
            'besøger',
            'flytte',
            'flytter',
            'overførsel',
            'overføring',
            # NO
            'overføring',
            'overføre',
            'overfører',
            'besøke',
            'besøker',
            'flytte',
            'flytter',
            # SE
            'besöka',
            'besöker',
            'flytta',
            'flyttar',
            'överföring',
            'överföra',
            'överför',
            # FI
            'vierailla',
            'vierailee',
            'siirtyä',
            'siirto',
            'siirtää',
            # FI
            'heimsækja',
            'heimsækir',
            'flytja',
            'flytur',
            'skipta',
            'skiptir',
            'flutningur',
        },
        'tolerance': 1,
    },
    'Waiting Time': {
        'triggers': {
            # EN
            'wait',
            'waiting',
            'estimate',
            'approx',
            'time',
            'queue',
            'training',
            # DK
            'ventetid',
            'vente',
            'venter',
            'kø',
            'tid',
            'træning',
            # NO
            'ventetid',
            'vente',
            'venter',
            'kø',
            'tid',
            'trening',
            # SE
            'väntetid',
            'vänta',
            'väntar',
            'kö',
            'tid',
            'träning',
            # FI
            'odottaa',
            'odotusaika',
            'aika',
            'jono',
            'harjoittelu',
            # IS
            'bíða',
            'bíður',
            'biðtími',
            'biðröð',
            'tími',
            'þjálfun',
        },
        'tolerance': 2,
    },
}