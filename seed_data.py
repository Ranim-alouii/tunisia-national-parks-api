from sqlmodel import Session

from database import engine, init_db
from models import ParkDB, SpeciesDB, ParkSpeciesLink


def seed():
    init_db()

    with Session(engine) as session:
        # clear existing data (simple for development)
        session.query(ParkSpeciesLink).delete()
        session.query(SpeciesDB).delete()
        session.query(ParkDB).delete()

        # create parks
        ichkeul = ParkDB(
            name="Parc national de l'Ichkeul",
            governorate="Bizerte",
            description="Parc national autour du lac Ichkeul, zone humide importante pour les oiseaux migrateurs.",
            latitude=37.169,
            longitude=9.672,
            area_km2=126.0,
        )
        chaambi = ParkDB(
            name="Parc national de Chaambi",
            governorate="Kasserine",
            description="Parc de montagne autour du Djebel Chaambi, abritant une faune et flore de haute altitude.",
            latitude=35.233,
            longitude=8.672,
            area_km2=67.0,
        )

        session.add(ichkeul)
        session.add(chaambi)
        session.commit()
        session.refresh(ichkeul)
        session.refresh(chaambi)

        # create species
        gazelle = SpeciesDB(
            name="Gazelle de Cuvier",
            type="animal",
            scientific_name="Gazella cuvieri",
            description="Antilope saharienne présente dans certains parcs du centre et du sud tunisien.",
            threats="Braconnage, perte d'habitat, dérangement par les activités humaines.",
            protection_measures="Renforcer la surveillance et sensibiliser les visiteurs à ne pas poursuivre les animaux.",
        )
        cerf = SpeciesDB(
            name="Cerf de Barbarie",
            type="animal",
            scientific_name="Cervus elaphus barbarus",
            description="Sous-espèce de cerf présente dans les massifs forestiers du nord-ouest tunisien.",
            threats="Fragmentation des forêts, braconnage, incendies.",
            protection_measures="Protéger les forêts et lutter contre les incendies.",
        )
        pin = SpeciesDB(
            name="Pin d'Alep",
            type="plant",
            scientific_name="Pinus halepensis",
            description="Espèce de pin très répandue dans les forêts tunisiennes.",
            threats="Incendies répétés, sécheresse, coupes abusives.",
            protection_measures="Prévenir les incendies et contrôler l'exploitation du bois.",
        )

        session.add(gazelle)
        session.add(cerf)
        session.add(pin)
        session.commit()
        session.refresh(gazelle)
        session.refresh(cerf)
        session.refresh(pin)

        # link species to parks
        links = [
            ParkSpeciesLink(park_id=chaambi.id, species_id=gazelle.id),
            ParkSpeciesLink(park_id=ichkeul.id, species_id=cerf.id),
            ParkSpeciesLink(park_id=ichkeul.id, species_id=pin.id),
            ParkSpeciesLink(park_id=chaambi.id, species_id=pin.id),
        ]
        session.add_all(links)
        session.commit()


if __name__ == "__main__":
    seed()
