
from questrade import QuestradeClient
from pprint import pprint

c = QuestradeClient()
pprint(c.get_accounts())
