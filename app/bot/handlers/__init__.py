from . import basic, autoregister, help, adduser, transactions

all_routers = [
    basic.router,
    help.router,
    adduser.router,
    transactions.router
    # autoregister.router
]
