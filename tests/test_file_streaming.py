import pytest
from bareasgi_static.file_streaming import file_writer


@pytest.mark.asyncio
async def test_file_writer():
    with open(__file__, 'rb') as fp:
        expected = fp.read()

    writer = file_writer(__file__)
    received = b''
    async for block in writer:
        received += block

    assert received == expected
