from comands.commands import *
from comands.cart_handler import *
from comands.order_handler import *
from comands.start_command import StartCommand

class CommandFactory:
    def __init__(self, menu_repository, cart_repository, user_repository, order_repository):
        self.menu_repository = menu_repository
        self.cart_repository = cart_repository
        self.user_repository = user_repository
        self.order_repository = order_repository

        self.command_map = {
            "start": lambda: StartCommand(),
            "menu": lambda: MenuCommand(self.menu_repository),
            "button_handler": lambda: self.set_command_context(ButtonHandler()),
            "details": lambda: DetailsCommand(self.menu_repository),
            "all_details": lambda: AllDetailsCommand(self.menu_repository),
            "add_to_cart": lambda: AddToCartCommand(self.menu_repository, self.cart_repository),
            "open_cart": lambda: OpenCartCommand(self.cart_repository),
            "clean_cart": lambda: CleanCartCommand(self.cart_repository),
            "start_order": lambda: self.set_command_context(StartOrderCommand(self.user_repository, self.order_repository, self.cart_repository)),
            "confirm_order": lambda: ConfirmOrderCommand(self.user_repository, self.order_repository, self.cart_repository),
            "cancel_order": lambda: CancelOrderCommand(),
            "request_order_confirmation": lambda: RequestOrderConfirmationCommand(self.user_repository, self.cart_repository),
            "request_phone_number": lambda: RequestPhoneNumberCommand(),
            "request_location": lambda: RequestLocationCommand(),
            "got_phone_number": lambda: self.set_command_context(GotPhoneNumberCommand(self.user_repository)),
            "got_location": lambda: self.set_command_context(GotLocationCommand(self.user_repository)),
        }

    def set_command_context(self, command):
        if hasattr(command, 'set_factory'):
            command.set_factory(self)
        return command

    def get_command(self, command_name):
        command_constructor = self.command_map.get(command_name)
        if command_constructor:
            return command_constructor()
        else:
            raise ValueError(f"Unknown command: {command_name}")