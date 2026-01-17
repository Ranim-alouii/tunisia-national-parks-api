
#Add image URLs to species for visual display
#You can update these URLs with real images later


from sqlmodel import Session, select
from database import engine
from models import SpeciesDB

# Image URLs for species (using placeholder service - replace with real images)
SPECIES_IMAGES = {
    # MAMMALS
    "Cervus elaphus barbarus": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Cervus_elaphus_barbarus.jpg/800px-Cervus_elaphus_barbarus.jpg",
    "Oryx dammah": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/8a/Oryx_dammah_-Marwell_Wildlife%2C_Hampshire%2C_England-8a.jpg/800px-Oryx_dammah_-Marwell_Wildlife%2C_Hampshire%2C_England-8a.jpg",
    "Gazella dorcas": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/93/Gazella_dorcas.jpg/800px-Gazella_dorcas.jpg",
    "Ammotragus lervia": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0b/Ammotragus_lervia_-Bioparc_Zoo_de_Doue%2C_France-8a.jpg/800px-Ammotragus_lervia_-Bioparc_Zoo_de_Doue%2C_France-8a.jpg",
    "Canis aureus": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6d/Golden_jackal_%28Canis_aureus%29.jpg/800px-Golden_jackal_%28Canis_aureus%29.jpg",
    "Sus scrofa": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Wildschein%2C_N%C3%A4he_Pulverstampftor%2C_Hauptsmoorwald.jpg/800px-Wildschein%2C_N%C3%A4he_Pulverstampftor%2C_Hauptsmoorwald.jpg",
    "Hyaena hyaena": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Hyaena_hyaena_Hardwicke.jpg/800px-Hyaena_hyaena_Hardwicke.jpg",
    "Struthio camelus camelus": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/77/Somali_Ostrich.jpg/800px-Somali_Ostrich.jpg",
    "Vulpes vulpes": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bb/Vulpes_vulpes_1_%28Martin_Mecnarowski%29.jpg/800px-Vulpes_vulpes_1_%28Martin_Mecnarowski%29.jpg",
    "Hystrix cristata": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d6/Hystrix_cristata_%28porcupine%29_juvenile.JPG/800px-Hystrix_cristata_%28porcupine%29_juvenile.JPG",
    "Atelerix algirus": "https://upload.wikimedia.org/wikipedia/commons/thumb/c/ce/Atelerix_algirus_Hardwicke.jpg/800px-Atelerix_algirus_Hardwicke.jpg",
    "Genetta genetta": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/86/Genetta_genetta_felina_%28Wroclaw_zoo%29-2.JPG/800px-Genetta_genetta_felina_%28Wroclaw_zoo%29-2.JPG",
    "Herpestes ichneumon": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2f/Egyptian_mongoose_%28Herpestes_ichneumon%29.jpg/800px-Egyptian_mongoose_%28Herpestes_ichneumon%29.jpg",
    
    # BIRDS
    "Phoenicopterus roseus": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ec/Phoenicopterus_roseus_-_two_flamingos.jpg/800px-Phoenicopterus_roseus_-_two_flamingos.jpg",
    "Calonectris diomedea": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fc/Calonectris_diomedea_-_2.jpg/800px-Calonectris_diomedea_-_2.jpg",
    "Aquila chrysaetos": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Golden_Eagle_%28Aquila_chrysaetos%29_in_flight.jpg/800px-Golden_Eagle_%28Aquila_chrysaetos%29_in_flight.jpg",
    "Ciconia ciconia": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9e/Ciconia_ciconia_%28aka%29.jpg/800px-Ciconia_ciconia_%28aka%29.jpg",
    "Buteo rufinus": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Long-legged_buzzard_%28Buteo_rufinus_cirtensis%29_adult.jpg/800px-Long-legged_buzzard_%28Buteo_rufinus_cirtensis%29_adult.jpg",
    "Chlamydotis undulata": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/91/Chlamydotis_undulata.jpg/800px-Chlamydotis_undulata.jpg",
    "Milvus milvus": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/12/Red_Kite_-_Gigrin_Farm_-_Nov_2013.jpg/800px-Red_Kite_-_Gigrin_Farm_-_Nov_2013.jpg",
    "Falco tinnunculus": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/aa/Common_kestrel_falco_tinnunculus.jpg/800px-Common_kestrel_falco_tinnunculus.jpg",
    
    # REPTILES
    "Testudo graeca": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a4/Testudo_graeca_ibera_close_up.jpg/800px-Testudo_graeca_ibera_close_up.jpg",
    "Vipera latastei": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/V%C3%ADbora-de-lataste_%28Vipera_latastei%29.jpg/800px-V%C3%ADbora-de-lataste_%28Vipera_latastei%29.jpg",
    "Chamaeleo chamaeleon": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3f/Chamaeleo_chamaeleon_01.JPG/800px-Chamaeleo_chamaeleon_01.JPG",
    "Timon lepidus": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/09/Timon_lepidus_1.jpg/800px-Timon_lepidus_1.jpg",
    
    # INSECTS
    "Lyristes plebejus": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5e/Cicada_orni.jpg/800px-Cicada_orni.jpg",
    "Mantis religiosa": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b6/Mantis_religiosa_-_male.jpg/800px-Mantis_religiosa_-_male.jpg",
    
    # TREES & SHRUBS
    "Pinus halepensis": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Pinus_halepensis.jpg/800px-Pinus_halepensis.jpg",
    "Quercus suber": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a3/Cork_oak_trunk_section.jpg/800px-Cork_oak_trunk_section.jpg",
    "Tetraclinis articulata": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/6b/Tetraclinis_articulata.JPG/800px-Tetraclinis_articulata.JPG",
    "Acacia raddiana": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d7/Acacia_raddiana_kz1.jpg/800px-Acacia_raddiana_kz1.jpg",
    "Juniperus phoenicea": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/48/Juniperus_phoenicea.jpg/800px-Juniperus_phoenicea.jpg",
    "Quercus canariensis": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Quercus_canariensis_kz2.JPG/800px-Quercus_canariensis_kz2.JPG",
    "Olea europaea var. sylvestris": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/ff/Olea_europaea_subsp._europaea_var._sylvestris.jpg/800px-Olea_europaea_subsp._europaea_var._sylvestris.jpg",
    "Ceratonia siliqua": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b2/Ceratonia_siliqua_JPG1a.jpg/800px-Ceratonia_siliqua_JPG1a.jpg",
    "Ziziphus lotus": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Ziziphus_lotus.jpg/800px-Ziziphus_lotus.jpg",
    "Pistacia lentiscus": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Pistacia_lentiscus_fruits.jpg/800px-Pistacia_lentiscus_fruits.jpg",
    "Myrtus communis": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/Myrtus_communis_flower.jpg/800px-Myrtus_communis_flower.jpg",
    "Nerium oleander": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3d/Nerium_oleander_flowers_leaves.jpg/800px-Nerium_oleander_flowers_leaves.jpg",
    "Phoenix dactylifera": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3a/Date_Palm_Fruit.jpg/800px-Date_Palm_Fruit.jpg",
    "Rhus coriaria": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d2/Rhus_coriaria2.jpg/800px-Rhus_coriaria2.jpg",
    
    # MEDICINAL HERBS
    "Rosmarinus officinalis": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0f/Rosmarinus_officinalis133095820.jpg/800px-Rosmarinus_officinalis133095820.jpg",
    "Thymus vulgaris": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/68/Thymus_vulgaris_-_K%C3%B6hler%E2%80%93s_Medizinal-Pflanzen-207.jpg/800px-Thymus_vulgaris_-_K%C3%B6hler%E2%80%93s_Medizinal-Pflanzen-207.jpg",
    "Lavandula dentata": "https://upload.wikimedia.org/wikipedia/commons/thumb/7/7f/Lavandula_dentata_kz1.jpg/800px-Lavandula_dentata_kz1.jpg",
    "Artemisia herba-alba": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/87/Artemisia_herba-alba.jpg/800px-Artemisia_herba-alba.jpg",
    "Globularia alypum": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/92/Globularia_alypum_001.jpg/800px-Globularia_alypum_001.jpg",
    "Mentha pulegium": "https://upload.wikimedia.org/wikipedia/commons/thumb/5/52/Mentha_pulegium_001.JPG/800px-Mentha_pulegium_001.JPG",
    "Eucalyptus globulus": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e2/Eucalyptus_globulus_-_K%C3%B6hler%E2%80%93s_Medizinal-Pflanzen-003.jpg/800px-Eucalyptus_globulus_-_K%C3%B6hler%E2%80%93s_Medizinal-Pflanzen-003.jpg",
    "Foeniculum vulgare": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/81/Foeniculum_vulgare_20060806_132.jpg/800px-Foeniculum_vulgare_20060806_132.jpg",
    "Allium roseum": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/ed/Allium_roseum_Enfola_01.jpg/800px-Allium_roseum_Enfola_01.jpg",
    "Ruta montana": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a5/Ruta_montana_002.JPG/800px-Ruta_montana_002.JPG",
    "Stipa tenacissima": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/2c/Stipa_tenacissima_L.jpg/800px-Stipa_tenacissima_L.jpg",
    "Retama raetam": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ae/Retama_raetam_1.jpg/800px-Retama_raetam_1.jpg",
}


def add_species_images():
    """Add image URLs to all species"""
    
    with Session(engine) as session:
        print("=== ADDING IMAGES TO SPECIES ===\n")
        
        all_species = session.exec(select(SpeciesDB)).all()
        updated = 0
        not_found = 0
        
        for species in all_species:
            if species.scientific_name in SPECIES_IMAGES:
                species.image_url = SPECIES_IMAGES[species.scientific_name]
                session.add(species)
                
                icon = "🌿" if species.type == "plant" else "🦌"
                print(f"  ✅ {icon} {species.name} → Image added")
                updated += 1
            else:
                icon = "🌿" if species.type == "plant" else "🦌"
                print(f"  ⚠️  {icon} {species.name} → No image found")
                not_found += 1
        
        session.commit()
        
        print(f"\n{'='*60}")
        print(f"✅ IMAGES ADDED!")
        print(f"{'='*60}")
        print(f"  Updated: {updated} species")
        print(f"  Missing: {not_found} species")
        print(f"  Total: {len(all_species)} species")
        print(f"\n📸 Species now have images for visual display!")


if __name__ == "__main__":
    add_species_images()
