# Powtórki Online API

## Docs

Swagger at:
`/docs`

OpenApi at:
`/openapi.json`

## Installation

Create new env python3.9 or python3.10

`pip instal -r requirements.txt`

## Run

To run development server from main directory type:

`uvicorn app.main:app --reload --header server:PowtorkiOnlineApi`

To run production server from main directory type:

`uvicorn app.main:app --workers 12 --header server:PowtorkiOnlineApi`