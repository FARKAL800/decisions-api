#!/bin/bash
python case_scraper.py https://echanges.dila.gouv.fr/OPENDATA/CASS /Cases && python -m decision_api.main
