"""Curated gazetteer of real colonia/municipio names for gen_listings.py.

CDMX (Ciudad de México)
-----------------------
``CDMX_COLONIAS`` is sourced from the CDMX open-data portal (datos.cdmx.gob.mx),
dataset "Colonias del IECM 2019" (CSV export). It is grouped by alcaldía
(municipio) and sampled to ~16 real colonia names per alcaldía (252 total) to
keep this file small; names are cleaned (title-cased, trailing classification
tags like "(Pblo)"/"(U Hab)" stripped, best-effort accent restoration since the
source export has no diacritics at all). See docs/data-notes.md for the exact
URL and retrieval date.

Municipio (alcaldía) names themselves are read at generation time from
``data/geo/agebs_cdmx.geojson`` properties (``NOM_MUN``), which is the INEGI
Marco Geoestadístico AGEB layer via the same CDMX open-data portal -- this
keeps municipio and AGEB-polygon data joined to one source of truth instead of
duplicated here. The 16 keys below must match those NOM_MUN values exactly.

Guadalajara and Monterrey metros
---------------------------------
INEGI's public AGEB layer has no colonia-level names and geo-lab does not
(yet) source AGEB polygons for these two cities, so ``GDL_MUNICIPIOS`` and
``MTY_MUNICIPIOS`` are a small hand-curated gazetteer of well-known real
municipios/colonias, per BRIEF.md's explicit fallback instruction. Each
municipio carries an approximate lat/lng bounding box (fetched from
OpenStreetMap Nominatim, a real place lookup -- not fabricated coordinates)
used to sample points when no AGEB polygon is available, and a rough
population-share weight (approximate, from public 2020-census-era figures
remembered at authoring time, NOT a cited dataset) used only to bias which
municipio a synthetic listing lands in.
"""

CDMX_COLONIAS = {
    "Azcapotzalco": ["Aguilera", "Coltongo", "Del Recreo", "El Rosario C", "Hogares Ferrocarrileros", "La Preciosa", "Manuel Rivera Anaya Croc I", "Nuevo San Rafael", "Plenitud", "Pro Hogar Ii", "San Bartolo Cahualtongo", "San Martin Xochinahuac", "San Pedro Xalpa Ii", "Santa Catarina", "Santiago Ahuizotla", "Tlatilco"],
    "Benito Juárez": ["Acacias", "Américas Unidas-del Lago", "Credito Constructor", "Del Valle Iv", "Ermita", "Insurgentes Mixcoac", "Letran Valle", "Miravalle", "Narvarte Ii", "Narvarte Vi", "Nonoalco", "Piedad Narvarte", "Portales Iv", "San Jose Insurgentes", "Sta Cruz Atoyac", "Xoco"],
    "Coyoacán": ["Adolfo Ruiz Cortines I", "Altillo", "Campestre Coyoacan", "Ciudad Universitaria", "Ctm Vi Culhuacán", "Educacion", "Emiliano Zapata", "Imán", "La Cantera", "Los Girasoles I", "Nueva Diaz Ordaz", "Pedregal de Santa Úrsula Ii", "Pedregal de Sto Domingo Vii", "Presidentes Ejidales Segunda Sección", "Santa Cecilia", "Villa Panamericana 2da. Seccin"],
    "Cuajimalpa de Morelos": ["1o de Mayo", "Adolfo López Mateos", "Amado Nervo", "Cola de Pato", "Cruz Blanca", "El Molinito", "El Yaqui", "Jesus del Monte", "La Venta", "Loma del Padre", "Lomas de Vista Hermosa", "Memetla", "Portal del Sol", "San Jose de los Cedros Ii", "San Pablo Chimalpa", "Texcalco"],
    "Cuauhtémoc": ["Algarin", "Buenavista I", "Centro Ii", "Centro Vi", "Cuauhtémoc", "Doctores Iv", "Felipe Pescador", "Guerrero Iv", "Juárez", "Morelos Iii", "Obrera I", "Paulino Navarro", "Roma Norte Ii", "San Rafael I", "Santa María Insurgentes", "Tabacalera"],
    "Gustavo A. Madero": ["15 de Agosto", "Benito Juárez", "Chalma de Guadalupe Ii", "Del Obrero", "Estanzuela", "Gertrudis Sanchez 1a Sección", "Industrial I", "La Casilda", "La Pastora", "Luis Donaldo Colosio", "Nueva Vallejo", "Providencia Iii", "San Jose de la Escalera", "San Juan de Aragon 7 Secc I", "Solidaridad Nacional", "Valle de Madero"],
    "Iztacalco": ["Agricola Oriental I", "Agricola Oriental Iv", "Agricola Oriental Vii", "Campamento 2 de Octubre Ii", "Cuchilla Ramos Millan", "Gabriel Ramos Millan", "Infonavit Iztacalco I", "Juventino Rosas I", "La Cruz", "Mosco Chinampa", "Pantitlán Iii", "Picos Iztacalco 1-a", "Ramos Millan Bramadero Ii", "San Fco Xicaltongo", "Santa Cruz", "Tlacotal Ramos Millan"],
    "Iztapalapa": ["12 de Diciembre", "Bellavista", "Chinampac de Juárez Ii", "Desarrollo Urbano Quetzalcoatl Iii", "El Rodeo", "Francisco Villa", "Ignacio Zaragoza", "La Estación", "Lomas Estrella Iii", "Minas Polvorilla", "Plenitud", "Rinconada el Molino", "San Lorenzo Tezonco", "Santa Barbara I", "Sinatel", "Valle de San Lorenzo I"],
    "La Magdalena Contreras": ["Atacaxco", "Batan Viejo", "El Ermitao", "El Rosal", "Huayatla", "Independencia Batan Sur", "Ixtlahualtongo", "La Cruz", "La Malinche", "Las Huertas", "Lomas de San Bernabe", "Plazuela del Pedregal", "Pueblo Nuevo Bajo", "San Bernabe Ocotepec", "San Nicolas Totolapan", "Tierra Colorada"],
    "Miguel Hidalgo": ["10 de Abril", "América", "Anáhuac Lago Norte", "Argentina Antigua", "Chapultepec Polanco", "Escandon I", "Ignacio Manuel Altamirano", "Lomas Virreyes", "Los Morales", "Molino del Rey", "Nueva Argentina", "Pensil Sur", "Popotla I", "San Diego Ocoyoacac", "Santo Tomas", "Torre Blanca"],
    "Milpa Alta": ["San Agustin Ohtenco", "San Antonio Tecomitl", "San Bartolome Xicomulco", "San Francisco Tecoxpa", "San Jeronimo Miacatlan", "San Juan Tepenahuac", "San Lorenzo Tlacoyucan", "San Pablo Oztotepec", "San Pedro Atocpan", "San Salvador Cuauhtenco", "Santa Ana Tlacotenco", "Villa Milpa Alta"],
    "Tlalpan": ["2 de Octubre", "Belisario Dominguez", "Coapa-villa Cuemanco", "Ejidos de San Pedro Martir I", "Fuentes del Pedregal", "Isidro Fabela I", "La Libertad - Ixtlahuaca", "Lomas de Padierna", "Miguel Hidalgo", "Narciso Mendoza-villa Coapa Super Manzana 6", "Pedregal de Sn Nicolas 2a Secc", "Progreso Tlalpan", "San Lorenzo Huipulco", "Santo Tomas Ajusco", "Tezontitla - el Calvario", "Verano"],
    "Tláhuac": ["3 de Mayo", "Cuitlahuac", "El Rosario", "Emiliano Zapata 2a", "Jardines del Llano-u.h. Villa Tlatempa", "La Estación", "La Mesa", "Los Olivos", "Ojo de Agua", "Quiahuatla", "San Juan Ixtayopan", "San Nicolas Tetelco", "Santa Cecilia", "Selene 2da Secc", "Tepantitlamilco", "Unidades Habitacionales de Santa Ana Poniente I"],
    "Venustiano Carranza": ["10 de Mayo", "7 de Julio", "Aquiles Serdan", "Bahia", "Cuatro Arboles", "El Arenal 3a Sección", "Emiliano Zapata", "Ignacio Zaragoza I", "Jardín Balbuena I", "Lorenzo Boturini", "Moctezuma 1a Sección", "Moctezuma 2a Sección Iv", "Pensador Mexicano I", "Primero de Mayo", "Romero Rubio", "Valentin Gómez Farias"],
    "Xochimilco": ["Altos Tepetlica", "Bosque Residencial del Sur", "El Carmen", "Jardines del Sur", "La Concepcion Tlacoapa", "La Santisima", "Los Cerrillos Iii", "Paseos del Sur", "San Bartolo el Chico", "San Francisco Tlalnepantla", "San Juan", "San Lorenzo la Cebada I", "San Mateo Xalpa", "Santa Cruz Chavarrieta", "Santiago Tepalcatlalpan", "Tierra Nueva"],
    "Álvaro Obregón": ["19 de Mayo", "Arcos de Centenario", "Bella Vista", "Conciencia Proletaria", "El Capulin", "Galeana", "Jalalpa Tepito", "La Loma", "Liberacion Proletaria", "Lomas de Puerta Grande", "Margarita M de Juárez", "Olivar del Conde 1ra Sección Ii", "Presidentes", "San Bartolo Ameyalco", "Tecolalco", "Torres San Antonio"],
}

# Guadalajara metro area (Jalisco). bbox = (min_lat, min_lng, max_lat, max_lng),
# from OSM Nominatim place lookups (retrieved alongside the rest of the open
# data, see docs/data-notes.md). weight is an approximate population share.
GDL_MUNICIPIOS = {
    "Guadalajara": {
        "bbox": (20.5120, -103.4984, 20.8320, -103.1784),
        "weight": 1.39,
        "colonias": [
            "Centro", "Americana", "Lafayette", "Moderna", "Chapultepec Country Club",
            "Providencia", "Ladrón de Guevara", "Arcos Vallarta", "Vallarta Norte",
            "Vallarta Poniente", "Vallarta San Jorge", "Jardines del Bosque",
            "Mezquitán Country", "Santa Teresita", "Analco", "Oblatos",
            "El Retiro", "Independencia", "Mexicaltzingo", "Huentitán El Alto",
        ],
    },
    "Zapopan": {
        "bbox": (20.5611, -103.5514, 20.8811, -103.2314),
        "weight": 1.48,
        "colonias": [
            "Puerta de Hierro", "Valle Real", "Santa Margarita", "Colinas de San Javier",
            "Arcos de Zapopan", "Ciudad Granja", "Base Aérea", "Tesistán",
            "San Juan de Ocotán", "Real del Valle", "Paseos del Sol", "Lomas de Zapopan",
            "Seattle", "El Batán", "La Estancia", "Miramar", "Chapalita Oriente",
        ],
    },
    "San Pedro Tlaquepaque": {
        "bbox": (20.4798, -103.4720, 20.7998, -103.1520),
        "weight": 0.66,
        "colonias": [
            "Centro Tlaquepaque", "El Álamo", "Las Juntas", "La Aurora", "El Refugio",
            "Santa Anita", "Eduardo Guerra", "Toluquilla", "Las Liebres",
            "Lomas del Camichín", "San Pedrito", "Jardines del Sol",
        ],
    },
    "Tonalá": {
        "bbox": (20.4641, -103.4021, 20.7841, -103.0821),
        "weight": 0.60,
        "colonias": [
            "Centro Tonalá", "Loma Dorada", "Jalisco", "El Rosario", "Coyula",
            "Santa Paula", "Zalatitán", "Puente Grande", "Las Pilas",
        ],
    },
    "Tlajomulco de Zúñiga": {
        "bbox": (20.4337, -103.4870, 20.5137, -103.4070),
        "weight": 0.73,
        "colonias": [
            "Chulavista", "San Agustín", "Santa Fe", "Lomas de Tejeda",
            "Hacienda Santa Fe", "Los Gavilanes", "La Alameda", "El Palomar",
        ],
    },
}

# Monterrey metro area (Nuevo León). Same sourcing notes as GDL_MUNICIPIOS.
MTY_MUNICIPIOS = {
    "Monterrey": {
        "bbox": (25.5202, -100.4753, 25.8402, -100.1553),
        "weight": 1.14,
        "colonias": [
            "Centro", "Obispado", "Mitras Centro", "Mitras Norte", "Contry",
            "Roma", "Vista Hermosa", "Cumbres", "Del Norte", "Independencia",
            "Bellavista", "Tecnológico", "Chepevera", "Altavista", "Loma Larga",
            "San Jerónimo", "Anáhuac",
        ],
    },
    "Guadalupe": {
        "bbox": (25.5151, -100.3752, 25.8351, -100.0552),
        "weight": 0.62,
        "colonias": [
            "Valle Verde", "Real de Palmas", "Nueva Castilla", "Balcones de Alcalá",
            "Hacienda las Fuentes", "Framboyanes", "Paseo de las Torres",
        ],
    },
    "San Nicolás de los Garza": {
        "bbox": (25.5958, -100.4496, 25.9158, -100.1296),
        "weight": 0.43,
        "colonias": [
            "Anáhuac", "Residencial San Nicolás", "Praderas de San Nicolás",
            "Las Puentes", "Los Presidentes", "Industrial", "Talleres Universidad",
        ],
    },
    "Apodaca": {
        "bbox": (25.6217, -100.3488, 25.9417, -100.0288),
        "weight": 0.66,
        "colonias": [
            "Villas de San José", "Privadas del Sol", "Santa Rosa", "San Pablo",
            "Huinalá", "Concordia", "Puerta del Norte",
        ],
    },
    "San Pedro Garza García": {
        "bbox": (25.6252, -100.4418, 25.7052, -100.3618),
        "weight": 0.13,
        "colonias": [
            "Valle Oriente", "Del Valle", "San Agustín", "Fuentes del Valle",
            "Chipinque", "Valle del Campestre", "Lomas del Valle", "Carrizalejo",
        ],
    },
    "Santa Catarina": {
        "bbox": (25.6345, -100.5016, 25.7145, -100.4216),
        "weight": 0.31,
        "colonias": [
            "Las Encinas", "La Fama", "San Miguel", "Santiaguito",
            "Portal de Santa Catarina", "Villas de Santa Catarina",
        ],
    },
    "General Escobedo": {
        "bbox": (25.6485, -100.4824, 25.9685, -100.1624),
        "weight": 0.49,
        "colonias": [
            "Praderas de Escobedo", "Hacienda Escobedo", "Real de Escobedo", "San Rafael",
        ],
    },
}
