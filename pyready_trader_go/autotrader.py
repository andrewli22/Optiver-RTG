# Copyright 2021 Optiver Asia Pacific Pty. Ltd.
#
# This file is part of Ready Trader Go.
#
#     Ready Trader Go is free software: you can redistribute it and/or
#     modify it under the terms of the GNU Affero General Public License
#     as published by the Free Software Foundation, either version 3 of
#     the License, or (at your option) any later version.
#
#     Ready Trader Go is distributed in the hope that it will be useful,
#     but WITHOUT ANY WARRANTY; without even the implied warranty of
#     MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#     GNU Affero General Public License for more details.
#
#     You should have received a copy of the GNU Affero General Public
#     License along with Ready Trader Go.  If not, see
#     <https://www.gnu.org/licenses/>.
import asyncio
from email.mime import base
import itertools
from re import S
from socket import NI_NAMEREQD
from turtle import update
import pandas as pd
from typing import List

from ready_trader_go import BaseAutoTrader, Instrument, Lifespan, MAXIMUM_ASK, MINIMUM_BID, Side

import matplotlib.pyplot as plt
LOT_SIZE = 10
POSITION_LIMIT = 100
TICK_SIZE_IN_CENTS = 100


class AutoTrader(BaseAutoTrader):
    """Example Auto-trader.

    When it starts this auto-trader places ten-lot bid and ask orders at the
    current best-bid and best-ask prices respectively. Thereafter, if it has
    a long position (it has bought more lots than it has sold) it reduces its
    bid and ask prices. Conversely, if it has a short position (it has sold
    more lots than it has bought) then it increases its bid and ask prices.
    """

    def __init__(self, loop: asyncio.AbstractEventLoop, team_name: str, secret: str):
        """Initialise a new instance of the AutoTrader class."""
        super().__init__(loop, team_name, secret)
        self.order_ids = itertools.count(1)
        self.bids = set()
        self.asks = set()
        self.ask_id = self.ask_price = self.bid_id = self.bid_price = self.position = 0
        self.nine_period = []
        self.twenty_six_period = []
        self.fifty_two_period = []
        
        self.updateCounter = 0
        self.converl = []
        self.bassl = []
        self.Aspan = []
        self.Bspan = []
        self.y = []
        self.conversion_line = self.base_line = self.span_A = self.span_B = 0
    


    def on_error_message(self, client_order_id: int, error_message: bytes) -> None:
        """Called when the exchange detects an error.

        If the error pertains to a particular order, then the client_order_id
        will identify that order, otherwise the client_order_id will be zero.
        """
        self.logger.warning("error with order %d: %s", client_order_id, error_message.decode())
        if client_order_id != 0:
            self.on_order_status_message(client_order_id, 0, 0, 0)

    def on_hedge_filled_message(self, client_order_id: int, price: int, volume: int) -> None:
        """Called when one of your hedge orders is filled, partially or fully.

        The price is the average price at which the order was (partially) filled,
        which may be better than the order's limit price. The volume is
        the number of lots filled at that price.

        If the order was unsuccessful, both the price and volume will be zero.
        """
        self.logger.info("received hedge filled for order %d with average price %d and volume %d", client_order_id,
                         price, volume)

    def indicator(self, ask_prices, bid_prices):
        
        if (bid_prices[0] != 0):
            self.nine_period.append(bid_prices[0])
            if (len(self.nine_period) == 10):
                self.nine_period.pop(0)
        
        if (bid_prices[0] != 0):
            self.twenty_six_period.append(bid_prices[0])
            if (len(self.twenty_six_period) == 26):
                self.twenty_six_period.pop(0)
        
        if (bid_prices[0] != 0):
            self.fifty_two_period.append(bid_prices[0])
            if (len(self.fifty_two_period) == 52):
                self.fifty_two_period.pop(0)


        if len(self.nine_period) > 0:
            
            self.conversion_line = (min(self.nine_period) + max(self.nine_period))/2
            self.base_line = (min(self.twenty_six_period) + max(self.twenty_six_period))/2
            self.span_A = (self.conversion_line + self.base_line)/2
            self.span_B = (min(self.fifty_two_period) + max(self.fifty_two_period))/2

            self.updateCounter += 1

            self.bassl.append(self.base_line)
            self.converl.append(self.conversion_line)
            self.Aspan.append(self.span_A)
            self.Bspan.append(self.span_B)
            self.y.append(self.updateCounter)


            print("conversion ", self.conversion_line)
            print("base ", self.base_line)
            print("span A ", self.span_A)
            print("span B ", self.span_B, self.updateCounter)

            if self.updateCounter % 100 == 0:
                w = []
                for i in range(len(self.Aspan)):
                    if self.Aspan[i] > self.Bspan[i]:
                        w.append(True)
                    else:
                        w.append(False)

                red = []
                for i in range(len(self.Aspan)):
                    if self.Aspan[i] < self.Bspan[i]:
                        red.append(True)
                    else:
                        red.append(False)

                plt.plot(self.y, self.Aspan, color='green')
                plt.plot(self.y, self.Bspan, color='red')
                plt.fill_between(self.y, self.Aspan, self.Bspan, where = w, color='green', alpha=0.3)
                plt.fill_between(self.y, self.Aspan, self.Bspan, where = red, color='red', alpha=0.3)
                #plt.plot(self.y, self.converl, color='orange')
                #plt.plot(self.y, self.bassl, color='blue')
                plt.title('Price VS Time', fontsize=14)
                plt.xlabel('Time', fontsize=14)
                plt.ylabel('Price', fontsize=14)
                plt.grid(True)
                plt.show()

    def on_order_book_update_message(self, instrument: int, sequence_number: int, ask_prices: List[int],
                                     ask_volumes: List[int], bid_prices: List[int], bid_volumes: List[int]) -> None:
        """Called periodically to report the status of an order book.

        The sequence number can be used to detect missed or out-of-order
        messages. The five best available ask (i.e. sell) and bid (i.e. buy)
        prices are reported along with the volume available at each of those
        price levels.
        """
        self.indicator(ask_prices, bid_prices)

        # if (span_A > span_B and conversion_line < base_line):
        #     self.send_insert_order(self.bid_id, Side.BUY, new_bid_price, LOT_SIZE, Lifespan.GOOD_FOR_DAY)
        # else:
        #     self.send_insert_order(self.ask_id, Side.SELL, new_ask_price, LOT_SIZE, Lifespan.GOOD_FOR_DAY)
        self.logger.info("received order book for instrument %d with sequence number %d", instrument,
                         sequence_number)
        if instrument == Instrument.FUTURE and self.conversion_line != 0 and self.base_line != 0 and self.span_A != 0 and self.span_B != 0:
            price_adjustment = - (self.position // LOT_SIZE) * TICK_SIZE_IN_CENTS
            new_bid_price = bid_prices[0] + price_adjustment if bid_prices[0] != 0 else 0
            new_ask_price = ask_prices[0] + price_adjustment if ask_prices[0] != 0 else 0

            if self.bid_id != 0 and new_bid_price not in (self.bid_price, 0):
                print("A")
                self.send_cancel_order(self.bid_id)
                self.bid_id = 0
            if self.ask_id != 0 and new_ask_price not in (self.ask_price, 0):
                print("B")
                self.send_cancel_order(self.ask_id)
                self.ask_id = 0

            if self.bid_id == 0 and new_bid_price != 0 and self.position < POSITION_LIMIT:
                print("D")
                print(self.span_A > self.span_B)
                print(self.conversion_line < self.base_line)
                if (self.span_A > self.span_B and self.conversion_line < self.base_line):
                    print("E")
                    self.bid_id = next(self.order_ids)
                    self.bid_price = new_bid_price
                    self.send_insert_order(self.bid_id, Side.BUY, new_bid_price, LOT_SIZE, Lifespan.GOOD_FOR_DAY)
                    self.bids.add(self.bid_id)

            if self.ask_id == 0 and new_ask_price != 0 and self.position > -POSITION_LIMIT:
                print("F")
                if (self.span_A > self.span_B and self.conversion_line > self.base_line):
                    print("G")
                    self.ask_id = next(self.order_ids)
                    self.ask_price = new_ask_price
                    self.send_insert_order(self.ask_id, Side.SELL, new_ask_price, LOT_SIZE, Lifespan.GOOD_FOR_DAY)
                    self.asks.add(self.ask_id)

    def on_order_filled_message(self, client_order_id: int, price: int, volume: int) -> None:
        """Called when when of your orders is filled, partially or fully.

        The price is the price at which the order was (partially) filled,
        which may be better than the order's limit price. The volume is
        the number of lots filled at that price.
        """
        self.logger.info("received order filled for order %d with price %d and volume %d", client_order_id,
                         price, volume)
        if client_order_id in self.bids:
            self.position += volume
            self.send_hedge_order(next(self.order_ids), Side.ASK, MINIMUM_BID, volume)
        elif client_order_id in self.asks:
            self.position -= volume
            self.send_hedge_order(next(self.order_ids), Side.BID,
                                  MAXIMUM_ASK//TICK_SIZE_IN_CENTS*TICK_SIZE_IN_CENTS, volume)

    def on_order_status_message(self, client_order_id: int, fill_volume: int, remaining_volume: int,
                                fees: int) -> None:
        """Called when the status of one of your orders changes.

        The fill_volume is the number of lots already traded, remaining_volume
        is the number of lots yet to be traded and fees is the total fees for
        this order. Remember that you pay fees for being a market taker, but
        you receive fees for being a market maker, so fees can be negative.

        If an order is cancelled its remaining volume will be zero.
        """
        self.logger.info("received order status for order %d with fill volume %d remaining %d and fees %d",
                         client_order_id, fill_volume, remaining_volume, fees)
        if remaining_volume == 0:
            if client_order_id == self.bid_id:
                self.bid_id = 0
            elif client_order_id == self.ask_id:
                self.ask_id = 0

            # It could be either a bid or an ask
            self.bids.discard(client_order_id)
            self.asks.discard(client_order_id)

    def on_trade_ticks_message(self, instrument: int, sequence_number: int, ask_prices: List[int],
                               ask_volumes: List[int], bid_prices: List[int], bid_volumes: List[int]) -> None:
        """Called periodically when there is trading activity on the market.

        The five best ask (i.e. sell) and bid (i.e. buy) prices at which there
        has been trading activity are reported along with the aggregated volume
        traded at each of those price levels.

        If there are less than five prices on a side, then zeros will appear at
        the end of both the prices and volumes arrays.
        """
        self.logger.info("received trade ticks for instrument %d with sequence number %d", instrument,
                         sequence_number)
