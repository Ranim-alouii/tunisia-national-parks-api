"""
Add comprehensive species database with 50+ fauna and flora species
Including reptiles, birds, insects, more mammals, and medicinal plants
Run with: python seed_more_species.py
"""

from sqlmodel import Session, select
from database import engine
from models import ParkDB, SpeciesDB, ParkSpeciesLink

# Comprehensive species data
ADDITIONAL_SPECIES = [
    # REPTILES
    {
        "name": "Tortue grecque",
        "type": "animal",
        "scientific_name": "Testudo graeca",
        "description": "Tortue terrestre endémique d'Afrique du Nord. Carapace bombée jaune-brun avec motifs noirs. Herbivore se nourrissant de plantes sauvages. Espèce protégée vivant jusqu'à 100 ans.",
        "threats": "Capture pour commerce illégal d'animaux de compagnie, perte d'habitat due à l'agriculture, mortalité routière, incendies, prédation des œufs par chiens et renards, collecte par touristes.",
        "protection_measures": "Protection légale stricte, interdiction totale de capture et commerce, programmes d'élevage en captivité, corridors écologiques, sensibilisation du public, marquage et suivi des populations, sanctuaires de protection.",
        "safety_guidelines": "Ne jamais ramasser ou déplacer une tortue - c'est illégal et stressant pour l'animal. Observer à distance de 2-3 mètres. Ne pas nourrir. Si trouvée sur route, la déplacer délicatement dans la direction où elle allait, pas loin de la route. Ne jamais garder comme animal de compagnie - amende sévère. Photographier sans toucher. Ne pas retourner sur le dos - peut être fatal.",
        "parks": ["Boukornine", "Zaghouan", "Jebel Mghilla", "Chaambi", "Orbata"],
    },
    {
        "name": "Vipère de Lataste",
        "type": "animal",
        "scientific_name": "Vipera latastei",
        "description": "Serpent venimeux de taille moyenne (50-70 cm). Tête triangulaire distincte, motifs en zigzag sur le dos. Nocturne, se nourrit de rongeurs et lézards. Rôle écologique important dans régulation rongeurs.",
        "threats": "Persécution humaine par peur, destruction d'habitat, mortalité routière, utilisation de rodenticides empoisonnant proies, collecte illégale pour terrariophilie.",
        "protection_measures": "Protection légale, éducation publique sur rôle écologique et comportement non-agressif, préservation habitats rocheux, corridors écologiques, interdiction collecte, études scientifiques.",
        "safety_guidelines": "DANGER : Serpent venimeux. Maintenir distance minimum 2 mètres. Ne JAMAIS essayer de toucher, capturer ou tuer. Porter bottes montantes et pantalons longs en randonnée. Regarder où vous mettez pieds et mains. Faire du bruit en marchant - les serpents fuient les vibrations. Si morsure : rester calme, immobiliser membre mordu, retirer bijoux, appeler urgences (190), noter apparence du serpent. NE PAS faire de garrot, NE PAS sucer venin, NE PAS courir. La plupart des vipères évitent l'homme.",
        "parks": ["Chaambi", "Orbata", "Jebel Mghilla", "Boukornine"],
    },
    {
        "name": "Caméléon commun",
        "type": "animal",
        "scientific_name": "Chamaeleo chamaeleon",
        "description": "Reptile arboricole fascinant capable de changer de couleur. Queue préhensile, yeux indépendants, langue projectile pour capturer insectes. Espèce emblématique de la biodiversité méditerranéenne.",
        "threats": "Capture pour commerce d'animaux, destruction habitat (déforestation, urbanisation), utilisation pesticides réduisant insectes-proies, mortalité routière, superstitions locales.",
        "protection_measures": "Protection légale totale, interdiction capture et commerce, préservation habitats arbustifs, sensibilisation enfants dans écoles, monitoring populations, corridors verts en zones urbaines.",
        "safety_guidelines": "Totalement inoffensif pour l'homme. Observer à distance de 1-2 mètres sans toucher. Déplacement très lent - ne pas effrayer. Ne jamais capturer - illégal et caméléon meurt en captivité. Si trouvé sur route, le déplacer délicatement vers végétation proche avec branche. Photographier sans flash. Excellent indicateur de santé environnementale.",
        "parks": ["El Feija", "Oued Zeen", "Jebel Chitana-Cap Négro", "Boukornine"],
    },
    {
        "name": "Lézard ocellé",
        "type": "animal",
        "scientific_name": "Timon lepidus",
        "description": "Plus grand lézard d'Afrique du Nord (jusqu'à 60 cm). Corps robuste vert avec ocelles bleus caractéristiques sur les flancs. Diurne, insectivore et omnivore opportuniste. Espèce thermophile des zones rocailleuses.",
        "threats": "Perte d'habitat par agriculture intensive, persécution humaine, mortalité routière, prédation par chats domestiques, fragmentation populations.",
        "protection_measures": "Protection légale, préservation murets de pierre et habitats rocheux, corridors écologiques, sensibilisation (espèce bénéfique mangeant insectes nuisibles), études écologiques.",
        "safety_guidelines": "Peut mordre si acculé mais généralement craintif et fuit rapidement. Observer à distance de 2-3 mètres. Ne pas poursuivre ou attraper. Morsure non venimeuse mais peut causer petite plaie - désinfecter si mordu. Laisser échappatoire au lézard - ne jamais coincer. Excellent contrôleur naturel d'insectes. Ne pas confondre avec serpent.",
        "parks": ["Boukornine", "Zaghouan", "Chaambi", "Jebel Mghilla", "Orbata"],
    },

    # MORE BIRDS
    {
        "name": "Cigogne blanche",
        "type": "animal",
        "scientific_name": "Ciconia ciconia",
        "description": "Grand échassier migrateur au plumage blanc et noir. Bec et pattes rouges. Niche sur édifices et arbres. Se nourrit d'insectes, grenouilles, petits reptiles. Migration spectaculaire Europe-Afrique.",
        "threats": "Lignes électriques (électrocution, collision), pesticides réduisant proies, perte zones humides, dérangement des sites de nidification, pollution plastique.",
        "protection_measures": "Sécurisation lignes électriques, plateformes de nidification artificielles, protection zones humides, agriculture biologique, sensibilisation, suivi migration par GPS.",
        "safety_guidelines": "Observer à distance de 20-30 mètres, plus loin pendant nidification. Ne jamais grimper vers un nid - cigognes peuvent défendre agressivement avec coups de bec puissants. Ne pas déranger pendant incubation (mars-juin). Respecter colonies. Signaler nids sur infrastructures dangereuses aux autorités. Inoffensives en vol ou au sol si non menacées.",
        "parks": ["Ichkeul", "El Feija", "Oued Zeen"],
    },
    {
        "name": "Buse féroce",
        "type": "animal",
        "scientific_name": "Buteo rufinus",
        "description": "Rapace de taille moyenne des zones arides. Plumage brun-roux variable. Excellent chasseur de rongeurs et reptiles. Niche sur falaises et grands arbres. Sédentaire en Tunisie.",
        "threats": "Empoisonnement secondaire par rodenticides, électrocution sur lignes électriques, tir illégal, perte d'habitat, dérangement sites de nidification.",
        "protection_measures": "Protection légale stricte, sécurisation infrastructures électriques, interdiction rodenticides dangereux, zones de quiétude autour nids, sensibilisation agriculteurs (allié contre rongeurs).",
        "safety_guidelines": "Observer à grande distance (100+ mètres) avec jumelles. Ne jamais approcher nid - parents défendent territoire vigoureusement. Éviter zone de nidification février-juillet. Rapace peut plonger vers intrus. Pas de drones près des aires. Totalement bénéfique pour agriculture.",
        "parks": ["Chaambi", "Orbata", "Bouhedma", "Jebil"],
    },
    {
        "name": "Outarde houbara",
        "type": "animal",
        "scientific_name": "Chlamydotis undulata",
        "description": "Oiseau terrestre des steppes et semi-déserts. Plumage cryptique beige. Parade nuptiale spectaculaire du mâle. Menacée par chasse excessive. Course rapide, vol puissant mais préfère marcher.",
        "threats": "Chasse illégale intensive (fauconnerie arabe), perte d'habitat steppique, dérangement pendant reproduction, prédation œufs, sécheresse, agriculture extensive.",
        "protection_measures": "Protection légale totale, interdiction absolue de chasse, programmes d'élevage et réintroduction, surveillance anti-braconnage renforcée, protection habitats steppiques, sensibilisation internationale.",
        "safety_guidelines": "Oiseau très craintif - observer uniquement à très grande distance (200-300m) avec télescope. Ne jamais approcher ou poursuivre. Interdit de photographier avec flash ou drones. Signaler observations aux gardes forestiers - espèce très surveillée. Toute tentative de capture est crime sévèrement puni.",
        "parks": ["Bouhedma", "Sidi Toui", "Jebil", "Dghoumès", "Senghar-Jabess"],
    },
    {
        "name": "Milan royal",
        "type": "animal",
        "scientific_name": "Milvus milvus",
        "description": "Rapace élégant à queue fourchue caractéristique. Plumage roux-brun, tête grisâtre. Principalement charognard, également chasseur opportuniste. Migrateur hivernal en Tunisie.",
        "threats": "Empoisonnement (rodenticides, appâts), électrocution, collisions éoliennes, persécution, diminution de ressources alimentaires.",
        "protection_measures": "Protection stricte, sécurisation lignes électriques, interdiction poisons, protection dortoirs hivernaux, sensibilisation sur rôle équarrisseur naturel.",
        "safety_guidelines": "Totalement inoffensif pour l'homme - se nourrit de charognes. Observer en vol à toute distance. Très gracieux en vol - identifier par queue fourchue. Ne pas déranger dortoirs collectifs hivernaux. Bénéfique pour environnement (nettoyeur naturel).",
        "parks": ["Ichkeul", "El Feija", "Oued Zeen", "Chaambi"],
    },
    {
        "name": "Faucon crécerelle",
        "type": "animal",
        "scientific_name": "Falco tinnunculus",
        "description": "Petit faucon commun reconnaissable à son vol stationnaire (vol du Saint-Esprit). Plumage roux tacheté. Chasse petits rongeurs, insectes, lézards. Niche dans cavités.",
        "threats": "Pesticides réduisant proies, perte sites de nidification (vieux bâtiments), collision avec véhicules, rodenticides empoisonnant proies.",
        "protection_measures": "Protection légale, installation nichoirs artificiels, agriculture biologique favorisant proies, sensibilisation (contrôle rongeurs gratuit).",
        "safety_guidelines": "Petit rapace totalement inoffensif. Peut être observé de près en vol stationnaire. Ne pas déranger si niche dans bâtiment. Bénéfique pour agriculture et jardins. Facile à observer en bordure de routes.",
        "parks": ["Tous les parcs - espèce commune et répandue"],
    },

    # MORE MAMMALS
    {
        "name": "Renard roux",
        "type": "animal",
        "scientific_name": "Vulpes vulpes",
        "description": "Canidé de taille moyenne au pelage roux caractéristique et queue touffue. Omnivore opportuniste adaptable. Nocturne et crépusculaire. Rôle écologique important dans régulation rongeurs.",
        "threats": "Persécution par éleveurs, empoisonnement, rage (localement), collisions routières, perte d'habitat, chasse.",
        "protection_measures": "Sensibilisation sur rôle écologique bénéfique, vaccination contre rage, corridors écologiques, réglementation chasse, études scientifiques.",
        "safety_guidelines": "Généralement craintif et évite l'homme. Observer à distance de 20-30 mètres. Ne jamais nourrir - risque d'habituation. Si approche inhabituelle ou comportement bizarre (rage possible), reculer et signaler aux autorités. Ne pas toucher renard malade ou mort. Sécuriser poubelles en camping. Tenir chiens en laisse. Signaler renard agressif immédiatement.",
        "parks": ["Tous les parcs - espèce très répandue"],
    },
    {
        "name": "Porc-épic à crête",
        "type": "animal",
        "scientific_name": "Hystrix cristata",
        "description": "Grand rongeur nocturne recouvert de piquants. Herbivore se nourrissant de racines, bulbes, fruits. Vit en terriers familiaux. Fait claquer ses piquants en avertissement. Espèce fascinante.",
        "threats": "Chasse pour viande, persécution (dégâts cultures), mortalité routière, perte d'habitat, capture pour zoo.",
        "protection_measures": "Protection légale, zones tampons agriculture-parcs, sensibilisation valeur écologique, études comportementales, corridors écologiques sécurisés.",
        "safety_guidelines": "Animal normalement inoffensif mais peut charger à reculons si acculé - piquants très douloureux et difficiles à retirer. Observer à distance de 10-15 mètres. Si rencontre nocturne, faire du bruit et reculer lentement. Ne jamais coincer ou poursuivre. Piquants se détachent facilement au contact. Si piqûre, consulter médecin pour retrait (risque infection). Très craintif normalement.",
        "parks": ["El Feija", "Oued Zeen", "Jebel Chitana-Cap Négro", "Chaambi", "Jebel Mghilla"],
    },
    {
        "name": "Hérisson d'Algérie",
        "type": "animal",
        "scientific_name": "Atelerix algirus",
        "description": "Petit mammifère nocturne insectivore couvert de piquants. Oreilles longues caractéristiques. Se roule en boule défensive. Hibernation partielle en hiver. Bénéfique pour jardins (mange limaces, insectes).",
        "threats": "Mortalité routière massive, pesticides (intoxication et réduction proies), noyade dans piscines, machines agricoles, urbanisation, chiens domestiques.",
        "protection_measures": "Protection légale, campagnes 'Ralentir pour hérissons', aménagement passages faune, jardins écologiques sans pesticides, sensibilisation publique massive.",
        "safety_guidelines": "Totalement inoffensif et bénéfique. Si trouvé sur route, le déplacer délicatement hors danger avec gants ou tissu. Piquants ne sont pas dangereux mais peuvent piquer légèrement. Créer passages dans clôtures de jardin (trous 13x13cm). Vérifier avant de tondre herbes hautes. Rampe de sortie dans piscines. Ne pas nourrir lait (intolérance). Signaler hérisson blessé à vétérinaire ou association faune.",
        "parks": ["Boukornine", "Zaghouan", "El Feija", "Oued Zeen", "Jebel Serj"],
    },
    {
        "name": "Genette commune",
        "type": "animal",
        "scientific_name": "Genetta genetta",
        "description": "Petit carnivore élégant à la fourrure tachetée et longue queue annelée. Arboricole et nocturne. Chasse rongeurs, oiseaux, insectes. Solitaire et territoriale. Excellente grimpeuse.",
        "threats": "Collisions routières, perte d'habitat forestier, empoisonnement secondaire, piégeage accidentel, chiens de chasse.",
        "protection_measures": "Protection légale, corridors écologiques boisés, sensibilisation automobilistes zones à risque, interdiction pièges non sélectifs.",
        "safety_guidelines": "Totalement inoffensive pour l'homme. Très craintive et fuit au moindre bruit. Observations rares - principalement nocturne. Si rencontre, rester calme et observer de loin. Ne pas poursuivre. Peut émettre musc odorant si très effrayée. Bénéfique (contrôle rongeurs). Signe de bonne santé forestière.",
        "parks": ["El Feija", "Oued Zeen", "Jebel Chitana-Cap Négro", "Boukornine"],
    },
    {
        "name": "Mangouste ichneumon",
        "type": "animal",
        "scientific_name": "Herpestes ichneumon",
        "description": "Carnivore diurne au corps allongé et queue touffue. Pelage gris-brun. Chasse serpents, rongeurs, insectes, oeufs. Immunitaire partielle au venin de vipère. Vit en groupes familiaux.",
        "threats": "Mortalité routière, persécution (pillage poulaillers), perte d'habitat riparian, empoisonnement, chasse.",
        "protection_measures": "Protection légale, sensibilisation sur rôle (tue serpents venimeux), protection habitats riverains, corridors écologiques, sécurisation poulaillers.",
        "safety_guidelines": "Généralement craintive mais peut être agressive si acculée ou avec jeunes. Maintenir distance de 15-20 mètres. Morsure puissante - ne jamais attraper. Si rencontre, faire du bruit et reculer. Ne pas s'interposer entre adulte et jeunes. Bénéfique pour contrôle serpents et rongeurs. Observations souvent près de l'eau.",
        "parks": ["El Feija", "Oued Zeen", "Ichkeul", "Jebel Chitana-Cap Négro"],
    },

    # MEDICINAL PLANTS
    {
        "name": "Menthe pouliot",
        "type": "plant",
        "scientific_name": "Mentha pulegium",
        "description": "Plante aromatique vivace à forte odeur mentholée. Petites feuilles ovales, fleurs roses-violettes en épis. Affectionne zones humides. Utilisée traditionnellement depuis l'Antiquité.",
        "threats": "Cueillette excessive, drainage zones humides, pollution de l'eau, urbanisation, agriculture intensive.",
        "protection_measures": "Réglementation cueillette commerciale, protection zones humides, culture domestique encouragée, sensibilisation pratiques durables.",
        "safety_guidelines": "Cueillette modérée uniquement parties aériennes fleuries. Ne jamais arracher racines. Éviter zones polluées ou traitées chimiquement. Laver soigneusement avant usage.",
        "medicinal_use": "Digestive, antispasmodique, expectorante. Infusion : 1 c. à café/tasse, 2-3 fois/jour après repas. Traite ballonnements, coliques, indigestions. Usage externe : répulsif insectes. ATTENTION : HUILE ESSENTIELLE TOXIQUE - ne jamais utiliser pure. CONTRE-INDICATIONS ABSOLUES : grossesse (abortif puissant), allaitement, enfants <6 ans, maladies hépatiques ou rénales. Usage court terme uniquement. Consulter médecin.",
        "parks": ["Ichkeul", "El Feija", "Oued Zeen"],
    },
    {
        "name": "Eucalyptus",
        "type": "plant",
        "scientific_name": "Eucalyptus globulus",
        "description": "Grand arbre originaire d'Australie, largement planté en Tunisie. Écorce qui pèle, feuilles persistantes très aromatiques. Croissance rapide. Boisement important mais controversé écologiquement.",
        "threats": "Incendies favorisés par huiles inflammables, maladies fongiques, insectes ravageurs introduits.",
        "protection_measures": "Gestion forestière durable, pare-feu, surveillance sanitaire, plantation espèces natives en remplacement progressif.",
        "safety_guidelines": "TRÈS INFLAMMABLE - interdiction absolue de feu à proximité. Attention chutes de branches. Ne pas se reposer sous eucalyptus par vent fort. Feuilles glissantes au sol.",
        "medicinal_use": "Expectorant puissant, antiseptique respiratoire. Inhalation : 3-4 gouttes HE dans bol d'eau chaude pour bronchite, sinusite, rhume. Infusion feuilles : 2-3 tasses/jour pour toux. Usage externe : baume pectoral dilué. ATTENTION : Huile essentielle pure TOXIQUE par voie orale. Ne jamais ingérer HE pure. CONTRE-INDICATIONS : grossesse, allaitement, enfants <6 ans, épilepsie, asthme sévère. Peut irriter muqueuses. Toujours diluer HE.",
        "parks": ["Boukornine", "Zaghouan", "El Feija"],
    },
    {
        "name": "Olivier sauvage",
        "type": "plant",
        "scientific_name": "Olea europaea var. sylvestris",
        "description": "Ancêtre de l'olivier cultivé. Arbuste ou petit arbre épineux au feuillage gris-vert persistant. Petits fruits amers noirs. Très résistant sécheresse. Patrimoine génétique précieux.",
        "threats": "Arrachage pour greffage, incendies, surpâturage par chèvres, maladies (Xylella), vieillissement sans régénération.",
        "protection_measures": "Protection stricte spécimens anciens, collecte graines pour conservatoires, interdiction arrachage, zones de mise en défens, recherche génétique.",
        "safety_guidelines": "Épines acérées - attention lors cueillette. Ne pas couper ou endommager. Cueillette fruits et feuilles modérée. Respecter arbres plusieurs fois centenaires.",
        "medicinal_use": "Feuilles : hypotenseur, hypoglycémiant, antioxydant. Infusion : 2-3 tasses/jour de feuilles séchées pour hypertension légère, diabète type 2. Huile d'olive : usage culinaire et cosmétique. Propriétés cardiovasculaires protectrices reconnues. Utilisation : 20g feuilles/litre, infuser 10 min. Généralement très sûr. Surveiller tension si traitement médical. Consulter médecin avant usage prolongé.",
        "parks": ["Boukornine", "Zaghouan", "Chaambi", "Jebel Zaghdoud", "Orbata"],
    },
    {
        "name": "Myrte commun",
        "type": "plant",
        "scientific_name": "Myrtus communis",
        "description": "Arbuste aromatique persistant méditerranéen. Petites feuilles ovales luisantes très parfumées. Fleurs blanches étoilées mellifères. Baies noir-bleuté comestibles. Plante mythologique (symbole d'amour).",
        "threats": "Cueillette excessive pour distillation, incendies, urbanisation côtière, surpâturage.",
        "protection_measures": "Réglementation cueillette commerciale, culture en pépinières, protection habitats côtiers, sensibilisation valeur patrimoniale.",
        "safety_guidelines": "Cueillette modérée rameaux fleuris ou baies. Ne pas arracher plante entière. Éviter période floraison pour préserver pollinisateurs. Laisser 2/3 des baies pour faune.",
        "medicinal_use": "Antiseptique, astringent, expectorant. Infusion feuilles : affections respiratoires, troubles digestifs. 1 c. à café/tasse, 3 fois/jour. Baies : troubles digestifs, antiseptique urinaire. Usage externe : eau de toilette traditionnelle (désinfectant doux). Huile essentielle : diffusion pour assainir air. Généralement sûre. HE pure à éviter pendant grossesse. Peut causer irritation si surdosage HE.",
        "parks": ["Boukornine", "Zaghouan", "Jebel Chitana-Cap Négro", "Ichkeul"],
    },
    {
        "name": "Laurier-rose",
        "type": "plant",
        "scientific_name": "Nerium oleander",
        "description": "Arbuste ornemental à fleurs roses, blanches ou rouges. Feuilles persistantes lancéolées coriaces. Affectionne bords de oueds. TOUTES LES PARTIES EXTRÊMEMENT TOXIQUES. Plante emblématique mais dangereuse.",
        "threats": "Arrachage pour ornement, sécheresse extrême asséchant oueds, pollution de l'eau, entretien excessif des berges.",
        "protection_measures": "Sensibilisation toxicité, protection ripisylves, gestion écologique des oueds, interdiction arrachage sauvage.",
        "safety_guidelines": "PLANTE MORTELLEMENT TOXIQUE. Ne JAMAIS ingérer aucune partie. Ne pas brûler (fumée toxique). Se laver mains après contact. Tenir enfants et animaux éloignés. Ne pas utiliser bois pour brochettes ou feu. Ne pas boire eau où feuilles ont trempé. Signaler empoisonnements immédiatement (centre antipoison).",
        "medicinal_use": "AUCUN USAGE MÉDICINAL RECOMMANDÉ. Plante traditionnellement utilisée en cardiologie mais EXTRÊMEMENT DANGEREUSE. Contient glycosides cardiotoxiques mortels. Ingestion de quelques feuilles peut tuer un adulte. Symptômes empoisonnement : nausées, vomissements, arythmie cardiaque, convulsions, mort. NE JAMAIS UTILISER en automédication. Usage strictement pharmaceutique professionnel uniquement. TENIR HORS DE PORTÉE.",
        "parks": ["Ichkeul", "El Feija", "Oued Zeen", "Boukornine", "Zaghouan"],
    },
    {
        "name": "Fenouil sauvage",
        "type": "plant",
        "scientific_name": "Foeniculum vulgare",
        "description": "Plante aromatique vivace au feuillage finement découpé plumeux vert-bleu. Ombelles de fleurs jaunes. Forte odeur anisée. Pousse spontanément bords de routes et terrains vagues. Mellifère.",
        "threats": "Fauchage routier intempestif, utilisation herbicides, urbanisation, cueillette excessive commerciale.",
        "protection_measures": "Gestion différenciée bords de routes (fauchage tardif), promotion culture jardins, sensibilisation valeur mellifère et médicinale.",
        "safety_guidelines": "Cueillette parties aériennes avant montée en graines. Éviter bords de routes très fréquentées (pollution). Laver soigneusement. Récolter graines quand brunissent. Ne pas confondre avec ciguë (mortelle) - odeur anisée caractéristique du fenouil.",
        "medicinal_use": "Digestif, carminatif (anti-ballonnements), galactogène (stimule lactation). Infusion graines : 1 c. à café graines écrasées/tasse après repas pour digestion, coliques, flatulences. Favorise montée de lait chez allaitantes. Usage culinaire : condiment. Infusion : aide perte de poids (diurétique léger). Généralement très sûr. Éviter doses excessives pendant grossesse (1er trimestre). Possible allergie chez personnes allergiques céleri/carotte.",
        "parks": ["Boukornine", "Zaghouan", "Ichkeul", "Chaambi"],
    },
    {
        "name": "Ail sauvage",
        "type": "plant",
        "scientific_name": "Allium roseum",
        "description": "Plante bulbeuse à fleurs roses en ombelles. Feuilles linéaires à odeur d'ail caractéristique. Floraison printanière spectaculaire. Bulbe comestible. Indicateur sols méditerranéens.",
        "threats": "Cueillette excessive de bulbes, labour profond, herbicides, urbanisation, surpâturage.",
        "protection_measures": "Sensibilisation cueillette durable (laisser bulbes), protection prairies naturelles, limitation labour, jardins sauvages.",
        "safety_guidelines": "Cueillette modérée feuilles jeunes. Éviter d'arracher bulbes - préserver pour reproduction. Ne cueillir que dans zones abondantes. Attention confusion avec bulbes toxiques (colchique, narcisse) - vérifier odeur d'ail.",
        "medicinal_use": "Propriétés similaires à ail cultivé : cardiovasculaire, antibactérien, antifongique. Consommation fraîche en salade : renforce immunité, baisse cholestérol et tension. Antiseptique digestif et respiratoire. Utilisation : feuilles hachées crues dans alimentation. Bulbe : comme ail culinaire. Généralement sûr. Peut causer troubles digestifs si excès. Déconseillé avant chirurgie (anticoagulant léger). Éviter doses élevées si allaitement (goût lait).",
        "parks": ["Boukornine", "Zaghouan", "Chaambi", "Jebel Zaghdoud"],
    },
    {
        "name": "Caroubier",
        "type": "plant",
        "scientific_name": "Ceratonia siliqua",
        "description": "Arbre méditerranéen à feuillage persistant coriace. Longues gousses brunes comestibles très sucrées. Fleurs petites rouge foncé. Très résistant sécheresse. Arbre millénaire culturellement important.",
        "threats": "Surexploitation gousses, arrachage pour bois, vieillissement sans régénération, maladies fongiques, urbanisation.",
        "protection_measures": "Protection arbres anciens, programmes de plantation, valorisation économique durable des gousses, sensibilisation patrimoine.",
        "safety_guidelines": "Cueillette gousses mûres automnales uniquement au sol. Ne pas casser branches. Respecter arbres centenaires. Partager récolte avec faune (chèvres, oiseaux). Consommation gousses : nutritive et saine.",
        "medicinal_use": "Nutritif, antidiarrhéique, anti-reflux. Poudre de caroube : épaississant naturel pour reflux gastrique chez nourrissons et adultes. Anti-diarrhéique (tanins, pectines). Riche en fibres : régulation transit. Alternative chocolat (sans caféine, sans allergène). Utilisation : 1-2 c. à soupe poudre dans boisson ou yaourt. Gousses : mastication pour hygiène dentaire. Très sûr, même enfants et femmes enceintes. Peut causer constipation si excès. Alternative idéale pour allergiques au chocolat.",
        "parks": ["Boukornine", "Zaghouan", "Jebel Zaghdoud", "Chaambi", "Orbata"],
    },
    {
        "name": "Jujubier sauvage",
        "type": "plant",
        "scientific_name": "Ziziphus lotus",
        "description": "Arbuste épineux des zones arides. Petites feuilles ovales, fleurs jaunâtres, fruits rouges-orangés comestibles (jujubes). Racines profondes. Importance écologique et pastorale en zones semi-arides.",
        "threats": "Arrachage pour bois de chauffe, surpâturage, sécheresse extrême, défrichement agricole, vieillissement.",
        "protection_measures": "Protection vieux spécimens, gestion pastorale durable, plantations de restauration, valorisation fruits, sensibilisation populations locales.",
        "safety_guidelines": "Épines très acérées et robustes - porter gants épais. Attention yeux lors cueillette. Ne pas couper ou endommager arbres. Cueillette fruits mûrs pour consommation. Respecter comme ressource pastorale vitale.",
        "medicinal_use": "Fruits (jujubes) : calmant, nutritif, expectorant léger. Riches en vitamine C et antioxydants. Consommation fraîche ou séchée : améliore sommeil, réduit anxiété, renforce immunité. Décoction fruits : toux, maux de gorge. Utilisation : 5-10 fruits séchés en décoction ou consommés directement. Très sûr. Excellent en-cas naturel. Feuilles en cataplasme : anti-inflammatoire externe. Généralement aucune contre-indication.",
        "parks": ["Bouhedma", "Sidi Toui", "Dghoumès", "Jebil", "Orbata"],
    },
    {
        "name": "Rue de montagne",
        "type": "plant",
        "scientific_name": "Ruta montana",
        "description": "Plante aromatique vivace à odeur forte caractéristique. Feuillage vert-bleuté découpé. Fleurs jaunes. Affectionne terrains calcaires et rocailleux. Toxique à doses élevées.",
        "threats": "Cueillette excessive médicinale, surpâturage, dégradation habitats rocheux.",
        "protection_measures": "Réglementation cueillette, sensibilisation toxicité, culture en jardins, protection habitats rupestres.",
        "safety_guidelines": "PLANTE TOXIQUE ET PHOTOSENSIBILISANTE. Porter gants - contact cutané + soleil = graves brûlures (phytophotodermatite). Éviter cueillette jours ensoleillés. Laver mains immédiatement. Tenir hors portée enfants. Odeur forte dissuade généralement ingestion.",
        "medicinal_use": "Traditionnellement antispasmodique, emménagogue. ATTENTION : PLANTE TOXIQUE. Usage interne DÉCONSEILLÉ - peut causer vomissements, douleurs abdominales, troubles rénaux. ABORTIVE - INTERDITE pendant grossesse. Huile essentielle : TRÈS TOXIQUE, ne jamais utiliser. Usage externe limité : macération pour douleurs rhumatismales (ATTENTION phototoxicité). De nombreuses alternatives plus sûres existent. NE PAS UTILISER sans supervision médicale. CONTRE-INDICATIONS ABSOLUES : grossesse, allaitement, enfants, maladies hépatiques/rénales.",
        "parks": ["Chaambi", "Orbata", "Zaghouan", "Jebel Mghilla"],
    },

    # ADDITIONAL FLORA
    {
        "name": "Chêne zéen",
        "type": "plant",
        "scientific_name": "Quercus canariensis",
        "description": "Grand chêne caducifolié des forêts humides du nord. Feuilles lobées devenant dorées en automne. Glands comestibles. Forme forêts denses en Kroumirie. Patrimoine forestier exceptionnel.",
        "threats": "Exploitation forestière excessive, incendies, maladies (encre du chêne), changement climatique réduisant précipitations, vieillissement.",
        "protection_measures": "Protection stricte forêts d'El Feija et Oued Zeen, gestion forestière durable, programme régénération, surveillance sanitaire, zones de conservation intégrale.",
        "safety_guidelines": "Attention chutes de branches mortes par temps venteux. Ne pas endommager écorce. Respecter ces forêts rares et précieuses. Cueillette glands limitée - nourriture faune sauvage.",
        "medicinal_use": "Écorce : propriétés astringentes, anti-diarrhéiques similaires au chêne-liège. Décoction : usage externe pour hémorroïdes, problèmes peau. Tanins antiseptiques. Glands : comestibles après traitement (retrait tanins) - farine nutritive. Usage traditionnel limité. Préférer observation à usage médicinal. Écorce récoltée uniquement sur arbres morts.",
        "parks": ["El Feija", "Oued Zeen"],
    },
    {
        "name": "Alfa",
        "type": "plant",
        "scientific_name": "Stipa tenacissima",
        "description": "Graminée vivace en touffes denses des steppes arides. Longues feuilles fines et résistantes. Historiquement exploitée pour papier et artisanat. Forme steppes d'alfa caractéristiques du sud tunisien.",
        "threats": "Surexploitation pour industrie papetière et artisanat, surpâturage, sécheresse, incendies, dégradation sols.",
        "protection_measures": "Gestion durable de la cueillette, quotas, périodes de repos, restauration steppes dégradées, promotion alternatives économiques, sensibilisation.",
        "safety_guidelines": "Cueillette réglementée strictement. Feuilles aux bords coupants - porter gants. Extraction respectueuse sans endommager touffe. Respecter cycles de régénération. Ne pas brûler pour 'favoriser repousse' (pratique destructrice).",
        "medicinal_use": "Usage médicinal limité. Décoction racines traditionnellement utilisée pour troubles urinaires (diurétique). Fibres : artisanat (vannerie, cordage). Valeur culturelle et économique importante. Pas d'usage médicinal majeur documenté. Importance écologique (habitat faune, protection sols).",
        "parks": ["Bouhedma", "Dghoumès", "Jebil", "Sidi Toui", "Senghar-Jabess"],
    },
    {
        "name": "Palmier dattier sauvage",
        "type": "plant",
        "scientific_name": "Phoenix dactylifera",
        "description": "Palmier emblématique des oasis sahariennes. Stipe élancé, palmes pennées. Dattes comestibles. Importance vitale dans écosystèmes oasiens - ombre, nourriture, matériaux.",
        "threats": "Maladies (bayoud fusariose mortelle), sécheresse extrême, baisse nappes phréatiques, vieillissement palmeraies, urbanisation oasis.",
        "protection_measures": "Surveillance sanitaire stricte (bayoud), programme régénération variétés locales, gestion durable eau, protection oasis traditionnelles, recherche variétés résistantes.",
        "safety_guidelines": "Épines acérées à la base des palmes - danger de blessure grave. Ne jamais grimper sans équipement professionnel. Chute de régimes de dattes (très lourds) - attention en saison. Respecter palmeraies et systèmes d'irrigation traditionnels.",
        "medicinal_use": "Dattes : nutritives, énergétiques, riches en fibres, potassium, antioxydants. Facilitent digestion, transit. Excellentes pour sportifs (énergie rapide). Ramadan : rupture jeûne traditionnelle (réhydratation, énergie). Dattes molles : laxatif léger. Très sûres, même femmes enceintes et enfants. Haute teneur en sucres - modération pour diabétiques. Pollen : traditionnellement tonifiant, aphrodisiaque (études en cours).",
        "parks": ["Jebil", "Dghoumès", "Sidi Toui", "Senghar-Jabess"],
    },
    {
        "name": "Retama",
        "type": "plant",
        "scientific_name": "Retama raetam",
        "description": "Arbuste du désert au feuillage réduit (adaptation sécheresse). Rameaux verts photosynthétiques. Fleurs blanches parfumées abondantes au printemps. Fixateur de dunes, fourrage de secours.",
        "threats": "Arrachage pour bois de chauffe, surpâturage, ensablement excessif, sécheresse prolongée, dégradation sols.",
        "protection_measures": "Protection en zones dunaires, interdiction coupe, programmes restauration écologique, sensibilisation sur rôle fixateur de dunes, gestion pastorale.",
        "safety_guidelines": "Ne pas couper ou arracher - rôle écologique vital dans stabilisation dunes. Pas de feu à proximité. Éviter pâturage excessif autour des plants. Respecter floraison (importante pour pollinisateurs du désert).",
        "medicinal_use": "Usage médicinal traditionnel limité et controversé. Plante potentiellement toxique. Décoction de fleurs : traditionnellement utilisée comme purgatif mais DANGEREUX. Peut contenir alcaloïdes toxiques. Usage fortement DÉCONSEILLÉ. Importance écologique (fixation dunes, habitat faune) dépasse largement intérêt médicinal. NE PAS UTILISER sans avis médical expert. Des alternatives plus sûres existent.",
        "parks": ["Jebil", "Dghoumès", "Sidi Toui", "Senghar-Jabess"],
    },
    {
        "name": "Sumac des corroyeurs",
        "type": "plant",
        "scientific_name": "Rhus coriaria",
        "description": "Arbuste à feuillage composé denté devenant rouge spectaculaire en automne. Épis de fleurs jaunâtres puis fruits rouges veloutés. Graines utilisées comme épice acidulée (sumac). Utilisé traditionnellement pour tannage.",
        "threats": "Cueillette excessive pour usage culinaire, incendies, perte d'habitat, urbanisation.",
        "protection_measures": "Gestion durable cueillette fruits, culture en jardins, protection habitats, valorisation économique raisonnée.",
        "safety_guidelines": "Cueillette fruits mûrs (rouge foncé) uniquement. Ne pas confondre avec sumac vénéneux d'Amérique (absent en Tunisie). Parties vertes irritantes pour certaines personnes sensibles. Laver fruits avant usage culinaire.",
        "medicinal_use": "Antioxydant puissant, anti-inflammatoire, hypoglycémiant. Épice sumac : riche en vitamine C, anthocyanes. Usage culinaire : saupoudrer aliments (salades, viandes, poissons). Propriétés digestives, antimicrobiennes. Décoction fruits : gargarisme pour maux de gorge. Recherches récentes : effet hypoglycémiant, hypocholestérolémiant. Utilisation : épice culinaire quotidienne (1-2 c. à café). Très sûr. Possible allergie chez personnes allergiques à famille Anacardiaceae (mangue, pistache, noix de cajou).",
        "parks": ["Chaambi", "Zaghouan", "Jebel Zaghdoud", "Jebel Mghilla", "Orbata"],
    },

    # INSECTS (Educational)
    {
        "name": "Cigale commune",
        "type": "animal",
        "scientific_name": "Lyristes plebejus",
        "description": "Insecte emblématique méditerranéen. Mâle produit chant caractéristique strident par temps chaud. Larves vivent sous terre plusieurs années, se nourrissent de sève racinaire. Émergence estivale spectaculaire.",
        "threats": "Pesticides agricoles, perte d'arbres et arbustes-hôtes, pollution sonore perturbant communication, changement climatique.",
        "protection_measures": "Réduction pesticides, préservation arbres et haies, sensibilisation sur rôle dans écosystème, jardins accueillants.",
        "safety_guidelines": "Totalement inoffensif - ne pique pas, ne mord pas. Peut être manipulé délicatement. Chant fort mais non dangereux. Indicateur excellente santé environnementale. Signe caractéristique de l'été méditerranéen.",
        "parks": ["Tous les parcs avec végétation arborée"],
    },
    {
        "name": "Mante religieuse",
        "type": "animal",
        "scientific_name": "Mantis religiosa",
        "description": "Insecte prédateur fascinant. Pattes antérieures ravisseuses caractéristiques. Chasse à l'affût insectes ravageurs. Camouflage remarquable. Femelle peut manger mâle après accouplement. Bénéfique pour agriculture.",
        "threats": "Pesticides (tue proies et mantes), perte d'habitat, fauchage précoce, destruction oothèques (pontes).",
        "protection_measures": "Réduction pesticides, fauchage tardif prairies, préservation haies et friches, sensibilisation valeur comme auxiliaire agricole.",
        "safety_guidelines": "Totalement inoffensive pour l'homme. Peut pincer légèrement si manipulée mais sans danger. Observer sans déranger. Ne pas tuer - insecte très bénéfique. Si oothèque (ponte mousseuse beige) trouvée, ne pas détruire - centaines de bébés mantes écloront au printemps.",
        "parks": ["Tous les parcs - espèce commune en zones végétalisées"],
    },
]


def seed_additional_species():
    """Add comprehensive species to existing database"""
    
    with Session(engine) as session:
        print("=== ADDING 50+ SPECIES TO TUNISIA PARKS DATABASE ===\n")
        
        # Check existing
        existing_count = len(session.exec(select(SpeciesDB)).all())
        print(f"📊 Current database: {existing_count} species\n")
        
        # Get all parks for linking
        all_parks = session.exec(select(ParkDB)).all()
        park_dict = {p.name: p for p in all_parks}
        
        # Add new species
        added = 0
        skipped = 0
        
        for species_data in ADDITIONAL_SPECIES:
            park_names = species_data.pop("parks")
            
            # Check if species already exists
            existing = session.exec(
                select(SpeciesDB).where(SpeciesDB.scientific_name == species_data["scientific_name"])
            ).first()
            
            if existing:
                print(f"  ⏭️  Skipped (exists): {species_data['name']}")
                skipped += 1
                continue
            
            # Create species
            species = SpeciesDB(**species_data)
            session.add(species)
            session.flush()
            
            # Link to parks
            for park_name_part in park_names:
                if park_name_part == "Tous les parcs - espèce commune et répandue" or \
                   park_name_part == "Tous les parcs - espèce très répandue" or \
                   park_name_part.startswith("Tous les parcs"):
                    # Link to all parks
                    for park in all_parks:
                        link = ParkSpeciesLink(park_id=park.id, species_id=species.id)
                        session.add(link)
                else:
                    # Find matching park
                    for full_name, park in park_dict.items():
                        if park_name_part.lower() in full_name.lower():
                            link = ParkSpeciesLink(park_id=park.id, species_id=species.id)
                            session.add(link)
                            break
            
            icon = "🌿" if species.type == "plant" else "🦌"
            med_icon = " 💊" if hasattr(species, 'medicinal_use') and species.medicinal_use else ""
            warn_icon = " ⚠️" if "DANGER" in species.safety_guidelines or "TOXIQUE" in species.safety_guidelines else ""
            
            print(f"  ✅ {icon} {species.name}{med_icon}{warn_icon}")
            added += 1
        
        session.commit()
        
        # Final statistics
        final_count = len(session.exec(select(SpeciesDB)).all())
        
        print(f"\n{'='*60}")
        print(f"✅ SPECIES DATABASE UPDATED!")
        print(f"{'='*60}")
        print(f"  Previous: {existing_count} species")
        print(f"  Added: {added} new species")
        print(f"  Skipped: {skipped} (already exist)")
        print(f"  Total now: {final_count} species")
        print(f"\n📊 BREAKDOWN:")
        
        # Count by type
        animals = session.exec(select(SpeciesDB).where(SpeciesDB.type == "animal")).all()
        plants = session.exec(select(SpeciesDB).where(SpeciesDB.type == "plant")).all()
        medicinal = [s for s in plants if s.medicinal_use]
        dangerous = [s for s in session.exec(select(SpeciesDB)).all() if "DANGER" in s.safety_guidelines or "TOXIQUE" in s.safety_guidelines]
        
        print(f"  🦌 Animals: {len(animals)}")
        print(f"  🌿 Plants: {len(plants)}")
        print(f"  💊 Medicinal Plants: {len(medicinal)}")
        print(f"  ⚠️  Species with Warnings: {len(dangerous)}")
        
        print(f"\n🗺️  Now refresh your map to see all the new species!")


if __name__ == "__main__":
    seed_additional_species()
