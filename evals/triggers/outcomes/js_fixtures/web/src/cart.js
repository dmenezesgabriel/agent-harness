"use strict";
// Cart totals and checkout for the web shop.

function orderTotal(cart) {
  let total = 0;
  for (const item of cart.items) {
    total += item.priceCents * item.qty;
  }
  return total;
}

function checkout(cart) {
  const total = orderTotal(cart);
  return { totalCents: total, lines: cart.items.length };
}

module.exports = { orderTotal, checkout };
