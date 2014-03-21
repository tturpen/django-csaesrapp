class DuplicateSentenceIds(Exception):
    """Raise if there are duplicate sentence ids in the prompts"""
    def __init__(self,message):
        raise self 