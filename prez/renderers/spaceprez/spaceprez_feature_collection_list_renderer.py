from typing import Dict, Optional, Union

from fastapi.responses import Response, JSONResponse, PlainTextResponse
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DCAT, DCTERMS, RDF, RDFS
from connegp import MEDIATYPE_NAMES

from renderers import ListRenderer
from config import *
from profiles.spaceprez_profiles import oai, dd, geo
from models.spaceprez import SpacePrezFeatureCollectionList
from utils import templates


class SpacePrezFeatureCollectionListRenderer(ListRenderer):
    profiles = {"oai": oai, "geo": geo, "dd": dd}
    default_profile_token = "oai"

    def __init__(
        self,
        request: object,
        instance_uri: str,
        label: str,
        comment: str,
        feature_collection_list: SpacePrezFeatureCollectionList,
        page: int,
        per_page: int,
        member_count: int,
    ) -> None:
        super().__init__(
            request,
            SpacePrezFeatureCollectionListRenderer.profiles,
            SpacePrezFeatureCollectionListRenderer.default_profile_token,
            instance_uri,
            feature_collection_list.members,
            label,
            comment,
            page,
            per_page,
            member_count,
        )
        self.feature_collection_list = feature_collection_list

    def _render_oai_html(self, template_context: Union[Dict, None]):
        """Renders the HTML representation of the OAI profile for a list of feature collections"""
        _template_context = {
            "request": self.request,
            "members": self.members,
            "dataset": self.feature_collection_list.dataset,
            "uri": self.instance_uri,
            "pages": self.pages,
            "label": self.label,
            "comment": self.comment,
            "profiles": self.profiles,
            "default_profile": self.default_profile_token,
            "mediatype_names": dict(
                MEDIATYPE_NAMES, **{"application/geo+json": "GeoJSON"}
            ),
        }
        if template_context is not None:
            _template_context.update(template_context)
        return templates.TemplateResponse(
            "spaceprez/spaceprez_feature_collections.html",
            context=_template_context,
            headers=self.headers,
        )

    def _render_oai_json(self) -> JSONResponse:
        """Renders the JSON representation of the OAI profile for a dataset"""
        collections = []

        for member in self.members:
            collections.append(
                {
                    "id": member["id"],
                    "title": member["title"],
                    "links": [
                        {
                            "href": self.request.url_for(
                                "features",
                                dataset_id=self.feature_collection_list.dataset["id"],
                                collection_id=member["id"],
                            ),
                            "rel": "items",
                            "type": self.mediatype,
                            "title": member["title"],
                        },
                    ],
                }
            )

        content = {
            "collections": collections,
            "links": [
                {
                    "href": str(self.request.url),
                    "rel": "self",
                    "type": self.mediatype,
                    "title": "this document",
                },
                {
                    "href": str(self.request.base_url)[:-1]
                    + str(self.request.url.path),
                    "rel": "alternate",
                    "type": "text/html",
                    "title": "this document as HTML",
                },
            ],
        }

        return JSONResponse(
            content=content,
            media_type="application/json",
            headers=self.headers,
        )

    def _render_oai(self, template_context: Union[Dict, None]):
        """Renders the OAI profile for a list of feature collections"""
        if self.mediatype == "text/html":
            return self._render_oai_html(template_context)
        else:  # else return JSON
            return self._render_oai_json()

    def _render_dd_json(self) -> JSONResponse:
        """Renders the json representation of the dd profile for a list of feature collections"""
        return JSONResponse(
            content=self.feature_collection_list.get_feature_collection_flat_list(),
            media_type="application/json",
            headers=self.headers,
        )

    def _render_dd(self):
        """Renders the dd profile for a list of feature collections"""
        return self._render_dd_json()

    def _generate_geo_rdf(self) -> Graph:
        """Generates a Graph of the GeoSPARQL representation"""
        g = self._generate_mem_rdf()
        g.bind("dcat", DCAT)
        g.bind("dcterms", DCTERMS)
        for s in g.subjects(predicate=RDF.type, object=RDF.Bag):
            g.remove((s, RDF.type, RDF.Bag))
            g.add((s, RDF.type, DCAT.Catalog))

            for p, o in g.predicate_objects(subject=s):
                if p == RDFS.label:
                    g.remove((s, p, o))
                    g.add((s, DCTERMS.title, o))
                elif p == RDFS.comment:
                    g.remove((s, p, o))
                    g.add((s, DCTERMS.description, o))

            api = URIRef(self.instance_uri)
            g.add((api, RDF.type, DCAT.DataService))
            g.add((api, DCTERMS.title, Literal("System ConnegP API")))
            g.add(
                (
                    api,
                    DCTERMS.description,
                    Literal(
                        "A Content Negotiation by Profile-compliant service that provides "
                        "access to all of this catalogue's information"
                    ),
                )
            )
            g.add((api, DCTERMS.type, URIRef("http://purl.org/dc/dcmitype/Service")))
            g.add((api, DCAT.endpointURL, api))

            sparql = URIRef(self.instance_uri + "/sparql")
            g.add((sparql, RDF.type, DCAT.DataService))
            g.add((sparql, DCTERMS.title, Literal("System SPARQL Service")))
            g.add(
                (
                    sparql,
                    DCTERMS.description,
                    Literal(
                        "A SPARQL Protocol-compliant service that provides access "
                        "to all of this catalogue's information"
                    ),
                )
            )
            g.add((sparql, DCTERMS.type, URIRef("http://purl.org/dc/dcmitype/Service")))
            g.add((sparql, DCAT.endpointURL, sparql))

        for s, o in g.subject_objects(predicate=RDFS.member):
            g.remove((s, RDFS.member, o))
            g.add((o, RDF.type, DCAT.FeatureCollection))
            g.add((s, DCAT.dataset, o))
            for p2, o2 in g.predicate_objects(subject=o):
                if p2 == RDFS.label:
                    g.remove((o, p2, o2))
                    g.add((o, DCTERMS.title, o2))
                elif p2 == RDFS.comment:
                    g.remove((o, p2, o2))
                    g.add((o, DCTERMS.description, o2))

        return g

    def _render_geo_rdf(self) -> Response:
        """Renders the RDF representation of the GeoSPAQRL profile for a list of feature collections"""
        g = self._generate_geo_rdf()
        return self._make_rdf_response(g)

    def _render_geo(self):
        """Renders the GeoSPARQL profile for a list of feature collections"""
        return self._render_geo_rdf()

    def render(
        self, template_context: Optional[Dict] = None
    ) -> Union[
        PlainTextResponse, templates.TemplateResponse, Response, JSONResponse, None
    ]:
        if self.error is not None:
            return PlainTextResponse(self.error, status_code=400)
        elif self.profile == "mem":
            return self._render_mem(template_context)
        elif self.profile == "alt":
            return self._render_alt(template_context)
        elif self.profile == "oai":
            return self._render_oai(template_context)
        elif self.profile == "geo":
            return self._render_geo()
        elif self.profile == "dd":
            return self._render_dd()
        else:
            return None
