from typing import Dict, Optional, Union

from fastapi.responses import Response, JSONResponse, PlainTextResponse
from connegp import RDF_MEDIATYPES, MEDIATYPE_NAMES

from renderers import ListRenderer
from config import *
from profiles.vocprez_profiles import dcat, dd
from models.vocprez import VocPrezCollectionList
from utils import templates


class VocPrezCollectionListRenderer(ListRenderer):
    profiles = {"dcat": dcat, "dd": dd}
    default_profile_token = "dcat"

    def __init__(
        self,
        request: object,
        instance_uri: str,
        label: str,
        comment: str,
        collection_list: VocPrezCollectionList,
        page: int,
        per_page: int,
        member_count: int
    ) -> None:
        super().__init__(
            request,
            VocPrezCollectionListRenderer.profiles,
            VocPrezCollectionListRenderer.default_profile_token,
            instance_uri,
            collection_list.members,
            label,
            comment,
            page,
            per_page,
            member_count
        )
        self.collection_list = collection_list

    def _render_dcat_html(self, template_context: Union[Dict, None]):
        """Renders the HTML representation of the DCAT profile for a dataset"""
        _template_context = {
            "request": self.request,
            "members": self.members,
            "uri": self.instance_uri,
            "pages": self.pages,
            "label": self.label,
            "comment": self.comment,
            "profiles": self.profiles,
            "default_profile": self.default_profile_token,
            "mediatype_names": MEDIATYPE_NAMES
        }
        if template_context is not None:
            _template_context.update(template_context)
        return templates.TemplateResponse(
            "vocprez/vocprez_collections.html", context=_template_context, headers=self.headers
        )

    def _render_dcat_json(self):
        return JSONResponse(
            content={
                "uri": self.instance_uri,
                "members": self.members,
                "label": self.label,
                "comment": self.comment,
            },
            media_type="application/json",
            headers=self.headers,
        )

    def _render_dcat_rdf(self):
        return Response(content="test DCAT RDF")

    def _render_dcat(self, template_context: Union[Dict, None]):
        if self.mediatype == "text/html":
            return self._render_dcat_html(template_context)
        elif self.mediatype in RDF_MEDIATYPES:
            return self._render_dcat_rdf()
        else:  # application/json
            return self._render_dcat_json()
    
    def _render_dd_json(self) -> JSONResponse:
        """Renders the json representation of the dd profile for a list of collections"""
        return JSONResponse(
            content=self.collection_list.get_collection_flat_list(),
            media_type="application/json",
            headers=self.headers,
        )

    def _render_dd(self):
        """Renders the dd profile for a list of collections"""
        return self._render_dd_json()

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
        elif self.profile == "dcat":
            return self._render_dcat(template_context)
        elif self.profile == "dd":
            return self._render_dd()
        else:
            return None
