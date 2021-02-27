from unsee_dl.unsee_old import get_album_id_from_url, is_beta_album_id


def test_get_album_id_from_url():
    assert get_album_id_from_url("https://app.unsee.cc/#243dbd04") == "243dbd04"
    assert (
        get_album_id_from_url("https://beta-app.unsee.cc/#t5jy62MGOCbRucOh")
        == "t5jy62MGOCbRucOh"
    )


def test_is_beta_album_id():
    assert not is_beta_album_id("243dbd04")
    assert is_beta_album_id("t5jy62MGOCbRucOh")
