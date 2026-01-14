"""Basic import tests to verify dependencies are installed correctly."""

import pytest


def test_import_pandas():
    import pandas as pd
    assert pd.__version__


def test_import_numpy():
    import numpy as np
    assert np.__version__


def test_import_requests():
    import requests
    assert requests.__version__


def test_import_flask():
    from flask import Flask
    app = Flask(__name__)
    assert app is not None


def test_import_beautifulsoup():
    from bs4 import BeautifulSoup
    soup = BeautifulSoup("<html></html>", "html.parser")
    assert soup is not None


def test_import_backtrader():
    import backtrader as bt
    cerebro = bt.Cerebro()
    assert cerebro is not None
