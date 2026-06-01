from __future__ import annotations

from story_forge.models import EventConsequence
from story_forge.worldpacks.base import (
    CanonAnchor,
    EndingTemplate,
    EventTemplate,
    LocationSeed,
    MemoryTrigger,
    NpcSeed,
    WorldPack,
)


def _loc(location_id: str, name: str, description: str, tags: list[str], connections: list[str]) -> LocationSeed:
    return LocationSeed(
        location_id=location_id,
        name=name,
        description=description,
        tags=tags,
        connections=connections,
    )


def _npc(
    npc_id: str,
    name: str,
    role: str,
    home_location_id: str,
    description: str,
    traits: list[str],
    loyalty: int,
    fear: int,
    desire: int,
    stability: int,
    relationship_to_player: int,
) -> NpcSeed:
    return NpcSeed(
        npc_id=npc_id,
        name=name,
        role=role,
        home_location_id=home_location_id,
        description=description,
        traits=traits,
        loyalty=loyalty,
        fear=fear,
        desire=desire,
        stability=stability,
        relationship_to_player=relationship_to_player,
    )


def _event(
    template_id: str,
    title: str,
    event_type: str,
    location_id: str,
    summary: str,
    scene_opening: str,
    participants: list[str],
    choice_texts: list[str],
    required_keywords: list[str],
    impact_level: int,
    world_flags_add: list[str] | None = None,
    relationship_deltas: dict[str, int] | None = None,
    loyalty_deltas: dict[str, int] | None = None,
    fear_deltas: dict[str, int] | None = None,
    stability_deltas: dict[str, int] | None = None,
    score_effects: dict[str, float] | None = None,
    memory_tags: list[str] | None = None,
    next_location_id: str | None = None,
    required_world_flags: list[str] | None = None,
    required_memory_types: list[str] | None = None,
    required_canon_types: list[str] | None = None,
    consequence: EventConsequence | None = None,
) -> EventTemplate:
    return EventTemplate(
        template_id=template_id,
        title=title,
        event_type=event_type,
        location_id=location_id,
        summary=summary,
        scene_opening=scene_opening,
        participants=participants,
        choice_texts=choice_texts,
        required_keywords=required_keywords,
        impact_level=impact_level,
        world_flags_add=world_flags_add or [],
        relationship_deltas=relationship_deltas or {},
        loyalty_deltas=loyalty_deltas or {},
        fear_deltas=fear_deltas or {},
        stability_deltas=stability_deltas or {},
        score_effects=score_effects or {},
        memory_tags=memory_tags or [],
        next_location_id=next_location_id,
        required_world_flags=required_world_flags or [],
        required_memory_types=required_memory_types or [],
        required_canon_types=required_canon_types or [],
        consequence=consequence,
    )


LOCATIONS = [
    _loc("gloambridge", "Gloambridge", "A bridge-town where funeral crows outnumber merchants.", ["river", "market", "omens"], ["thornmere", "blacksalt_harbor"]),
    _loc("ashen_keep", "Ashen Keep", "The burned royal fortress overlooking the dead capital.", ["castle", "throne", "ruin"], ["gloambridge", "red_widow_court"]),
    _loc("thornmere", "Thornmere", "A drowned fen where witches barter with marrow and reeds.", ["marsh", "witchcraft", "plague"], ["gloambridge", "wolfglass_wood", "sunken_abbey"]),
    _loc("sunken_abbey", "Sunken Abbey", "A half-flooded abbey hoarding relics beneath black water.", ["abbey", "relic", "faith"], ["thornmere", "hollow_belltower"]),
    _loc("wolfglass_wood", "Wolfglass Wood", "A moonlit forest of silver bark and feral oaths.", ["forest", "pack", "hunt"], ["thornmere", "blacksalt_harbor"]),
    _loc("blacksalt_harbor", "Blacksalt Harbor", "A salt-crusted port ruled by smugglers and corpse tides.", ["harbor", "smuggling", "tide"], ["gloambridge", "wolfglass_wood", "gallows_road"]),
    _loc("gallows_road", "Gallows Road", "A trade road lined with shrines and swinging iron cages.", ["road", "executions", "caravans"], ["blacksalt_harbor", "emberwake_mine"]),
    _loc("emberwake_mine", "Emberwake Mine", "A fissured mine that glows red beneath the mountain.", ["mine", "labor", "fire"], ["gallows_road", "hollow_belltower"]),
    _loc("hollow_belltower", "Hollow Bell Tower", "A shattered tower where the moon bell waits to be rung.", ["bell", "choir", "ghost"], ["sunken_abbey", "emberwake_mine", "vesper_catacombs"]),
    _loc("vesper_catacombs", "Vesper Catacombs", "A city of bones beneath the capital's broken streets.", ["dead", "crypt", "memory"], ["hollow_belltower", "red_widow_court"]),
    _loc("red_widow_court", "Red Widow Court", "A noble court fed by masks, poison, and blackmail.", ["court", "intrigue", "silk"], ["ashen_keep", "vesper_catacombs", "crown_of_cinders"]),
    _loc("crown_of_cinders", "Crown of Cinders", "The rift-citadel where the last gate to the eclipse burns.", ["gate", "crown", "finale"], ["red_widow_court"]),
]


NPCS = [
    _npc("edda_veyr", "Edda Veyr", "Exiled heir", "ashen_keep", "A scarred claimant refusing to let the kingdom rot quietly.", ["defiant", "royal", "wounded"], 42, 24, 82, 68, 10),
    _npc("brother_caldus", "Brother Caldus", "Abbey prior", "sunken_abbey", "A velvet-voiced zealot guarding a dying light.", ["zealous", "calculating", "severe"], 54, 18, 63, 71, -6),
    _npc("mora_vael", "Mora Vael", "Fen witch", "thornmere", "A marsh oracle who charges in secrets instead of coin.", ["oracular", "merciless", "ancient"], 31, 12, 76, 59, 0),
    _npc("ser_jorren", "Ser Jorren Ashcloak", "Knight captain", "ashen_keep", "A loyal captain deciding whether duty is still holy.", ["dutiful", "tired", "honorable"], 67, 22, 44, 73, 6),
    _npc("yselle_quill", "Yselle Quill", "Court spider", "red_widow_court", "A smiling blackmailer who records every weakness.", ["silken", "ruthless", "precise"], 38, 9, 71, 84, -10),
    _npc("brannik_reed", "Brannik Reed", "Ferryman", "blacksalt_harbor", "A ferryman who knows where the dead still listen.", ["patient", "grave", "observant"], 48, 14, 37, 88, 2),
    _npc("naeva_hollow", "Naeva Hollow", "Bell singer", "hollow_belltower", "A haunted singer whose voice disturbs sleeping relics.", ["haunted", "gentle", "fragile"], 44, 26, 58, 52, 8),
    _npc("rook_fen", "Rook Fen", "Outlaw ranger", "wolfglass_wood", "A pack-sworn scout who trusts deeds more than blood.", ["feral", "loyal", "watchful"], 58, 19, 53, 77, 4),
]


CANON_ANCHORS = [
    CanonAnchor("anchor_king_dead", "death", "king_aldric", "King Aldric died beneath the eclipse and the throne remains empty."),
    CanonAnchor("anchor_eclipse", "world_state", "eclipsed_sun", "The sun has not fully risen in nine years."),
    CanonAnchor("anchor_abbey_shard", "lore", "sunken_abbey", "The Sunken Abbey holds a relic called the Sun Shard."),
    CanonAnchor("anchor_bell", "lore", "hollow_belltower", "The moon bell cracked on the Night of Veils and has not rung since."),
    CanonAnchor("anchor_harbor", "faction_outcome", "blacksalt_harbor", "The Salt Syndicate controls Blacksalt Harbor by debt and fear."),
    CanonAnchor("anchor_mere", "world_state", "thornmere", "Thornmere remembers blood offerings and returns them in dreams."),
]


MEMORY_TRIGGERS = [
    MemoryTrigger("oath_kept", ["alliance", "resolution"], ["oath", "swear", "promise"], ["ashen_keep", "wolfglass_wood"], "oath", "resolve", 0.82, "{title} bound the player to a vow.", ["edda_veyr", "rook_fen"]),
    MemoryTrigger("oath_broken", ["betrayal"], ["lie", "betray", "abandon"], ["any"], "betrayal_scar", "shame", 0.9, "{title} proved the player breaks faith.", []),
    MemoryTrigger("blood_price", ["battle", "death"], ["kill", "blood", "burn"], ["any"], "blood_price", "grief", 0.88, "{title} demanded blood in {location}.", []),
    MemoryTrigger("occult_touch", ["discovery", "resolution"], ["relic", "shard", "bell", "rite"], ["sunken_abbey", "hollow_belltower", "vesper_catacombs"], "occult_touch", "wonder", 0.74, "{title} brushed the player against forbidden power.", []),
    MemoryTrigger("royal_claim", ["alliance", "resolution"], ["crown", "heir", "throne"], ["ashen_keep", "crown_of_cinders"], "royal_claim", "ambition", 0.8, "{title} tightened the player's tie to the throne.", ["edda_veyr"]),
    MemoryTrigger("mercy_shown", ["alliance"], ["spare", "protect", "shield"], ["any"], "mercy", "hope", 0.68, "{title} marked an act of mercy.", []),
    MemoryTrigger("hunger_for_power", ["discovery", "betrayal", "resolution"], ["take", "claim", "power"], ["any"], "power_hunger", "desire", 0.76, "{title} fed the player's hunger for dominion.", []),
    MemoryTrigger("exile_step", ["travel"], ["flee", "leave", "cross", "travel"], ["any"], "exile", "anticipation", 0.55, "{title} pushed the player farther from safety.", []),
    MemoryTrigger("dead_listening", ["discovery", "resolution"], ["dead", "grave", "bones", "song"], ["vesper_catacombs", "hollow_belltower"], "dead_listening", "dread", 0.7, "{title} woke memories among the dead.", ["naeva_hollow", "brannik_reed"]),
    MemoryTrigger("saltbound_debt", ["alliance", "betrayal", "travel"], ["coin", "debt", "ferry", "smuggle"], ["gloambridge", "blacksalt_harbor"], "saltbound_debt", "tension", 0.64, "{title} deepened a debt on the river roads.", ["brannik_reed"]),
]


PRESENTATION = {
    "tone_prefix": "Beneath the eclipsed sky, ",
    "archetype_template": "{archetype} hangs over the scene like a distant omen.",
    "visual_recall_header": "[Ash Recall Triggered]",
    "visual_hook_template": "Carried Mark: {hook}",
}


EVENT_TEMPLATES = [
    _event("df_01", "Crow Warning at Gloambridge", "discovery", "gloambridge", "Crow-priests reveal that the eclipse is feeding on royal blood.", "A ring of crows lands along the bridge rail and speaks through Naeva's borrowed breath.", ["naeva_hollow"], ["Follow the omen into the market crypt.", "Ask who the crows want dead.", "Burn the warning and deny the sign."], ["crow", "warning", "omen"], 3, ["omens_stirring"], {"naeva_hollow": 3}, score_effects={"morality": 4, "world_impact": 3}, memory_tags=["omen", "prophecy"]),
    _event("df_02", "Ferry into Thornmere", "travel", "gloambridge", "Brannik poles a coffin-ferry toward Thornmere through corpse lantern fog.", "Brannik Reed offers silence, a lantern, and a narrow route into the fen.", ["brannik_reed"], ["Pay Brannik and cross into Thornmere.", "Threaten Brannik to row faster.", "Ask what the dead whispered about the marsh."], ["thornmere", "ferry", "marsh"], 2, ["river_crossed"], {"brannik_reed": 2}, fear_deltas={"brannik_reed": -1}, score_effects={"world_impact": 2}, memory_tags=["travel", "river"], next_location_id="thornmere"),
    _event("df_03", "Oath to Edda", "alliance", "ashen_keep", "Edda asks for a public oath before the cracked throne of her father.", "In the soot-black throne room, Edda Veyr extends a scarred hand toward the crown dais.", ["edda_veyr", "ser_jorren"], ["Swear to raise Edda's banner.", "Refuse and demand proof instead.", "Offer quiet aid without public allegiance."], ["edda", "oath", "heir", "kneel"], 4, ["heir_supported"], {"edda_veyr": 8, "ser_jorren": 4}, loyalty_deltas={"edda_veyr": 12, "ser_jorren": 6}, score_effects={"morality": 8, "relationships": 6}, memory_tags=["oath", "throne"]),
    _event("df_04", "Ashen Armory", "discovery", "ashen_keep", "A sealed armory opens to reveal star-iron blades and the ledger of missing heirs.", "Dust peels from the armory door as Jorren breaks an old royal seal.", ["ser_jorren"], ["Claim a star-iron blade.", "Read the ledger first.", "Seal the armory again before anyone sees."], ["armory", "steel", "ledger", "sword"], 3, ["star_iron_found"], {"ser_jorren": 2}, score_effects={"power": 8}, memory_tags=["relic", "royal"]),
    _event("df_05", "Mora's Reed Bargain", "alliance", "thornmere", "Mora offers marsh-safe passage in exchange for a true name buried in grief.", "Mora Vael waits knee-deep in black water, reeds braided through her hair like crowns.", ["mora_vael"], ["Trade a painful memory for her guidance.", "Lie and test her sight.", "Demand aid without paying the price."], ["mora", "bargain", "witch", "reed"], 3, ["fen_bargain"], {"mora_vael": 5}, loyalty_deltas={"mora_vael": 6}, score_effects={"morality": -2, "world_impact": 4}, memory_tags=["bargain", "witchcraft"]),
    _event("df_06", "Trail into Wolfglass", "travel", "thornmere", "Rook marks a hidden trail from the reeds into Wolfglass Wood.", "A wolf-pelt marker hangs from a dead alder, pointing north into silver timber.", ["rook_fen"], ["Follow Rook into Wolfglass.", "Stay in Thornmere and watch the reeds.", "Ask Rook who hunts the trail."], ["wolfglass", "wood", "forest"], 2, ["forest_entered"], {"rook_fen": 2}, score_effects={"world_impact": 2}, memory_tags=["travel", "forest"], next_location_id="wolfglass_wood"),
    _event("df_07", "Confession at the Abbey", "discovery", "sunken_abbey", "Brother Caldus reveals that the Sun Shard dims whenever mercy prevails.", "Cold water laps around the confession stalls as Caldus opens a reliquary of cracked gold.", ["brother_caldus"], ["Demand to see the Sun Shard.", "Confess a sin to test Caldus.", "Steal the reliquary key."], ["abbey", "confess", "shard", "relic"], 4, ["sun_shard_seen"], {"brother_caldus": 3}, score_effects={"power": 5, "world_impact": 5}, memory_tags=["relic", "faith"]),
    _event("df_08", "Purge by Lantern Fire", "battle", "sunken_abbey", "Caldus orders a lantern purge against plague-sick pilgrims in the nave.", "Lantern light turns the floodwater gold as armed choristers drag the sick toward the altar.", ["brother_caldus"], ["Stop the purge by force.", "Aid the purge to win Caldus's trust.", "Smuggle survivors into the crypt."], ["purge", "inquisitor", "burn"], 5, ["abbey_bloodied", "unrest"], {"brother_caldus": -6}, loyalty_deltas={"brother_caldus": -8}, score_effects={"morality": -12, "world_impact": 10}, memory_tags=["purge", "blood"]),
    _event("df_09", "Pack Oath under Wolfglass", "alliance", "wolfglass_wood", "Rook offers the player a hunter's oath before the glass-barked trees.", "Moonlight fractures on silver trunks while Rook Fen waits with a knife and wolfbone cup.", ["rook_fen"], ["Take the pack oath.", "Refuse and keep distance.", "Ask Rook to hunt for Edda instead."], ["rook", "pack", "hunt", "oath"], 3, ["pack_sworn"], {"rook_fen": 7}, loyalty_deltas={"rook_fen": 10}, score_effects={"relationships": 8, "morality": 3}, memory_tags=["pack", "oath"]),
    _event("df_10", "Smuggler Coast Route", "travel", "wolfglass_wood", "Rook reveals a smuggler path from Wolfglass to Blacksalt Harbor.", "A hidden animal track slopes down from the trees toward salt wind and distant bells.", ["rook_fen"], ["Take the coast route to Blacksalt Harbor.", "Stay and stalk the glass stag instead.", "Send Rook ahead alone."], ["harbor", "blacksalt", "coast"], 2, ["coast_road"], {"rook_fen": 1}, score_effects={"world_impact": 2}, memory_tags=["travel", "smuggling"], next_location_id="blacksalt_harbor"),
    _event("df_11", "Smuggler Pact", "alliance", "blacksalt_harbor", "The Salt Syndicate offers passage and poison if the player takes on a harbor debt.", "Brannik leads you into a warehouse where ledgers and knives lie on the same table.", ["brannik_reed", "yselle_quill"], ["Accept the debt for safe passage.", "Burn the ledger and flee.", "Negotiate better terms with names instead of coin."], ["smuggle", "syndicate", "ship", "coin"], 3, ["saltbound"], {"brannik_reed": 3, "yselle_quill": 1}, score_effects={"power": 4, "relationships": 3}, memory_tags=["debt", "harbor"]),
    _event("df_12", "Road to the Gallows", "travel", "blacksalt_harbor", "A shackled caravan leaves Blacksalt for the Gallows Road at dusk.", "Rust-red wheels creak inland while Brannik counts who has no right to return.", ["brannik_reed"], ["Ride with the caravan to Gallows Road.", "Cut the shackles and scatter the prisoners.", "Mark the caravan for an ambush later."], ["gallows", "road", "inland"], 2, ["gallows_route"], {"brannik_reed": 1}, score_effects={"world_impact": 1}, memory_tags=["travel", "chain"], next_location_id="gallows_road"),
    _event("df_13", "Free the Condemned", "alliance", "gallows_road", "Prisoners bound for Emberwake beg for a blade before the crows take their eyes.", "Iron cages sway over a ditch of votive candles as the condemned whisper through split lips.", ["ser_jorren"], ["Break the cages and free them.", "Choose one prisoner to save.", "Turn away and keep moving."], ["free", "condemned", "rope"], 4, ["condemned_freed"], {"ser_jorren": 5}, score_effects={"morality": 10, "relationships": 4}, memory_tags=["mercy", "rebellion"]),
    _event("df_14", "Mine Cart into Emberwake", "travel", "gallows_road", "A prisoner cart rumbles toward Emberwake beneath a rain of ash.", "The road narrows into a rail line cut straight into the burning hillside.", ["ser_jorren"], ["Board the cart and descend to Emberwake.", "Shadow the convoy on foot.", "Sabotage the rails before departure."], ["mine", "emberwake", "cart"], 2, ["mine_approach"], {"ser_jorren": 1}, score_effects={"world_impact": 2}, memory_tags=["travel", "ash"], next_location_id="emberwake_mine"),
    _event("df_15", "Miner Revolt", "battle", "emberwake_mine", "The miners rise against overseers as the red seam fractures beneath them.", "Pick hammers beat a war rhythm while sparks fall like bloodied snow.", ["edda_veyr", "ser_jorren"], ["Lead the revolt.", "Protect the overseers for leverage.", "Seal the fracture and save whoever survives."], ["revolt", "miners", "collapse", "pickaxe"], 5, ["mine_revolt", "unrest"], {"edda_veyr": 4, "ser_jorren": -4}, score_effects={"morality": 6, "power": 6, "world_impact": 12}, memory_tags=["revolt", "fire"]),
    _event("df_16", "Bell Tower Ascent", "travel", "emberwake_mine", "A soot ladder climbs from Emberwake into the Hollow Bell Tower.", "The ladder clings to black stone while the tower above hums with sleeping voices.", ["naeva_hollow"], ["Climb to the Hollow Bell Tower.", "Stay in the mine and search deeper seams.", "Send Naeva ahead to listen."], ["belltower", "bell", "tower"], 2, ["tower_approach"], {"naeva_hollow": 2}, score_effects={"world_impact": 2}, memory_tags=["travel", "bell"], next_location_id="hollow_belltower"),
    _event("df_17", "Ring the Moon Bell", "resolution", "hollow_belltower", "The moon bell rings and every oath in the kingdom wakes at once.", "Naeva's voice threads through the cracked bell as moonlight spills into the tower throat.", ["naeva_hollow"], ["Ring the bell in full.", "Silence Naeva before the strike lands.", "Turn the bell toward the dead instead of the living."], ["ring", "bell", "moon"], 4, ["black_bell_rung"], {"naeva_hollow": 6}, score_effects={"world_impact": 9, "tension_resolution": 12}, memory_tags=["bell", "awakening"], consequence=EventConsequence(set_arc_flags={"bell_rung": True})),
    _event("df_18", "Descent into Vesper", "travel", "hollow_belltower", "A choir stair drops from the tower into the Vesper Catacombs.", "Loose stone peels away to reveal a spiral cut with names of the forgotten dead.", ["naeva_hollow", "brannik_reed"], ["Descend into the catacombs.", "Seal the stair and deny the dead.", "Ask Brannik what waits below."], ["catacombs", "crypt", "dead"], 2, ["catacombs_open"], {"brannik_reed": 2, "naeva_hollow": 1}, score_effects={"world_impact": 2}, memory_tags=["travel", "dead"], next_location_id="vesper_catacombs"),
    _event("df_19", "Bind the Revenant", "discovery", "vesper_catacombs", "A royal revenant offers forgotten maps in exchange for a living heartbeat.", "Chains drag across ossuary tiles as the revenant prince kneels inside a chalk seal.", ["mora_vael", "brannik_reed"], ["Bind the revenant and take the maps.", "Break the seal and let it roam.", "Offer your own blood for the truth."], ["revenant", "bind", "bones"], 4, ["dead_bargain"], {"mora_vael": 2, "brannik_reed": 2}, score_effects={"power": 6, "world_impact": 5}, memory_tags=["dead", "map"]),
    _event("df_20", "Passage to Red Widow Court", "travel", "vesper_catacombs", "A hidden lift carries the player from the catacombs into the silk halls above.", "Torchlight becomes perfume as the dead city's lift rises into velvet and masks.", ["yselle_quill"], ["Take the hidden lift to Red Widow Court.", "Stay below and question the bones.", "Mark the lift for a future escape."], ["court", "widow", "ball"], 2, ["court_reached"], {"yselle_quill": 2}, score_effects={"world_impact": 2}, memory_tags=["travel", "court"], next_location_id="red_widow_court"),
    _event("df_21", "Masked Bargain", "betrayal", "red_widow_court", "Yselle offers the names of traitors if the player surrenders one loyal ally to scandal.", "Red silk and candle smoke hide every face except Yselle Quill's smile.", ["yselle_quill", "edda_veyr"], ["Trade an ally's name for the dossier.", "Refuse the bargain and burn the papers.", "Feed Yselle a false confession instead."], ["mask", "bargain", "blackmail", "dossier"], 4, ["court_scandal"], {"yselle_quill": 5, "edda_veyr": -8}, score_effects={"power": 7, "relationships": -8, "morality": -10}, memory_tags=["betrayal", "court"]),
    _event("df_22", "Road to the Crown", "travel", "red_widow_court", "A masked procession opens the last road toward the Crown of Cinders.", "The court parts like a wound, revealing a stair of ash to the burning gate.", ["edda_veyr", "yselle_quill"], ["Join the procession to the Crown of Cinders.", "Assassinate the herald and take the road alone.", "Turn back and gather more allies."], ["cinders", "crown", "gate"], 2, ["crown_road"], {"edda_veyr": 2}, score_effects={"world_impact": 2}, memory_tags=["travel", "finale"], next_location_id="crown_of_cinders"),
    _event("df_23", "Gate of Ash", "resolution", "crown_of_cinders", "The eclipse gate opens and the kingdom's buried grief pours through it.", "At the citadel lip, the gate burns black and the wind tastes like old funerals.", ["edda_veyr", "naeva_hollow"], ["Open the gate wider for power.", "Seal the gate with blood and relic.", "Hold the gate while others flee."], ["gate", "ash", "open"], 5, ["gate_reached"], {"edda_veyr": 3, "naeva_hollow": 2}, score_effects={"power": 8, "world_impact": 14, "tension_resolution": 8}, memory_tags=["gate", "eclipse"], consequence=EventConsequence(set_arc_flags={"gate_confronted": True})),
    _event("df_24", "Claim the Throne", "resolution", "crown_of_cinders", "A crown of living ash settles on whoever speaks the kingdom's true wound aloud.", "The throne rises out of cinderfall and waits for a ruler cruel enough or kind enough to survive it.", ["edda_veyr", "ser_jorren"], ["Crown Edda before the gate.", "Take the crown yourself.", "Shatter the throne and deny rule to everyone."], ["throne", "crown", "rule"], 5, ["crown_claimed"], {"edda_veyr": 10, "ser_jorren": 4}, score_effects={"power": 16, "morality": -4, "world_impact": 10}, memory_tags=["throne", "rule"]),
    _event("df_25", "Brannik's Underpass", "travel", "any", "Brannik reveals a flood-carved underpass linking ruin to river.", "Brannik lifts a lantern and shows where water once bit a path through the kingdom's foundations.", ["brannik_reed"], ["Use the underpass to return to Gloambridge.", "Demand Brannik lead you to harbor stores.", "Memorize the route and move on."], ["brannik", "underpass", "ferry"], 2, ["hidden_route"], {"brannik_reed": 2}, score_effects={"world_impact": 1}, memory_tags=["travel", "river"], next_location_id="gloambridge"),
    _event("df_26", "Naeva's Grief Song", "discovery", "any", "Naeva sings a grief song that reveals which memory still rules the player.", "Her voice catches on the edges of the room and pulls one memory into the open like a blade.", ["naeva_hollow"], ["Listen and answer honestly.", "Silence the song before it names you.", "Ask Naeva to turn the song toward the dead."], ["song", "naeva", "mourn"], 3, ["grief_song"], {"naeva_hollow": 4}, score_effects={"morality": 5, "relationships": 4}, memory_tags=["song", "memory"]),
    _event("df_27", "Yselle's Double Cross", "betrayal", "any", "Yselle sells the player's last secret to the highest bidder and waits to see who bleeds.", "A sealed letter breaks in your hand moments before the ambush begins.", ["yselle_quill"], ["Turn the ambush back on Yselle.", "Absorb the betrayal and bargain anyway.", "Expose Yselle publicly and lose all subtlety."], ["yselle", "spy", "double", "letter"], 4, ["double_cross"], {"yselle_quill": -12}, score_effects={"relationships": -10, "morality": -3, "world_impact": 6}, memory_tags=["spy", "betrayal"]),
    _event("df_28", "Caldus and the False Sun", "discovery", "any", "Caldus admits the Sun Shard was forged to control faith, not restore daylight.", "Brother Caldus lowers his voice and finally names the relic for what it is: a leash.", ["brother_caldus"], ["Expose the lie to everyone.", "Keep the secret and use it later.", "Take the shard and leave Caldus broken."], ["caldus", "sun", "relic"], 4, ["false_sun_known"], {"brother_caldus": -2}, score_effects={"power": 5, "morality": -2, "world_impact": 6}, memory_tags=["relic", "truth"]),
    _event("df_29", "Sacrifice the Shard", "resolution", "any", "The Sun Shard can seal the gate, but only if fed a living claimant or the player's own soul-mark.", "Light gathers around the shard with the patience of a blade waiting for the neck.", ["edda_veyr", "brother_caldus"], ["Offer yourself to seal the gate.", "Demand Edda bear the sacrifice.", "Break the shard and accept the consequences."], ["sacrifice", "shard", "seal"], 5, ["gate_sealed", "veil_healed"], {"edda_veyr": 5, "brother_caldus": -4}, score_effects={"morality": 18, "tension_resolution": 20, "world_impact": 12}, memory_tags=["sacrifice", "seal"], required_world_flags=["gate_reached"]),
    _event("df_30", "Nightless Rite", "resolution", "any", "A hidden rite can end the eclipse without a crown, but only if bell, blood, and truth align.", "The rite circle wakes beneath both moon and ash, demanding honesty from every survivor present.", ["naeva_hollow", "mora_vael", "rook_fen"], ["Complete the Nightless Rite.", "Take its power without finishing the rite.", "Destroy the rite before anyone can claim it."], ["nightless", "rite", "true", "dawn"], 5, ["nightless_secret", "veil_healed"], {"naeva_hollow": 6, "mora_vael": 4, "rook_fen": 4}, score_effects={"morality": 12, "power": 4, "relationships": 10, "tension_resolution": 18}, memory_tags=["rite", "truth"], required_world_flags=["black_bell_rung", "false_sun_known"]),
]


ENDING_TEMPLATES = [
    EndingTemplate("end_hero", "Hero Ending", "The player restores a fragile dawn and leaves the kingdom scarred but breathing.", min_scores={"morality": 25, "relationships": 10, "world_impact": 15}),
    EndingTemplate("end_sacrifice", "Sacrifice Ending", "The gate is sealed through deliberate loss, and the realm survives because someone chose not to.", min_scores={"morality": 40, "tension_resolution": 35}, required_flags=["gate_sealed"]),
    EndingTemplate("end_power", "Power Ending", "The player claims the ash crown and rules through dread, order, and hunger.", min_scores={"power": 45}, max_scores={"morality": 20}, required_flags=["crown_claimed"]),
    EndingTemplate("end_survival", "Survival Ending", "The player escapes with a handful of allies while the kingdom continues to rot behind them.", max_scores={"world_impact": 18}, min_scores={"relationships": -5}),
    EndingTemplate("end_corruption", "Corruption Ending", "The bell and the gate answer ambition first, and the player becomes part of the eclipse.", min_scores={"power": 25}, max_scores={"morality": -5}, required_flags=["black_bell_rung"]),
    EndingTemplate("end_true", "True Nightless Ending", "Bell, shard, and oath align; the eclipse breaks without a throne, and the dead finally fall silent.", min_scores={"morality": 20, "relationships": 12, "tension_resolution": 45}, required_flags=["nightless_secret", "veil_healed"], required_memory_types=["royal_claim", "occult_touch"]),
]


DARK_FANTASY_PACK = WorldPack(
    pack_id="ashen_fall",
    name="Ashen Fall",
    premise="An eclipsed kingdom can be restored, ruled, escaped, or damned depending on what truths the player is willing to carry.",
    tone="grim dark fantasy",
    start_location_id="gloambridge",
    factions={
        "crown_remnant": "Broken loyalists still sworn to the dead king's line.",
        "hollow_church": "A relic-hoarding church that treats light as property.",
        "salt_syndicate": "Harbor smugglers who trade in debt, poison, and passage.",
        "fen_pact": "Witches and marsh families bound by blood-offerings.",
        "glass_pack": "Outlaws and hunters surviving beneath Wolfglass boughs.",
    },
    locations=LOCATIONS,
    npcs=NPCS,
    event_templates=EVENT_TEMPLATES,
    ending_templates=ENDING_TEMPLATES,
    canon_anchors=CANON_ANCHORS,
    memory_triggers=MEMORY_TRIGGERS,
    presentation=PRESENTATION,
)
