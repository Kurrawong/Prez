from typing import List, Dict, Optional
import json

from rdflib import Graph
from rdflib.namespace import DCTERMS, SKOS, RDFS, XSD

from config import *
from models import PrezModel


class SpacePrezFeature(PrezModel):
    # class attributes for property grouping & order
    main_props = [
        str(DCTERMS.title),
        # str(DCTERMS.description),
    ]
    geom_props = [str(GEO.hasGeometry)]
    hidden_props = [
        str(DCTERMS.identifier),
        str(DCTERMS.description),
    ]

    def __init__(
        self,
        graph: Graph,
        id: Optional[str] = None,
        uri: Optional[str] = None,
    ) -> None:
        super().__init__(graph)

        if id is None and uri is None:
            raise ValueError("Either an ID or a URI must be provided")

        query_by_id = f"""
            ?f dcterms:identifier ?id .
            FILTER (STR(?id) = "{id}")
        """

        query_by_uri = f"""
            BIND (<{uri}> as ?f) 
            ?f dcterms:identifier ?id .
        """

        r = self.graph.query(
            f"""
            PREFIX dcterms: <{DCTERMS}>
            PREFIX geo: <{GEO}>
            PREFIX rdfs: <{RDFS}>
            PREFIX skos: <{SKOS}>
            PREFIX xsd: <{XSD}>
            SELECT *
            WHERE {{
                {query_by_id if id is not None else query_by_uri}
                ?f a geo:Feature ;
                    dcterms:title ?title .
                FILTER(lang(?title) = "" || lang(?title) = "en")
                # OPTIONAL {{
                #     ?f dcterms:title ?label .
                # }}
                # BIND(COALESCE(?label, CONCAT("Feature ", ?id)) AS ?title)
                OPTIONAL {{
                    ?f dcterms:description ?desc .
                }}
                ?coll a geo:FeatureCollection ;
                    rdfs:member ?f ;
                    dcterms:identifier ?coll_id ;
                    dcterms:title ?coll_label .
                FILTER(lang(?coll_label) = "" || lang(?coll_label) = "en")
                ?d a dcat:Dataset ;
                    dcterms:identifier ?d_id ;
                    dcterms:title ?d_label .
                FILTER(lang(?d_label) = "" || lang(?d_label) = "en")
            }}
        """
        )

        result = r.bindings[0]
        self.uri = result["f"]
        self.id = result["id"]
        self.title = result["title"]
        self.description = result["desc"] if result.get("desc") else None
        self.collection = {
            "uri": result["coll"],
            "id": result["coll_id"],
            "title": result["coll_label"],
        }
        self.dataset = {
            "uri": result["d"],
            "id": result["d_id"],
            "title": result["d_label"],
        }
        self.geometries = {}

    # override
    def to_dict(self) -> Dict:
        return {
            "uri": self.uri,
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "properties": self._get_properties(),
            "geometries": self.geometries,
            "collection": self.collection,
            "dataset": self.dataset,
        }

    def to_geojson(self) -> Dict:
        """Returns the GeoJSON representation for the OpenAPI profile"""
        r = self.graph.query(
            f"""
            PREFIX geo: <{GEO}>
            SELECT ?geojson
            WHERE {{
                BIND (<{self.uri}> as ?f)
                ?f geo:hasGeometry/geo:asGeoJSON ?geojson .
            }}
        """
        )

        geom = r.bindings[0].get("geojson")

        g_dict = {
            "type": "Feature",
            "id": self.id,
            "geometry": json.loads(geom) if geom is not None else {},
            "properties": {},
        }

        return g_dict

    # override
    def _get_properties(self) -> List[Dict]:
        props_dict = self._get_props()

        # group props in order, filtering out hidden props
        properties = []
        main_props = []
        geom_props = []
        other_props = []

        for prop in props_dict:
            if prop["value"] in SpacePrezFeature.hidden_props:
                continue
            elif prop["value"] in SpacePrezFeature.main_props:
                main_props.append(prop)
            elif prop["value"] in SpacePrezFeature.geom_props:
                geom_props.append(prop)
                for bnode in prop["objects"][0]["rows"]:
                    bnode_prop_name = bnode["value"].split("#")[1]
                    if bnode_prop_name in ["asDGGS", "asGeoJSON", "asWKT"]:
                        self.geometries[bnode_prop_name] = bnode["objects"][0]["value"]
            else:
                other_props.append(prop)

        # sorts & combines into a single list
        properties.extend(main_props)
        properties.extend(geom_props)
        properties.extend(other_props)

        return properties
