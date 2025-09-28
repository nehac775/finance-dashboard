import src.finance as fin

def test_fetch_history():
    df = fin.fetch_history("AAPL")
    assert isinstance(df, type(__import__('pandas').DataFrame))
