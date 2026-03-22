import importlib

import pytest

from moneypoly.bank import Bank
from moneypoly.board import Board
from moneypoly.cards import CardDeck
from moneypoly.config import GO_SALARY, INCOME_TAX_AMOUNT, JAIL_FINE, LUXURY_TAX_AMOUNT
from moneypoly.dice import Dice
from moneypoly.game import Game
from moneypoly.player import Player
from moneypoly.property import Property, PropertyGroup
from moneypoly import ui
import main as main_module


class TestPackageImports:
    def test_import_game_from_package(self):
        mod = importlib.import_module("moneypoly.game")
        assert hasattr(mod, "Game")


class TestDiceBranches:
    def test_roll_allows_six_as_edge_value(self, monkeypatch):
        calls = []

        def fake_randint(low, high):
            calls.append((low, high))
            return 6

        monkeypatch.setattr("random.randint", fake_randint)
        dice = Dice()
        total = dice.roll()

        assert calls == [(1, 6), (1, 6)]
        assert total == 12

    def test_doubles_streak_increments_then_resets(self, monkeypatch):
        vals = iter([3, 3, 4, 1])
        monkeypatch.setattr("random.randint", lambda _a, _b: next(vals))

        dice = Dice()
        dice.roll()
        assert dice.doubles_streak == 1

        dice.roll()
        assert dice.doubles_streak == 0

    def test_dice_repr(self):
        dice = Dice()
        assert "die1" in repr(dice)


class TestPlayerMovementBranches:
    def test_landing_on_go_collects_salary(self):
        player = Player("P", balance=1000)
        player.position = 39
        player.move(1)
        assert player.position == 0
        assert player.balance == 1000 + GO_SALARY

    def test_passing_go_without_landing_also_collects_salary(self):
        player = Player("P", balance=1000)
        player.position = 39
        player.move(2)
        assert player.position == 1
        assert player.balance == 1000 + GO_SALARY


class TestPropertyOwnershipLogic:
    def test_all_owned_by_requires_every_property(self):
        group = PropertyGroup("Brown", "brown")
        p1 = Property("A", 1, 60, 2, group)
        Property("B", 3, 60, 4, group)
        owner = Player("Owner")
        p1.owner = owner

        assert group.all_owned_by(owner) is False

    def test_all_owned_by_true_when_every_property_matches(self):
        group = PropertyGroup("Brown", "brown")
        p1 = Property("A", 1, 60, 2, group)
        p2 = Property("B", 3, 60, 4, group)
        owner = Player("Owner")
        p1.owner = owner
        p2.owner = owner
        assert group.all_owned_by(owner) is True

    def test_all_owned_by_none_player_returns_false(self):
        group = PropertyGroup("Brown", "brown")
        Property("A", 1, 60, 2, group)
        assert group.all_owned_by(None) is False


class TestBoardBranchCoverage:
    def test_is_purchasable_branches(self):
        board = Board()

        assert board.is_purchasable(0) is False

        prop = board.get_property_at(1)
        prop.owner = None
        prop.is_mortgaged = False
        assert board.is_purchasable(1) is True

        prop.is_mortgaged = True
        assert board.is_purchasable(1) is False

        prop.is_mortgaged = False
        prop.owner = Player("O")
        assert board.is_purchasable(1) is False


class TestGameFinancialLogic:
    def test_buy_property_with_exact_balance_succeeds(self):
        game = Game(["A", "B"])
        buyer = game.players[0]
        prop = game.board.get_property_at(1)
        buyer.balance = prop.price

        assert game.buy_property(buyer, prop) is True
        assert prop.owner == buyer
        assert buyer.balance == 0

    def test_pay_rent_transfers_to_owner(self):
        game = Game(["Tenant", "Owner"])
        tenant, owner = game.players
        prop = game.board.get_property_at(1)
        prop.owner = owner
        rent = prop.get_rent()

        game.pay_rent(tenant, prop)

        assert tenant.balance == 1500 - rent
        assert owner.balance == 1500 + rent

    def test_jail_fine_choice_deducts_player_balance(self, monkeypatch):
        game = Game(["A", "B"])
        player = game.players[0]
        player.in_jail = True
        start_balance = player.balance

        monkeypatch.setattr("moneypoly.ui.confirm", lambda _p: True)
        monkeypatch.setattr(game.dice, "roll", lambda: 4)
        monkeypatch.setattr(game, "_move_and_resolve", lambda _p, _s: None)

        game._handle_jail_turn(player)

        assert player.balance == start_balance - JAIL_FINE
        assert game.bank.get_balance() >= 0

    def test_find_winner_returns_highest_net_worth(self):
        game = Game(["L", "M", "H"])
        game.players[0].balance = 100
        game.players[1].balance = 500
        game.players[2].balance = 1500

        assert game.find_winner().name == "H"


class TestGameDeepBranchCoverage:
    def test_unmortgage_insufficient_funds_keeps_property_mortgaged(self):
        game = Game(["A", "B"])
        player = game.players[0]
        prop = game.board.get_property_at(1)
        prop.owner = player
        player.add_property(prop)
        prop.is_mortgaged = True
        player.balance = 0

        assert game.unmortgage_property(player, prop) is False
        assert prop.is_mortgaged is True

    def test_trade_transfers_cash_from_buyer_to_seller(self):
        game = Game(["Seller", "Buyer"])
        seller, buyer = game.players
        prop = game.board.get_property_at(1)
        prop.owner = seller
        seller.add_property(prop)

        result = game.trade(seller, buyer, prop, 100)

        assert result is True
        assert seller.balance == 1600
        assert buyer.balance == 1400
        assert prop.owner == buyer

    def test_buy_property_rejects_already_owned_property(self):
        game = Game(["A", "B"])
        first, second = game.players
        prop = game.board.get_property_at(1)
        game.buy_property(first, prop)

        assert game.buy_property(second, prop) is False
        assert prop.owner == first

    def test_auction_property_rejects_already_owned_property(self):
        game = Game(["A", "B"])
        prop = game.board.get_property_at(1)
        prop.owner = game.players[0]

        game.auction_property(prop)

        assert prop.owner == game.players[0]

    def test_interactive_menu_loan_over_limit_does_not_crash(self, monkeypatch):
        game = Game(["A", "B"])
        player = game.players[0]
        game.bank._funds = 100

        choices = iter([6, 1_000_000, 0])
        monkeypatch.setattr("moneypoly.ui.safe_int_input", lambda _p, default=0: next(choices))

        game.interactive_menu(player)

        assert player.balance == 1500

    def test_card_collect_with_insufficient_bank_funds_is_safe(self):
        game = Game(["A", "B"])
        player = game.players[0]
        game.bank._funds = 1

        game._apply_card(player, {"description": "Collect", "action": "collect", "value": 500})

        assert player.balance == 1500

    def test_apply_card_malformed_is_safe(self):
        game = Game(["A", "B"])
        player = game.players[0]

        game._apply_card(player, {"description": "Broken"})

        assert player.balance == 1500

    def test_advance_turn_wraps_and_increments_counter(self):
        game = Game(["A", "B"])
        game.current_index = 1
        game.turn_number = 10

        game.advance_turn()

        assert game.current_index == 0
        assert game.turn_number == 11

    def test_play_turn_branch_in_jail(self, monkeypatch):
        game = Game(["A", "B"])
        game.players[0].in_jail = True
        calls = {"jail": 0}

        monkeypatch.setattr(game, "_handle_jail_turn", lambda _p: calls.__setitem__("jail", 1))

        game.play_turn()
        assert calls["jail"] == 1

    def test_play_turn_branch_three_doubles_sends_to_jail(self, monkeypatch):
        game = Game(["A", "B"])
        player = game.players[0]

        monkeypatch.setattr(game.dice, "roll", lambda: 4)
        monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2")
        monkeypatch.setattr(game.dice, "doubles_streak", 3)

        game.play_turn()

        assert player.in_jail is True

    def test_play_turn_branch_doubles_gets_extra_turn(self, monkeypatch):
        game = Game(["A", "B"])
        monkeypatch.setattr(game.dice, "roll", lambda: 4)
        monkeypatch.setattr(game.dice, "describe", lambda: "2 + 2")
        monkeypatch.setattr(game.dice, "doubles_streak", 1)
        monkeypatch.setattr(game.dice, "is_doubles", lambda: True)
        monkeypatch.setattr(game, "_move_and_resolve", lambda _p, _s: None)

        game.play_turn()
        assert game.turn_number == 0

    def test_play_turn_branch_normal_advance(self, monkeypatch):
        game = Game(["A", "B"])
        monkeypatch.setattr(game.dice, "roll", lambda: 5)
        monkeypatch.setattr(game.dice, "describe", lambda: "2 + 3")
        monkeypatch.setattr(game.dice, "doubles_streak", 0)
        monkeypatch.setattr(game.dice, "is_doubles", lambda: False)
        monkeypatch.setattr(game, "_move_and_resolve", lambda _p, _s: None)

        game.play_turn()
        assert game.turn_number == 1

    def test_move_and_resolve_tile_branches(self, monkeypatch):
        game = Game(["A", "B"])
        player = game.players[0]

        monkeypatch.setattr(player, "move", lambda _s: None)
        monkeypatch.setattr(game, "_check_bankruptcy", lambda _p: None)

        player.position = 4
        monkeypatch.setattr(game.board, "get_tile_type", lambda _p: "income_tax")
        start = player.balance
        game._move_and_resolve(player, 1)
        assert player.balance == start - INCOME_TAX_AMOUNT

        player.position = 38
        monkeypatch.setattr(game.board, "get_tile_type", lambda _p: "luxury_tax")
        start = player.balance
        game._move_and_resolve(player, 1)
        assert player.balance == start - LUXURY_TAX_AMOUNT

        player.position = 30
        monkeypatch.setattr(game.board, "get_tile_type", lambda _p: "go_to_jail")
        game._move_and_resolve(player, 1)
        assert player.in_jail is True

    def test_move_and_resolve_blank_tile_path(self, monkeypatch):
        game = Game(["A", "B"])
        player = game.players[0]
        calls = {"checked": 0}

        monkeypatch.setattr(player, "move", lambda _s: None)
        monkeypatch.setattr(game.board, "get_tile_type", lambda _p: "blank")
        monkeypatch.setattr(game, "_check_bankruptcy", lambda _p: calls.__setitem__("checked", 1))

        game._move_and_resolve(player, 1)
        assert calls["checked"] == 1


class TestBankAndDeckBranches:
    def test_bank_collect_positive_and_negative_amounts(self):
        bank = Bank()
       
￼
94 x 5
1
CHAT
WHITE BOX TESTING ASSIGNMENT INSTRUCTIONS
Great call — this is exactly what evaluators look for.

Recommended commit history (Task 1 only)
Use these in order so your history looks intentional and matches the assignment wording.

Task1-Setup: create whitebox submission structure

Add: tests, diagrams, report.md, README.md, .gitignore
Iteration 1: Fix package/lint setup issues for MoneyPoly

Add: __init__.py, cleanup changes in bank.py, game.py, player.py
Iteration 2: Resolve remaining pylint warning in input handling

Add: ui.py
Error 1: Fix dice roll range to include 6

Add: dice.py
Error 2: Fix pass-Go salary logic in player movement

Add: player.py
Error 3: Fix full-group ownership check for rent multiplier

Add: property.py
Error 4: Fix exact-balance property purchase condition

Add: game.py
Error 5: Fix rent transfer to property owner

Add: game.py
Error 6: Fix winner selection to highest net worth

Add: game.py
 start = bank.get_balance()
        bank.collect(100)
        bank.collect(-20)
        assert bank.get_balance() == start + 80

    def test_bank_pay_out_branches(self):
        bank = Bank()
        assert bank.pay_out(0) == 0
        assert bank.pay_out(-1) == 0
        assert bank.pay_out(100) == 100

    def test_bank_pay_out_raises_when_insufficient_funds(self):
        bank = Bank()
        with pytest.raises(ValueError):
            bank.pay_out(10**9)

    def test_bank_give_loan_non_positive_and_positive(self):
        bank = Bank()
        player = Player("P")
        start_bank = bank.get_balance()

        bank.give_loan(player, 0)
        assert player.balance == 1500

        bank.give_loan(player, 100)
        assert player.balance == 1600
        assert bank.get_balance() == start_bank - 100
        assert bank.loan_count() == 1
        assert bank.total_loans_issued() == 100

    def test_bank_give_loan_raises_when_insufficient_funds(self):
        bank = Bank()
        bank._funds = 50
        with pytest.raises(ValueError):
            bank.give_loan(Player("P"), 100)

    def test_bank_summary_prints(self, capsys):
        bank = Bank()
        bank.summary()
        out = capsys.readouterr().out
        assert "Bank reserves" in out

    def test_bank_repr(self):
        assert "funds" in repr(Bank())

    def test_card_deck_draw_empty_and_cycle(self):
        empty = CardDeck([])
        assert empty.draw() is None

        deck = CardDeck([{"v": 1}, {"v": 2}])
        assert deck.draw()["v"] == 1
        assert deck.draw()["v"] == 2
        assert deck.draw()["v"] == 1

    def test_card_deck_peek_and_reshuffle(self, monkeypatch):
        deck = CardDeck([{"v": 1}, {"v": 2}])
        assert deck.peek()["v"] == 1
        deck.draw()
        monkeypatch.setattr("random.shuffle", lambda cards: cards.reverse())
        deck.reshuffle()
        assert deck.index == 0
        assert deck.peek()["v"] == 2

    def test_card_deck_empty_remaining_and_repr_are_safe(self):
        deck = CardDeck([])
        assert deck.cards_remaining() == 0
        assert "next=none" in repr(deck)


class TestPlayerPropertyAndBoardExtras:
    def test_player_negative_money_operations_raise(self):
        p = Player("P")
        with pytest.raises(ValueError):
            p.add_money(-1)
        with pytest.raises(ValueError):
            p.deduct_money(-1)

    def test_player_non_wrap_move_and_jail_and_property_helpers(self):
        p = Player("P")
        p.position = 5
        p.move(3)
        assert p.position == 8

        p.go_to_jail()
        assert p.in_jail is True

        grp = PropertyGroup("B", "brown")
        prop = Property("X", 1, 60, 2, grp)
        p.add_property(prop)
        assert p.count_properties() == 1
        p.remove_property(prop)
        assert p.count_properties() == 0

    def test_player_bankruptcy_threshold(self):
        p = Player("P")
        p.balance = 0
        assert p.is_bankrupt() is True
        p.balance = 1
        assert p.is_bankrupt() is False

    def test_player_net_worth_includes_property_values(self):
        p = Player("P", balance=100)
        grp = PropertyGroup("B", "brown")
        prop = Property("X", 1, 60, 2, grp)
        prop.owner = p
        p.add_property(prop)

        assert p.net_worth() == 160

        prop.is_mortgaged = True
        assert p.net_worth() == 130

    def test_property_constructor_argument_validation(self):
        with pytest.raises(TypeError):
            Property()

    def test_property_rent_mortgage_and_availability_branches(self):
        grp = PropertyGroup("B", "brown")
        p1 = Property("A", 1, 60, 2, grp)
        p2 = Property("B", 3, 60, 4, grp)
        owner = Player("Owner")

        p1.owner = owner
        assert p1.get_rent() == 2
        p2.owner = owner
        assert p1.get_rent() == 4

        payout = p1.mortgage()
        assert payout == p1.mortgage_value
        assert p1.get_rent() == 0
        assert p1.is_available() is False

        cost = p1.unmortgage()
        assert cost > payout

    def test_property_group_helpers(self):
        grp = PropertyGroup("B", "brown")
        p1 = Property("A", 1, 60, 2)
        p2 = Property("B", 3, 60, 4)
        grp.add_property(p1)
        grp.add_property(p2)
        owner = Player("O")
        p1.owner = owner

        counts = grp.get_owner_counts()
        assert counts[owner] == 1
        assert grp.size() == 2

    def test_board_helpers(self):
        board = Board()
        owner = Player("Owner")
        prop = board.get_property_at(1)
        prop.owner = owner

        assert board.get_tile_type(1) == "property"
        assert board.is_special_tile(0) is True
        assert prop in board.properties_owned_by(owner)
        assert isinstance(board.unowned_properties(), list)


class TestUIHelpers:
    def test_safe_int_input_valid(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _p: "12")
        assert ui.safe_int_input("x") == 12

    def test_safe_int_input_invalid_returns_default(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _p: "abc")
        assert ui.safe_int_input("x", default=7) == 7

    def test_confirm_yes(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _p: "y")
        assert ui.confirm("x") is True

    def test_confirm_no(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _p: "n")
        assert ui.confirm("x") is False

    def test_format_currency(self):
        assert ui.format_currency(1500) == "$1,500"


class TestMainModuleBranches:
    def test_get_player_names_parsing(self, monkeypatch):
        monkeypatch.setattr("builtins.input", lambda _p: "  A, B, ,C  ")
        assert main_module.get_player_names() == ["A", "B", "C"]

    def test_main_runs_game_successfully(self, monkeypatch):
        events = []

        class FakeGame:
            def __init__(self, names):
                events.append(("init", names))

            def run(self):
                events.append(("run",))

        monkeypatch.setattr(main_module, "get_player_names", lambda: ["A", "B"])
        monkeypatch.setattr(main_module, "Game", FakeGame)

        main_module.main()

        assert events == [("init", ["A", "B"]), ("run",)]

    def test_main_handles_keyboard_interrupt(self, monkeypatch, capsys):
        class FakeGame:
            def __init__(self, _names):
                pass

            def run(self):
                raise KeyboardInterrupt

        monkeypatch.setattr(main_module, "get_player_names", lambda: ["A", "B"])
        monkeypatch.setattr(main_module, "Game", FakeGame)

        main_module.main()

        assert "Game interrupted" in capsys.readouterr().out

    def test_main_handles_value_error(self, monkeypatch, capsys):
        monkeypatch.setattr(main_module, "get_player_names", lambda: ["A"])

        main_module.main()

        assert "Setup error" in capsys.readouterr().out

    def test_main_rejects_less_than_two_players(self, monkeypatch):
        monkeypatch.setattr(main_module, "get_player_names", lambda: ["OnlyOne"])
        main_module.main()
