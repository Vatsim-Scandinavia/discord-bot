from typing import Any

import discord
import discord.abc


async def send_faq_embed(
    channel: discord.abc.Messageable, user_mention: str, topic: str, description: str
) -> None:
    embed = discord.Embed(description=description, color=discord.Color(0x43C6E7))
    await channel.send(
        f"{user_mention} I believe you're asking about {topic}:", embed=embed
    )


faq_triggers: dict[str, dict[str, Any]] = {
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
            'trained',
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
            'trening',
            # SE
            'ansökan',
            'ansöka',
            'ansöker',
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
        'threshold': 2,
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
            'overføre',
            'overfører',
            'besøke',
            'besøker',
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
        'threshold': 1,
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
            'trening',
            # SE
            'väntetid',
            'vänta',
            'väntar',
            'kö',
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
        'threshold': 2,
    },
}
