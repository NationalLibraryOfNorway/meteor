"""Test methods from the author_names module"""


from metadata_extract import author_name


def test_is_all_caps_spaced():
    assert author_name.is_all_caps_spaced('John Doe') is False
    assert author_name.is_all_caps_spaced('R A P P O R T') is True


def test_remove_parenthesis():
    text = 'Alice (forfatter), Bob (utgiver)'
    assert author_name.remove_parenthesis(text) == 'Alice , Bob '


def test_get_author_names():
    authors_string = 'Anne Mette Ødegård, Rolf K. Andersen, Bjorn Dapi og Cecilie Aagestad'
    authors = author_name.get_author_names(authors_string)
    assert set(authors) == {'Anne Mette Ødegård', 'Rolf K. Andersen',
                            'Bjorn Dapi', 'Cecilie Aagestad'}


def test_create_author_dict():
    assert author_name.create_author_dict('Anne Mette Ødegård') == \
        {'firstname': 'Anne Mette', 'lastname': 'Ødegård'}
    assert author_name.create_author_dict('Rolf K. Andersen') == \
        {'firstname': 'Rolf K.', 'lastname': 'Andersen'}
    assert author_name.create_author_dict('Bjørn Dapi') == \
        {'firstname': 'Bjørn', 'lastname': 'Dapi'}
