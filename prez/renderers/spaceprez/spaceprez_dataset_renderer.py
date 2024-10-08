from typing import Dict, Optional, Union

from fastapi.responses import Response, JSONResponse, PlainTextResponse
from rdflib import Graph, URIRef, Literal
from rdflib.namespace import DCAT, DCTERMS, RDF
from connegp import MEDIATYPE_NAMES

from config import *
from renderers import Renderer
from profiles.spaceprez_profiles import dcat, oai, geo
from models.spaceprez import SpacePrezDataset
from utils import templates


class SpacePrezDatasetRenderer(Renderer):
    profiles = {"oai": oai, "dcat": dcat, "geo": geo}
    default_profile_token = "oai"

    def __init__(self, request: object, instance_uri: str) -> None:
        super().__init__(
            request,
            SpacePrezDatasetRenderer.profiles,
            SpacePrezDatasetRenderer.default_profile_token,
            instance_uri,
        )

    def set_dataset(self, dataset: SpacePrezDataset) -> None:
        self.dataset = dataset

    def _render_oai_html(
        self, template_context: Union[Dict, None]
    ) -> templates.TemplateResponse:
        """Renders the HTML representation of the OAI profile for a dataset"""
        _template_context = {
            "request": self.request,
            "dataset": self.dataset.to_dict(),
            "uri": self.instance_uri,
            "profiles": self.profiles,
            "default_profile": self.default_profile_token,
            "mediatype_names": dict(
                MEDIATYPE_NAMES, **{"application/geo+json": "GeoJSON"}
            ),
        }
        if template_context is not None:
            _template_context.update(template_context)
        return templates.TemplateResponse(
            "spaceprez/spaceprez_dataset.html",
            context=_template_context,
            headers=self.headers,
        )

    def _render_oai_json(self) -> JSONResponse:
        """Renders the JSON representation of the OAI profile for a dataset"""
        content = {
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
            ]
        }

        return JSONResponse(
            content=content,
            media_type="application/json",
            headers=self.headers,
        )

    # def _render_oai_geojson(self) -> JSONResponse:
    #     """Renders the GeoJSON representation of the OAI profile for a dataset"""
    #     return JSONResponse(
    #         content={"test": "test"},
    #         media_type="application/geo+json",
    #         headers=self.headers,
    #     )

    def _render_oai(self, template_context: Union[Dict, None]):
        """Renders the OAI profile for a dataset"""
        if self.mediatype == "text/html":
            return self._render_oai_html(template_context)
        else:  # else return JSON
            return self._render_oai_json()

    def _render_dcat_html(
        self, template_context: Union[Dict, None]
    ) -> templates.TemplateResponse:
        """Renders the HTML representation of the DCAT profile for a dataset"""
        return self._render_oai_html(template_context)

    def _generate_dcat_rdf(self) -> Graph:
        """Generates a Graph of the DCAT representation"""
        g = Graph()
        g.bind("dcat", DCAT)
        g.bind("dcterms", DCTERMS)
        ds = URIRef(self.dataset.uri)
        g.add((ds, RDF.type, DCAT.Dataset))
        g.add((ds, DCTERMS.title, Literal(self.dataset.title)))
        g.add((ds, DCTERMS.description, Literal(self.dataset.description)))

        api = URIRef(self.instance_uri)
        g.add((api, DCAT.servesDataset, ds))
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
        g.add((sparql, DCAT.servesDataset, ds))
        g.add((sparql, RDF.type, DCAT.DataService))
        g.add((sparql, DCTERMS.title, Literal("System SPARQL Service")))
        g.add(
            (
                sparql,
                DCTERMS.description,
                Literal(
                    "A SPARQL Protocol-compliant service that provides access to all "
                    "of this catalogue's information"
                ),
            )
        )
        g.add((sparql, DCTERMS.type, URIRef("http://purl.org/dc/dcmitype/Service")))
        g.add((sparql, DCAT.endpointURL, sparql))

        return g

    def _render_dcat_rdf(self) -> Response:
        """Renders the RDF representation of the DCAT profile for a dataset"""
        g = self._generate_dcat_rdf()
        return self._make_rdf_response(g)

    def _render_dcat(self, template_context: Union[Dict, None]):
        """Renders the DCAT profile for a dataset"""
        if self.mediatype == "text/html":
            return self._render_dcat_html(template_context)
        else:  # all other formats are RDF
            return self._render_dcat_rdf()

    def _generate_geo_rdf(self) -> Graph:
        """Generates a Graph of the GeoSPARQL representation"""
        r = self.dataset.graph.query(
            f"""
        PREFIX dcat: <{DCAT}>
        PREFIX dcterms: <{DCTERMS}>
        PREFIX geo: <{GEO}>
        CONSTRUCT {{
            ?d a dcat:Dataset ;
                ?d_pred ?d_o ;
                geo:hasBoundingBox ?geom .
            ?geom ?geom_p ?geom_o .
        }}
        WHERE {{
            BIND (<{self.dataset.uri}> AS ?d)
            ?d a dcat:Dataset .
            OPTIONAL {{
                ?d ?d_pred ?d_o .
                FILTER (STRSTARTS(STR(?d_pred), STR(geo:)))
            }}
            OPTIONAL {{
                ?d geo:hasBoundingBox ?geom .
                ?geom ?geom_p ?geom_o .
            }}
        }}
        """
        )

        g = r.graph
        g.bind("dcat", DCAT)
        g.bind("dcterms", DCTERMS)
        g.bind("geo", GEO)

        return g

    def _render_geo_rdf(self) -> Response:
        """Renders the RDF representation of the GeoSPAQRL profile for a dataset"""
        g = self._generate_geo_rdf()
        return self._make_rdf_response(g)

    def _render_geo(self):
        """Renders the GeoSPARQL profile for a dataset"""
        return self._render_geo_rdf()

    def render(
        self, template_context: Optional[Dict] = None
    ) -> Union[
        PlainTextResponse, templates.TemplateResponse, Response, JSONResponse, None
    ]:
        if self.error is not None:
            return PlainTextResponse(self.error, status_code=400)
        elif self.profile == "alt":
            return self._render_alt(template_context)
        elif self.profile == "oai":
            return self._render_oai(template_context)
        elif self.profile == "dcat":
            return self._render_dcat(template_context)
        elif self.profile == "geo":
            return self._render_geo()
        else:
            return None
