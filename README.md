![](prez-logo.png)

# Prez
Prez is a Linked Data API framework tool that delivers read-only access to Knowledge Graph data according to particular domain _profiles_.

Prez comes in two main profile flavours:

- _VocPrez_ - for vocabularies, based on the [SKOS](https://www.w3.org/TR/skos-reference/) data model
- _SpacePrez_ - for spatial data, based on [OGC API](https://docs.ogc.org/is/17-069r3/17-069r3.html) specification and the [GeoSPARQL](https://opengeospatial.github.io/ogc-geosparql/geosparql11/spec.html) data model

Prez is pretty straight-forward to install and operate and while being high-performance, using modern [FastAPI](https://fastapi.tiangolo.com/) Python web framework. 

Prez is quite simple and expects "high quality" data to work well. By requiring that you create high quality for it, Prez ensures your value is retained in your data and not in a black box application: you remain in control!

## Features

- Linked Data delivery of any RDF graph content
    - human (HTML) & machine (RDF) formats
    - configurable alternative profiles available
- structured according to standardised APIs
    - e.g. [OGC API: Features](http://www.opengis.net/doc/IS/ogcapi-features-1/1.0) for spatial data
    - Open API/Swagger UI for developers
- highly customisable UI
    - Prez can always be made to look just the way you want it to
- data-driven
    - all of Prez' content delivery is driven by data configurations which you are in control of

A demo installation of a combined Voc and Space Prez is online at <https://prez.surroundaustralia.com>.

## Installing

### Local operation

Prez is 'just' a Python web framework API, so you can copy this repository to a local file location, install dependencies, configure its data back-end and run.

Install Python dependencies using Poetry (optional), which you can install [here](https://python-poetry.org/docs/#installation) (recommended), or by running:

```bash
pip install poetry 
```

Then run `poetry install` in the root directory, `Prez/`.

Otherwise install using `pip` as per regular Python applications:

```bash
pip install -r requirements.txt 
```

### Containers

You can run Prez as a Docker container:

```bash
docker pull surroundaustralia/prez
```

### Configuration

Each instance of Prez can be a VocPrez, a SpacePrez or both, all in one. Each will need to be configured: Prez needs to know where to get its data from. These repositories contain example configurantions and scritps for building configurations:

- VocPrez - [surround-prez-vocabs](https://github.com/surroundaustralia/surround-prez-vocabs)
- SpacePrez - [surround-prez-features](https://github.com/surroundaustralia/surround-prez-features)

### Running
To get started without any configuration, run `python3 app.py` in the `Prez/prez/` directory.

## Data
Each kind of Prez, VocPrez or SpacePrez, requires that data is reads conforms to a particular data specification:

- VocPrez
    - https://github.com/surroundaustralia/vocprez-profile
- SpacePrez
    - https://github.com/surroundaustralia/spaceprez-profile

Those specifications - data profiles - provide validators to allow you to check whether your data matches expectations _before_ you point Prez at it!

## Application Structure
The standard process for an entity endpoint is as follows:

1. An endpoint within a router is accessed (in `routers/`)
2. Endpoint calls SPARQL service to POST a SPARQL query (in `services/`)
3. The resulting RDFlib Graph is ingested by a model object (in `models/`)
4. A renderer object is created which uses the model object (in `renderers/`)
5. The endpoint returns the renderer's `render()` function
    - The response can be a renderered template (in `templates/`)

## Dev Dependencies

- SASS
    - Run the SASS watcher from the `sass/` folder like so:
        - If using dart-sass: `sass --no-source-map --watch main.scss ../css/index.css`
        - If using node-sass: `sass --source-map=none --watch main.scss ../css/index.css`

## License

Prez was originally developerd by [SURROUND Australia Pty Letd](https://surroundaustralia.com), building on top of previous tools such as [the original VocPrez](https://github.com/rdflib/VocPrez). In that form, it is licensed under the [BSD-3-Clause License](https://opensource.org/licenses/BSD-3-Clause). See [the original Prez LICENSE](https://github.com/surroundaustralia/Prez/blob/main/LICENSE) file for details.

This version of Prez and the contents of this repository are also available under the [BSD-3-Clause License](https://opensource.org/licenses/BSD-3-Clause). See [this repository's LICENSE](LICENSE) file for details.

## Contact & Support

Prez is commercially supported by:

**Kurrawong AI**  
https://kurrawong.net  
info@kurrawong.net  

If you just want more information:  

*Nicholas J. Car*  
Kurrawong AI  
nick@kurrawong.net
