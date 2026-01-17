#Complete seed script with all 17 Tunisia National Parks
#Including fauna, flora, threats, protection measures, safety guidelines
#Run with: python seed_complete_parks.py


from sqlmodel import Session, select, delete
from database import engine, get_engine, init_db
from models import ParkDB, SpeciesDB, ParkSpeciesLink, TrailDB
from typing import List, Dict

# Complete list of all 17 Tunisia National Parks
TUNISIA_PARKS_COMPLETE = [
    {
        "name": "Parc National d'Ichkeul",
        "governorate": "Bizerte",
        "description": "Site du patrimoine mondial de l'UNESCO depuis 1980. Lac et marécages accueillant des centaines de milliers d'oiseaux migrateurs : canards, oies, cigognes, flamants roses. Zone humide d'importance internationale avec plus de 500 espèces de plantes et 229 espèces animales.",
        "latitude": 37.1617,
        "longitude": 9.6742,
        "area_km2": 126.0,
    },
    {
        "name": "Parc National de Boukornine",
        "governorate": "Ben Arous",
        "description": "Situé à proximité de Tunis, protège le djebel Boukornine avec des forêts de thuyas de Berbérie. Sentiers de randonnée offrant des vues panoramiques. Biodiversité méditerranéenne riche avec nombreuses espèces d'oiseaux.",
        "latitude": 36.6833,
        "longitude": 10.2167,
        "area_km2": 19.39,
    },
    {
        "name": "Parc National de Zaghouan",
        "governorate": "Zaghouan",
        "description": "Entoure le djebel Zaghouan et protège les sources historiques alimentant l'aqueduc romain de Carthage. Forêts de genévrier de Phénicie, pins d'Alep et habitat pour rapaces. Site historique et naturel important.",
        "latitude": 36.4000,
        "longitude": 10.1500,
        "area_km2": 20.4,
    },
    {
        "name": "Parc National de Zembra et Zembretta",
        "governorate": "Nabeul",
        "description": "Îles protégées dans le golfe de Tunis. Écosystèmes insulaires uniques avec colonies d'oiseaux marins dont le puffin cendré (142 000 couples). Accessible uniquement par bateau avec autorisation. Zone marine protégée.",
        "latitude": 37.1167,
        "longitude": 10.8167,
        "area_km2": 50.95,
    },
    {
        "name": "Parc National d'El Feija",
        "governorate": "Jendouba",
        "description": "La région la plus humide de Tunisie en Kroumirie. Forêts denses de chênes zéens et chênes-lièges. Zone de protection du cerf de Barbarie. Plus de 20 espèces de mammifères, 70 espèces d'oiseaux et 20 espèces de reptiles.",
        "latitude": 36.5500,
        "longitude": 8.5333,
        "area_km2": 26.32,
    },
    {
        "name": "Parc National de Chaambi",
        "governorate": "Kasserine",
        "description": "Abrite le plus haut sommet de Tunisie (djebel Chaambi, 1544m). Dernières forêts de pins d'Alep de haute altitude. Habitat de la gazelle de montagne, mouflon à manchettes et nombreuses espèces endémiques. Zone de montagne protégée.",
        "latitude": 35.1667,
        "longitude": 8.6667,
        "area_km2": 67.23,
    },
    {
        "name": "Parc National de Bouhedma",
        "governorate": "Sidi Bouzid",
        "description": "Pseudo-savane à acacia raddiana. Programme réussi de réintroduction de l'oryx algazelle et gazelle dorcas. Écosystème de steppe aride unique. Conservation d'espèces sahélo-sahariennes menacées.",
        "latitude": 34.5333,
        "longitude": 9.6667,
        "area_km2": 164.88,
    },
    {
        "name": "Parc National de Jebil",
        "governorate": "Kebili",
        "description": "Le plus grand parc national de Tunisie dans le Grand Erg Oriental. Dunes de sable spectaculaires, gravures rupestres préhistoriques. Faune saharienne adaptée aux conditions extrêmes. Paysages désertiques préservés.",
        "latitude": 33.3000,
        "longitude": 9.5000,
        "area_km2": 1500.0,
    },
    {
        "name": "Parc National de Dghoumès",
        "governorate": "Tozeur",
        "description": "Écosystème saharien avec dunes, oasis et zones humides salées. Biodiversité du Sahara avec gazelles et oiseaux du désert. Efforts continus de conservation et restauration écologique depuis 2001.",
        "latitude": 33.9000,
        "longitude": 8.4500,
        "area_km2": 80.0,
    },
    {
        "name": "Parc National de Sidi Toui",
        "governorate": "Medenine",
        "description": "Steppe et semi-désert. Programme de réintroduction de l'autruche à cou rouge du Maroc. Conservation de l'oryx et gazelles. Végétation de jujubiers et esparto. Proche de la frontière libyenne.",
        "latitude": 33.0833,
        "longitude": 10.3167,
        "area_km2": 63.15,
    },
    {
        "name": "Parc National de l'Orbata",
        "governorate": "Gafsa",
        "description": "Écosystème de transition entre le Tell et le Sahara. Forêts de genévriers rouges et biodiversité de montagne aride. 123 espèces de vertébrés dont 3 amphibiens, 24 reptiles, 77 oiseaux et 19 mammifères. Site d'écotourisme scientifique.",
        "latitude": 34.7000,
        "longitude": 8.7500,
        "area_km2": 57.46,
    },
    {
        "name": "Parc National de Jebel Chitana-Cap Négro",
        "governorate": "Béja",
        "description": "Formations de chênes-lièges et écosystèmes côtiers méditerranéens. Zone de transition entre forêts humides et côte. Biodiversité riche en espèces forestières et maritimes.",
        "latitude": 37.0500,
        "longitude": 8.9000,
        "area_km2": 101.22,
    },
    {
        "name": "Parc National de Jebel Serj",
        "governorate": "Siliana",
        "description": "Forêts de chênes-lièges et écosystèmes montagneux. Conservation de la flore et faune forestière méditerranéenne. Zone tampon importante entre régions agricoles et espaces naturels.",
        "latitude": 36.1000,
        "longitude": 9.4000,
        "area_km2": 17.20,
    },
    {
        "name": "Parc National de Jebel Mghilla",
        "governorate": "Kasserine",
        "description": "Écosystèmes de pins d'Alep. Faune diversifiée : hyène rayée, sanglier, chacal, renard roux, porc-épic, genette, mangouste, hérisson, tortue terrestre, serpent de Montpellier, perdrix, caille, tourterelle, aigle royal, aigle de Bonelli, faucon crécerelle.",
        "latitude": 34.9000,
        "longitude": 9.3000,
        "area_km2": 162.49,
    },
    {
        "name": "Parc National de Jebel Zaghdoud",
        "governorate": "Kairouan",
        "description": "Écosystème de caroubiers et chênes. Paysage montagneux avec pins d'Alep, oliviers lentisques, genévriers rouges et sumacs. Paradis pour botanistes avec flore adaptée aux différentes altitudes.",
        "latitude": 35.7000,
        "longitude": 9.8000,
        "area_km2": 17.92,
    },
    {
        "name": "Parc National de Oued Zeen",
        "governorate": "Jendouba",
        "description": "Formation de chênes zéens, écosystème forestier humide. Biodiversité forestière riche avec nombreuses espèces de mammifères et oiseaux forestiers. Cours d'eau et zones ripariennes.",
        "latitude": 36.5000,
        "longitude": 8.7000,
        "area_km2": 67.00,
    },
    {
        "name": "Parc National de Senghar-Jabess",
        "governorate": "Tataouine",
        "description": "Le deuxième plus grand parc de Tunisie. Écosystèmes désertiques du grand sud. Conservation d'espèces adaptées aux conditions sahariennes extrêmes. Paysages rocheux et zones d'erg.",
        "latitude": 31.5000,
        "longitude": 9.8000,
        "area_km2": 2870.00,
    },
]

# Fauna and Flora database with threats, protection, safety, and medicinal properties
SPECIES_DATA = [
    # MAMMALS - Endangered and Protected
    {
        "name": "Cerf de Barbarie",
        "type": "animal",
        "scientific_name": "Cervus elaphus barbarus",
        "description": "Sous-espèce endémique de cerf vivant dans les forêts humides du nord. Pelage brun-roux, bois ramifiés chez les mâles. Herbivore se nourrissant de feuilles, écorces et herbes.",
        "threats": "Chasse illégale, perte d'habitat forestier, fragmentation des populations, maladies transmises par le bétail domestique, dérangement humain pendant la reproduction.",
        "protection_measures": "Programme de réintroduction à El Feija, zones de protection stricte dans les parcs, patrouilles anti-braconnage renforcées, corridors écologiques entre habitats, monitoring GPS des populations, sensibilisation des communautés locales.",
        "safety_guidelines": "Observer à distance minimale de 50 mètres. Ne jamais nourrir les cerfs. Éviter tout contact pendant la saison du rut (septembre-octobre) car les mâles sont agressifs. Rester silencieux pour ne pas les effrayer. Ne jamais s'approcher des faons seuls - la mère est probablement proche. Utiliser des jumelles pour l'observation. Interdiction absolue de chasser ou capturer.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Cervus_elaphus_barbarus.jpg/800px-Cervus_elaphus_barbarus.jpg",
        "parks": ["El Feija", "Oued Zeen"],
    },
    {
        "name": "Oryx algazelle",
        "type": "animal",
        "scientific_name": "Oryx dammah",
        "description": "Grande antilope du Sahara à cornes longues et recourbées. Pelage blanc avec des marques brunes sur la tête. Adapté à la vie désertique, peut survivre sans boire pendant de longues périodes.",
        "threats": "Éteint à l'état sauvage en Afrique. En Tunisie : braconnage persistant, compétition avec le bétail domestique pour les pâturages, sécheresses prolongées, dégradation de l'habitat par surpâturage.",
        "protection_measures": "Programme de réintroduction réussi depuis 1985 avec environ 200 individus dans quatre aires protégées. Surveillance 24h/24 par les gardes forestiers. Clôtures de protection dans certaines zones. Reproduction en captivité comme assurance. Collaboration internationale pour la conservation. Alimentation supplémentaire pendant les sécheresses.",
        "safety_guidelines": "Maintenir une distance de sécurité de 100 mètres. Les oryx peuvent charger s'ils se sentent menacés - leurs cornes sont dangereuses. Ne jamais s'interposer entre un adulte et son petit. Observer depuis un véhicule quand possible. Éviter les mouvements brusques. Ne pas tenter de toucher ou nourrir. En cas de charge, reculer lentement sans courir. Respecter absolument les zones clôturées.",
        "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8c/Scimitar-horned_Oryx%2C_Oryx_dammah.JPG/800px-Scimitar-horned_Oryx%2C_Oryx_dammah.JPG",
        "parks": ["Bouhedma", "Sidi Toui", "Jebil", "Dghoumès"],
    },
    {
        "name": "Gazelle dorcas",
        "type": "animal",
        "scientific_name": "Gazella dorcas",
        "description": "Petite gazelle élégante adaptée aux milieux arides. Pelage beige sable, cornes annelées, pattes fines. Herbivore se nourrissant d'herbes, feuilles d'acacias et plantes du désert.",
        "threats": "Braconnage intensif, perte d'habitat par agriculture extensive, compétition avec bétail domestique, sécheresse climatique, fragmentation des populations, prédation par chiens errants.",
        "protection_measures": "Réintroduction dans plusieurs parcs du sud, surveillance renforcée, programmes d'élevage en semi-captivité, restauration d'habitat, création de points d'eau, sensibilisation anti-braconnage, sanctions sévères pour capture illégale.",
        "safety_guidelines": "Observer à distance minimale de 30-50 mètres avec jumelles. Les gazelles sont craintives et s'enfuient facilement - éviter de les stresser. Ne jamais poursuivre en véhicule. Rester silencieux et éviter gestes brusques. Ne pas bloquer leur route de fuite. Interdiction de nourrir ou toucher. Les jeunes gazelles cachées dans les buissons ne sont pas abandonnées - ne pas les approcher.",
        "parks": ["Bouhedma", "Sidi Toui", "Jebil", "Dghoumès", "Senghar-Jabess"],
    },
    {
        "name": "Mouflon à manchettes",
        "type": "animal",
        "scientific_name": "Ammotragus lervia",
        "description": "Capridé robuste des zones montagneuses et semi-désertiques. Cornes massives recourbées, crinière caractéristique sur le poitrail. Excellent grimpeur vivant dans les falaises rocheuses.",
        "threats": "Chasse illégale pour viande et trophées, perte d'habitat montagneux, dérangement par activités humaines (randonnée, escalade), maladies du bétail, compétition avec chèvres domestiques.",
        "protection_measures": "Protection stricte dans Chaambi et Orbata, interdiction totale de chasse, zones de quiétude sans accès humain, surveillance des populations par caméras-pièges, éducation environnementale, réglementation du tourisme en montagne.",
        "safety_guidelines": "Observer uniquement depuis sentiers balisés à distance de 50-100 mètres. Les mouflons en hauteur peuvent faire tomber des pierres - attention sous les falaises. Mâles territoriaux potentiellement agressifs pendant le rut. Ne jamais grimper vers eux dans les rochers. Éviter période de mise-bas (mars-avril). Interdiction de nourrir. Respecter zones interdites d'accès.",
        "parks": ["Chaambi", "Orbata", "Bouhedma"],
    },
    {
        "name": "Chacal doré",
        "type": "animal",
        "scientific_name": "Canis aureus",
        "description": "Canidé de taille moyenne au pelage doré-gris. Omnivore opportuniste chassant petits mammifères, oiseaux et consommant fruits. Social, vit en couples ou petits groupes familiaux.",
        "threats": "Persécution par éleveurs (perçu comme nuisible), empoisonnement par rodenticides et pesticides, collisions routières, perte d'habitat, chasse illégale.",
        "protection_measures": "Sensibilisation sur rôle écologique (régulation rongeurs), interdiction d'empoisonnement, corridors écologiques, études scientifiques pour évaluation populations, programmes éducatifs dans écoles rurales.",
        "safety_guidelines": "Les chacals sont généralement craintifs et évitent l'homme. Observer à distance de 30 mètres minimum. Ne jamais nourrir - risque d'habituation dangereuse. Sécuriser nourriture en camping. Si approche inhabituelle, faire du bruit et reculer lentement. Ne jamais s'approcher d'un chacal malade ou blessé (risque de rage). Tenir enfants et animaux domestiques sous surveillance. Signaler comportement anormal aux gardes.",
        "parks": ["El Feija", "Oued Zeen", "Jebel Mghilla", "Chaambi", "Orbata"],
    },
    {
        "name": "Sanglier",
        "type": "animal",
        "scientific_name": "Sus scrofa",
        "description": "Mammifère robuste au pelage sombre. Omnivore fouillant le sol avec son groin. Vit en groupes familiaux (hardes). Actif surtout crépuscule et nuit.",
        "threats": "Chasse excessive, empoisonnement, perte d'habitat forestier, conflits avec agriculture (dégâts aux cultures), maladies (peste porcine).",
        "protection_measures": "Réglementation stricte de la chasse dans les parcs, zones tampons autour aires agricoles, surveillance sanitaire, études de population, gestion adaptative.",
        "safety_guidelines": "DANGER : Les sangliers peuvent être agressifs, surtout les femelles avec marcassins et les mâles pendant le rut. Maintenir distance de 50-100 mètres. Si rencontre proche, rester calme, parler d'une voix forte, reculer lentement sans courir. Ne jamais s'interposer entre laie et ses petits. En cas de charge, grimper sur un rocher ou dans un arbre. Éviter randonnées nocturnes dans leurs zones. Faire du bruit en marchant. Interdiction totale de nourrir.",
        "parks": ["El Feija", "Oued Zeen", "Jebel Chitana-Cap Négro", "Jebel Mghilla", "Boukornine"],
    },
    {
        "name": "Hyène rayée",
        "type": "animal",
        "scientific_name": "Hyaena hyaena",
        "description": "Carnivore-charognard nocturne au pelage gris rayé. Rôle écologique crucial d'équarrisseur naturel. Solitaire ou petits groupes. Excellent odorat.",
        "threats": "Persécution humaine due à superstitions, braconnage pour parties du corps (médecine traditionnelle), empoisonnement, collisions routières, perte d'habitat.",
        "protection_measures": "Protection légale totale, campagnes contre superstitions, études comportementales, surveillance populations, sensibilisation sur rôle écologique vital, sanctions sévères contre braconnage.",
        "safety_guidelines": "Les hyènes évitent généralement l'homme. Observer uniquement la nuit avec guide autorisé, distance 30-50 mètres. Ne jamais approcher, même si animal semble calme. Ne pas nourrir. Sécuriser campements et déchets. Morsure très puissante - ne jamais tenter de toucher. Si rencontre, faire du bruit et utiliser lampe. Ne pas courir. Signaler observations aux autorités du parc.",
        "parks": ["Jebel Mghilla", "Chaambi", "Orbata"],
    },
    {
        "name": "Autruche à cou rouge",
        "type": "animal",
        "scientific_name": "Struthio camelus camelus",
        "description": "Plus grand oiseau du monde, incapable de voler. Mâle noir avec cou et pattes rouges. Peut courir à 70 km/h. Régime omnivore opportuniste.",
        "threats": "Éteinte en Tunisie, réintroduite du Maroc. Menaces : braconnage pour plumes et œufs, prédation des œufs, sécheresse extrême, dérangement humain pendant nidification.",
        "protection_measures": "Programme de réintroduction à Sidi Toui, surveillance constante des nids, protection stricte pendant reproduction, alimentation supplémentaire si nécessaire, suivi GPS des individus.",
        "safety_guidelines": "DANGER : L'autruche peut être très dangereuse. Coups de pattes puissants pouvant tuer un homme. Maintenir distance minimum 50-100 mètres. Observer depuis véhicule. Ne jamais approcher un nid - parents extrêmement agressifs. En cas d'agression, courir en zigzag, chercher abri (arbre, rocher). Ne pas se coucher au sol. Éviter vêtements colorés qui attirent attention. Respecter strictement zones interdites.",
        "parks": ["Sidi Toui", "Jebil", "Senghar-Jabess"],
    },
    
    # BIRDS - Key Species
    {
        "name": "Flamant rose",
        "type": "animal",
        "scientific_name": "Phoenicopterus roseus",
        "description": "Grand échassier au plumage rose caractéristique. Se nourrit de petits crustacés et algues par filtration. Vit en colonies de milliers d'individus. Migrateur.",
        "threats": "Pollution des zones humides, dérangement humain pendant nidification, assèchement des lacs, changement salinité de l'eau, prédation des œufs.",
        "protection_measures": "Protection stricte d'Ichkeul (UNESCO), zones de quiétude interdites au public, gestion niveaux d'eau, monitoring des colonies, sensibilisation visiteurs, limitation accès pendant reproduction.",
        "safety_guidelines": "Observer uniquement depuis points d'observation aménagés, jumelles obligatoires. Distance minimale 100-200 mètres pour ne pas déranger colonies. Interdiction absolue d'approcher zones de nidification. Rester silencieux. Pas de drones. Éviter période de reproduction (avril-juin). Les flamants stressés s'envolent en masse - risque d'abandon des nids.",
        "parks": ["Ichkeul", "Dghoumès"],
    },
    {
        "name": "Puffin cendré",
        "type": "animal",
        "scientific_name": "Calonectris diomedea",
        "description": "Oiseau marin pélagique nichant en colonies sur îles. Plumage gris-brun dessus, blanc dessous. Excellent plongeur chassant poissons. Plus grande colonie de Méditerranée à Zembra (142 000 couples).",
        "threats": "Pollution marine plastique, surpêche réduisant ressources alimentaires, prédation par rats introduits, pollution lumineuse désorientant jeunes, changement climatique affectant proies.",
        "protection_measures": "Zembra classée réserve naturelle intégrale, accès strictement réglementé, campagnes dératisation, monitoring populations, études scientifiques, protection nids, sensibilisation pêcheurs.",
        "safety_guidelines": "Accès à Zembra uniquement avec autorisation officielle et guide agréé. Débarquement interdit pendant période de nidification (mars-octobre). Observer depuis bateau à distance minimale 100 mètres des falaises. Interdiction totale d'approcher colonies. Pas de lumières fortes la nuit. Respecter sentiers balisés si autorisation terrestre. Ne pas toucher œufs ou poussins.",
        "parks": ["Zembra et Zembretta"],
    },
    {
        "name": "Aigle royal",
        "type": "animal",
        "scientific_name": "Aquila chrysaetos",
        "description": "Grand rapace des montagnes. Envergure jusqu'à 2,3m. Plumage brun sombre avec nuque dorée. Chasse lièvres, perdrix, reptiles. Couple fidèle, niche sur falaises.",
        "threats": "Électrocution sur lignes électriques, empoisonnement par rodenticides, dérangement des aires de nidification, diminution proies, tir illégal.",
        "protection_measures": "Protection légale stricte, sécurisation lignes électriques dans zones sensibles, surveillance nids, zones de quiétude, interdiction escalade près des aires, sensibilisation.",
        "safety_guidelines": "Observer à grande distance (200-500m) avec télescope ou jumelles puissantes. Ne jamais approcher nid ou aire de chasse. Éviter zone de nidification février-juillet. L'aigle peut attaquer par piqué si nid menacé. Interdiction drones. Signaler observations avec localisation précise aux gardes pour monitoring.",
        "parks": ["Chaambi", "Jebel Mghilla", "Zaghouan", "Orbata"],
    },
    
    # FLORA - Trees and Medicinal Plants
    {
        "name": "Pin d'Alep",
        "type": "plant",
        "scientific_name": "Pinus halepensis",
        "description": "Conifère méditerranéen résistant à la sécheresse. Écorce grise se fissurant avec l'âge. Aiguilles groupées par deux. Cônes ovoïdes. Forme forêts en montagne.",
        "threats": "Incendies forestiers favorisés par sécheresse, coupes illégales pour bois, maladies fongiques, insectes ravageurs (chenille processionnaire), changement climatique.",
        "protection_measures": "Surveillance incendies avec tours de guet, pare-feu, reboisement après sinistres, interdiction coupes non autorisées, traitement chenilles processionnaires, corridors écologiques.",
        "safety_guidelines": "NE PAS TOUCHER les chenilles processionnaires (mars-mai) - urticantes dangereuses, allergies graves possibles. En cas de contact : rincer abondamment, consulter médecin. Ne pas allumer feux en forêt. Respecter interdictions accès période risque incendie. Rester sur sentiers balisés. Ne pas cueillir plantes. Signaler arbres malades ou morts.",
        "medicinal_use": "Résine (térébenthine) traditionnellement utilisée comme antiseptique externe et expectorant. Bourgeons en décoction pour affections respiratoires. ATTENTION : Usage interne déconseillé sans avis médical - peut être irritant.",
        "parks": ["Chaambi", "Boukornine", "Zaghouan", "Jebel Mghilla", "Jebel Zaghdoud"],
    },
    {
        "name": "Chêne-liège",
        "type": "plant",
        "scientific_name": "Quercus suber",
        "description": "Arbre à feuillage persistant caractérisé par son écorce épaisse de liège. Feuilles coriaces dentées. Produit glands. Écosystème forestier humide du nord.",
        "threats": "Surexploitation du liège, incendies, maladies (encre du chêne), vieillissement populations, manque de régénération naturelle, changement climatique.",
        "protection_measures": "Réglementation stricte exploitation liège, programme régénération, protection incendies, zones de conservation intégrale, études sanitaires, reboisement.",
        "safety_guidelines": "Ne pas écorcer ou endommager arbres - protection légale stricte. Attention aux chutes de branches mortes en période venteuse. Respecter période de récolte légale du liège (été). Ne pas faire de feu sous les arbres. Cueillette glands interdite dans parcs nationaux.",
        "medicinal_use": "Écorce en décoction : propriétés astringentes, anti-diarrhéiques. Traitement traditionnel des hémorroïdes en usage externe. Tanins aux propriétés antiseptiques. Usage : décoction 20g/litre, 2-3 tasses par jour. PRÉCAUTION : ne pas utiliser pendant grossesse.",
        "parks": ["El Feija", "Oued Zeen", "Jebel Chitana-Cap Négro", "Jebel Serj"],
    },
    {
        "name": "Thuya de Berbérie",
        "type": "plant",
        "scientific_name": "Tetraclinis articulata",
        "description": "Conifère endémique d'Afrique du Nord. Bois aromatique très dense et résistant, utilisé en artisanat traditionnel. Feuillage écailleux vert foncé. Espèce relique ancienne.",
        "threats": "Surexploitation pour bois précieux (loupes), incendies, pâturage empêchant régénération, changement climatique, maladies.",
        "protection_measures": "Interdiction stricte de coupe dans parcs nationaux, programme conservation ex-situ, reboisement, sensibilisation artisans, développement alternatives durables.",
        "safety_guidelines": "Coupe strictement interdite - amende et prison. Ne pas prélever branches ou écorce. Respect absolu de cet arbre protégé. Acheter artisanat uniquement de sources légales certifiées. Signaler coupes illégales aux autorités.",
        "medicinal_use": "Résine (sandaraque) utilisée traditionnellement pour affections respiratoires, antiseptique. Feuilles en infusion : propriétés digestives. ATTENTION : Huile essentielle toxique par voie interne - usage externe uniquement dilué. Éviter pendant grossesse et allaitement.",
        "parks": ["Boukornine", "Zaghouan"],
    },
    {
        "name": "Acacia raddiana",
        "type": "plant",
        "scientific_name": "Acacia raddiana",
        "description": "Arbre épineux du Sahara. Feuillage fin bipenne, fleurs jaunes en boules, gousses caractéristiques. Racines profondes. Rôle crucial dans écosystème désertique - ombre, nourriture, fixation azote.",
        "threats": "Sécheresse extrême prolongée, surpâturage par dromadaires et chèvres, coupe pour bois de chauffe, vieillissement sans régénération, changement climatique.",
        "protection_measures": "Protection des vieux arbres, restriction pâturage dans zones sensibles, aide à régénération (mise en défens, plantations), sensibilisation populations locales, gestion durable.",
        "safety_guidelines": "Attention aux épines longues et acérées - risque de blessure et infection. Porter chaussures fermées et vêtements longs. Ne pas casser branches. Respecter arbres qui sont ressources vitales pour faune. Ombre appréciée mais vérifier absence animaux dangereux (serpents, scorpions) avant de s'installer.",
        "medicinal_use": "Gomme arabique (exsudat) : propriétés adoucissantes, anti-inflammatoires pour gorge et système digestif. Écorce en décoction : traitement traditionnel diarrhées. Feuilles broyées : cataplasme anti-inflammatoire. Usage : gomme dissoute dans eau tiède, 1-2 cuillères/jour. Généralement sûr mais consulter médecin si troubles persistent.",
        "parks": ["Bouhedma", "Jebil", "Dghoumès", "Sidi Toui", "Senghar-Jabess"],
    },
    {
        "name": "Genévrier de Phénicie",
        "type": "plant",
        "scientific_name": "Juniperus phoenicea",
        "description": "Conifère arbustif méditerranéen. Feuillage écailleux persistant vert sombre. Baies bleu-noir. Croissance lente, peut vivre plusieurs siècles. Adapté sols pauvres et rocailleux.",
        "threats": "Incendies, surpâturage chèvres, arrachage pour cultures, vieillissement sans régénération, changement climatique.",
        "protection_measures": "Protection stricte dans parcs, réglementation pâturage, plantation jeunes plants, zones de mise en défens, sensibilisation valeur écologique.",
        "safety_guidelines": "Ne pas cueillir baies ou branches - protection légale. Attention terrain rocailleux autour des genévriers. Pas de feu à proximité - très inflammable. Respecter ces arbres anciens à croissance lente.",
        "medicinal_use": "Baies (genièvre) : propriétés diurétiques, digestives, antiseptiques. Infusion : 10-15 baies écrasées/tasse, 2-3 tasses/jour. Inhalation vapeur pour bronches. CONTRE-INDICATIONS IMPORTANTES : grossesse, allaitement, insuffisance rénale. Usage prolongé déconseillé (>4 semaines). Consulter médecin avant usage.",
        "parks": ["Zaghouan", "Orbata", "Chaambi"],
    },
    {
        "name": "Romarin",
        "type": "plant",
        "scientific_name": "Rosmarinus officinalis",
        "description": "Arbuste aromatique méditerranéen. Feuilles persistantes linéaires vert foncé, très parfumées. Fleurs bleues mellifères. Résistant sécheresse. Abondant sur collines calcaires.",
        "threats": "Cueillette excessive commerciale, urbanisation, incendies, dégradation habitat par pâturage.",
        "protection_measures": "Réglementation cueillette dans parcs, sensibilisation pratiques durables, promotion culture domestique, contrôle commerce.",
        "safety_guidelines": "Cueillette limitée usage personnel uniquement, interdite dans zones protégées. Prélever seulement sommités fleuries, ne pas arracher plante. Laisser 2/3 de la plante. Pas de cueillette plants isolés. Éviter période floraison (mars-mai) pour préserver pollinisateurs.",
        "medicinal_use": "Plante médicinale majeure : stimulant circulatoire, digestif, hépatique. Antioxydant puissant. Infusion : 1 c. à café feuilles/tasse, 3 fois/jour. Améliore mémoire et concentration. Usage externe : huile de massage pour douleurs rhumatismales. Inhalation : affections respiratoires. ATTENTION : huile essentielle pure interdite pendant grossesse, épilepsie, hypertension.",
        "parks": ["Boukornine", "Zaghouan", "Jebel Zaghdoud", "Chaambi"],
    },
    {
        "name": "Thym",
        "type": "plant",
        "scientific_name": "Thymus vulgaris",
        "description": "Plante aromatique vivace en coussinets bas. Petites feuilles ovales très odorantes. Fleurs roses-mauves mellifères. Abondant en zones arides méditerranéennes et montagneuses.",
        "threats": "Surexploitation commerciale, pâturage excessif, cueillette destructrice (arrachage), sécheresse.",
        "protection_measures": "Quotas de cueillette, formation cueilleurs aux bonnes pratiques, promotion culture, contrôle commerce illégal, zones de conservation.",
        "safety_guidelines": "Cueillette respectueuse : couper parties aériennes aux ciseaux, ne jamais arracher. Maximum 1/3 de la plante. Période optimale : avant floraison complète. Interdiction cueillette dans parcs sans autorisation. Laisser plants pour pollinisateurs.",
        "medicinal_use": "Antiseptique et expectorant puissant. Traitement infections respiratoires (toux, bronchite, rhume). Digestif, antispasmodique. Infusion : 1-2 c. à café/tasse, 3-4 fois/jour. Gargarisme : maux de gorge, infections buccales. Bain : ajouter infusion forte pour propriétés revigorantes. Généralement sûr. Huile essentielle : usage externe dilué ou diffusion. Éviter HE pure sur peau et usage interne sans avis médical.",
        "parks": ["Chaambi", "Zaghouan", "Orbata", "Boukornine", "Jebel Zaghdoud"],
    },
    {
        "name": "Lavande dentée",
        "type": "plant",
        "scientific_name": "Lavandula dentata",
        "description": "Arbuste aromatique méditerranéen. Feuilles grises dentées caractéristiques, très parfumées. Épis floraux bleu-violet prolongés. Mellifère important. Résiste bien sécheresse.",
        "threats": "Cueillette commerciale excessive, urbanisation zones côtières, incendies, hybridation avec lavandes cultivées.",
        "protection_measures": "Réglementation cueillette, promotion jardins de conservation, sensibilisation, zones protégées.",
        "safety_guidelines": "Cueillette modérée uniquement pour usage personnel. Couper épis floraux sans endommager plante. Période : début floraison. Respecter zones protégées. Ne pas utiliser herbicides ou pesticides à proximité.",
        "medicinal_use": "Propriétés calmantes, antiseptiques, cicatrisantes. Infusion : anxiété, troubles du sommeil, maux de tête. 1-2 c. à café fleurs/tasse avant coucher. Usage externe : désinfection petites plaies, piqûres insectes. Bain relaxant. Huile essentielle : diffusion aromathérapie, massage dilué (10 gouttes/50ml huile végétale). Généralement très sûre. Peut provoquer somnolence - attention conduite après utilisation.",
        "parks": ["Boukornine", "Zaghouan", "Jebel Zaghdoud"],
    },
    {
        "name": "Pistachier lentisque",
        "type": "plant",
        "scientific_name": "Pistacia lentiscus",
        "description": "Arbuste persistant méditerranéen au feuillage coriace. Feuilles composées pennées. Petits fruits rouges puis noirs. Résine aromatique (mastic). Très résistant sécheresse et incendies.",
        "threats": "Exploitation résine, arrachage pour urbanisation, incendies répétés, surpâturage.",
        "protection_measures": "Gestion durable récolte résine, protection habitats, reboisement, sensibilisation.",
        "safety_guidelines": "Récolte résine strictement réglementée. Ne pas inciser écorce sans autorisation. Cueillette fruits modérée pour usage personnel. Respecter cycles naturels de la plante.",
        "medicinal_use": "Résine (mastic) : propriétés digestives remarquables, protection gastrique, action contre Helicobacter pylori. Mâcher petite quantité résine : hygiène buccale, haleine fraîche, problèmes digestifs. Feuilles en décoction : diarrhées, troubles digestifs. Usage externe : cicatrisant, anti-inflammatoire. Généralement sûr. Éviter doses excessives de résine (peut causer troubles digestifs paradoxalement).",
        "parks": ["Boukornine", "Ichkeul", "Zaghouan", "Jebel Zaghdoud", "Chaambi"],
    },
    {
        "name": "Armoise blanche",
        "type": "plant",
        "scientific_name": "Artemisia herba-alba",
        "description": "Plante vivace aromatique des zones arides. Feuillage argenté très découpé, fortement odorant. Petites fleurs jaunâtres. Commune dans steppes et zones semi-désertiques. Plante pastorale importante.",
        "threats": "Surpâturage, arrachage pour usage médicinal commercial, sécheresse prolongée, dégradation sols.",
        "protection_measures": "Gestion pastorale durable, réglementation cueillette commerciale, restauration steppes dégradées, sensibilisation usage raisonné.",
        "safety_guidelines": "Cueillette modérée, uniquement parties aériennes fleuries. Ne pas arracher racines. Respecter zones de pâturage pour bétail. Cueillette interdite en période sécheresse extrême.",
        "medicinal_use": "Plante médicinale traditionnelle majeure en Tunisie : propriétés digestives, vermifuges, antidiabétiques. Infusion : troubles digestifs, ballonnements, diabète léger. 1 c. à café/tasse, 2-3 fois/jour après repas. ATTENTION : TOXIQUE À FORTE DOSE (thuyone). Ne jamais dépasser doses recommandées. CONTRE-INDICATIONS ABSOLUES : grossesse (abortif), allaitement, épilepsie, enfants. Usage court terme uniquement (max 2 semaines). Consulter médecin obligatoirement.",
        "parks": ["Bouhedma", "Chaambi", "Orbata", "Dghoumès", "Jebil"],
    },
    {
        "name": "Globulaire turbith",
        "type": "plant",
        "scientific_name": "Globularia alypum",
        "description": "Petit arbuste ramifié des zones arides. Feuilles persistantes coriaces bleutées. Fleurs bleues en capitules sphériques. Résiste bien à sécheresse. Toxique pour bétail.",
        "threats": "Cueillette excessive médicinale, surpâturage, dégradation habitat, urbanisation.",
        "protection_measures": "Contrôle commerce, sensibilisation toxicité, promotion alternatives cultivées, protection habitats.",
        "safety_guidelines": "PLANTE TOXIQUE - Manipulation avec précautions. Ne pas confondre avec autres plantes. Cueillette uniquement par personnes formées. Tenir hors portée enfants et animaux.",
        "medicinal_use": "Traditionnellement utilisée comme purgatif puissant, traitement paludisme et diabète. ATTENTION : PLANTE TRÈS TOXIQUE. Usage interne DANGEREUX - peut causer vomissements violents, diarrhées, crampes. USAGE DÉCONSEILLÉ sans supervision médicale stricte. NE JAMAIS utiliser pendant grossesse, allaitement, chez enfants, personnes âgées, problèmes cardiovasculaires, rénaux ou digestifs. Des alternatives plus sûres existent - consulter médecin ou pharmacien.",
        "parks": ["Bouhedma", "Dghoumès", "Jebil", "Chaambi", "Orbata"],
    },
]

# Hiking trails for various parks
TRAILS_DATA = [
    # Ichkeul Trails
    {
        "park_name": "Parc National d'Ichkeul",
        "name": "Circuit des Flamants Roses",
        "description": "Boucle autour du lac d'Ichkeul avec observation des flamants roses et autres oiseaux migrateurs. Sentier plat le long des rives.",
        "difficulty": "facile",
        "length_km": 8.5,
        "duration_hours": 3,
        "elevation_gain": 50,
        "trail_type": "boucle",
        "highlights": ["Observation flamants", "Zone humide UNESCO", "Faune migratoire"]
    },
    {
        "park_name": "Parc National d'Ichkeul",
        "name": "Chemin des Marécages",
        "description": "Sentier sur pilotis traversant les marécages. Accès aux zones les plus humides du parc avec observation rapprochée de la biodiversité.",
        "difficulty": "facile",
        "length_km": 4.2,
        "duration_hours": 2,
        "elevation_gain": 20,
        "trail_type": "aller-retour",
        "highlights": ["Marécages", "Sentier sur pilotis", "Biodiversité aquatique"]
    },

    # Boukornine Trails
    {
        "park_name": "Parc National de Boukornine",
        "name": "Sommet du Djebel Boukornine",
        "description": "Ascension du point culminant offrant des vues panoramiques sur Tunis et la région. Sentier escarpé avec passages rocheux.",
        "difficulty": "difficile",
        "length_km": 12.0,
        "duration_hours": 5,
        "elevation_gain": 420,
        "trail_type": "aller-retour",
        "highlights": ["Vue panoramique", "Sommet", "Flore méditerranéenne"]
    },
    {
        "park_name": "Parc National de Boukornine",
        "name": "Boucle des Thuyas",
        "description": "Circuit dans la forêt de thuyas de Berbérie. Découverte des conifères endémiques et de la flore méditerranéenne.",
        "difficulty": "modéré",
        "length_km": 6.8,
        "duration_hours": 2.5,
        "elevation_gain": 180,
        "trail_type": "boucle",
        "highlights": ["Thuyas de Berbérie", "Forêt méditerranéenne", "Flore endémique"]
    },

    # Zaghouan Trails
    {
        "park_name": "Parc National de Zaghouan",
        "name": "Sources Romaines",
        "description": "Sentier historique menant aux sources romaines qui alimentaient Carthage. Paysages de genévriers et pins d'Alep.",
        "difficulty": "modéré",
        "length_km": 7.5,
        "duration_hours": 3,
        "elevation_gain": 220,
        "trail_type": "aller-retour",
        "highlights": ["Sources romaines", "Histoire antique", "Genévriers anciens"]
    },

    # El Feija Trails
    {
        "park_name": "Parc National d'El Feija",
        "name": "Forêt des Cerfs",
        "description": "Exploration de la forêt de chênes zéens avec possibilité d'observer les cerfs de Barbarie. Sentier ombragé en sous-bois.",
        "difficulty": "facile",
        "length_km": 5.2,
        "duration_hours": 2,
        "elevation_gain": 80,
        "trail_type": "boucle",
        "highlights": ["Cerfs de Barbarie", "Chênes zéens", "Forêt humide"]
    },
    {
        "park_name": "Parc National d'El Feija",
        "name": "Rivières et Cascades",
        "description": "Sentier le long des cours d'eau et cascades de la région. Végétation luxuriante et points de vue sur les gorges.",
        "difficulty": "modéré",
        "length_km": 9.0,
        "duration_hours": 3.5,
        "elevation_gain": 150,
        "trail_type": "linéaire",
        "highlights": ["Cascades", "Gorges", "Cours d'eau"]
    },

    # Chaambi Trails
    {
        "park_name": "Parc National de Chaambi",
        "name": "Ascension du Djebel Chaambi",
        "description": "La grande ascension vers le plus haut sommet de Tunisie (1544m). Sentier alpin avec vues spectaculaires. Expérience exigeante.",
        "difficulty": "difficile",
        "length_km": 18.0,
        "duration_hours": 8,
        "elevation_gain": 850,
        "trail_type": "aller-retour",
        "highlights": ["Plus haut sommet", "Vue panoramique", "Alpinisme"]
    },
    {
        "park_name": "Parc National de Chaambi",
        "name": "Pins d'Alep Trail",
        "description": "Balade dans les dernières forêts de pins d'Alep de haute altitude. Flore et faune d'altitude exceptionnelle.",
        "difficulty": "modéré",
        "length_km": 8.5,
        "duration_hours": 3.5,
        "elevation_gain": 280,
        "trail_type": "boucle",
        "highlights": ["Pins d'Alep", "Haute altitude", "Faune alpine"]
    },

    # Bouhedma Trails
    {
        "park_name": "Parc National de Bouhedma",
        "name": "Désert des Oryx",
        "description": "Traversée du désert avec observation des oryx et gazelles dans leur habitat naturel. Paysages sahariens authentiques.",
        "difficulty": "modéré",
        "length_km": 15.0,
        "duration_hours": 6,
        "elevation_gain": 120,
        "trail_type": "boucle",
        "highlights": ["Oryx algazelle", "Gazelles dorcas", "Désert authentique"]
    },
    {
        "park_name": "Parc National de Bouhedma",
        "name": "Oasis des Acacias",
        "description": "Circuit autour des acacias raddiana et points d'eau. Découverte de la flore désertique et faune associée.",
        "difficulty": "facile",
        "length_km": 6.0,
        "duration_hours": 2.5,
        "elevation_gain": 40,
        "trail_type": "boucle",
        "highlights": ["Acacias", "Oasis", "Flore désertique"]
    },

    # Jebil Trails
    {
        "park_name": "Parc National de Jebil",
        "name": "Dunes Géantes",
        "description": "Randonnée dans les plus grandes dunes du Grand Erg Oriental. Expérience saharienne authentique avec navigation à la boussole.",
        "difficulty": "difficile",
        "length_km": 25.0,
        "duration_hours": 10,
        "elevation_gain": 200,
        "trail_type": "boucle",
        "highlights": ["Dunes géantes", "Navigation désert", "Sahara authentique"]
    },

    # Oued Zeen Trails
    {
        "park_name": "Parc National de Oued Zeen",
        "name": "Forêt Pluviale",
        "description": "Immersion dans la forêt de chênes zéens, la plus humide de Tunisie. Observation de la faune forestière et cascades.",
        "difficulty": "modéré",
        "length_km": 10.5,
        "duration_hours": 4,
        "elevation_gain": 300,
        "trail_type": "aller-retour",
        "highlights": ["Chênes zéens", "Forêt pluviale", "Cascades"]
    },

    # Orbata Trails
    {
        "park_name": "Parc National de l'Orbata",
        "name": "Genévriers Rouges",
        "description": "Ascension vers les genévriers rouges de haute altitude. Paysages montagneux et flore exceptionnelle.",
        "difficulty": "difficile",
        "length_km": 14.0,
        "duration_hours": 6,
        "elevation_gain": 600,
        "trail_type": "aller-retour",
        "highlights": ["Genévriers rouges", "Haute montagne", "Flore alpine"]
    },

    # Jebel Serj Trails
    {
        "park_name": "Parc National de Jebel Serj",
        "name": "Liège Ancien",
        "description": "Exploration des forêts de chênes-lièges centenaires. Apprentissage de l'exploitation traditionnelle du liège.",
        "difficulty": "facile",
        "length_km": 4.5,
        "duration_hours": 2,
        "elevation_gain": 100,
        "trail_type": "boucle",
        "highlights": ["Chênes-lièges", "Exploitation liège", "Arbres centenaires"]
    },

    # Jebel Mghilla Trails
    {
        "park_name": "Parc National de Jebel Mghilla",
        "name": "Observatoire Faunique",
        "description": "Sentier d'observation de la faune diversifiée du parc. Points de vue aménagés pour l'observation des rapaces et mammifères.",
        "difficulty": "modéré",
        "length_km": 7.8,
        "duration_hours": 3,
        "elevation_gain": 250,
        "trail_type": "boucle",
        "highlights": ["Observation faune", "Rapaces", "Mammifères"]
    },

    # Jebel Zaghdoud Trails
    {
        "park_name": "Parc National de Jebel Zaghdoud",
        "name": "Caroubiers et Pins",
        "description": "Balade dans les forêts de caroubiers et pins d'Alep. Végétation variée selon les altitudes avec points de vue sur la région.",
        "difficulty": "modéré",
        "length_km": 6.2,
        "duration_hours": 2.5,
        "elevation_gain": 180,
        "trail_type": "boucle",
        "highlights": ["Caroubiers", "Pins d'Alep", "Végétation altitude"]
    },

    # Zembra Trails (limited access)
    {
        "park_name": "Parc National de Zembra et Zembretta",
        "name": "Côtes des Puffins",
        "description": "Sentier côtier avec observation des puffins cendrés. Accessible uniquement avec guide autorisé. Paysages marins exceptionnels.",
        "difficulty": "modéré",
        "length_km": 3.5,
        "duration_hours": 2,
        "elevation_gain": 80,
        "trail_type": "aller-retour",
        "highlights": ["Puffins cendrés", "Côtes rocheuses", "Île inhabitée"]
    }
]


def seed_complete_database():
    """Seed database with complete park and species information"""
    init_db()
    
    with Session(get_engine()) as session:
        print("=== TUNISIA NATIONAL PARKS COMPLETE DATABASE SEED ===\n")
        
        # Check existing data
        existing_parks = session.exec(select(ParkDB)).all()
        existing_species = session.exec(select(SpeciesDB)).all()
        
        if existing_parks or existing_species:
            print(f"⚠️  Database contains {len(existing_parks)} parks and {len(existing_species)} species - clearing and re-seeding...")

            # Clear database
            for species in existing_species:
                session.delete(species)
            for park in existing_parks:
                session.delete(park)
            session.exec(delete(ParkSpeciesLink))
            session.commit()
            print("✓ Database cleared\n")
        
        # Add all 17 parks
        print("📍 Adding 17 National Parks...")
        park_objects = {}
        for park_data in TUNISIA_PARKS_COMPLETE:
            # Add required google_maps_url
            park_data["google_maps_url"] = f"https://www.google.com/maps?q={park_data['latitude']},{park_data['longitude']}"
            park = ParkDB(**park_data)
            session.add(park)
            session.flush()  # Get ID immediately
            park_objects[park_data["name"]] = park
            print(f"  ✓ {park.name} ({park.governorate}) - {park.area_km2} km²")
        
        session.commit()
        print(f"\n✅ Added {len(TUNISIA_PARKS_COMPLETE)} national parks\n")
        
        # Add all species with complete information
        print("🦌 Adding Flora & Fauna with Safety Guidelines...")
        species_count = 0
        for species_data in SPECIES_DATA:
            park_names = species_data.pop("parks")
            
            species = SpeciesDB(**species_data)
            session.add(species)
            session.flush()
            
            # Link to parks
            for park_name_part in park_names:
                for full_park_name, park_obj in park_objects.items():
                    if park_name_part.lower() in full_park_name.lower():
                        link = ParkSpeciesLink(park_id=park_obj.id, species_id=species.species_id)
                        session.add(link)
            
            species_count += 1
            icon = "🌿" if species.type == "plant" else "🦌"
            print(f"  {icon} {species.name} ({species.scientific_name})")
            if hasattr(species, 'medicinal_use') and species.medicinal_use:
                print(f"     💊 Medicinal properties documented")
        
        session.commit()
        print(f"\n✅ Added {species_count} species with complete data\n")

        # Add trails
        print("🥾 Adding Hiking Trails...")
        trails_count = 0
        for trail_data in TRAILS_DATA:
            park_name = trail_data.pop("park_name")
            park_obj = None
            for full_park_name, park in park_objects.items():
                if park_name.lower() in full_park_name.lower():
                    park_obj = park
                    break

            if park_obj:
                trail_data["park_id"] = park_obj.id
                # Convert highlights list to JSON string
                if "highlights" in trail_data and isinstance(trail_data["highlights"], list):
                    import json
                    trail_data["highlights"] = json.dumps(trail_data["highlights"])
                trail = TrailDB(**trail_data)
                session.add(trail)
                trails_count += 1
                print(f"  🥾 {trail.name} ({trail.difficulty}) - {trail.length_km} km")

        session.commit()
        print(f"\n✅ Added {trails_count} hiking trails\n")

        # Summary statistics
        print("📊 DATABASE SUMMARY:")
        print(f"   • Total Parks: 17")
        print(f"   • Total Species: {species_count}")
        print(f"   • Mammals: {sum(1 for s in SPECIES_DATA if s['type'] == 'animal' and 'mammifère' in s.get('description', '').lower() or any(x in s['name'].lower() for x in ['cerf', 'oryx', 'gazelle', 'mouflon', 'chacal', 'sanglier', 'hyène']))}")
        print(f"   • Birds: {sum(1 for s in SPECIES_DATA if s['type'] == 'animal' and any(x in s['name'].lower() for x in ['flamant', 'puffin', 'aigle', 'autruche']))}")
        print(f"   • Flora: {sum(1 for s in SPECIES_DATA if s['type'] == 'plant')}")
        print(f"   • Medicinal Plants: {sum(1 for s in SPECIES_DATA if s['type'] == 'plant' and 'medicinal_use' in s)}")
        print(f"   • With Safety Guidelines: {len(SPECIES_DATA)}")
        print(f"   • With Threat Analysis: {len(SPECIES_DATA)}")
        print(f"   • With Protection Measures: {len(SPECIES_DATA)}\n")
        
        # Parks by governorate
        gov_counts = {}
        for park in TUNISIA_PARKS_COMPLETE:
            gov = park['governorate']
            gov_counts[gov] = gov_counts.get(gov, 0) + 1
        
        print("🗺️  PARKS BY GOVERNORATE:")
        for gov, count in sorted(gov_counts.items()):
            parks_in_gov = [p['name'].replace('Parc National ', '').replace('de ', '').replace("d'", '').replace('des îles de ', '') for p in TUNISIA_PARKS_COMPLETE if p['governorate'] == gov]
            print(f"   {gov}: {count} park(s) - {', '.join(parks_in_gov)}")
        
        print("\n✅ COMPLETE DATABASE SEEDING SUCCESSFUL!")
        print("🌿 All Tunisia national parks with fauna, flora, threats, protection, and safety data loaded.\n")


if __name__ == "__main__":
    seed_complete_database()
