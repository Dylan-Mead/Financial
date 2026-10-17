from unittest.mock import Mock, patch

from news import news_analyzer_1


def test_retrieve_articles_retries_a_temporary_connection_error():
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"news": []}

    with (
        patch.object(
            news_analyzer_1.requests,
            "get",
            side_effect=[
                news_analyzer_1.requests.ConnectionError("network unavailable"),
                response,
            ],
        ) as get,
        patch.object(news_analyzer_1.time, "sleep") as sleep,
    ):
        articles = news_analyzer_1.retrieve_articles(
            ["AAPL"],
            {"APCA-API-KEY-ID": "test", "APCA-API-SECRET-KEY": "test"},
        )

    assert articles == []
    assert get.call_count == 2
    sleep.assert_called_once_with(news_analyzer_1.INITIAL_RETRY_DELAY_SECONDS)
